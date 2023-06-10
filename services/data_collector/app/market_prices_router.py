""" Implement the endpoints for the app """

from datetime import datetime
from typing import Dict, List

from app.config import settings
from app.database import MARKET_PRICES_INDEX, elastic_client
from app.logic.plants_council_scraper import plants_council_scraper
from app.schemas import MarketPricesRequest
from app.utils import format_prices_data
from fastapi import APIRouter, Depends, HTTPException, status

market_prices_router = APIRouter()


@market_prices_router.post(
    "/load_prices",
    status_code=status.HTTP_201_CREATED,
    summary="Save the prices of the given vegetable in the given period",
)
def load_market_prices(request: MarketPricesRequest):
    plants_council_scraper.scrap_historic_prices(
        vegetable_name=request.vegetable_name,
        start_date=request.start_date,
        end_date=request.end_date,
        save=True,
        get_results=False
    )


@market_prices_router.get(
    "/scrap_prices",
    summary="Scrap prices of the given vegetable in the given period",
    response_description="Vegetable prices per date")
def scrap_market_prices(
    request: MarketPricesRequest = Depends()
) -> List[Dict[datetime, Dict[str, float]]]:
    prices_data = plants_council_scraper.scrap_historic_prices(
        vegetable_name=request.vegetable_name,
        start_date=request.start_date,
        end_date=request.end_date,
        save=False,
        get_results=True,
    )
    return format_prices_data(prices_data)


@market_prices_router.get(
    "/",
    summary="Get a period vegetable prices from the DB",
    response_description="Vegetable prices per date")
def get_market_prices(
    request: MarketPricesRequest = Depends()
) -> List[Dict[datetime, Dict[str, float]]]:
    matched_vegetable_query = {
        "bool": {
            "must": [
                {"match": {"vegetable_name": request.vegetable_name}},
                {"range": {"date": {"gte": request.start_date,
                                    "lte": request.end_date}}},
            ]
        }}
    no_metadata_filter = "hits.hits._source"

    response = elastic_client.search(index=MARKET_PRICES_INDEX,
                                     query=matched_vegetable_query,
                                     filter_path=no_metadata_filter,
                                     size=settings.max_prices_query_size)

    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No data available")

    prices_data = [doc["_source"] for doc in response["hits"]["hits"]]
    return format_prices_data(prices_data)
