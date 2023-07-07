""" Environment variables settings """

from pydantic import BaseSettings


class Settings(BaseSettings):
    """ Environment variables configuration """
    debug: bool

    es_url: str
    max_es_query_size: int


settings: Settings = Settings()  # type: ignore
