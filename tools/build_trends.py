"""Rebuild data/trends.json (Model 2) from the saved arXiv snapshot.

    python -m tools.build_trends

src/database/arxiv_monthly.json holds new-paper counts per month for each signal in
src/backend/data/signals.json, collected from the arXiv API (export.arxiv.org/api/query,
one request per signal per month, 3+ s apart). This lets the app ship real trend data even on
hosts that can not call arXiv. On Replit the "Refresh trend data" button
re-collects it live.
"""
import json
from pathlib import Path

from src.backend import trends

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "src" / "database" / "arxiv_monthly.json"


def main():
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if snap.get("complete") is False:
        raise SystemExit("Snapshot is still incomplete - run python -m tools.collect_arxiv to finish it.")
    signals = json.loads((trends.DATA_DIR / "signals.json").read_text(encoding="utf-8"))["signals"]
    data = trends.build(snap["counts"], signals, snap["collected_at"],
                        source=trends.SOURCE + f" (snapshot collected {snap['collected_at'][:10]})")
    (trends.DATA_DIR / "trends.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data["backtest"], indent=2))
    for sid, s in data["signals"].items():
        print(f"{sid:20s} growth {s['growth']:+.0%}  80% range {s['growth_low']:+.0%} .. {s['growth_high']:+.0%}  r2={s['r2']}")


if __name__ == "__main__":
    main()
