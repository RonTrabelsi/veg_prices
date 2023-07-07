""" General utils for the service """

from elasticsearch import Elasticsearch

from src.config import settings

MARKET_PRICES_INDEX = "market_prices_index"
STATISTICS_INDEX = "statistics_index"

es_client = Elasticsearch(settings.es_url)
