from app.config import get_campaign_config


def get_unique_countries(campaign: str) -> list[str]:
    """Get unique countries"""

    config = get_campaign_config(campaign)
    countries_list = config.countries_list

    unique_countries = []
    for alpha3code, country_name, demonym in countries_list:
        unique_countries.append(country_name)

    return unique_countries


def get_country_regions(campaign: str, country: str) -> list[str]:
    """Get country regions"""

    config = get_campaign_config(campaign=campaign)

    regions = config.country_to_regions.get(country)
    if regions:
        return regions

    return []
