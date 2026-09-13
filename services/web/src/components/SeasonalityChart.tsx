import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { MonthStat, Seasonality } from "../api";
import { monthShort, pct, price } from "../format";

const COLORS = { up: "#2f855a", down: "#c53030", neutral: "#a0aec0" };

function color(month: MonthStat, best: number[], worst: number[]) {
  if (best.includes(month.month)) return COLORS.up;
  if (worst.includes(month.month)) return COLORS.down;
  return COLORS.neutral;
}

export default function SeasonalityChart({ seasonality, currentMonth }: { seasonality: Seasonality; currentMonth: number }) {
  const names = (months: number[]) => months.map((month) => seasonality.months[month - 1].name_he).join(", ");
  return (
    <section className="card seasonality">
      <header className="card-header">
        <h2>העונה משנה הכול</h2>
        <span className="stamp">מחיר ממוצע בכל חודש לעומת הממוצע השנתי ({price(seasonality.annual_mean)})</span>
      </header>

      <div className="legend-line">
        <span className="dot up" /> החודשים היקרים: <strong>{names(seasonality.best_months)}</strong>
        <span className="sep">·</span>
        <span className="dot down" /> הזולים: <strong>{names(seasonality.worst_months)}</strong>
      </div>

      <div className="chart" dir="ltr">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={seasonality.months} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <XAxis dataKey="month" tickFormatter={monthShort} tick={{ fontSize: 11 }} interval={0} />
            <YAxis tickFormatter={(value: number) => `${value > 0 ? "+" : ""}${value}%`} tick={{ fontSize: 12 }} />
            <ReferenceLine y={0} stroke="#4a5568" />
            <Tooltip
              formatter={(value: any, _name: any, item: any) => [`${pct(value)} · ${price(item.payload.mean)}`, "לעומת הממוצע"]}
              labelFormatter={(label: any) => seasonality.months[Number(label) - 1]?.name_he ?? String(label)}
              contentStyle={{ direction: "rtl", fontFamily: "inherit" }}
            />
            <Bar dataKey="vs_annual_pct" radius={[4, 4, 0, 0]}>
              {seasonality.months.map((month) => (
                <Cell
                  key={month.month}
                  fill={color(month, seasonality.best_months, seasonality.worst_months)}
                  stroke={month.month === currentMonth ? "#1a202c" : undefined}
                  strokeWidth={month.month === currentMonth ? 2 : 0}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="footnote">המסגרת השחורה מסמנת את החודש הנוכחי. מבוסס על {seasonality.baseline_years.length} שנים.</p>
    </section>
  );
}
