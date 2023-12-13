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

import json
import logging
import os.path

import numpy as np
import pandas as pd
from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.oauth2 import service_account
from pandas import DataFrame

from app import databases
from app.helpers import q_col_names, code_hierarchy
from app.logginglib import init_custom_logger

logger = logging.getLogger(__name__)
init_custom_logger(logger)

table_name = "wra_prod.responses"


def save_df_as_csv(campaign_code: str) -> DataFrame:
    """
    Only for exporting legacy campaigns to a CSV file.
    Get the dataframe from BigQuery, parse it, and save to a CSV file.

    :param campaign_code: The campaign code.
    """

    databases.create_databases(campaign_codes=[campaign_code])

    # BQ client
    bigquery_client = __get_bigquery_client()

    # Use BigQuery Storage client for faster results to dataframe
    bigquery_storage_client = __get_bigquery_storage_client()

    # Query
    query = __get_query(campaign_code=campaign_code)

    # Query job
    query_job = bigquery_client.query(query)

    # Results
    results = query_job.result()

    # Dataframe
    df_responses = results.to_dataframe(bqstorage_client=bigquery_storage_client)

    # Parse
    df_responses = __parse_df(campaign_code=campaign_code, df=df_responses)

    # Save to CSV file
    save_to_csv = True
    if save_to_csv:
        df_responses.to_csv(
            path_or_buf=os.path.join("data", f"{campaign_code}.csv"),
            index=False,
            header=True,
        )

    return df_responses


