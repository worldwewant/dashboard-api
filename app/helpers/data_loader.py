"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import copy
import json
import logging
import os

import pandas as pd

from app import constants, databases, q_codes_finder
from app import crud
from app import env
from app import global_variables
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.logginglib import init_custom_logger
from app.schemas.country import Country
from app.schemas.region import Region
from app.services import azure_blob_storage_interactions
from app.services import google_cloud_storage_interactions
from app.services import google_maps_interactions
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignService
from app.services.translations_cache import TranslationsCache

logger = logging.getLogger(__name__)
init_custom_logger(logger)


def load_campaign_data(campaign_code: str):
    """
    Load campaign data.

    :param campaign_code: The campaign code.
    """

    # Will create a tmp copy of the db to write campaign data to
    # If writing of the data succeeds, then the current db will be replaced with the tmp db at the end of this function
    # This is to make sure new data loads correctly into the db
    # If an error occurs while loading new data, then the current db stays as is and the error is logged
    db_tmp = copy.deepcopy(databases.get_campaign_db(campaign_code=campaign_code))

    # CRUD
    campaign_crud = crud.Campaign(campaign_code=campaign_code, db=db_tmp)

    # Get df
    df_responses = get_campaign_df(campaign_code=campaign_code)
    if df_responses is None:
        raise Exception(f"Could not load dataframe for campaign {campaign_code}.")

    # Columns
    columns = df_responses.columns.tolist()

    # Set q codes
    campaign_q_codes = q_codes_finder.find_in_df(df=df_responses)
    campaign_crud.set_q_codes(q_codes=campaign_q_codes)

    # Value 'prefer not to say' should always start with a capital letter
    if "setting" in columns:
        df_responses["setting"] = df_responses["setting"].apply(
            lambda x: x.title() if x and x.lower() == "prefer not to say" else x
        )
    if "gender" in columns:
        df_responses["gender"] = df_responses["gender"].apply(
            lambda x: x.title() if x and x.lower() == "prefer not to say" else x
        )
    if "age" in columns:
        df_responses["age"] = df_responses["age"].apply(
            lambda x: x.title() if x and x.lower() == "prefer not to say" else x
        )

    # Apply title
    if "setting" in columns:
        df_responses["setting"] = df_responses["setting"].apply(
            lambda x: x.title() if x else x
        )

    # Apply strip and upper
    if "alpha2country" in columns:
        df_responses["alpha2country"] = df_responses["alpha2country"].apply(
            lambda x: x.strip().upper() if x else x
        )

    # Apply strip
    if "setting" in columns:
        df_responses["setting"] = df_responses["setting"].apply(
            lambda x: x.strip() if x else x
        )
    if "region" in columns:
        df_responses["region"] = df_responses["region"].apply(
            lambda x: x.strip() if x else x
        )
    if "province" in columns:
        df_responses["province"] = df_responses["province"].apply(
            lambda x: x.strip() if x else x
        )
    if "age" in columns:
        df_responses["age"] = df_responses["age"].apply(lambda x: x.strip() if x else x)
    if "response_year" in columns:
        df_responses["response_year"] = df_responses["response_year"].apply(
            lambda x: x.strip() if x else x
        )

    # Add canonical_country column
    df_responses["canonical_country"] = df_responses["alpha2country"].map(
        lambda x: constants.COUNTRIES_DATA[x]["name"]
    )

    # Set ages
    ages = df_responses["age"].unique().tolist()
    ages = [age for age in ages if age]
    campaign_crud.set_ages(ages=ages)

    # Age bucket
    # Note: Campaigns wra03a and midwife already contain age as an age bucket
    if campaign_code == "wra03a" or campaign_code == "midwife":
        df_responses["age_bucket"] = df_responses["age"]
        df_responses["age_bucket_default"] = df_responses["age"]
        df_responses["age"] = ""
    else:
        # Range for age bucket might differ from campaign to campaign
        df_responses["age_bucket"] = df_responses["age"].apply(
            lambda x: get_age_bucket(age=x, campaign_code=campaign_code)
        )

        # Default age bucket, all campaigns will have the same range
        df_responses["age_bucket_default"] = df_responses["age"].apply(
            lambda x: get_age_bucket(age=x)
        )

    # Set age buckets
    age_buckets = df_responses["age_bucket"].unique().tolist()
    age_buckets = [age_bucket for age_bucket in age_buckets if age_bucket is not None]
    campaign_crud.set_age_buckets(age_buckets=age_buckets)

    # Set age buckets default
    age_buckets_default = df_responses["age_bucket_default"].unique().tolist()
    age_buckets_default = [x for x in age_buckets_default if x is not None]
    campaign_crud.set_age_buckets_default(age_buckets_default=age_buckets_default)

    # Set response years
    if "response_year" in columns:
        response_years = df_responses["response_year"].unique().tolist()
        campaign_crud.set_response_years(response_years=response_years)
    else:
        df_responses["response_year"] = ""

    # Create countries
    countries: dict[str, Country] = {}
    countries_alpha2_codes = df_responses[["alpha2country"]].drop_duplicates()
    for idx in range(len(countries_alpha2_codes)):
        alpha2_code = countries_alpha2_codes["alpha2country"].iloc[idx]
        country = constants.COUNTRIES_DATA.get(alpha2_code)
        countries[alpha2_code] = Country(
            alpha2_code=alpha2_code,
            name=country.get("name"),
            demonym=country.get("demonym"),
        )

    # Add regions and provinces to countries
    unique_canonical_country_region_province = df_responses[
        ["alpha2country", "region", "province"]
    ].drop_duplicates()
    for idx in range(len(unique_canonical_country_region_province)):
        alpha2_code = unique_canonical_country_region_province["alpha2country"].iloc[
            idx
        ]
        region = unique_canonical_country_region_province["region"].iloc[idx]
        province = unique_canonical_country_region_province["province"].iloc[idx]
        if region:
            country = countries.get(alpha2_code)
            if country and (region not in country.regions):
                country.regions.append(
                    Region(code=region, name=region, province=province)
                )

    # Set countries
    campaign_crud.set_countries(countries=countries)

    # Set genders
    genders = []
    df_responses["gender"] = df_responses["gender"].apply(
        lambda x: x.strip() if x else x
    )
    for gender in df_responses["gender"].value_counts().index:
        if gender:
            genders.append(gender)
    campaign_crud.set_genders(genders=genders)

    # Set living settings
    living_settings = []
    for living_setting in df_responses["setting"].value_counts().index:
        if living_setting:
            living_settings.append(living_setting)
    campaign_crud.set_living_settings(living_settings=living_settings)

    # Set professions
    professions = []
    for profession in df_responses["profession"].value_counts().index:
        professions.append(profession)
    campaign_crud.set_professions(professions=professions)

    # Set dataframe
    campaign_crud.set_dataframe(df=df_responses)

    # Set tmp db as current db
    databases.set_campaign_db(campaign_code=campaign_code, db=db_tmp)


