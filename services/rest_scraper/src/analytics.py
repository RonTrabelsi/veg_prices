""" Decision analytics on top of the indexed prices, weather and holidays """

import math
from datetime import datetime, timedelta
from logging import Logger
from time import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch, NotFoundError

from common.holidays_consts import DEMAND_GROUPS, GROUP_NAMES_HE
from common.weather_consts import GROWING_REGIONS, HEAT_STRESS_TMAX, SOURCE_FORECAST

# The source has no data between 2009 and 2014 and the earlier years are a different price regime
BASELINE_SINCE_YEAR = 2015
# Forecast horizons offered to the farmer
HORIZONS_DAYS = [7, 14, 28, 56, 84]
# +/- days around the same calendar day averaged into the seasonal norm
NORM_HALF_WINDOW_DAYS = 7
# A year takes part in the baseline only with at least this many priced days
MIN_DAYS_PER_YEAR = 120
MIN_BASELINE_YEARS = 3
# Forecast error is estimated on the last full years, one origin per week
BACKTEST_YEARS = 3
BACKTEST_STEP_DAYS = 7
# Weather affects supply with a lag of about two months (fruit development)
WEATHER_LAG_MONTHS = 2
WEATHER_SIGNAL_DAYS = 60
WEATHER_MIN_CORRELATION = 0.2
WEATHER_MAX_PRESSURE_PCT = 15.0
# Candidate blends of "today's price" and "the seasonal norm"; the backtest picks the best one per horizon.
# ratio: carry today's deviation from the norm proportionally, additive: carry today's price as is (w=1 is naive)
BLEND_FORMS = ("ratio", "additive")
BLEND_WEIGHTS = [round(step / 10, 1) for step in range(11)]
# Recommendation thresholds on the one-month horizon
VERDICT_HORIZON_DAYS = 28
VERDICT_THRESHOLD_PCT = 8.0
CACHE_TTL_SECONDS = 600
MAX_QUERY_SIZE = 10000
# Windows (days relative to the holiday first day) used for the holiday effect profile
HOLIDAY_WINDOWS = [("-28..-15", -28, -15), ("-14..-8", -14, -8), ("-7..-1", -7, -1), ("0..6", 0, 6), ("7..20", 7, 20)]
PRE_HOLIDAY_WINDOW = "-7..-1"
UPCOMING_HOLIDAYS_DAYS = 200
MONTH_NAMES_HE = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר",
                  "נובמבר", "דצמבר"]


class InsufficientDataError(Exception):
    """ Raised when a vegetable does not have enough history for the analytics """


