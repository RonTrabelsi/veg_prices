""" General utils for the service """

from app.config import settings
from elasticsearch import Elasticsearch

MARKET_PRICES_INDEX = "market_prices_index"

ELASTICSEARCH_URL = f"{settings.elastic_protocol}://" \
                    f"{settings.elastic_hostname}:" \
                    f"{settings.elastic_port}"
elastic_client = Elasticsearch(ELASTICSEARCH_URL)


def create_market_prices_index() -> None:
    """ Create market prices index if it doesn't exist """
    if not elastic_client.indices.exists(index=MARKET_PRICES_INDEX):
        elastic_client.indices.create(index=MARKET_PRICES_INDEX)
