""" Implement the decision analytics router used by the farmer web app """

from logging import getLogger
from typing import Any, Dict, List, Optional

from common.weather_consts import GROWING_REGIONS, PRIMARY_REGION
from fastapi import APIRouter, HTTPException, Query, status
from src.analytics import Analytics, InsufficientDataError, clean
from src.database import HOLIDAYS_INDEX, MARKET_PRICES_INDEX, WEATHER_INDEX, es_client
from src.loggers import REST_SCRAPER_LOGGER_NAME

# Cherry tomatoes: ~75 days from transplant to first harvest, ~30 days of picking
DEFAULT_DAYS_TO_HARVEST = 75
DEFAULT_HARVEST_WINDOW_DAYS = 30
DEFAULT_HISTORY_DAYS = 400

analytics = Analytics(
    es_client=es_client,
    logger=getLogger(REST_SCRAPER_LOGGER_NAME),
    prices_index=MARKET_PRICES_INDEX,
    weather_index=WEATHER_INDEX,
    holidays_index=HOLIDAYS_INDEX,
    primary_region=PRIMARY_REGION,
)

analytics_router = APIRouter()


def run(block, *args, **kwargs) -> Dict[str, Any]:
    """ Run an analytics block, mapping missing data to a client error """
    try:
        return clean(block(*args, **kwargs))
    except InsufficientDataError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


def region_or_400(region: Optional[str]) -> str:
    region = region or PRIMARY_REGION
    if region not in GROWING_REGIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown region {region}")
    return region


@analytics_router.get("/vegetables", summary="Vegetables with data and their coverage")
def list_vegetables() -> List[Dict[str, Any]]:
    return clean(analytics.list_vegetables())


@analytics_router.get("/dashboard", summary="Everything the farmer app renders, in one call")
def dashboard(
    vegetable: str = Query(..., description="Exact vegetable name as indexed"),
    days_to_harvest: int = Query(DEFAULT_DAYS_TO_HARVEST, ge=1, le=365),
    harvest_window_days: int = Query(DEFAULT_HARVEST_WINDOW_DAYS, ge=1, le=180),
    history_days: int = Query(DEFAULT_HISTORY_DAYS, ge=30, le=4000),
    region: Optional[str] = Query(None),
) -> Dict[str, Any]:
    return run(analytics.dashboard, vegetable, days_to_harvest, harvest_window_days, history_days,
               region_or_400(region))


@analytics_router.get("/overview")
def overview(vegetable: str) -> Dict[str, Any]:
    base = analytics_base(vegetable)
    return run(analytics.overview, base["prices"], base["series"], base["norm"], base["level"])


@analytics_router.get("/seasonality")
def seasonality(vegetable: str) -> Dict[str, Any]:
    base = analytics_base(vegetable)
    return run(analytics.seasonality, base["series"])


@analytics_router.get("/holidays")
def holidays(vegetable: str) -> Dict[str, Any]:
    base = analytics_base(vegetable)
    return run(analytics.holiday_effects, base["series"], base["holidays"])


@analytics_router.get("/forecast")
def forecast(vegetable: str, region: Optional[str] = Query(None)) -> Dict[str, Any]:
    base = analytics_base(vegetable)
    weather = analytics.weather_signal(base["series"], region_or_400(region))
    occurrences = analytics.holiday_occurrences(base["holidays"])
    return run(analytics.forecast, base["prices"], base["series"], base["norm"], base["level"], occurrences, weather)


@analytics_router.get("/history")
def history(vegetable: str, days: int = Query(DEFAULT_HISTORY_DAYS, ge=30, le=4000)) -> Dict[str, Any]:
    base = analytics_base(vegetable)
    return run(analytics.history, base["prices"], base["series"], base["norm"], base["level"], base["holidays"],
               days)


@analytics_router.get("/planting")
def planting(
    vegetable: str,
    days_to_harvest: int = Query(DEFAULT_DAYS_TO_HARVEST, ge=1, le=365),
    harvest_window_days: int = Query(DEFAULT_HARVEST_WINDOW_DAYS, ge=1, le=180),
) -> Dict[str, Any]:
    base = analytics_base(vegetable)
    return run(analytics.planting, base["series"], base["norm"], base["level"], days_to_harvest,
               harvest_window_days)


@analytics_router.get("/weather-signal")
def weather_signal(vegetable: str, region: Optional[str] = Query(None)) -> Optional[Dict[str, Any]]:
    base = analytics_base(vegetable)
    return clean(analytics.weather_signal(base["series"], region_or_400(region)))


def analytics_base(vegetable: str) -> Dict[str, Any]:
    """ :return: the cached base series of the vegetable, or a client error when it lacks history """
    try:
        return analytics.base(vegetable)
    except InsufficientDataError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
