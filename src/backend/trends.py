"""AI-trend signal layer (Must-have #2) powered by Model 2 (trend_model.py).

For every signal in data/signals.json we count new arXiv papers per month for the last 36 full
months, then Model 2 fits a log-linear trend per signal:
    growth        = expected yearly growth of research in that area
    growth_low/high = 80% interval  -> drives the low/high range of the Edge Score
    forecast      = next 36 months with an 80% band
Results go to data/trends.json with the source and fetch date, which the UI always shows.
If arXiv is unreachable we keep the last cached file (fallback) and say so.

Refresh live:            python -m src.backend.trends        (~20 min: 360 requests, 3 s apart)
Rebuild from a snapshot: python -m tools.build_trends        (src/database/arxiv_monthly.json)
"""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from . import trend_model
from .data_store import DATA_DIR

ARXIV_URL = "https://export.arxiv.org/api/query"
SOURCE = "arXiv API – new papers per month and topic; trend and range by Model 2 (log-linear regression)"
PAUSE_SECONDS = 3  # arXiv asks clients to wait ~3 s between requests
MONTHS = 36


def last_full_months(n=MONTHS, today=None):
    today = today or datetime.now(timezone.utc)
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        out.append((y, m))
    return list(reversed(out))


def _count_month(query, y, m):
    import calendar
    last = calendar.monthrange(y, m)[1]
    rng = f"submittedDate:[{y}{m:02d}010000 TO {y}{m:02d}{last}2359]"
    params = {"search_query": f"({query}) AND {rng}", "start": 0, "max_results": 1}
    url = ARXIV_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "FutureEdge-SDC2026/0.2"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        xml = resp.read().decode("utf-8")
    hit = re.search(r"<opensearch:totalResults[^>]*>(\d+)<", xml)
    if not hit or "/api/errors" in xml:
        raise ValueError("arXiv returned an error")
    return int(hit.group(1))


def build(monthly, signals, fetched_at, source=SOURCE):
    """monthly: {signal_id: {"YYYY-MM": count}} -> trends.json structure (pure function, testable)."""
    out, backtests = {}, []
    for sig in signals:
        series = monthly.get(sig["id"], {})
        months = sorted(series)
        counts = [series[k] for k in months]
        if len(counts) < 12:
            continue
        f = trend_model.fit(counts)
        bt = trend_model.backtest(counts)
        if bt:
            backtests.append(bt)
        last = months[-1]
        y, m = int(last[:4]), int(last[5:])
        steps = []
        for p in f["forecast"]:
            m += 1
            if m == 13:
                y, m = y + 1, 1
            steps.append({"month": f"{y}-{m:02d}", **{k: p[k] for k in ("mid", "low", "high")}})
        out[sig["id"]] = {
            "label": sig["label"], "query": sig["query"],
            "growth": f["growth"], "growth_low": f["growth_low"], "growth_high": f["growth_high"],
            "r2": f["r2"], "last_12m": sum(counts[-12:]), "previous_12m": sum(counts[-24:-12]) if len(counts) >= 24 else None,
            "monthly": {k: series[k] for k in months}, "forecast": steps, "backtest": bt,
        }
    summary = None
    if backtests:
        n = len(backtests)
        summary = {
            "what": "Fit on the first 24 months, predict the total papers of the last 12 months, per signal",
            "signals": n,
            "model_mean_error": round(sum(b["model_error"] for b in backtests) / n, 3),
            "naive_mean_error": round(sum(b["naive_error"] for b in backtests) / n, 3),
            "naive": "next 12 months = last 12 months",
            "model_better_on": sum(b["model_error"] < b["naive_error"] for b in backtests),
            "inside_80pct_band": sum(b["in_band"] for b in backtests),
        }
    return {
        "source": source, "source_url": "https://info.arxiv.org/help/api/", "fetched_at": fetched_at,
        "is_sample": False, "model": "Model 2: log-linear regression on monthly arXiv counts, 80% intervals",
        "backtest": summary, "signals": out,
    }


def refresh(progress=print):
    signals = json.loads((DATA_DIR / "signals.json").read_text(encoding="utf-8"))["signals"]
    monthly = {}
    for sig in signals:
        monthly[sig["id"]] = {}
        for y, m in last_full_months():
            for attempt in range(3):
                try:
                    monthly[sig["id"]][f"{y}-{m:02d}"] = _count_month(sig["query"], y, m)
                    break
                except Exception:
                    time.sleep(PAUSE_SECONDS * (attempt + 2))
            time.sleep(PAUSE_SECONDS)
        progress(f"{sig['id']}: {len(monthly[sig['id']])} months")
    data = build(monthly, signals, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    (DATA_DIR / "trends.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


if __name__ == "__main__":
    refresh()
