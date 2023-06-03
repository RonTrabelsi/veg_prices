""" General utils for the service """

from pymongo import MongoClient

from app.config import settings

DB_NAME = "data_collector_db"
MARKET_PRICES_COLLECTION_NAME = "market_prices_collection_name"


mongo_client = MongoClient(settings.mongo_hostname, settings.mongo_port)
mongo_db = mongo_client[DB_NAME]
market_prices_collection = mongo_db[MARKET_PRICES_COLLECTION_NAME]
