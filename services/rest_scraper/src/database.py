""" General utils for the service """

from common.indices import HOLIDAYS_INDEX, MARKET_PRICES_INDEX, STATISTICS_INDEX, WEATHER_INDEX
from elasticsearch import Elasticsearch

from src.config import settings

__all__ = ["MARKET_PRICES_INDEX", "STATISTICS_INDEX", "WEATHER_INDEX", "HOLIDAYS_INDEX", "es_client"]

es_client = Elasticsearch(settings.es_url)
