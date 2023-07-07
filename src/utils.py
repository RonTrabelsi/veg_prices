""" General consts for the app """

from datetime import datetime
from typing import Any, Dict, List

from src.database import INDEXES, elastic_client

# default start date for prices scraping
DEFAULT_START_DATE = datetime(2000, 1, 1)


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
    """ Format the given data to a date to value format """
    value_to_dates = [
        {date_data["date"]: date_data["value"]}
        for date_data in series_data
    ]
    return value_to_dates


def create_indexes() -> None:
    """ Create elasticsearch indexes """
    for index in INDEXES:
        if not elastic_client.indices.exists(index=index):
            elastic_client.indices.create(index=index)
