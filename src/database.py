""" General utils for the service """

from elasticsearch import Elasticsearch

from src.config import settings

MARKET_PRICES_INDEX = "market_prices_index"
STATISTICAL_DATA_INDEX = "statistical_data_index"

indexes = [MARKET_PRICES_INDEX, STATISTICAL_DATA_INDEX]

elasticsearch_url = (f"{settings.elastic_protocol}://"
                     f"{settings.elastic_hostname}:"
                     f"{settings.elastic_port}")
elastic_client = Elasticsearch(elasticsearch_url)


def create_indexes() -> None:
    """ Create all indexes if them don't exist """
    for index in indexes:
        if not elastic_client.indices.exists(index=index):
            elastic_client.indices.create(index=index)
