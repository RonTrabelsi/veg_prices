import { Forecast, Overview, VerdictLabel } from "../api";
import { date, horizonLabel, pct, price, trendClass } from "../format";

const VERDICTS: Record<VerdictLabel, { title: string; hint: string; icon: string }> = {
  wait: { title: "כדאי לחכות", hint: "המחיר צפוי לעלות בחודש הקרוב", icon: "⏳" },
  sell: { title: "כדאי למכור עכשיו", hint: "המחיר צפוי לרדת בחודש הקרוב", icon: "✅" },
  hold: { title: "המחיר צפוי להישאר יציב", hint: "אין יתרון ברור לחכות או להזדרז", icon: "➡️" },
};

export default function ForecastCard({ forecast, overview }: { forecast: Forecast; overview: Overview }) {
  const verdict = VERDICTS[forecast.verdict.label];
  const month = forecast.horizons.find((point) => point.horizon_days === forecast.verdict.horizon_days);
  return (
    <section className="card forecast">
      <header className="card-header">
        <h2>מה צפוי?</h2>
      </header>

      <div className={`verdict ${forecast.verdict.label} ${forecast.verdict.confidence}`}>
        <span className="verdict-icon" aria-hidden>
          {verdict.icon}
        </span>
        <div>
          <div className="verdict-title">{verdict.title}</div>
          <div className="verdict-hint">
            {verdict.hint} · {pct(forecast.verdict.change_pct)} · ביטחון {forecast.verdict.confidence === "high" ? "גבוה" : "נמוך"}
          </div>
        </div>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>מתי</th>
            <th>מחיר צפוי</th>
            <th>טווח סביר</th>
            <th>שינוי</th>
          </tr>
        </thead>
        <tbody>
          {forecast.horizons.map((point) => (
            <tr key={point.horizon_days}>
              <td>
                <div>{horizonLabel(point.horizon_days)}</div>
                <div className="muted small">{date(point.target_date)}</div>
              </td>
              <td className="strong">{price(point.point)}</td>
              <td className="muted">
                {price(point.low)} – {price(point.high)}
              </td>
              <td>
                <span className={`chip ${trendClass(point.change_vs_now_pct)}`}>{pct(point.change_vs_now_pct)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="footnote">
        התחזית משלבת את המחיר הנוכחי ({price(overview.last_price)}) עם המחיר האופייני לעונה. הטווח מכסה 80% ממקרי העבר, לפי בדיקה על
        השנים האחרונות.
        {month?.mae != null && month.naive_mae != null && (
          <>
            {" "}
            בתחזית לחודש: שגיאה ממוצעת {price(month.mae)}, לעומת {price(month.naive_mae)} אם מניחים שהמחיר לא ישתנה.
          </>
        )}
        {month && month.weather_adjustment !== 0 && <> כולל התאמה למזג האוויר של {pct((month.weather_adjustment / (month.point - month.weather_adjustment)) * 100)}.</>}
      </p>
    </section>
  );
}
