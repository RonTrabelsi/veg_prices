""" Implement market prices router """

from datetime import datetime, timedelta
from logging import getLogger
from typing import Dict, List

from common.plants_council_scraper import PlantsCouncilScraper
from fastapi import APIRouter, Depends, HTTPException, status
from src.config import settings
from src.database import MARKET_PRICES_INDEX, es_client
from src.loggers import REST_SCRAPER_LOGGER_NAME
from src.schemas import MarketPricesRequest
from src.utils import format_prices_data

plants_council_scraper = PlantsCouncilScraper(
    es_client=es_client,
    logger=getLogger(REST_SCRAPER_LOGGER_NAME),
    es_prices_index_name=MARKET_PRICES_INDEX,
)

market_prices_router = APIRouter()

# Days of prices scanned when discovering product names
PRODUCTS_LOOKBACK_DAYS = 45


@market_prices_router.get("/products", summary="Discover product names on the source website")
def discover_products(query: str) -> List[str]:
    """
    The website search matches by substring, so a partial name (e.g. "עגבני") returns every product
    containing it. :return: the exact product names found for the given query
    """
    end_date = datetime.now()
    rows = plants_council_scraper.scrap_prices_page(
        vegetable_name=query,
        start_date=end_date - timedelta(days=PRODUCTS_LOOKBACK_DAYS),
        end_date=end_date,
        page_number=1,
    )
    return sorted({row["vegetable_name"] for row in rows})


@market_prices_router.post("/load_prices", status_code=status.HTTP_201_CREATED)
def load_market_prices(request: MarketPricesRequest):
    plants_council_scraper.scrap_historic_prices(
        vegetable_name=request.vegetable_name,
        start_date=request.start_date,
        end_date=request.end_date,
        save=True,
        get_results=False
    )


@market_prices_router.get("/scrap_prices")
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


@market_prices_router.get("/")
def get_market_prices(
    request: MarketPricesRequest = Depends()
) -> List[Dict[datetime, Dict[str, float]]]:
    matched_vegetable_prices_query = {
        "bool": {
            "must": [
                {"match": {"vegetable_name": request.vegetable_name}},
                {"range": {"date": {"gte": request.start_date,
                                    "lte": request.end_date}}},
            ]
        }}
    no_metadata_filter = "hits.hits._source"

    response = es_client.search(index=MARKET_PRICES_INDEX,
                                query=matched_vegetable_prices_query,
                                filter_path=no_metadata_filter,
                                size=settings.max_es_query_size)

    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No data available")

    prices_data = [doc["_source"] for doc in response["hits"]["hits"]]
    return format_prices_data(prices_data)