def clean(obj: Any) -> Any:
    """ :return: the given nested structure with numpy / pandas types converted to JSON friendly values """
    if isinstance(obj, dict):
        return {key: clean(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(value) for value in obj]
    if isinstance(obj, (np.floating, float)):
        value = float(obj)
        return None if math.isnan(value) or math.isinf(value) else round(value, 3)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.strftime("%Y-%m-%d")
    return obj


class Analytics:
    def __init__(self, es_client: Elasticsearch, logger: Logger, prices_index: str, weather_index: str,
                 holidays_index: str, primary_region: str) -> None:
        self.es_client = es_client
        self.logger = logger
        self.prices_index = prices_index
        self.weather_index = weather_index
        self.holidays_index = holidays_index
        self.primary_region = primary_region
        self._cache: Dict[Tuple, Tuple[float, Any]] = {}

    # ------------------------------------------------------------------ loading

    def search_all(self, index: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ :return: all documents matching the query, sorted by date (empty when the index does not exist) """
        try:
            response = self.es_client.search(index=index, query=query, size=MAX_QUERY_SIZE,
                                             sort=[{"date": "asc"}], filter_path="hits.hits._source")
        except NotFoundError:
            return []
        return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]

    def load_prices(self, vegetable: str) -> pd.DataFrame:
        """ :return: raw daily prices of the vegetable indexed by date """
        docs = self.search_all(self.prices_index, {"term": {"vegetable_name.keyword": vegetable}})
        if not docs:
            raise InsufficientDataError(f"No prices data for {vegetable}")
        prices = pd.DataFrame(docs)
        prices["date"] = pd.to_datetime(prices["date"])
        prices = prices.set_index("date").sort_index()
        prices = prices[~prices.index.duplicated(keep="last")]
        return prices[["regular_price", "special_price"]].astype(float)

    def load_weather(self, region: str) -> pd.DataFrame:
        """ :return: daily weather of the region indexed by date (empty if never loaded) """
        docs = self.search_all(self.weather_index, {"term": {"region": region}})
        if not docs:
            return pd.DataFrame()
        weather = pd.DataFrame(docs)
        weather["date"] = pd.to_datetime(weather["date"])
        return weather.set_index("date").sort_index()

    def load_holidays(self) -> pd.DataFrame:
        """ :return: the holidays calendar (empty if never loaded) """
        docs = self.search_all(self.holidays_index, {"terms": {"group": DEMAND_GROUPS}})
        if not docs:
            return pd.DataFrame()
        holidays = pd.DataFrame(docs)
        holidays["date"] = pd.to_datetime(holidays["date"])
        return holidays

    def list_vegetables(self) -> List[Dict[str, Any]]:
        """ :return: all vegetables with data, with their data range and size """
        aggs = {"vegetables": {"terms": {"field": "vegetable_name.keyword", "size": 100},
                               "aggs": {"first": {"min": {"field": "date"}}, "last": {"max": {"field": "date"}},
                                        "last_price": {"top_hits": {"size": 1, "sort": [{"date": "desc"}],
                                                                    "_source": ["regular_price"]}}}}}
        try:
            response = self.es_client.search(index=self.prices_index, size=0, aggs=aggs)
        except NotFoundError:
            return []
        vegetables = []
        for bucket in response["aggregations"]["vegetables"]["buckets"]:
            last_hit = bucket["last_price"]["hits"]["hits"]
            vegetables.append({
                "name": bucket["key"],
                "days": bucket["doc_count"],
                "data_from": bucket["first"]["value_as_string"][:10],
                "data_to": bucket["last"]["value_as_string"][:10],
                "last_price": last_hit[0]["_source"]["regular_price"] if last_hit else None,
                "has_analytics": bucket["doc_count"] >= MIN_DAYS_PER_YEAR * MIN_BASELINE_YEARS,
            })
        return sorted(vegetables, key=lambda veg: -veg["days"])

    # ------------------------------------------------------------------ core series

    @staticmethod
    def daily_series(prices: pd.DataFrame) -> pd.Series:
        """ :return: regular price as a continuous daily series (short gaps interpolated) """
        return prices["regular_price"].asfreq("D").interpolate(limit=5)

    @staticmethod
    def year_slice(series: pd.Series, year: int) -> pd.Series:
        return series[series.index.year == year]

    def seasonal_norm(self, series: pd.Series, exclude_year: Optional[int] = None) -> Tuple[pd.Series, int]:
        """
        :return: the typical price per day of year (median across baseline years of a centered rolling mean),
                 and the number of years it is based on
        """
        rows = {}
        for year in range(BASELINE_SINCE_YEAR, series.index.max().year + 1):
            if year == exclude_year:
                continue
            year_prices = self.year_slice(series, year)
            if year_prices.notna().sum() < MIN_DAYS_PER_YEAR:
                continue
            rolled = year_prices.rolling(2 * NORM_HALF_WINDOW_DAYS + 1, center=True, min_periods=5).mean()
            rows[year] = pd.Series(rolled.values, index=year_prices.index.dayofyear)
        if len(rows) < MIN_BASELINE_YEARS:
            raise InsufficientDataError("Not enough full years for a seasonal baseline")
        table = pd.DataFrame(rows)
        norm = table.median(axis=1).reindex(range(1, 367)).interpolate(limit_direction="both")
        return norm, len(rows)

    @staticmethod
    def norm_at(dates: pd.DatetimeIndex, norm: pd.Series, level: float = 1.0) -> np.ndarray:
        """ :return: the level adjusted seasonal norm on the given dates """
        return norm.reindex(pd.DatetimeIndex(dates).dayofyear).values * level

    def level_factor(self, series: pd.Series, norm: pd.Series) -> float:
        """ :return: how the last year's price level compares to the baseline (handles inflation / level shifts) """
        last_date = series.dropna().index.max()
        last_year = series[series.index > last_date - timedelta(days=365)]
        ratio = last_year.mean() / np.nanmean(self.norm_at(last_year.index, norm))
        return float(np.clip(ratio, 0.5, 2.0))

    def anomaly(self, series: pd.Series, norm: pd.Series) -> pd.Series:
        """ :return: price relative to the seasonal norm (0 = typical), with a per-year level adjustment """
        anomaly = pd.Series(np.nan, index=series.index)
        for year in series.index.year.unique():
            year_prices = self.year_slice(series, year)
            expected = self.norm_at(year_prices.index, norm)
            level = year_prices.mean() / np.nanmean(expected) if year_prices.notna().sum() >= 30 else 1.0
            anomaly[year_prices.index] = year_prices / (expected * level) - 1
        return anomaly

    # ------------------------------------------------------------------ analytics blocks

    def overview(self, prices: pd.DataFrame, series: pd.Series, norm: pd.Series, level: float) -> Dict[str, Any]:
        last_date = prices.index.max()
        last_price = float(prices.loc[last_date, "regular_price"])
        norm_now = float(self.norm_at(pd.DatetimeIndex([last_date]), norm, level)[0])
        baseline = series[series.index.year >= BASELINE_SINCE_YEAR]
        same_month = baseline[baseline.index.month == last_date.month].dropna()

        def change(days: int) -> Optional[float]:
            past = series.get(last_date - timedelta(days=days))
            return None if past is None or math.isnan(past) else (last_price / past - 1) * 100

        return {
            "last_date": last_date,
            "last_price": last_price,
            "special_price": prices.loc[last_date, "special_price"],
            "change_7d_pct": change(7),
            "change_30d_pct": change(30),
            "seasonal_norm_now": norm_now,
            "vs_norm_pct": (last_price / norm_now - 1) * 100,
            "month": int(last_date.month),
            "month_name_he": MONTH_NAMES_HE[last_date.month - 1],
            "month_percentile": float((same_month < last_price).mean() * 100) if len(same_month) else None,
            "days_since_update": (datetime.now() - last_date).days,
        }

    def seasonality(self, series: pd.Series) -> Dict[str, Any]:
        baseline = series[series.index.year >= BASELINE_SINCE_YEAR].dropna()
        annual_mean = baseline.mean()
        by_year_month = baseline.groupby([baseline.index.year, baseline.index.month]).mean().unstack()
        ranks = by_year_month.rank(axis=1).mean()
        months = []
        for month in range(1, 13):
            values = baseline[baseline.index.month == month]
            months.append({
                "month": month,
                "name_he": MONTH_NAMES_HE[month - 1],
                "mean": values.mean(),
                "median": values.median(),
                "p25": values.quantile(0.25),
                "p75": values.quantile(0.75),
                "vs_annual_pct": (values.mean() / annual_mean - 1) * 100,
                "avg_rank": ranks.get(month),
                "n_years": int(by_year_month[month].notna().sum()) if month in by_year_month else 0,
            })
        ordered = sorted(months, key=lambda month: month["mean"])
        return {
            "annual_mean": annual_mean,
            "baseline_years": [int(year) for year in by_year_month.index],
            "months": months,
            "best_months": [month["month"] for month in ordered[-3:]][::-1],
            "worst_months": [month["month"] for month in ordered[:3]],
        }

    def holiday_effects(self, series: pd.Series, holidays: pd.DataFrame) -> Dict[str, Any]:
        if holidays.empty:
            return {"upcoming": [], "effects": []}
        first_days = holidays[~holidays["is_erev"]].groupby(["group", holidays["date"].dt.year])["date"].min()
        last_data_year = series.dropna().index.max().year
        today = pd.Timestamp(datetime.now().date())

        effects = []
        for group in DEMAND_GROUPS:
            if group not in first_days.index.get_level_values(0):
                continue
            windows = {name: [] for name, _, _ in HOLIDAY_WINDOWS}
            # selecting the group leaves a Series indexed by year
            for year, holiday_date in first_days[group].items():
                if year < BASELINE_SINCE_YEAR or year > last_data_year:
                    continue
                year_prices = self.year_slice(series, year)
                if year_prices.notna().sum() < MIN_DAYS_PER_YEAR:
                    continue
                year_mean = year_prices.mean()
                for name, start, end in HOLIDAY_WINDOWS:
                    window = series[holiday_date + timedelta(days=start): holiday_date + timedelta(days=end)]
                    if window.notna().sum() >= 3:
                        windows[name].append((window.mean() / year_mean - 1) * 100)
            pre = windows[PRE_HOLIDAY_WINDOW]
            if len(pre) < MIN_BASELINE_YEARS:
                continue
            effects.append({
                "group": group,
                "name_he": GROUP_NAMES_HE[group],
                "n_years": len(pre),
                "windows": [{"window": name, "from_day": start, "to_day": end,
                             "effect_pct": float(np.mean(windows[name])) if windows[name] else None}
                            for name, start, end in HOLIDAY_WINDOWS],
                "pre_holiday_effect_pct": float(np.mean(pre)),
                "consistency_pct": float(np.mean([value > 0 for value in pre]) * 100),
            })
        effect_by_group = {effect["group"]: effect for effect in effects}

        upcoming = []
        for (group, _), holiday_date in first_days.items():
            days_until = (holiday_date - today).days
            if 0 <= days_until <= UPCOMING_HOLIDAYS_DAYS:
                upcoming.append({"group": group, "name_he": GROUP_NAMES_HE[group], "date": holiday_date,
                                 "days_until": days_until,
                                 "pre_holiday_effect_pct": effect_by_group.get(group, {}).get("pre_holiday_effect_pct"),
                                 "consistency_pct": effect_by_group.get(group, {}).get("consistency_pct")})
        upcoming.sort(key=lambda holiday: holiday["days_until"])
        return {"upcoming": upcoming, "effects": effects}

    @staticmethod
    def blend(form: str, weight: float, price_now, norm_now, norm_target):
        """ :return: the forecast for the given blend form and persistence weight """
        carried = price_now * norm_target / norm_now if form == "ratio" else price_now
        return weight * carried + (1 - weight) * norm_target

    def backtest(self, series: pd.Series) -> Dict[int, Dict[str, Any]]:
        """
        Replay the last full years with out-of-year baselines, pick per horizon the blend that minimizes the
        absolute error, and measure it. :return: chosen blend and its errors per horizon
        """
        samples = {horizon: [] for horizon in HORIZONS_DAYS}
        last_year = series.dropna().index.max().year
        for year in range(last_year - BACKTEST_YEARS, last_year):
            try:
                norm, _ = self.seasonal_norm(series, exclude_year=year)
            except InsufficientDataError:
                continue
            previous = self.year_slice(series, year - 1)
            if previous.notna().sum() < MIN_DAYS_PER_YEAR:
                continue
            level = previous.mean() / np.nanmean(self.norm_at(previous.index, norm))
            for origin in pd.date_range(f"{year}-01-01", f"{year}-12-31", freq=f"{BACKTEST_STEP_DAYS}D"):
                price_now = series.get(origin)
                if price_now is None or math.isnan(price_now):
                    continue
                norm_now = float(self.norm_at(pd.DatetimeIndex([origin]), norm, level)[0])
                for horizon in HORIZONS_DAYS:
                    target = origin + timedelta(days=horizon)
                    actual = series.get(target)
                    if actual is None or math.isnan(actual):
                        continue
                    norm_target = float(self.norm_at(pd.DatetimeIndex([target]), norm, level)[0])
                    samples[horizon].append((price_now, norm_now, norm_target, actual))

        result = {}
        for horizon in HORIZONS_DAYS:
            if not samples[horizon]:
                result[horizon] = {"n": 0, "form": "additive", "weight": 1.0, "mae": None, "p80_abs_error": None,
                                   "naive_mae": None, "norm_mae": None}
                continue
            price_now, norm_now, norm_target, actual = np.array(samples[horizon]).T
            best = None
            for form in BLEND_FORMS:
                for weight in BLEND_WEIGHTS:
                    errors = np.abs(self.blend(form, weight, price_now, norm_now, norm_target) - actual)
                    if best is None or errors.mean() < best[0]:
                        best = (errors.mean(), form, weight, errors)
            mae, form, weight, errors = best
            result[horizon] = {
                "n": int(len(actual)),
                "form": form,
                "weight": float(weight),
                "mae": float(mae),
                "p80_abs_error": float(np.quantile(errors, 0.8)),
                "naive_mae": float(np.abs(price_now - actual).mean()),
                "norm_mae": float(np.abs(norm_target - actual).mean()),
            }
        return result

    def forecast(self, prices: pd.DataFrame, series: pd.Series, norm: pd.Series, level: float,
                 weather_pressure_pct: Optional[float]) -> Dict[str, Any]:
        last_date = prices.index.max()
        last_price = float(prices.loc[last_date, "regular_price"])
        norm_now = float(self.norm_at(pd.DatetimeIndex([last_date]), norm, level)[0])
        backtest = self.backtest(series)

        horizons = []
        for horizon in HORIZONS_DAYS:
            target = last_date + timedelta(days=horizon)
            norm_target = float(self.norm_at(pd.DatetimeIndex([target]), norm, level)[0])
            chosen = backtest[horizon]
            persistence = last_price * norm_target / norm_now if chosen["form"] == "ratio" else last_price
            weight = chosen["weight"]
            point = float(self.blend(chosen["form"], weight, last_price, norm_now, norm_target))
            weather_adjustment = 0.0
            if weather_pressure_pct and horizon >= 28:
                weather_adjustment = point * weather_pressure_pct / 100 * min(1.0, horizon / 56)
                point += weather_adjustment
            band = chosen["p80_abs_error"] or 0.0
            horizons.append({
                "horizon_days": horizon,
                "target_date": target,
                "point": point,
                "low": max(0.0, point - band),
                "high": point + band,
                "change_vs_now_pct": (point / last_price - 1) * 100,
                "seasonal_norm": norm_target,
                "persistence": persistence,
                "persistence_weight": weight,
                "blend_form": chosen["form"],
                "weather_adjustment": weather_adjustment,
                "n": chosen["n"],
                "mae": chosen["mae"],
                "p80_abs_error": chosen["p80_abs_error"],
                "naive_mae": chosen["naive_mae"],
                "norm_mae": chosen["norm_mae"],
            })

        verdict_point = next(point for point in horizons if point["horizon_days"] == VERDICT_HORIZON_DAYS)
        change = verdict_point["change_vs_now_pct"]
        if change >= VERDICT_THRESHOLD_PCT:
            label = "wait"
        elif change <= -VERDICT_THRESHOLD_PCT:
            label = "sell"
        else:
            label = "hold"
        band_pct = (verdict_point["p80_abs_error"] or 0.0) / last_price * 100
        return {
            "last_date": last_date,
            "last_price": last_price,
            "horizons": horizons,
            "verdict": {"label": label, "horizon_days": VERDICT_HORIZON_DAYS, "change_pct": change,
                        "confidence": "high" if abs(change) > band_pct else "low", "band_pct": band_pct},
        }

    def history(self, prices: pd.DataFrame, series: pd.Series, norm: pd.Series, level: float,
                holidays: pd.DataFrame, days: int) -> Dict[str, Any]:
        last_date = prices.index.max()
        start = last_date - timedelta(days=days)
        recent = prices[prices.index > start]
        weekly = recent.resample("7D").mean()
        norm_weekly = pd.Series(self.norm_at(series[series.index > start].index, norm, level),
                                index=series[series.index > start].index).resample("7D").mean()
        points = [{"date": date, "price": row["regular_price"], "special": row["special_price"],
                   "norm": norm_weekly.get(date)} for date, row in weekly.iterrows()]
        markers = []
        if not holidays.empty:
            first_days = holidays[~holidays["is_erev"]].groupby(["group", holidays["date"].dt.year])["date"].min()
            for (group, _), holiday_date in first_days.items():
                if start < holiday_date <= last_date + timedelta(days=90):
                    markers.append({"date": holiday_date, "group": group, "name_he": GROUP_NAMES_HE[group]})
        yearly = prices["regular_price"].groupby(prices.index.year).agg(["mean", "count"])
        return {
            "weekly": points,
            "markers": sorted(markers, key=lambda marker: marker["date"]),
            "yearly": [{"year": int(year), "mean": row["mean"], "n_days": int(row["count"])}
                       for year, row in yearly.iterrows()],
        }

    def planting(self, series: pd.Series, norm: pd.Series, level: float, days_to_harvest: int,
                 harvest_window_days: int) -> Dict[str, Any]:
        today = pd.Timestamp(datetime.now().date())
        annual_norm = float(norm.mean() * level)
        weeks = []
        for week in range(52):
            plant_date = today + timedelta(days=7 * week)
            harvest_start = plant_date + timedelta(days=days_to_harvest)
            harvest_end = harvest_start + timedelta(days=harvest_window_days)
            expected = float(np.nanmean(self.norm_at(pd.date_range(harvest_start, harvest_end), norm, level)))
            weeks.append({"plant_date": plant_date, "harvest_start": harvest_start, "harvest_end": harvest_end,
                          "expected_price": expected, "vs_annual_pct": (expected / annual_norm - 1) * 100})
        by_month = []
        for month in range(1, 13):
            days = pd.date_range(f"2001-{month:02d}-01", periods=28)
            expected = float(np.nanmean(self.norm_at(days, norm, level)))
            by_month.append({"month": month, "name_he": MONTH_NAMES_HE[month - 1], "expected_price": expected,
                             "vs_annual_pct": (expected / annual_norm - 1) * 100})
        return {
            "days_to_harvest": days_to_harvest,
            "harvest_window_days": harvest_window_days,
            "annual_norm": annual_norm,
            "weeks": weeks,
            "best_windows": sorted(weeks, key=lambda week: -week["expected_price"])[:5],
            "by_harvest_month": by_month,
        }

    def weather_signal(self, series: pd.Series, region: str) -> Optional[Dict[str, Any]]:
        weather = self.load_weather(region)
        if weather.empty:
            return None
        observed = weather[weather["source"] != SOURCE_FORECAST]
        last_observed = observed.index.max()
        climatology = observed["tmax"].groupby(observed.index.dayofyear).mean()
        climatology = climatology.reindex(range(1, 367)).interpolate(limit_direction="both")
        climatology = climatology.rolling(7, center=True, min_periods=1).mean()

        recent = observed["tmax"][observed.index > last_observed - timedelta(days=WEATHER_SIGNAL_DAYS)]
        tmax_anomaly = float((recent - climatology.reindex(recent.index.dayofyear).values).mean())
        last_month = observed[observed.index > last_observed - timedelta(days=30)]
        heat_days = int((last_month["tmax"] >= HEAT_STRESS_TMAX).sum())
        # how many such days the same 30 calendar days usually have (all years, excluding this window)
        window_doys = set(last_month.index.dayofyear)
        past = observed[(observed.index.dayofyear.isin(window_doys)) & (observed.index < last_month.index.min())]
        past_years = past.index.year.nunique()
        heat_days_normal = float((past["tmax"] >= HEAT_STRESS_TMAX).sum() / past_years) if past_years else None

        # monthly regression of the price deviation on the temperature deviation two months earlier
        monthly_price = series.resample("MS").mean()
        monthly_tmax = observed["tmax"].resample("MS").mean()
        price_pct = (monthly_price / monthly_price.groupby(monthly_price.index.month).transform("mean") - 1) * 100
        tmax_dev = monthly_tmax - monthly_tmax.groupby(monthly_tmax.index.month).transform("mean")
        joined = pd.concat([price_pct.rename("price"), tmax_dev.shift(WEATHER_LAG_MONTHS).rename("tmax")], axis=1)
        joined = joined[joined.index.year >= BASELINE_SINCE_YEAR].dropna()
        correlation = float(joined["price"].corr(joined["tmax"])) if len(joined) > 24 else 0.0
        slope = float(np.polyfit(joined["tmax"], joined["price"], 1)[0]) if len(joined) > 24 else 0.0
        pressure = 0.0
        if correlation >= WEATHER_MIN_CORRELATION:
            pressure = float(np.clip(slope * tmax_anomaly, -WEATHER_MAX_PRESSURE_PCT, WEATHER_MAX_PRESSURE_PCT))

        forecast = weather[weather["source"] == SOURCE_FORECAST]
        return {
            "region": region,
            "region_name": GROWING_REGIONS[region]["name_he"],
            "last_observed": last_observed,
            "tmax_anomaly_60d": tmax_anomaly,
            "heat_stress_days_30d": heat_days,
            "heat_stress_days_30d_normal": heat_days_normal,
            "heat_stress_tmax": HEAT_STRESS_TMAX,
            "lag_months": WEATHER_LAG_MONTHS,
            "correlation": correlation,
            "pct_per_degree": slope,
            "implied_pressure_pct": pressure,
            "n_months": int(len(joined)),
            "forecast": [{"date": date, "tmax": row["tmax"], "tmin": row["tmin"], "rain_mm": row["rain_mm"]}
                         for date, row in forecast.iterrows()],
        }

    # ------------------------------------------------------------------ entry points

    def base(self, vegetable: str) -> Dict[str, Any]:
        """ :return: the loaded and derived series every block builds on (cached per vegetable) """
        key = ("base", vegetable)
        cached = self._cache.get(key)
        if cached and time() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]
        prices = self.load_prices(vegetable)
        series = self.daily_series(prices)
        norm, n_years = self.seasonal_norm(series)
        level = self.level_factor(series, norm)
        base = {"prices": prices, "series": series, "norm": norm, "n_years": n_years, "level": level,
                "holidays": self.load_holidays()}
        self._cache[key] = (time(), base)
        return base

    def dashboard(self, vegetable: str, days_to_harvest: int, harvest_window_days: int,
                  history_days: int, region: Optional[str] = None) -> Dict[str, Any]:
        base = self.base(vegetable)
        region = region or self.primary_region
        try:
            weather = self.weather_signal(base["series"], region)
        except Exception as error:  # weather is an enrichment, never fail the dashboard on it
            self.logger.warning(f"Weather signal failed for {region}: {error}")
            weather = None
        pressure = weather["implied_pressure_pct"] if weather else None
        result = {
            "vegetable": vegetable,
            "meta": {
                "data_from": base["prices"].index.min(),
                "data_to": base["prices"].index.max(),
                "n_days": int(len(base["prices"])),
                "baseline_since": BASELINE_SINCE_YEAR,
                "baseline_years": base["n_years"],
                "level_factor": base["level"],
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            },
            "overview": self.overview(base["prices"], base["series"], base["norm"], base["level"]),
            "forecast": self.forecast(base["prices"], base["series"], base["norm"], base["level"], pressure),
            "seasonality": self.seasonality(base["series"]),
            "holidays": self.holiday_effects(base["series"], base["holidays"]),
            "history": self.history(base["prices"], base["series"], base["norm"], base["level"], base["holidays"],
                                    history_days),
            "planting": self.planting(base["series"], base["norm"], base["level"], days_to_harvest,
                                      harvest_window_days),
            "weather": weather,
        }
        return clean(result)
