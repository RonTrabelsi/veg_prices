""" Implement the holidays calendar router (Hebcal) """

from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional

from common.holidays_client import HolidaysClient
from common.holidays_consts import GROUP_NAMES_HE
from fastapi import APIRouter, Query, status
from src.config import settings
from src.database import HOLIDAYS_INDEX, es_client
from src.loggers import REST_SCRAPER_LOGGER_NAME
from src.schemas import HolidaysLoadRequest

holidays_client = HolidaysClient(
    es_client=es_client,
    logger=getLogger(REST_SCRAPER_LOGGER_NAME),
    es_holidays_index_name=HOLIDAYS_INDEX,
)

holidays_router = APIRouter()


@holidays_router.get("/groups", summary="Tracked holiday groups")
def get_groups() -> Dict[str, str]:
    return GROUP_NAMES_HE


@holidays_router.post("/load", status_code=status.HTTP_201_CREATED, summary="Load the holidays calendar")
def load_holidays(request: HolidaysLoadRequest) -> Dict[str, int]:
    return {"indexed": holidays_client.load_years(from_year=request.from_year, to_year=request.to_year)}


@holidays_router.get("/", summary="Holidays between dates")
def get_holidays(
    start_date: datetime = Query(datetime(2005, 1, 1)),
    end_date: Optional[datetime] = Query(None),
    group: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    must: List[Dict[str, Any]] = [{"range": {"date": {"gte": start_date, "lte": end_date or datetime(2100, 1, 1)}}}]
    if group:
        must.append({"term": {"group": group}})
    response = es_client.search(index=HOLIDAYS_INDEX, query={"bool": {"must": must}}, sort=[{"date": "asc"}],
                                size=settings.max_es_query_size, filter_path="hits.hits._source")
    return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
