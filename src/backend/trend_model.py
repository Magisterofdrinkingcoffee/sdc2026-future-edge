"""Model 2 – AI-trend forecaster.

Input: monthly counts of new arXiv papers for one AI research area (e.g. "LLM code generation").
Model: log-linear regression  log(papers + 1) = a + b * month   (ordinary least squares)
  - b is the monthly growth rate on a log scale; yearly growth = exp(12 b) - 1
  - its standard error gives an 80% interval for the growth  -> the "range" in the app
  - the same fit projects the next 36 months with an 80% prediction band
Validation (backtest): fit on the first 24 months, predict the total of the last 12 months, and
compare with the naive guess "next year = last year". See backtest().

Plain Python, no numpy, so it runs inside the app (Replit / Vercel) and in tools/build_trends.py.
"""
import math

Z80 = 1.2816  # two-sided 80% interval (normal approximation; n = 36 months)


def _ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    s2 = sum(r * r for r in resid) / (n - 2)
    return a, b, math.sqrt(s2), math.sqrt(s2 / sxx), mx, sxx


def fit(counts, horizon=36):
    """counts: list of monthly paper counts, oldest first. Returns growth, interval and forecast."""
    if len(counts) < 12:
        raise ValueError("need at least 12 months")
    xs = list(range(len(counts)))
    ys = [math.log(c + 1) for c in counts]
    a, b, s, se_b, mx, sxx = _ols(xs, ys)
    n = len(xs)
    growth = math.exp(12 * b) - 1
    low, high = math.exp(12 * (b - Z80 * se_b)) - 1, math.exp(12 * (b + Z80 * se_b)) - 1
    forecast = []
    for h in range(1, horizon + 1):
        x = n - 1 + h
        mid = a + b * x
        se = s * math.sqrt(1 + 1 / n + (x - mx) ** 2 / sxx)
        forecast.append({"step": h, "mid": round(math.exp(mid) - 1, 1),
                         "low": round(max(0.0, math.exp(mid - Z80 * se) - 1), 1),
                         "high": round(math.exp(mid + Z80 * se) - 1, 1)})
    ss_tot = sum((y - sum(ys) / n) ** 2 for y in ys)
    r2 = 1 - (s * s * (n - 2)) / ss_tot if ss_tot else 0.0
    return {"growth": round(growth, 3), "growth_low": round(low, 3), "growth_high": round(high, 3),
            "monthly_slope": round(b, 5), "r2": round(r2, 3), "n_months": n, "forecast": forecast}


def backtest(counts, train=24, test=12):
    """Fit on the first `train` months, predict the total of the next `test` months."""
    if len(counts) < train + test:
        return None
    tr, te = counts[:train], counts[train:train + test]
    f = fit(tr, horizon=test)
    pred = sum(p["mid"] for p in f["forecast"])
    low = sum(p["low"] for p in f["forecast"])
    high = sum(p["high"] for p in f["forecast"])
    actual = sum(te)
    naive = sum(tr[-test:])  # "next year = last year"
    return {"actual": actual, "model": round(pred), "naive": naive,
            "model_error": round(abs(pred - actual) / max(actual, 1), 3),
            "naive_error": round(abs(naive - actual) / max(actual, 1), 3),
            "in_band": low <= actual <= high}