def get_campaign_df(campaign_code: str) -> pd.DataFrame | None:
    """
    Get campaign dataframe.
    """

    # if env.ONLY_PMNCH and campaign_code == "pmn01a":
    #     # Get data from Azure Blob Storage
    #     mount_path: AzureBlobStorageContainerMountPath = "/pmnch_main"
    #     return pd.read_pickle(
    #         filepath_or_buffer=f"{mount_path}/what_young_people_want.pkl",
    #     )

    for campaign_config in CAMPAIGNS_CONFIG:
        if campaign_config["code"] == campaign_code:
            df = pd.read_csv(
                filepath_or_buffer=os.path.join("data", campaign_config["file"]),
                keep_default_na=False,
                dtype={"age": str, "response_year": str},
            )

            if "ingestion_time" in df.columns.tolist():
                df["ingestion_time"] = pd.to_datetime(df["ingestion_time"])

            return df


def get_age_bucket(age: str | int | None, campaign_code: str = None) -> str | None:
    """Convert age to an age bucket e.g. '30' to '25-34'"""

    if age is None:
        return age

    if isinstance(age, str):
        if age.isnumeric():
            age = int(age)
        else:
            return age  # Non-numeric e.g. 'Prefer not to say' or age value is already an age bucket

    if campaign_code == "healthwellbeing":
        if age >= 65:
            return "65+"
        if age >= 55:
            return "55-64"
        if age >= 45:
            return "45-54"
        if age >= 35:
            return "35-44"
        if age >= 25:
            return "25-34"
        if age >= 20:
            return "20-24"
        if age >= 15:
            return "15-19"
        if age >= 10:
            return "10-14"
        if age >= 0:
            return "< 10"
    else:
        if age >= 55:
            return "55+"
        if age >= 45:
            return "45-54"
        if age >= 35:
            return "35-44"
        if age >= 25:
            return "25-34"
        if age >= 20:
            return "20-24"
        if age >= 15:
            return "15-19"
        if age >= 10:
            return "10-14"
        if age >= 0:
            return "< 10"

    return "N/A"


def load_campaign_ngrams_unfiltered(campaign_code: str):
    """Load campaign ngrams unfiltered"""

    campaign_crud = crud.Campaign(campaign_code=campaign_code)
    campaign_service = CampaignService(campaign_code=campaign_code)

    df = campaign_crud.get_dataframe()

    # Q codes available in a campaign
    campaign_q_codes = campaign_crud.get_q_codes()

    for q_code in campaign_q_codes:
        (
            unigram_count_dict,
            bigram_count_dict,
            trigram_count_dict,
        ) = campaign_service.generate_ngrams(df=df, q_code=q_code)

        ngrams_unfiltered = {
            "unigram": unigram_count_dict,
            "bigram": bigram_count_dict,
            "trigram": trigram_count_dict,
        }

        campaign_crud.set_ngrams_unfiltered(
            ngrams_unfiltered=ngrams_unfiltered, q_code=q_code
        )


