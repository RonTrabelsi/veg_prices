import { Overview } from "../api";
import { date, pct, price, trendClass } from "../format";

export default function TodayCard({ overview }: { overview: Overview }) {
  const stale = overview.days_since_update > 3;
  return (
    <section className="card today">
      <header className="card-header">
        <h2>המחיר היום</h2>
        <span className={`stamp ${stale ? "warn" : ""}`}>
          {stale ? `לא עודכן ${overview.days_since_update} ימים · ` : ""}
          עודכן {date(overview.last_date)}
        </span>
      </header>

      <div className="big-price">
        <span className="value">{price(overview.last_price)}</span>
        <span className="unit">לק״ג</span>
      </div>
      {overview.special_price != null && (
        <div className="muted">
          מחיר מבצע: <strong>{price(overview.special_price)}</strong>
        </div>
      )}

      <div className="stats">
        <div className={`stat ${trendClass(overview.change_7d_pct)}`}>
          <span className="stat-value">{pct(overview.change_7d_pct)}</span>
          <span className="stat-label">לעומת שבוע שעבר</span>
        </div>
        <div className={`stat ${trendClass(overview.vs_norm_pct, 5)}`}>
          <span className="stat-value">{pct(overview.vs_norm_pct)}</span>
          <span className="stat-label">
            לעומת הרגיל ב{overview.month_name_he} ({price(overview.seasonal_norm_now)})
          </span>
        </div>
        <div className="stat neutral">
          <span className="stat-value">{overview.month_percentile == null ? "—" : `${Math.round(overview.month_percentile)}%`}</span>
          <span className="stat-label">מהימים ב{overview.month_name_he} בשנים האחרונות היו זולים יותר</span>
        </div>
      </div>
    </section>
  );
}
