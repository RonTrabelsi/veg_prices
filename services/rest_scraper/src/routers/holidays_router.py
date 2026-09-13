""" Implement the holidays calendar router (Hebcal) """

from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional

from common.holidays_client import HolidaysClient
from elasticsearch import NotFoundError
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


@holidays_router.get("/groups", summary="Holidays found in the calendar, as derived from the source")
def get_groups(tracked_only: bool = Query(True)) -> List[Dict[str, Any]]:
    aggs = {"groups": {"terms": {"field": "group.keyword", "size": 200},
                       "aggs": {"latest": {"top_hits": {"size": 1, "sort": [{"date": "desc"}],
                                                        "_source": ["group_name_he", "group_name_en", "subcat"]}}}}}
    query = {"term": {"is_tracked": True}} if tracked_only else {"match_all": {}}
    try:
        response = es_client.search(index=HOLIDAYS_INDEX, size=0, query=query, aggs=aggs)
    except NotFoundError:
        return []
    groups = []
    for bucket in response["aggregations"]["groups"]["buckets"]:
        latest = bucket["latest"]["hits"]["hits"][0]["_source"]
        groups.append({"group": bucket["key"], "name_he": latest["group_name_he"], "name_en": latest["group_name_en"],
                       "subcat": latest["subcat"], "days": bucket["doc_count"]})
    return sorted(groups, key=lambda group: group["name_en"])


@holidays_router.post("/load", status_code=status.HTTP_201_CREATED, summary="Load the holidays calendar")
def load_holidays(request: HolidaysLoadRequest) -> Dict[str, int]:
    return {"indexed": holidays_client.load_years(from_year=request.from_year, to_year=request.to_year)}


@holidays_router.get("/", summary="Holidays between dates")
def get_holidays(
    start_date: datetime = Query(datetime(2005, 1, 1)),
    end_date: Optional[datetime] = Query(None),
    group: Optional[str] = Query(None),
    tracked_only: bool = Query(False),
) -> List[Dict[str, Any]]:
    must: List[Dict[str, Any]] = [{"range": {"date": {"gte": start_date, "lte": end_date or datetime(2100, 1, 1)}}}]
    if group:
        must.append({"term": {"group": group}})
    if tracked_only:
        must.append({"term": {"is_tracked": True}})
    try:
        response = es_client.search(index=HOLIDAYS_INDEX, query={"bool": {"must": must}}, sort=[{"date": "asc"}],
                                    size=settings.max_es_query_size, filter_path="hits.hits._source")
    except NotFoundError:
        return []
    return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
