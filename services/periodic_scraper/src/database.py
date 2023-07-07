""" General utils for the service """

from elasticsearch import Elasticsearch

from src.config import settings

MARKET_PRICES_INDEX = "market_prices_index"
es_client = Elasticsearch(settings.es_url)
