""" General consts for the app """

from datetime import datetime
from typing import Any, Dict, List

from app.logic.plants_council_scraper import plants_council_scraper

# default start date and end date for prices scraping
DEFAULT_START_DATE = datetime(2000, 1, 1)
DEFAULT_END_DATE = datetime.now()

# Default vegetables to load their market prices info
DEFAULT_MARKET_PRICES_VEGETABLES = [
    'עגבניות שרי אשכולות אכות מעולה',
    'פלפל אדום איכות מעולה',
    'בצל יבש',
]


def format_vegetable_prices_data(
    vegetable_prices_data: Dict[str, Any]
) -> List[Dict[datetime, Dict[str, float]]]:
    """ 
    :return: the given vegetable prices data formatted to prices per date 
    """
    prices_per_dates = [
        {
            date_data["date"]: {
                "regular_price": date_data["regular_price"],
                "special_price": date_data["special_price"],
            }
        }
        for date_data in vegetable_prices_data
    ]

    return prices_per_dates


def load_default_market_prices() -> None:
    """ Scrap and dave default vegetables prices """
    for vegetable in DEFAULT_MARKET_PRICES_VEGETABLES:
        plants_council_scraper.save_historic_prices(vegetable,
                                                    DEFAULT_START_DATE,
                                                    DEFAULT_END_DATE)