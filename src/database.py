""" General utils for the service """

from elasticsearch import Elasticsearch

from src.config import settings

MARKET_PRICES_INDEX = "market_prices_index"
STATISTICAL_DATA_INDEX = "statistical_data_index"

INDEXES = [MARKET_PRICES_INDEX, STATISTICAL_DATA_INDEX]

elasticsearch_url = (f"{settings.elastic_protocol}://"
                     f"{settings.elastic_hostname}:"
                     f"{settings.elastic_port}")
elastic_client = Elasticsearch(elasticsearch_url)
