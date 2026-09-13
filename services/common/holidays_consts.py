""" Consts for the holidays fetcher (Hebcal, free, no API key) """

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

# Hebcal sub-categories analyzed as demand events. "major" is the calendar's own classification of the religious
# festivals and fasts. "modern" (state commemorations such as memorial days) and "minor" days are stored for
# completeness but not analyzed - add them here to track them.
TRACKED_SUBCATS = ("major",)

# Every day of a holiday is a separate calendar item. These rules reduce an item title to the holiday's name,
# e.g. "Pesach II (CH''M)" -> "Pesach", "Chanukah: 3 Candles" -> "Chanukah", "Rosh Hashana 5787" -> "Rosh Hashana",
# "סוכות ז׳ (הושענא רבה)" -> "סוכות". They are applied repeatedly until the title stops changing.
EREV_PREFIX_EN: str = "Erev "
EREV_PREFIX_HE: str = "ערב "
TITLE_SUFFIX_PATTERNS_EN = [
    r"\s*\([^)]*\)\s*$",                       # "(CH''M)", "(Hoshana Raba)"
    r":.*$",                                    # "Chanukah: 3 Candles"
    r"\s+\d{4}$",                               # "Rosh Hashana 5787"
    r"\s+(?:I|II|III|IV|V|VI|VII|VIII)$",       # "Sukkot II"
]
TITLE_SUFFIX_PATTERNS_HE = [
    r"\s*\([^)]*\)\s*$",
    r":.*$",
    r"\s+\d{4}$",
    r"\s+[א-ח]׳$",                              # "פסח א׳"
]
INTERMEDIATE_MARKERS = ("CH’’M", "CH''M", "חוה״מ")

# Dates of one holiday closer than this belong to the same occurrence (the same year)
OCCURRENCE_GAP_DAYS: int = 30
