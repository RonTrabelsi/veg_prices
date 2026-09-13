import { useEffect, useMemo, useState } from "react";
import { CatalogItem, fetchCatalog, friendlyError, loadVegetable } from "../api";
import { date, price } from "../format";

interface Props {
  current: string;
  onClose: () => void;
  onLoaded: (name: string) => void;
}

export default function CatalogPanel({ current, onClose, onLoaded }: Props) {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const refresh = (force = false) => {
    setLoading(true);
    setError(null);
    fetchCatalog(force)
      .then(setItems)
      .catch((err: Error) => setError(friendlyError(err.message)))
      .finally(() => setLoading(false));
  };

  useEffect(() => refresh(), []);

  const visible = useMemo(() => {
    const needle = filter.trim();
    return items.filter((item) => !needle || item.name.includes(needle));
  }, [items, filter]);

  const load = (item: CatalogItem) => {
    setBusy(item.name);
    setDone(null);
    setError(null);
    loadVegetable(item.name)
      .then((result) => {
        setDone(`${result.vegetable_name}: נטענו ${result.scraped_days.toLocaleString("he-IL")} ימי מחירים`);
        onLoaded(item.name);
        refresh(true);
      })
      .catch((err: Error) => setError(friendlyError(err.message)))
      .finally(() => setBusy(null));
  };

  return (
    <div className="overlay" onClick={onClose}>
      <section className="panel" onClick={(event) => event.stopPropagation()} role="dialog" aria-label="כל הירקות">
        <header className="panel-header">
          <div>
            <h2>כל הירקות באתר מועצת הצמחים</h2>
            <p className="muted small">בחירת ירק טוענת את כל היסטוריית המחירים שלו (עד דקה). ירק שנטען מתעדכן מאז אוטומטית כל יום.</p>
          </div>
          <button className="btn ghost" onClick={onClose} aria-label="סגירה">
            ✕
          </button>
        </header>

        <input className="search" placeholder="חיפוש…" value={filter} onChange={(event) => setFilter(event.target.value)} autoFocus />

        {error && <div className="banner error">{error}</div>}
        {done && <div className="banner ok">{done}</div>}
        {loading && <div className="banner loading">קורא את רשימת המוצרים מהאתר…</div>}

        <ul className="catalog">
          {visible.map((item) => {
            const tracked = item.indexed_days > 0;
            const isBusy = busy === item.name;
            return (
              <li key={item.name} className={`catalog-row ${item.name === current ? "current" : ""}`}>
                <div className="catalog-main">
                  <div className="strong">{item.name}</div>
                  <div className="muted small">
                    {item.last_price != null && item.last_date ? (
                      <>
                        {price(item.last_price)} באתר · {date(item.last_date)}
                      </>
                    ) : (
                      "לא מופיע באתר בשבועיים האחרונים"
                    )}
                    {tracked && item.data_from && (
                      <>
                        {" · "}
                        <span className="tracked">במעקב: {item.indexed_days.toLocaleString("he-IL")} ימים מ־{item.data_from.slice(0, 4)}</span>
                      </>
                    )}
                  </div>
                </div>
                <button className={`btn ${tracked ? "ghost" : ""}`} disabled={busy != null || item.days_on_site === 0} onClick={() => load(item)}>
                  {isBusy ? "טוען…" : tracked ? "עדכן" : "טען היסטוריה"}
                </button>
              </li>
            );
          })}
          {!loading && visible.length === 0 && <li className="muted">לא נמצאו ירקות.</li>}
        </ul>
      </section>
    </div>
  );
}
