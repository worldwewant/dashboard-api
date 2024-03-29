"""
MIT License

Copyright (c) 2023 World We Want. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

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

import logging
from datetime import date, datetime
from io import StringIO

import pandas as pd
import requests
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from app import crud
from app import databases
from app import http_exceptions
from app import utils
from app.api import dependencies
from app.core.settings import get_settings
from app.enums.legacy_campaign_code import LegacyCampaignCode
from app.logginglib import init_custom_logger
from app.schemas.campaign import Campaign
from app.schemas.campaign_request import CampaignRequest
from app.schemas.date_filter import DateFilter
from app.schemas.filter_options import FilterOptions
from app.services import azure_blob_storage_interactions
from app.services import google_cloud_storage_interactions
from app.services.api_cache import ApiCache
from app.services.campaign import CampaignService

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/campaigns")

api_cache = ApiCache()

settings = get_settings()


@router.post(
    path="/{campaign_code}",
    response_model=Campaign,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_campaign(
    campaign_req: CampaignRequest,
    _request: Request,
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    lang: str = Depends(dependencies.language_check),
    q_code: str = Depends(dependencies.q_code_check),
    response_year: str = Depends(dependencies.response_year_check),
):
    """
    Read campaign.
    """

    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Service
    campaign_service = CampaignService(
        campaign_code=campaign_code,
        response_year=response_year,
        language=lang,
        filter_1=filter_1,
        filter_2=filter_2,
    )

    # Campaign
    campaign = campaign_service.get_campaign(q_code=q_code)

    return campaign


@router.get(
    path="/{campaign_code}/filter-options",
    response_model=FilterOptions,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_filter_options(
    _request: Request,
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    lang: str = Depends(dependencies.language_check),
):
    """
    Read filter options for campaign.
    """

    # Service
    campaign_service = CampaignService(campaign_code=campaign_code, language=lang)

    # Filter options
    filter_options = campaign_service.get_filter_options()

    return filter_options


@router.get(
    path="/{campaign_code}/histogram-options",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_histogram_options(
    _request: Request,
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    lang: str = Depends(dependencies.language_check),
):
    """
    Read histogram options for campaign.
    """

    # Service
    campaign_service = CampaignService(campaign_code=campaign_code, language=lang)

    # Histogram options
    histogram_options = campaign_service.get_histogram_options()

    return histogram_options


@router.post(
    path="/{campaign_code}/data/public",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
def download_campaign_public_data(
    campaign_req: CampaignRequest,
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    response_year: str = Depends(dependencies.response_year_check),
):
    """
    Download campaign public data.
    This endpoint only works with legacy campaign healthwellbeing.
    """

    filter_1 = campaign_req.filter_1
    filter_2 = campaign_req.filter_2

    # Service
    campaign_service = CampaignService(
        campaign_code=campaign_code,
        response_year=response_year,
        language="en",
        filter_1=filter_1,
        filter_2=filter_2,
    )

    # Create unique filename code from campaign_code and filters by hashing
    unique_filename_code = ""
    if filter_1:
        unique_filename_code = unique_filename_code + utils.get_dict_hash_value(
            filter_1.dict()
        )
    if filter_2:
        unique_filename_code = unique_filename_code + utils.get_dict_hash_value(
            filter_2.dict()
        )
    if filter_1 or filter_2:
        unique_filename_code = (
            f"{utils.get_string_hash_value(campaign_code)}{unique_filename_code}"
        )

    # Get url and filename
    url, csv_filename = campaign_service.get_campaign_data_url_and_filename(
        cloud_service=settings.CLOUD_SERVICE, unique_filename_code=unique_filename_code
    )

    def iter_file():
        with requests.Session() as session:
            response = session.get(url=url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(1024 * 1024):
                yield chunk

    return StreamingResponse(
        content=iter_file(),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename={csv_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post(
    path="/{campaign_code}/data",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
def download_campaign_data(
    _request: Request,
    date_filter: DateFilter | None = None,
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    username: str = Depends(dependencies.verify_user),
):
    """
    Download campaign data.
    """

    # Get user
    users = databases.get_users_from_databases()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unknown user")

    # Check if user has access to campaign
    if campaign_code not in db_user.campaign_access:
        raise http_exceptions.UnauthorizedHTTPException(
            "User has no access to campaign"
        )

    # Service
    campaign_service = CampaignService(campaign_code=campaign_code)

    # Parse date
    date_format = "%Y-%m-%d"
    from_date: date | None = None
    to_date: date | None = None
    try:
        from_date = (
            datetime.strptime(date_filter.from_date, date_format).date()
            if date_filter and date_filter.from_date
            else None
        )
        to_date = (
            datetime.strptime(date_filter.to_date, date_format).date()
            if date_filter and date_filter.to_date
            else None
        )
    except ValueError as e:
        logger.warning(f"Could not parse date from date_filter: {str(e)}")

    # Azure
    if settings.CLOUD_SERVICE == "azure":
        # Cleanup
        azure_blob_storage_interactions.cleanup(
            container_name=settings.AZURE_STORAGE_CONTAINER_TMP_DATA
        )

    # Google
    elif settings.CLOUD_SERVICE == "google":
        # Cleanup
        google_cloud_storage_interactions.cleanup(
            bucket_name=settings.GOOGLE_CLOUD_STORAGE_BUCKET_TMP_DATA
        )

    # Get url and filename
    (
        url,
        csv_filename,
    ) = campaign_service.get_campaign_data_url_and_filename(
        cloud_service=settings.CLOUD_SERVICE, from_date=from_date, to_date=to_date
    )

    def iter_file():
        with requests.Session() as session:
            response = session.get(url=url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(1024 * 1024):
                yield chunk

    return StreamingResponse(
        content=iter_file(),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename={csv_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    path="/{campaign_code}/data/countries-breakdown",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def download_campaign_countries_breakdown(
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    _username: str = Depends(dependencies.verify_user),
):
    """
    Download campaign countries breakdown.
    """

    # CRUD
    campaign_crud = crud.Campaign(campaign_code=campaign_code)

    # Get dataframe
    df = campaign_crud.get_dataframe()

    # Countries breakdown
    df = pd.DataFrame({"count": df.groupby(["canonical_country"]).size()}).reset_index()

    # Sort
    df = df.sort_values(by="count", ascending=False)

    # Rename column
    df = df.rename(columns={"canonical_country": "country"})

    # To csv
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    return StreamingResponse(
        content=iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename=export_{campaign_code}_countries_breakdown.csv",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    path="/{campaign_code}/data/source-files-breakdown",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def download_campaign_source_files_breakdown(
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    _username: str = Depends(dependencies.verify_user),
):
    """
    Download campaign source files breakdown.
    """

    # CRUD
    campaign_crud = crud.Campaign(campaign_code=campaign_code)

    # Get dataframe
    df = campaign_crud.get_dataframe()

    # Source files breakdown
    df = pd.DataFrame({"count": df.groupby(["data_source"]).size()}).reset_index()

    # Sort
    df = df.sort_values(by="count", ascending=False)

    # To csv
    buffer = StringIO()
    df.to_csv(path_or_buf=buffer, index=False, header=True)

    return StreamingResponse(
        content=iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename=export_{campaign_code}_source_files_breakdown.csv",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
