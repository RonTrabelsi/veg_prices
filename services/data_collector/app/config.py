""" Environment variables settings """

from pydantic import BaseSettings


class Settings(BaseSettings):
    """ Environment variables configuration """
    debug: bool

    elastic_hostname: str
    elastic_port: int
    elastic_protocol: str

    load_default_market_prices: bool
    response_max_dates_data: int


settings: Settings = Settings()  # type: ignore
