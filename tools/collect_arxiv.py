"""Collect the real arXiv data for Model 2 (resumable), then rebuild data/trends.json.

    python -m tools.collect_arxiv

Counts new arXiv papers per month (Oct 2023 - Sep 2026) for every signal in
src/backend/data/signals.json. One request per signal per month, 3.5 s apart (arXiv's rule).
Saves after every answer to src/database/arxiv_monthly.json, so you can stop with Ctrl+C and
run it again later: it only asks for the months that are still missing.
If arXiv answers 429 (too many requests) it waits 60 s and tries again.
At the end it runs tools.build_trends (fit Model 2 + backtest) and prints the results.
Takes about 20 minutes from scratch. Needs only the Python standard library.
"""
import json
import time
import urllib.error
from datetime import datetime, timezone

from src.backend import trends
from tools import build_trends

FIRST, MONTHS, PAUSE = (2023, 10), 36, 3.5


def months():
    y, m = FIRST
    for _ in range(MONTHS):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def main():
    path = build_trends.SNAPSHOT
    snap = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"counts": {}}
    signals = json.loads((trends.DATA_DIR / "signals.json").read_text(encoding="utf-8"))["signals"]
    todo = [(s, y, m) for s in signals for y, m in months()
            if f"{y}-{m:02d}" not in snap["counts"].get(s["id"], {})]
    print(f"{len(todo)} months to collect (~{len(todo) * PAUSE / 60:.0f} min)")
    for i, (sig, y, m) in enumerate(todo, 1):
        while True:
            try:
                n = trends._count_month(sig["query"], y, m)
                break
            except urllib.error.HTTPError as e:
                wait = 60 if e.code in (429, 503) else 10
                print(f"  arXiv said {e.code}, waiting {wait} s")
                time.sleep(wait)
            except Exception as e:  # network hiccup or arXiv error page
                print(f"  {e}, waiting 10 s")
                time.sleep(10)
        snap["counts"].setdefault(sig["id"], {})[f"{y}-{m:02d}"] = n
        snap["collected_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        snap["source"] = "arXiv API export.arxiv.org (max_results=1, opensearch:totalResults per month)"
        snap["complete"] = i == len(todo)
        path.write_text(json.dumps(snap, indent=1), encoding="utf-8")
        print(f"[{i}/{len(todo)}] {sig['id']} {y}-{m:02d}: {n}")
        time.sleep(PAUSE)
    snap["complete"] = True
    path.write_text(json.dumps(snap, indent=1), encoding="utf-8")
    build_trends.main()
    print("\nDone. Commit src/database/arxiv_monthly.json and src/backend/data/trends.json.")


if __name__ == "__main__":
    main()