def __get_bigquery_client() -> bigquery.Client:
    """Get BigQuery client"""

    credentials = service_account.Credentials.from_service_account_file(
        filename="credentials.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )


def __get_bigquery_storage_client() -> bigquery_storage.BigQueryReadClient:
    """Get BigQuery storage client"""

    credentials = service_account.Credentials.from_service_account_file(
        filename="credentials.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return bigquery_storage.BigQueryReadClient(credentials=credentials)


def __get_query(campaign_code: str):
    """Get query"""

    # Set minimum age
    if campaign_code == "what_young_people_want":
        min_age = "10"
    elif campaign_code == "healthwellbeing":
        min_age = "0"
    else:
        min_age = "15"

    return f"""
        SELECT CASE WHEN response_english_text IS null THEN response_original_text ELSE CONCAT(response_original_text, ' (', response_english_text, ')')  END as q1_raw_response,
        response_original_lang as q1_original_language,
        response_nlu_category AS q1_canonical_code,
        response_lemmatized_text as q1_lemmatized,
        respondent_country_code as alpha2country,
        respondent_region_name as region,
        coalesce(cast(respondent_age as string),respondent_age_bucket) as age,
        REGEXP_REPLACE(REGEXP_REPLACE(INITCAP(respondent_gender), 'Twospirit', 'Two Spirit'), 'Unspecified', 'Prefer Not To Say') as gender,
        ingestion_time as ingestion_time,
        JSON_VALUE(respondent_additional_fields.data_source) as data_source,
        JSON_VALUE(respondent_additional_fields.profession) as profession,
        JSON_VALUE(respondent_additional_fields.setting) as setting,
        JSON_QUERY(respondent_additional_fields, '$.year') as response_year,
        respondent_additional_fields as additional_fields,
        FROM deft-stratum-290216.{table_name}
        WHERE campaign = '{campaign_code}'
        AND response_original_text is not null
        AND (respondent_age >= {min_age} OR respondent_age is null)
        AND respondent_country_code is not null
        AND response_nlu_category is not null
        AND response_lemmatized_text is not null
        AND LENGTH(response_original_text) > 3
       """


def __parse_df(campaign_code: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse df.
    """

    # Q codes
    if campaign_code == "giz":
        campaign_q_codes = ["q1", "q2"]
    else:
        campaign_q_codes = ["q1"]

    # Create additional q columns (q1_, q2_, etc.)
    df = __create_additional_q_columns(
        df=df, campaign_code=campaign_code, q_codes=campaign_q_codes
    )

    # Drop additional_fields
    df = df.drop("additional_fields", axis=1, errors="ignore")

    # Create province column
    if campaign_code == "wwwpakistan":
        df["province"] = df["region"].apply(lambda x: __extract_province_from_region(x))
    else:
        df["province"] = ""

    # Only keep ages 10-24 for what_young_people_want
    if campaign_code == "pmn01a":
        df["age"] = df["age"].apply(__filter_ages_10_to_24)
        df = df[df["age"].notna()]

    # What Young People Want has a hard coded rewrite of ENVIRONMENT merged with SAFETY.
    if campaign_code == "pmn01a":
        _map = {"ENVIRONMENT": "SAFETY"}
        df[q_col_names.get_canonical_code_col_name(q_code="q1")] = df[
            q_col_names.get_canonical_code_col_name(q_code="q1")
        ].apply(lambda x: _map.get(x, x))

    # Rename canonical_code OTHERQUESTIONABLE to NOTRELATED
    for q_code in campaign_q_codes:
        df[q_col_names.get_canonical_code_col_name(q_code=q_code)] = df[
            q_col_names.get_canonical_code_col_name(q_code=q_code)
        ].apply(lambda x: "NOTRELATED" if x == "OTHERQUESTIONABLE" else x)

    # Remove UNCODABLE responses
    for q_code in campaign_q_codes:
        df = df[
            ~df[q_col_names.get_canonical_code_col_name(q_code=q_code)].isin(
                ["UNCODABLE"]
            )
        ]

    # Get mapping to parent category
    mapping_to_parent_category = code_hierarchy.get_mapping_code_to_parent_category(
        campaign_code=campaign_code
    )

    # Add parent_category column
    for q_code in campaign_q_codes:
        df[q_col_names.get_parent_category_col_name(q_code=q_code)] = df[
            q_col_names.get_canonical_code_col_name(q_code=q_code)
        ].apply(
            lambda x: __get_parent_category(
                sub_categories=x, mapping_to_parent_category=mapping_to_parent_category
            )
        )

    return df


def __create_additional_q_columns(
    df: pd.DataFrame,
    campaign_code: str,
    q_codes: list[str],
) -> pd.DataFrame:
    """Create additional columns (q1_, q2_ etc.) from 'additional_fields'"""

    for q_code in [x for x in q_codes if x != "q1"]:
        # Create additional columns per question
        df[q_col_names.get_raw_response_col_name(q_code=q_code)] = ""
        df[q_col_names.get_lemmatized_col_name(q_code=q_code)] = ""
        df[q_col_names.get_canonical_code_col_name(q_code=q_code)] = ""
        df[q_col_names.get_original_language_col_name(q_code=q_code)] = ""

        # Fill additional columns per question
        df = df.apply(
            lambda x: __fill_additional_q_columns(
                row=x, campaign_code=campaign_code, q_code=q_code
            ),
            axis=1,
        )

    return df


def __fill_additional_q_columns(row: pd.Series, campaign_code: str, q_code: str):
    """Fill additional columns (q1_, q2_ etc.) from 'additional_fields'"""

    # 'additional_fields' can contain the response fields for q2, q3 etc.
    additional_fields = json.loads(row.get("additional_fields", "{}"))

    # If 'healthwellbeing' use the field 'issue' as the text at q2, other columns will use q1 by default
    if campaign_code == "healthwellbeing" and q_code == "q2":
        # Get issue
        issue = (
            str(additional_fields.get("issue")).capitalize()
            if additional_fields.get("issue")
            else ""
        )

        response_original_text = issue
        response_english_text = issue
        response_lemmatized_text = issue
        response_nlu_category = row.get("q1_canonical_code", "")
        response_original_lang = row.get("q1_original_language", "")
    else:
        response_original_text = additional_fields.get(
            f"{q_code}_response_original_text"
        )
        response_english_text = additional_fields.get(f"{q_code}_response_english_text")
        response_lemmatized_text = additional_fields.get(
            f"{q_code}_response_lemmatized_text"
        )
        response_nlu_category = additional_fields.get(f"{q_code}_response_nlu_category")
        response_original_lang = additional_fields.get(
            f"{q_code}_response_original_lang"
        )

    # For 'economic_empowerment_mexico' append 'original_text' and 'english_text'
    if campaign_code == "giz":
        if response_original_text and response_english_text:
            row[
                q_col_names.get_raw_response_col_name(q_code=q_code)
            ] = f"{response_original_text} ({response_english_text})"
        elif response_original_text:
            row[
                q_col_names.get_raw_response_col_name(q_code=q_code)
            ] = response_original_text
    else:
        row[
            q_col_names.get_raw_response_col_name(q_code=q_code)
        ] = response_original_text

    if response_lemmatized_text:
        row[
            q_col_names.get_lemmatized_col_name(q_code=q_code)
        ] = response_lemmatized_text
    if response_nlu_category:
        row[
            q_col_names.get_canonical_code_col_name(q_code=q_code)
        ] = response_nlu_category
    if response_original_lang:
        row[
            q_col_names.get_original_language_col_name(q_code=q_code)
        ] = response_original_lang

    return row


def __extract_province_from_region(region: str) -> str:
    """Extract province from region"""

    if not region:
        return ""

    region_name_split = region.split(",")
    if len(region_name_split) == 2:
        province = region_name_split[-1].strip()

        return province
    else:
        return ""


def __filter_ages_10_to_24(age: str) -> str | float:
    """Return age if between 10 and 24, else nan"""

    if isinstance(age, str):
        if age.isnumeric():
            age_int = int(age)
            if 10 <= age_int <= 24:
                return age

    return np.nan


def __get_parent_category(sub_categories: str, mapping_to_parent_category: dict) -> str:
    """Get parent category"""

    categories = [x.strip() for x in sub_categories.split("/") if x]
    parent_categories = [mapping_to_parent_category.get(x) for x in categories]

    if parent_categories:
        return "/".join(parent_categories)
    else:
        return ""
