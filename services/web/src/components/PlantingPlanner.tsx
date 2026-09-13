import { useEffect, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Planting, fetchPlanting } from "../api";
import { date, monthShort, pct, price, trendClass } from "../format";

export default function PlantingPlanner({ vegetable, initial }: { vegetable: string; initial: Planting }) {
  const [daysToHarvest, setDaysToHarvest] = useState(initial.days_to_harvest);
  const [windowDays, setWindowDays] = useState(initial.harvest_window_days);
  const [planting, setPlanting] = useState<Planting>(initial);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setPlanting(initial);
    setDaysToHarvest(initial.days_to_harvest);
    setWindowDays(initial.harvest_window_days);
  }, [initial]);

  useEffect(() => {
    if (daysToHarvest === planting.days_to_harvest && windowDays === planting.harvest_window_days) return;
    const timer = setTimeout(() => {
      setBusy(true);
      fetchPlanting(vegetable, daysToHarvest, windowDays)
        .then(setPlanting)
        .catch(() => undefined)
        .finally(() => setBusy(false));
    }, 400);
    return () => clearTimeout(timer);
  }, [daysToHarvest, windowDays, vegetable, planting]);

  const best = planting.best_windows.slice(0, 3);
  return (
    <section className="card planting">
      <header className="card-header">
        <h2>מתי לשתול?</h2>
        <span className="stamp">כדי שהקטיף ייפול בתקופה שבה המחיר גבוה</span>
      </header>

      <div className="inputs">
        <label>
          ימים משתילה לקטיף
          <input type="number" min={20} max={300} value={daysToHarvest} onChange={(event) => setDaysToHarvest(Number(event.target.value) || 0)} />
        </label>
        <label>
          ימי קטיף
          <input type="number" min={7} max={120} value={windowDays} onChange={(event) => setWindowDays(Number(event.target.value) || 0)} />
        </label>
        {busy && <span className="muted small">מחשב…</span>}
      </div>

      <ol className="windows">
        {best.map((window, index) => (
          <li key={window.plant_date} className="window">
            <span className="rank">{index + 1}</span>
            <div className="window-body">
              <div>
                שתילה <strong>{date(window.plant_date)}</strong> ← קטיף {date(window.harvest_start)} – {date(window.harvest_end)}
              </div>
              <div className="muted small">
                מחיר צפוי בקטיף <strong>{price(window.expected_price)}</strong>{" "}
                <span className={`chip ${trendClass(window.vs_annual_pct, 5)}`}>{pct(window.vs_annual_pct)} לעומת הממוצע</span>
              </div>
            </div>
          </li>
        ))}
      </ol>

      <h3 className="sub">מחיר אופייני לפי חודש הקטיף</h3>
      <div className="chart" dir="ltr">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={planting.by_harvest_month} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
            <XAxis dataKey="month" tickFormatter={monthShort} tick={{ fontSize: 11 }} interval={0} />
            <YAxis tick={{ fontSize: 11 }} domain={["auto", "auto"]} />
            <Tooltip
              formatter={(value: any, _name: any, item: any) => [`${price(value)} · ${pct(item.payload.vs_annual_pct)}`, "מחיר צפוי"]}
              labelFormatter={(label: any) => planting.by_harvest_month[Number(label) - 1]?.name_he ?? String(label)}
              contentStyle={{ direction: "rtl", fontFamily: "inherit" }}
            />
            <Bar dataKey="expected_price" radius={[3, 3, 0, 0]}>
              {planting.by_harvest_month.map((month) => (
                <Cell key={month.month} fill={month.vs_annual_pct >= 5 ? "#2f855a" : month.vs_annual_pct <= -5 ? "#c53030" : "#a0aec0"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="footnote">
        המחיר הצפוי הוא המחיר האופייני לעונה ברמת המחירים של השנה האחרונה. הוא לא מביא בחשבון מזג אוויר, מחסור בעובדים או שינויים בשטחי הגידול.
      </p>
    </section>
  );
}
