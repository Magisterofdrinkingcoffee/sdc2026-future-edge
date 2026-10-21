"""AI-trend signal layer (Must-have #2).

For every signal in data/signals.json we ask the arXiv API how many papers
matched the query in the last 12 months and in the 12 months before that.
growth = (recent - previous) / previous

Results are written to data/trends.json together with the source and the
fetch date, which the UI always shows. If arXiv is unreachable we keep the
last cached file (fallback) and say so.

Run manually:  python -m src.backend.trends
"""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from .data_store import DATA_DIR

ARXIV_URL = "http://export.arxiv.org/api/query"
SOURCE = "arXiv API – paper counts per topic, last 12 months vs previous 12 months"
PAUSE_SECONDS = 3  # arXiv asks clients to wait ~3 s between requests


def _count(query, start, end):
    rng = f"submittedDate:[{start:%Y%m%d}0000 TO {end:%Y%m%d}2359]"
    params = {"search_query": f"({query}) AND {rng}", "start": 0, "max_results": 0}
    url = ARXIV_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "FutureEdge-SDC2026/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read().decode("utf-8")
    m = re.search(r"<opensearch:totalResults[^>]*>(\d+)<", xml)
    if not m:
        raise ValueError("arXiv response had no totalResults")
    return int(m.group(1))


def refresh(progress=print):
    signals = json.loads((DATA_DIR / "signals.json").read_text(encoding="utf-8"))["signals"]
    now = datetime.now(timezone.utc)
    mid = now - timedelta(days=365)
    old = now - timedelta(days=730)
    out = {}
    for sig in signals:
        recent = _count(sig["query"], mid, now)
        time.sleep(PAUSE_SECONDS)
        previous = _count(sig["query"], old, mid)
        time.sleep(PAUSE_SECONDS)
        growth = (recent - previous) / previous if previous else None
        out[sig["id"]] = {
            "label": sig["label"],
            "query": sig["query"],
            "recent_12m": recent,
            "previous_12m": previous,
            "growth": round(growth, 3) if growth is not None else None,
        }
        progress(f"{sig['id']}: {previous} -> {recent} ({growth:+.0%})" if growth is not None else sig["id"])
    data = {
        "source": SOURCE,
        "source_url": "https://info.arxiv.org/help/api/",
        "fetched_at": now.isoformat(timespec="seconds"),
        "window": {"recent": [f"{mid:%Y-%m-%d}", f"{now:%Y-%m-%d}"], "previous": [f"{old:%Y-%m-%d}", f"{mid:%Y-%m-%d}"]},
        "is_sample": False,
        "signals": out,
    }
    (DATA_DIR / "trends.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


if __name__ == "__main__":
    refresh()
