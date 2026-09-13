""" Implement market prices router """

from datetime import datetime, timedelta
from logging import getLogger
from time import time
from typing import Any, Dict, List, Tuple

from common.plants_council_scraper import PlantsCouncilScraper
from elasticsearch import NotFoundError
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
# An empty search returns every product the website lists; two weeks are enough to see them all
CATALOG_LOOKBACK_DAYS = 14
CATALOG_CACHE_SECONDS = 3600
_catalog_cache: Dict[int, Tuple[float, List[Dict[str, Any]]]] = {}


def indexed_vegetables() -> Dict[str, Dict[str, Any]]:
    """ :return: coverage of every vegetable already in the index, by name """
    aggs = {"vegetables": {"terms": {"field": "vegetable_name.keyword", "size": 500},
                           "aggs": {"first": {"min": {"field": "date"}}, "last": {"max": {"field": "date"}}}}}
    try:
        response = es_client.search(index=MARKET_PRICES_INDEX, size=0, aggs=aggs)
    except NotFoundError:
        return {}
    return {
        bucket["key"]: {"indexed_days": bucket["doc_count"], "data_from": bucket["first"]["value_as_string"][:10],
                        "data_to": bucket["last"]["value_as_string"][:10]}
        for bucket in response["aggregations"]["vegetables"]["buckets"]
    }


@market_prices_router.get("/catalog", summary="Every product on the source website, with its index coverage")
def get_catalog(
    days: int = Query(CATALOG_LOOKBACK_DAYS, ge=1, le=90),
    refresh: bool = Query(False, description="Bypass the hourly cache"),
) -> List[Dict[str, Any]]:
    cached = _catalog_cache.get(days)
    if cached and not refresh and time() - cached[0] < CATALOG_CACHE_SECONDS:
        return cached[1]

    end_date = datetime.now()
    rows = plants_council_scraper.scrap_historic_prices(
        vegetable_name="", start_date=end_date - timedelta(days=days), end_date=end_date, save=False, get_results=True)
    on_site: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        entry = on_site.setdefault(row["vegetable_name"], {"days_on_site": 0, "last_date": None})
        entry["days_on_site"] += 1
        if entry["last_date"] is None or row["date"] > entry["last_date"]:
            entry.update(last_date=row["date"], last_price=row["regular_price"],
                         last_special_price=row["special_price"])

    indexed = indexed_vegetables()
    catalog = []
    for name in sorted(set(on_site) | set(indexed)):
        site = on_site.get(name, {"days_on_site": 0, "last_date": None, "last_price": None, "last_special_price": None})
        coverage = indexed.get(name, {"indexed_days": 0, "data_from": None, "data_to": None})
        catalog.append({"name": name, **site, **coverage})
    _catalog_cache[days] = (time(), catalog)
    return catalog


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
def load_market_prices(request: MarketPricesRequest) -> Dict[str, Any]:
    """ Load the vegetable prices into the index. Runs to completion (a full history takes up to a minute) """
    prices = plants_council_scraper.scrap_historic_prices(
        vegetable_name=request.vegetable_name,
        start_date=request.start_date,
        end_date=request.end_date,
        save=True,
        get_results=True,
    )
    _catalog_cache.clear()
    return {"vegetable_name": request.vegetable_name, "scraped_days": len(prices),
            "products": sorted({row["vegetable_name"] for row in prices})}


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
