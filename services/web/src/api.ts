/** Types mirroring the /analytics API and the fetch helpers */

export interface Vegetable {
  name: string;
  days: number;
  data_from: string;
  data_to: string;
  last_price: number | null;
  has_analytics: boolean;
}

export interface Overview {
  last_date: string;
  last_price: number;
  special_price: number | null;
  change_7d_pct: number | null;
  change_30d_pct: number | null;
  seasonal_norm_now: number;
  vs_norm_pct: number;
  month: number;
  month_name_he: string;
  month_percentile: number | null;
  days_since_update: number;
}

export interface ForecastPoint {
  horizon_days: number;
  target_date: string;
  point: number;
  low: number;
  high: number;
  change_vs_now_pct: number;
  seasonal_norm: number;
  persistence: number;
  persistence_weight: number;
  blend_form: "ratio" | "additive";
  weather_adjustment: number;
  n: number;
  mae: number | null;
  p80_abs_error: number | null;
  naive_mae: number | null;
  norm_mae: number | null;
}

export type VerdictLabel = "wait" | "sell" | "hold";

export interface Forecast {
  last_date: string;
  last_price: number;
  horizons: ForecastPoint[];
  verdict: { label: VerdictLabel; horizon_days: number; change_pct: number; confidence: "high" | "low"; band_pct: number };
}

export interface MonthStat {
  month: number;
  name_he: string;
  mean: number;
  median: number;
  p25: number;
  p75: number;
  vs_annual_pct: number;
  avg_rank: number | null;
  n_years: number;
}

export interface Seasonality {
  annual_mean: number;
  baseline_years: number[];
  months: MonthStat[];
  best_months: number[];
  worst_months: number[];
}

export interface HolidayEffect {
  group: string;
  name_he: string;
  name_en: string;
  subcat: string;
  n_years: number;
  windows: { window: string; from_day: number; to_day: number; effect_pct: number | null }[];
  pre_holiday_effect_pct: number;
  consistency_pct: number;
}

export interface UpcomingHoliday {
  group: string;
  name_he: string;
  name_en: string;
  subcat: string;
  date: string;
  days_until: number;
  pre_holiday_effect_pct: number | null;
  consistency_pct: number | null;
}

export interface History {
  weekly: { date: string; price: number | null; special: number | null; norm: number | null }[];
  markers: { date: string; group: string; name_he: string }[];
  yearly: { year: number; mean: number; n_days: number }[];
}

export interface PlantingWindow {
  plant_date: string;
  harvest_start: string;
  harvest_end: string;
  expected_price: number;
  vs_annual_pct: number;
}

export interface Planting {
  days_to_harvest: number;
  harvest_window_days: number;
  annual_norm: number;
  weeks: PlantingWindow[];
  best_windows: PlantingWindow[];
  by_harvest_month: { month: number; name_he: string; expected_price: number; vs_annual_pct: number }[];
}

export interface WeatherSignal {
  region: string;
  region_name: string;
  last_observed: string;
  tmax_anomaly_60d: number;
  heat_stress_days_30d: number;
  heat_stress_days_30d_normal: number | null;
  heat_stress_tmax: number;
  lag_months: number;
  correlation: number;
  pct_per_degree: number;
  implied_pressure_pct: number;
  n_months: number;
  forecast: { date: string; tmax: number; tmin: number; rain_mm: number }[];
}

export interface Dashboard {
  vegetable: string;
  meta: {
    data_from: string;
    data_to: string;
    n_days: number;
    baseline_since: number;
    baseline_years: number;
    level_factor: number;
    generated_at: string;
  };
  overview: Overview;
  forecast: Forecast;
  seasonality: Seasonality;
  holidays: { upcoming: UpcomingHoliday[]; effects: HolidayEffect[] };
  history: History;
  planting: Planting;
  weather: WeatherSignal | null;
}

export interface CatalogItem {
  name: string;
  days_on_site: number;
  last_date: string | null;
  last_price: number | null;
  last_special_price: number | null;
  indexed_days: number;
  data_from: string | null;
  data_to: string | null;
}

export interface LoadResult {
  vegetable_name: string;
  scraped_days: number;
  products: string[];
}

const API = "/api";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* not json */
    }
    throw new Error(detail);
  }
  return response.json();
}

export const fetchVegetables = () => getJson<Vegetable[]>("/analytics/vegetables");

export const fetchDashboard = (vegetable: string, daysToHarvest: number) =>
  getJson<Dashboard>(`/analytics/dashboard?vegetable=${encodeURIComponent(vegetable)}&days_to_harvest=${daysToHarvest}`);

export const fetchPlanting = (vegetable: string, daysToHarvest: number, harvestWindowDays: number) =>
  getJson<Planting>(
    `/analytics/planting?vegetable=${encodeURIComponent(vegetable)}&days_to_harvest=${daysToHarvest}&harvest_window_days=${harvestWindowDays}`
  );

export const fetchCatalog = (refresh = false) => getJson<CatalogItem[]>(`/market_prices/catalog${refresh ? "?refresh=true" : ""}`);

/** Load the full price history of a product. Synchronous on the server: up to a minute for a long history. */
export async function loadVegetable(name: string): Promise<LoadResult> {
  const response = await fetch(`${API}/market_prices/load_prices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vegetable_name: name }),
  });
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

/** Map API error details to something the farmer can read */
export const friendlyError = (message: string) => {
  if (/not enough full years/i.test(message)) return "לירק הזה אין עדיין מספיק שנות נתונים לניתוח עונתי (נדרשות לפחות 3 שנים מלאות).";
  if (/no prices data/i.test(message)) return "לירק הזה עוד לא נטענו מחירים.";
  if (/failed to fetch|networkerror/i.test(message)) return "לא ניתן להתחבר לשרת.";
  return message;
};
