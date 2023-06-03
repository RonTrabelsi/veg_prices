""" Implement the endpoints for the app """

from datetime import datetime
from typing import Dict, List

from app.database import elastic_client, MARKET_PRICES_INDEX
from app.logic.plants_council_scraper import plants_council_scraper
from app.schemas import MarketPricesRequest
from app.utils import (DEFAULT_END_DATE, DEFAULT_START_DATE,
                       format_vegetable_prices_data)
from fastapi import APIRouter, status

from app.config import settings

market_prices_router = APIRouter()


@market_prices_router.post(
    "/load_prices",
    status_code=status.HTTP_201_CREATED,
    summary="Save the prices of the given vegetable in the given period",
    response_description="Amount of dates prices saved",
)
def load_market_prices(request: MarketPricesRequest) -> int:
    saved_dates_amount = plants_council_scraper.save_historic_prices(
        vegetable_name=request.vegetable_name,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return saved_dates_amount


@market_prices_router.get(
    "/scrap_prices",
    summary="Scrap prices of the given vegetable in the given period",
    response_description="Vegetable prices per date")
def scrap_market_prices(
    vegetable_name: str,
    start_date: datetime = DEFAULT_START_DATE,
    end_date: datetime = DEFAULT_END_DATE,
) -> List[Dict[datetime, Dict[str, float]]]:
    vegetable_prices_data = plants_council_scraper.scrap_historic_prices(
        vegetable_name=vegetable_name,
        start_date=start_date,
        end_date=end_date,
    )
    return format_vegetable_prices_data(vegetable_prices_data)


@market_prices_router.get(
    "/",
    summary="Get a period vegetable prices from the DB",
    response_description="Vegetable prices per date")
def get_market_prices(
    vegetable_name: str
) -> List[Dict[datetime, Dict[str, float]]]:
    matched_vegetable_query = {"match": {"vegetable_name": vegetable_name}}
    no_metadata_filter = "hits.hits._source"

    response = elastic_client.search(index=MARKET_PRICES_INDEX,
                                     query=matched_vegetable_query,
                                     filter_path=no_metadata_filter,
                                     size=settings.response_max_dates_data)
    vegetable_prices_data = [doc["_source"]
                             for doc in response["hits"]["hits"]]
    
    return format_vegetable_prices_data(vegetable_prices_data)
