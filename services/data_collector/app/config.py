""" Environment variables settings """

from pydantic import BaseSettings


class Settings(BaseSettings):
    """ Environment variables configuration """
    debug: bool
    
    mongo_hostname: str
    mongo_port: int


settings: Settings = Settings()  # type: ignore
