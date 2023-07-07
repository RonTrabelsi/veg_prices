""" Implement router of statistical data from CBS API """

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from src.config import settings
from src.core.cbs_api_client import CbsApiClient
from src.database import STATISTICAL_DATA_INDEX, elastic_client
from src.schemas import StatisticalDataRequest
from src.utils import format_series_data

cbs_api_client = CbsApiClient(elastic_client=elastic_client)

statistical_data_router = APIRouter()


@statistical_data_router.post("/load_data", status_code=status.HTTP_201_CREATED)
def load_data(request: StatisticalDataRequest):
    cbs_api_client.collect_data(
        series_id=request.series_id,
        start_date=request.start_date,
        end_date=request.end_date,
        save=True,
        get_results=False
    )


@statistical_data_router.get("/fetch_data")
def fetch_statistical_data(
    request: StatisticalDataRequest = Depends()
) -> List[Dict[datetime, Any]]:
    series_data = cbs_api_client.collect_data(
        series_id=request.series_id,
        start_date=request.start_date,
        end_date=request.end_date,
        save=False,
        get_results=True,
    )
    return format_series_data(series_data)


@statistical_data_router.get("/")
def get_statistical_data(
    request: StatisticalDataRequest = Depends()
) -> List[Dict[datetime, Any]]:
    matched_series_data_query = {
        "bool": {
            "must": [
                {"match": {"series_id": request.series_id}},
                {"range": {"date": {"gte": request.start_date,
                                    "lte": request.end_date}}},
            ]
        }}
    no_metadata_filter = "hits.hits._source"

    response = elastic_client.search(index=STATISTICAL_DATA_INDEX,
                                     query=matched_series_data_query,
                                     filter_path=no_metadata_filter,
                                     size=settings.max_elasticsearch_query_size)

    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No data available")

    series_data = [doc["_source"] for doc in response["hits"]["hits"]]
    return format_series_data(series_data)


@statistical_data_router.get(
    "/get_series",
    summary="Get available data series",
    response_description="List of all available series is to name"
)
def get_series() -> Dict[str, str]:
    """ :return: all available series from DB """
    return {"a": "b"}
# TODO: Implement it using mongo


@statistical_data_router.post(
    "/register_series",
    summary="Register new list of data series",
)
def get_series() -> None:
    """ :return: all available series from DB """
    return {"a": "b"}
# TODO: Implement it using mongo
