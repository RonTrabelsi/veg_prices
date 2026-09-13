/** Hebrew formatting helpers */

const shekel = new Intl.NumberFormat("he-IL", { style: "currency", currency: "ILS", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const dayMonth = new Intl.DateTimeFormat("he-IL", { day: "numeric", month: "long" });
const dayMonthYear = new Intl.DateTimeFormat("he-IL", { day: "numeric", month: "long", year: "numeric" });
const shortDate = new Intl.DateTimeFormat("he-IL", { day: "numeric", month: "numeric" });
const weekday = new Intl.DateTimeFormat("he-IL", { weekday: "short" });

export const price = (value: number | null | undefined) => (value == null ? "—" : shekel.format(value));

export const pct = (value: number | null | undefined, digits = 0) => {
  if (value == null || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${Math.abs(value).toFixed(digits)}%`;
};

export const signed = (value: number, digits = 1, suffix = "") => {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${Math.abs(value).toFixed(digits)}${suffix}`;
};

export const date = (iso: string) => dayMonth.format(new Date(iso));
export const dateWithYear = (iso: string) => dayMonthYear.format(new Date(iso));
export const dateShort = (iso: string) => shortDate.format(new Date(iso));
export const weekdayShort = (iso: string) => weekday.format(new Date(iso));

export const horizonLabel = (days: number) =>
  ({ 7: "בעוד שבוע", 14: "בעוד שבועיים", 28: "בעוד חודש", 56: "בעוד חודשיים", 84: "בעוד 3 חודשים" } as Record<number, string>)[days] ??
  `בעוד ${days} ימים`;

export const daysUntil = (days: number) => {
  if (days === 0) return "היום";
  if (days === 1) return "מחר";
  if (days < 14) return `בעוד ${days} ימים`;
  const weeks = Math.round(days / 7);
  if (days < 60) return `בעוד ${weeks} שבועות`;
  return `בעוד ${Math.round(days / 30)} חודשים`;
};

/** Higher price is good for a seller */
export const trendClass = (value: number | null | undefined, threshold = 3) => {
  if (value == null) return "neutral";
  if (value >= threshold) return "up";
  if (value <= -threshold) return "down";
  return "neutral";
};

/** Short Hebrew month names for narrow chart axes (index 1..12) */
export const MONTH_SHORT_HE = ["", "ינו׳", "פבר׳", "מרץ", "אפר׳", "מאי", "יוני", "יולי", "אוג׳", "ספט׳", "אוק׳", "נוב׳", "דצמ׳"];
export const monthShort = (month: number) => MONTH_SHORT_HE[month] ?? String(month);