def load_initial_data():
    """Load initial data"""

    global_variables.is_loading_data = True

    try:
        # Load data
        load_campaigns_data()
        load_region_coordinates()
        load_translations_cache()
    except (Exception,) as e:
        logger.error(f"An error occurred while loading initial data: {str(e)}")

    global_variables.is_loading_data = False


def reload_data(
    clear_api_cache: bool,
    clear_google_cloud_storage_bucket: bool,
    clear_azure_blob_storage_container,
):
    """Reload data"""

    if global_variables.is_loading_data:
        return

    global_variables.is_loading_data = True

    try:
        # Reload data
        load_campaigns_data()
        load_region_coordinates()

        # Clear the API cache
        if clear_api_cache:
            ApiCache().clear_cache()

        # Clear bucket
        if clear_google_cloud_storage_bucket and not env.ONLY_PMNCH:
            google_cloud_storage_interactions.clear_bucket()

        # Clear container
        if clear_azure_blob_storage_container and env.ONLY_PMNCH:
            azure_blob_storage_interactions.clear_container(container_name="csv")
    except (Exception,) as e:
        logger.error(f"An error occurred while reloading data: {str(e)}")

    global_variables.is_loading_data = False


def load_campaigns_data():
    """Load campaigns data"""

    for campaign_config in CAMPAIGNS_CONFIG:
        campaign_config_code = campaign_config["code"]

        # Only load data for what_young_people_want
        if env.ONLY_PMNCH:
            if campaign_config_code != "pmn01a":
                continue

        print(f"INFO:\t  Loading data for campaign {campaign_config_code}...")

        try:
            load_campaign_data(campaign_code=campaign_config_code)
            load_campaign_ngrams_unfiltered(campaign_code=campaign_config_code)
            ApiCache().clear_cache()
        except (Exception,):
            logger.exception(
                f"""Error loading data for campaign {campaign_config_code}"""
            )

    print(f"INFO:\t  Loading campaigns data completed.")


def load_translations_cache():
    """Load translations cache"""

    print("INFO:\t  Loading translations cache...")

    TranslationsCache().load()

    print("INFO:\t  Loading translations cache completed.")


def load_region_coordinates():
    """Load region coordinates"""

    print(f"INFO:\t  Loading region coordinates...")

    region_coordinates_json = "region_coordinates.json"
    new_coordinates_added = False

    if global_variables.region_coordinates:
        coordinates = global_variables.region_coordinates
    else:
        with open(region_coordinates_json, "r") as file:
            coordinates: dict = json.loads(file.read())

    # Get new region coordinates (if coordinate is not in region_coordinates.json)
    focused_on_country_campaigns_codes = []
    for campaign_code in [x["code"] for x in CAMPAIGNS_CONFIG]:
        if campaign_code == "giz" or campaign_code == "wwwpakistan":
            focused_on_country_campaigns_codes.append(campaign_code)

    for campaign_code in focused_on_country_campaigns_codes:
        campaign_crud = crud.Campaign(campaign_code=campaign_code)
        countries = campaign_crud.get_countries_list()

        if not countries:
            continue

        country_alpha2_code = countries[0].alpha2_code
        country_name = countries[0].name
        country_regions = countries[0].regions

        locations = [
            {
                "country_alpha2_code": country_alpha2_code,
                "country_name": country_name,
                "location": region.name,
            }
            for region in country_regions
        ]
        for location in locations:
            location_country_alpha2_code = location["country_alpha2_code"]
            location_country_name = location["country_name"]
            location_name = location["location"]

            # If coordinate already exists, continue
            country_coordinates = coordinates.get(location_country_alpha2_code)
            if country_coordinates and location_name in country_coordinates.keys():
                continue

            # Get coordinate
            coordinate = google_maps_interactions.get_coordinate(
                location=f"{location_country_name}, {location_name}"
            )

            # Add coordinate to coordinates
            if not coordinates.get(location_country_alpha2_code):
                coordinates[location_country_alpha2_code] = {}
            coordinates[location_country_alpha2_code][location_name] = coordinate

            if not new_coordinates_added:
                new_coordinates_added = True

    # Save region coordinates (Only in development environment)
    if env.STAGE == "dev" and new_coordinates_added:
        with open(region_coordinates_json, "w") as file:
            file.write(json.dumps(coordinates, indent=2))

    global_variables.region_coordinates = coordinates

    print(f"INFO:\t  Loading region coordinates completed.")