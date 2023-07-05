""" General consts for the app """

from datetime import datetime
from typing import Any, Dict, List

from src.core.plants_council_scraper import plants_council_scraper

# default start date for prices scraping
DEFAULT_START_DATE = datetime(2000, 1, 1)

# Default vegetables to load their market prices info
DEFAULT_MARKET_PRICES_VEGETABLES = [
    'עגבניות שרי אשכולות אכות מעולה',
    'פלפל אדום איכות מעולה',
    'בצל יבש',
]


def format_prices_data(
    prices_data: Dict[str, Any]
) -> List[Dict[datetime, Dict[str, float]]]:
    """ 
    :return: the given vegetable prices data formatted to prices per date 
    """
    prices_to_dates = [
        {
            date_data["date"]: {
                "regular_price": date_data["regular_price"],
                "special_price": date_data["special_price"],
            }
        }
        for date_data in prices_data
    ]

    return prices_to_dates


def format_series_data(
    series_data: Dict[str, Any]
) -> List[Dict[datetime, Any]]:
    value_to_dates = [
        {date_data["date"]: date_data["value"]}
        for date_data in series_data
    ]
    return value_to_dates


def load_default_market_prices() -> None:
    """ Scrap and save default vegetables prices """
    current_date = datetime.now()
    for vegetable in DEFAULT_MARKET_PRICES_VEGETABLES:
        plants_council_scraper.save_historic_prices(vegetable,
                                                    DEFAULT_START_DATE,
                                                    current_date)
