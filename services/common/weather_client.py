""" Fetch daily weather per growing region from Open-Meteo and index it to elasticsearch """

from datetime import datetime, timedelta
from logging import Logger
from typing import Any, Dict, Iterable, List, Optional

from elasticsearch import Elasticsearch
from requests import Session

from .weather_consts import (COLD_STRESS_TMIN, DAILY_VARIABLES, DEFAULT_START_DATE, GROWING_REGIONS,
                             HEAT_STRESS_TMAX, OPEN_METEO_ARCHIVE_URL, OPEN_METEO_FORECAST_URL,
                             REFRESH_FORECAST_DAYS, REFRESH_PAST_DAYS, REQUEST_DATE_FORMAT, SOURCE_ARCHIVE,
                             SOURCE_FORECAST, TIMEZONE)


class WeatherClient:
    def __init__(self, es_client: Elasticsearch, logger: Logger, es_weather_index_name: str) -> None:
        self.session = Session()
        self.logger = logger
        self.es_client = es_client
        self.es_weather_index_name = es_weather_index_name

    @staticmethod
    def build_docs(region: str, daily: Dict[str, List[Any]], source: str) -> List[Dict[str, Any]]:
        """ :return: one document per day from an Open-Meteo 'daily' block, skipping days without data """
        region_name = GROWING_REGIONS[region]["name_he"]
        docs = []
        for day, tmax, tmin, rain in zip(daily["time"], daily["temperature_2m_max"],
                                         daily["temperature_2m_min"], daily["precipitation_sum"]):
            if tmax is None or tmin is None:
                continue
            docs.append({
                "region": region,
                "region_name": region_name,
                "date": datetime.strptime(day, REQUEST_DATE_FORMAT),
                "tmax": tmax,
                "tmin": tmin,
                "rain_mm": rain or 0.0,
                "heat_stress": tmax >= HEAT_STRESS_TMAX,
                "cold_stress": tmin <= COLD_STRESS_TMIN,
                "source": source,
            })
        return docs

    def fetch_archive(self, region: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """ Fetch historical daily weather of the region between the given dates """
        params = {
            "latitude": GROWING_REGIONS[region]["latitude"],
            "longitude": GROWING_REGIONS[region]["longitude"],
            "start_date": start_date.strftime(REQUEST_DATE_FORMAT),
            "end_date": end_date.strftime(REQUEST_DATE_FORMAT),
            "daily": DAILY_VARIABLES,
            "timezone": TIMEZONE,
        }
        response = self.session.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=120)
        response.raise_for_status()
        return self.build_docs(region, response.json()["daily"], SOURCE_ARCHIVE)

    def fetch_recent(self, region: str, past_days: int = REFRESH_PAST_DAYS,
                     forecast_days: int = REFRESH_FORECAST_DAYS) -> List[Dict[str, Any]]:
        """ Fetch the last days (measured) and the coming days (forecast) of the region """
        params = {
            "latitude": GROWING_REGIONS[region]["latitude"],
            "longitude": GROWING_REGIONS[region]["longitude"],
            "past_days": past_days,
            "forecast_days": forecast_days,
            "daily": DAILY_VARIABLES,
            "timezone": TIMEZONE,
        }
        response = self.session.get(OPEN_METEO_FORECAST_URL, params=params, timeout=60)
        response.raise_for_status()
        docs = self.build_docs(region, response.json()["daily"], SOURCE_FORECAST)
        # days up to yesterday are measurements, not forecast
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for doc in docs:
            if doc["date"] < today:
                doc["source"] = SOURCE_ARCHIVE
        return docs

    def load_history(self, regions: Optional[Iterable[str]] = None, start_date: datetime = DEFAULT_START_DATE,
                     end_date: Optional[datetime] = None) -> int:
        """ Load the full weather history of the given regions. :return: number of indexed days """
        end_date = end_date or datetime.now()
        indexed = 0
        for region in regions or GROWING_REGIONS:
            self.logger.info(f"Loading weather history of {region} between {start_date:%d/%m/%Y} and {end_date:%d/%m/%Y}")
            docs = self.fetch_archive(region, start_date, end_date)
            indexed += self.index_docs(docs)
            self.logger.info(f"Indexed {len(docs)} weather days of {region}")
        return indexed

    def load_recent(self, regions: Optional[Iterable[str]] = None) -> int:
        """ Refresh the last two weeks and the coming week. :return: number of indexed days """
        indexed = 0
        for region in regions or GROWING_REGIONS:
            docs = self.fetch_recent(region)
            indexed += self.index_docs(docs)
            self.logger.info(f"Refreshed {len(docs)} recent weather days of {region}")
        return indexed

    def index_docs(self, docs: List[Dict[str, Any]]) -> int:
        """ Upsert the given weather documents. :return: number of upserted documents """
        upserted = 0
        for doc in docs:
            doc_id = f"{doc['region']}_{doc['date']:%Y-%m-%d}"
            response = self.es_client.update(index=self.es_weather_index_name, id=doc_id,
                                             body={"doc": doc, "doc_as_upsert": True}, retry_on_conflict=3)
            if response["result"] in ("created", "updated"):
                upserted += 1
        return upserted
