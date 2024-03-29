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

import copy
import logging

from fastapi import APIRouter, status, Depends, Request

from app.api import dependencies
from app.core.settings import get_settings
from app.helpers.campaigns_config_loader import CAMPAIGNS_CONFIG
from app.http_exceptions import ResourceNotFoundHTTPException
from app.logginglib import init_custom_logger
from app.schemas.campaign_config import CampaignConfigResponse, CampaignConfigInternal
from app.services.api_cache import ApiCache
from app.services.translator import Translator

settings = get_settings()

router = APIRouter(prefix="/configurations")

api_cache = ApiCache()
logger = logging.getLogger(__name__)
init_custom_logger(logger)


@router.get(
    path="",
    response_model=list[CampaignConfigResponse],
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_campaigns_configurations(
    _request: Request, lang: str = Depends(dependencies.language_check)
):
    """
    Read campaigns configurations.
    """

    configurations: list[CampaignConfigResponse | CampaignConfigInternal] = [
        x for x in CAMPAIGNS_CONFIG.values()
    ]
    if configurations:
        configurations = copy.deepcopy(configurations)

        # Translate
        if settings.TRANSLATIONS_ENABLED and lang != "en":
            try:
                translator = Translator(
                    target_language=lang, cloud_service=settings.CLOUD_SERVICE
                )
                e = translator.extract_text
                t = translator.translate_text

                # Extract
                for configuration in configurations:
                    configuration.campaign_title = e(configuration.campaign_title)
                    configuration.campaign_subtext = e(configuration.campaign_subtext)
                    configuration.site_title = e(configuration.site_title)
                    configuration.site_description = e(configuration.site_description)
                    configuration.respondent_noun_singular = e(
                        configuration.respondent_noun_singular
                    )
                    configuration.respondent_noun_plural = e(
                        configuration.respondent_noun_plural
                    )

                translator.translate_extracted_texts()

                # Apply translations
                for configuration in configurations:
                    configuration.campaign_title = t(configuration.campaign_title)
                    configuration.campaign_subtext = t(configuration.campaign_subtext)
                    configuration.site_title = t(configuration.site_title)
                    configuration.site_description = t(configuration.site_description)
                    configuration.respondent_noun_singular = t(
                        configuration.respondent_noun_singular
                    )
                    configuration.respondent_noun_plural = t(
                        configuration.respondent_noun_plural
                    )
            except (Exception,) as e:
                logger.warning(
                    f"An error occurred during translation of campaign config: {str(e)}"
                )

        return configurations

    return []


@router.get(
    path="/{campaign_code}",
    response_model=CampaignConfigResponse,
    status_code=status.HTTP_200_OK,
)
@api_cache.cache_response
def read_campaign_configuration(
    _request: Request,
    campaign_code: str = Depends(dependencies.campaign_code_exists_check),
    lang: str = Depends(dependencies.language_check),
):
    """
    Read campaign configuration.
    """

    configuration = CAMPAIGNS_CONFIG.get(campaign_code)
    if configuration:
        configuration = copy.deepcopy(configuration)
        # Translate
        if settings.TRANSLATIONS_ENABLED and lang != "en":
            try:
                translator = Translator(
                    target_language=lang, cloud_service=settings.CLOUD_SERVICE
                )
                e = translator.extract_text
                t = translator.translate_text

                # Extract
                configuration.campaign_title = e(configuration.campaign_title)
                configuration.campaign_subtext = e(configuration.campaign_subtext)
                configuration.site_title = e(configuration.site_title)
                configuration.site_description = e(configuration.site_description)
                configuration.respondent_noun_singular = e(
                    configuration.respondent_noun_singular
                )
                configuration.respondent_noun_plural = e(
                    configuration.respondent_noun_plural
                )

                translator.translate_extracted_texts()

                # Apply translations
                configuration.campaign_title = t(configuration.campaign_title)
                configuration.campaign_subtext = t(configuration.campaign_subtext)
                configuration.site_title = t(configuration.site_title)
                configuration.site_description = t(configuration.site_description)
                configuration.respondent_noun_singular = t(
                    configuration.respondent_noun_singular
                )
                configuration.respondent_noun_plural = t(
                    configuration.respondent_noun_plural
                )
            except (Exception,) as e:
                logger.warning(
                    f"An error occurred during translation of campaign config: {str(e)}"
                )

        return configuration

    raise ResourceNotFoundHTTPException("Campaign configuration not found.")
