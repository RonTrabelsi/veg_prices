""" Implement the weather data router (Open-Meteo per growing region) """

from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional

from common.weather_client import WeatherClient
from common.weather_consts import GROWING_REGIONS
from fastapi import APIRouter, HTTPException, Query, status
from src.config import settings
from src.database import WEATHER_INDEX, es_client
from src.loggers import REST_SCRAPER_LOGGER_NAME
from src.schemas import WeatherLoadRequest

weather_client = WeatherClient(
    es_client=es_client,
    logger=getLogger(REST_SCRAPER_LOGGER_NAME),
    es_weather_index_name=WEATHER_INDEX,
)

weather_router = APIRouter()


def validate_regions(regions: Optional[List[str]]) -> List[str]:
    regions = regions or list(GROWING_REGIONS)
    unknown = [region for region in regions if region not in GROWING_REGIONS]
    if unknown:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown regions {unknown}")
    return regions


@weather_router.get("/regions", summary="Growing regions with weather data")
def get_regions() -> Dict[str, Dict[str, Any]]:
    return GROWING_REGIONS


@weather_router.post("/load", status_code=status.HTTP_201_CREATED, summary="Load weather history")
def load_weather(request: WeatherLoadRequest) -> Dict[str, int]:
    indexed = weather_client.load_history(
        regions=validate_regions(request.regions),
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return {"indexed": indexed}


@weather_router.post("/refresh", status_code=status.HTTP_201_CREATED,
                     summary="Refresh the last two weeks and the coming week")
def refresh_weather(regions: Optional[List[str]] = Query(None)) -> Dict[str, int]:
    return {"indexed": weather_client.load_recent(regions=validate_regions(regions))}


@weather_router.get("/", summary="Daily weather of a region")
def get_weather(
    region: str = Query(...),
    start_date: datetime = Query(datetime(2005, 1, 1)),
    end_date: Optional[datetime] = Query(None),
) -> List[Dict[str, Any]]:
    validate_regions([region])
    query = {"bool": {"must": [
        {"term": {"region": region}},
        {"range": {"date": {"gte": start_date, "lte": end_date or datetime.now()}}},
    ]}}
    response = es_client.search(index=WEATHER_INDEX, query=query, sort=[{"date": "asc"}],
                                size=settings.max_es_query_size, filter_path="hits.hits._source")
    return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
