""" Fetch the Israeli holidays calendar from Hebcal and index it to elasticsearch """

from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from requests import Session

from .holidays_consts import (DEFAULT_FROM_YEAR, EREV_PREFIX, HEBCAL_BASE_PARAMS, HEBCAL_URL, HOLIDAY_GROUPS,
                              RESPONSE_DATE_FORMAT, YEARS_AHEAD)


class HolidaysClient:
    def __init__(self, es_client: Elasticsearch, logger: Logger, es_holidays_index_name: str) -> None:
        self.session = Session()
        self.logger = logger
        self.es_client = es_client
        self.es_holidays_index_name = es_holidays_index_name

    @staticmethod
    def classify(title_en: str) -> Optional[str]:
        """ :return: the holiday group of the given Hebcal title, None for holidays we do not track """
        name = title_en[len(EREV_PREFIX):] if title_en.startswith(EREV_PREFIX) else title_en
        for prefix, group in HOLIDAY_GROUPS:
            if name.startswith(prefix):
                return group
        return None

    def build_doc(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """ :return: holiday document from a Hebcal calendar item """
        title_en = item["title"]
        is_erev = title_en.startswith(EREV_PREFIX)
        # "Pesach III (CH''M)" style titles -> intermediate days, "Pesach I" / plain title -> first day
        is_intermediate = "CH''M" in title_en or "(CH" in title_en
        return {
            "date": datetime.strptime(item["date"][:10], RESPONSE_DATE_FORMAT),
            "title_en": title_en,
            "title_he": item.get("hebrew", title_en),
            "subcat": item.get("subcat"),
            "group": self.classify(title_en),
            "is_erev": is_erev,
            "is_yomtov": bool(item.get("yomtov")),
            "is_intermediate": is_intermediate,
        }

    def fetch_year(self, year: int) -> List[Dict[str, Any]]:
        """ Fetch all holidays of the given civil year """
        response = self.session.get(HEBCAL_URL, params={**HEBCAL_BASE_PARAMS, "year": year}, timeout=60)
        response.raise_for_status()
        items = [item for item in response.json().get("items", []) if item.get("category") == "holiday"]
        return [self.build_doc(item) for item in items]

    def load_years(self, from_year: int = DEFAULT_FROM_YEAR, to_year: Optional[int] = None) -> int:
        """ Load the holidays calendar between the given years. :return: number of indexed holidays """
        to_year = to_year or datetime.now().year + YEARS_AHEAD
        indexed = 0
        for year in range(from_year, to_year + 1):
            docs = self.fetch_year(year)
            indexed += self.index_docs(docs)
            self.logger.info(f"Indexed {len(docs)} holidays of {year}")
        return indexed

    def index_docs(self, docs: List[Dict[str, Any]]) -> int:
        """ Upsert the given holiday documents. :return: number of upserted documents """
        upserted = 0
        for doc in docs:
            doc_id = f"{doc['date']:%Y-%m-%d}_{doc['title_en']}".replace(" ", "_")
            response = self.es_client.update(index=self.es_holidays_index_name, id=doc_id,
                                             body={"doc": doc, "doc_as_upsert": True}, retry_on_conflict=3)
            if response["result"] in ("created", "updated"):
                upserted += 1
        return upserted
