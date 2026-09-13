""" Fetch the Israeli holidays calendar from Hebcal and index it to elasticsearch """

from datetime import datetime
from logging import Logger
from re import sub
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from requests import Session

from .holidays_consts import (DEFAULT_FROM_YEAR, EREV_PREFIX_EN, EREV_PREFIX_HE, HEBCAL_BASE_PARAMS, HEBCAL_URL,
                              INTERMEDIATE_MARKERS, RESPONSE_DATE_FORMAT, TITLE_SUFFIX_PATTERNS_EN,
                              TITLE_SUFFIX_PATTERNS_HE, TRACKED_SUBCATS, YEARS_AHEAD)


class HolidaysClient:
    def __init__(self, es_client: Elasticsearch, logger: Logger, es_holidays_index_name: str) -> None:
        self.session = Session()
        self.logger = logger
        self.es_client = es_client
        self.es_holidays_index_name = es_holidays_index_name

    @staticmethod
    def base_name(title: str, erev_prefix: str, suffix_patterns: List[str]) -> str:
        """ :return: the holiday name behind a single day's title (see holidays_consts for the rules) """
        name = title[len(erev_prefix):] if title.startswith(erev_prefix) else title
        previous = None
        while name != previous:
            previous = name
            for pattern in suffix_patterns:
                name = sub(pattern, "", name)
            name = name.strip()
        return name

    @staticmethod
    def group_key(name_en: str) -> str:
        """ :return: a stable identifier of the holiday, e.g. "Yom HaAtzma'ut" -> "yom_haatzma_ut" """
        return sub(r"_+", "_", sub(r"[^a-z0-9]", "_", name_en.lower())).strip("_")

    def build_doc(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """ :return: holiday document from a Hebcal calendar item """
        title_en = item["title"]
        title_he = item.get("hebrew") or title_en
        name_en = self.base_name(title_en, EREV_PREFIX_EN, TITLE_SUFFIX_PATTERNS_EN)
        name_he = self.base_name(title_he, EREV_PREFIX_HE, TITLE_SUFFIX_PATTERNS_HE)
        return {
            "date": datetime.strptime(item["date"][:10], RESPONSE_DATE_FORMAT),
            "hdate": item.get("hdate"),
            "title_en": title_en,
            "title_he": title_he,
            "subcat": item.get("subcat"),
            "group": self.group_key(name_en),
            "group_name_en": name_en,
            "group_name_he": name_he,
            "is_erev": title_en.startswith(EREV_PREFIX_EN),
            "is_yomtov": bool(item.get("yomtov")),
            "is_intermediate": any(marker in title_en or marker in title_he for marker in INTERMEDIATE_MARKERS),
            "is_tracked": item.get("subcat") in TRACKED_SUBCATS,
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
            doc_id = f"{doc['date']:%Y-%m-%d}_{doc['group']}_{doc['title_en']}".replace(" ", "_")
            response = self.es_client.update(index=self.es_holidays_index_name, id=doc_id,
                                             body={"doc": doc, "doc_as_upsert": True}, retry_on_conflict=3)
            if response["result"] in ("created", "updated"):
                upserted += 1
        return upserted
