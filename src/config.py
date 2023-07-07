""" Environment variables settings """

from pydantic import BaseSettings


class Settings(BaseSettings):
    """ Environment variables configuration """
    debug: bool

    elastic_hostname: str
    elastic_port: int
    elastic_protocol: str

    max_elasticsearch_query_size: int


settings: Settings = Settings()  # type: ignore
