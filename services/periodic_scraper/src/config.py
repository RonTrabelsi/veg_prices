""" Environment variables settings """

from pydantic import BaseSettings


class Settings(BaseSettings):
    """ Environment variables configuration """
    es_url: str


settings: Settings = Settings()  # type: ignore
