""" Consts for the Jewish holidays fetcher (Hebcal, free, no API key) """

HEBCAL_URL: str = "https://www.hebcal.com/hebcal"

# Israel calendar, major + minor + modern holidays, no candle lighting / parasha / rosh chodesh noise
HEBCAL_BASE_PARAMS = {
    "v": "1", "cfg": "json", "i": "on",
    "maj": "on", "min": "on", "mod": "on",
    "nx": "off", "mf": "off", "ss": "off", "c": "off",
}

RESPONSE_DATE_FORMAT: str = "%Y-%m-%d"

# First year with prices data / how far ahead to keep the calendar loaded
DEFAULT_FROM_YEAR: int = 2005
YEARS_AHEAD: int = 2

# Holiday groups that matter for produce demand, keyed by the English title prefix Hebcal uses.
# Order matters: the first matching prefix wins ("Pesach Sheni" must not become "pesach").
HOLIDAY_GROUPS = [
    ("Pesach Sheni", None),
    ("Shushan Purim", None),
    ("Purim Katan", None),
    ("Rosh Hashana LaBehemot", None),
    ("Rosh Hashana", "rosh_hashana"),
    ("Yom Kippur", "yom_kippur"),
    ("Sukkot", "sukkot"),
    ("Shmini Atzeret", "shmini_atzeret"),
    ("Simchat Torah", "shmini_atzeret"),
    ("Chanukah", "chanukah"),
    ("Tu BiShvat", "tu_bishvat"),
    ("Purim", "purim"),
    ("Pesach", "pesach"),
    ("Yom HaAtzma'ut", "yom_haatzmaut"),
    ("Lag BaOmer", "lag_baomer"),
    ("Shavuot", "shavuot"),
    ("Tish'a B'Av", "tisha_bav"),
]

GROUP_NAMES_HE = {
    "rosh_hashana": "ראש השנה",
    "yom_kippur": "יום כיפור",
    "sukkot": "סוכות",
    "shmini_atzeret": "שמיני עצרת",
    "chanukah": "חנוכה",
    "tu_bishvat": "ט״ו בשבט",
    "purim": "פורים",
    "pesach": "פסח",
    "yom_haatzmaut": "יום העצמאות",
    "lag_baomer": "ל״ג בעומר",
    "shavuot": "שבועות",
    "tisha_bav": "תשעה באב",
}

# Groups shown to the farmer as demand events (multi-day, meal-heavy holidays)
DEMAND_GROUPS = ["rosh_hashana", "sukkot", "pesach", "shavuot", "yom_haatzmaut", "chanukah", "purim"]

EREV_PREFIX: str = "Erev "
