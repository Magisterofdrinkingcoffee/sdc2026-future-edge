"""Model 2 – AI-trend forecaster.

Input: monthly counts of new arXiv papers for one AI research area (e.g. "LLM code generation").
Model: damped log-linear trend
  1. ordinary least squares  log(papers + 1) = a + b * month
  2. project forward from the last fitted month with the slope fading by PHI each month
     (a "damped trend", Gardner & McKenzie 1985):  log level after h months = level + b * (PHI + PHI^2 + ... + PHI^h)
  - growth = expected change in papers over the next 12 months = exp(b * D12) - 1, D12 = PHI + ... + PHI^12
  - the standard error of b gives an 80% interval for that growth -> the "range" in the app
  - the next 36 months come with an 80% prediction band
Why damped: AI research boomed in 2023-24 and is slowing; a plain exponential over-shot badly in the
backtest. PHI is chosen by select_phi() using only the training months (no peeking at the test year).
Validation (backtest): fit on the first 24 months, predict the total of the last 12 months, and
compare with the naive guess "next year = last year". See backtest().

Plain Python, no numpy, so it runs inside the app (Replit / Vercel) and in tools/build_trends.py.
"""
import math

Z80 = 1.2816  # two-sided 80% interval (normal approximation; n = 36 months)
PHI = 0.8      # default damping; build() recomputes it with select_phi()
PHI_GRID = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.6, 0.5]


def _ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    s2 = sum(r * r for r in resid) / (n - 2)
    return a, b, math.sqrt(s2), math.sqrt(s2 / sxx), mx, sxx


def _damp(phi, h):
    return sum(phi ** k for k in range(1, h + 1))


def fit(counts, horizon=36, phi=PHI):
    """counts: list of monthly paper counts, oldest first. Returns growth, interval and forecast."""
    if len(counts) < 12:
        raise ValueError("need at least 12 months")
    xs = list(range(len(counts)))
    ys = [math.log(c + 1) for c in counts]
    a, b, s, se_b, mx, sxx = _ols(xs, ys)
    n = len(xs)
    level = a + b * (n - 1)
    d12 = _damp(phi, 12)
    growth = math.exp(b * d12) - 1
    low, high = math.exp((b - Z80 * se_b) * d12) - 1, math.exp((b + Z80 * se_b) * d12) - 1
    forecast = []
    for h in range(1, horizon + 1):
        x = n - 1 + _damp(phi, h)  # effective position on the fitted line
        mid = level + b * _damp(phi, h)
        se = s * math.sqrt(1 + 1 / n + (x - mx) ** 2 / sxx)
        forecast.append({"step": h, "mid": round(math.exp(mid) - 1, 1),
                         "low": round(max(0.0, math.exp(mid - Z80 * se) - 1), 1),
                         "high": round(math.exp(mid + Z80 * se) - 1, 1)})
    ss_tot = sum((y - sum(ys) / n) ** 2 for y in ys)
    r2 = 1 - (s * s * (n - 2)) / ss_tot if ss_tot else 0.0
    return {"growth": round(growth, 3), "growth_low": round(low, 3), "growth_high": round(high, 3),
            "past_growth": round(math.exp(12 * b) - 1, 3), "phi": phi,
            "monthly_slope": round(b, 5), "r2": round(r2, 3), "n_months": n, "forecast": forecast}


def _rel_error(counts, train, test, phi):
    f = fit(counts[:train], horizon=test, phi=phi)
    actual = sum(counts[train:train + test])
    return abs(sum(p["mid"] for p in f["forecast"]) - actual) / max(actual, 1)


def select_phi(series_list, train=24, grid=PHI_GRID, tolerance=0.005):
    """Pick the damping using only the first `train` months of every series: fit on the first half,
    predict the second half. Rule: the largest PHI whose mean error is within `tolerance` of the best."""
    half = train // 2
    usable = [s for s in series_list if len(s) >= train]
    if not usable:
        return PHI, {}
    errs = {p: sum(_rel_error(s, half, half, p) for s in usable) / len(usable) for p in grid}
    best = min(errs.values())
    return max(p for p in grid if errs[p] <= best + tolerance), {p: round(e, 3) for p, e in errs.items()}


def backtest(counts, train=24, test=12, phi=PHI):
    """Fit on the first `train` months, predict the total of the next `test` months."""
    if len(counts) < train + test:
        return None
    tr, te = counts[:train], counts[train:train + test]
    f = fit(tr, horizon=test, phi=phi)
    pred = sum(p["mid"] for p in f["forecast"])
    low = sum(p["low"] for p in f["forecast"])
    high = sum(p["high"] for p in f["forecast"])
    actual = sum(te)
    naive = sum(tr[-test:])  # "next year = last year"
    return {"actual": actual, "model": round(pred), "naive": naive,
            "model_error": round(abs(pred - actual) / max(actual, 1), 3),
            "naive_error": round(abs(naive - actual) / max(actual, 1), 3),
            "in_band": low <= actual <= high}
