"""Read verified CSV trade returns without inventing multi-year performance."""
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def calculate_metrics(returns, timestamps=None, exit_reasons=None):
    """Returns are fractional *per-trade* returns, not USD PnL or percentages."""
    values = pd.to_numeric(pd.Series(returns), errors="coerce")
    if values.empty or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("Non-finite or empty return series")
    if (values <= -1).any():
        raise ValueError("Fractional trade returns must be greater than -1")
    equity = (1.0 + values).cumprod()
    total_return = float(equity.iloc[-1] - 1.0)
    baseline = np.concatenate(([1.0], equity.to_numpy(dtype=float)))
    peaks = np.maximum.accumulate(baseline)
    max_drawdown = float(np.min(baseline / peaks - 1.0))
    winners = values[values > 0]
    losers = values[values < 0]
    win_rate = float(len(winners) / len(values))
    profit_factor = float(winners.sum() / abs(losers.sum())) if len(losers) else None
    if len(winners) and len(losers):
        payoff = float(winners.mean() / abs(losers.mean()))
        kelly = float(win_rate - (1.0 - win_rate) / payoff)
    else:
        kelly = None

    annualized_return = None
    five_year_return = None  # Requires a validated five-year data coverage manifest.
    observed_span_return = None
    observed_days = None
    if timestamps is not None:
        dates = pd.to_datetime(pd.Series(timestamps), errors="coerce", utc=True)
        if len(dates) == len(values) and dates.notna().all():
            observed_days = (dates.max() - dates.min()).total_seconds() / 86400.0
            if observed_days > 0 and total_return > -1:
                annualized_return = float((1.0 + total_return) ** (365.2425 / observed_days) - 1.0)
                if observed_days >= 365.2425 * 4.9:
                    observed_span_return = total_return  # Date span alone does not prove full coverage.

    tp_count = sl_count = None
    if exit_reasons is not None and len(exit_reasons) == len(values):
        reasons = pd.Series(exit_reasons).astype(str).str.lower().str.strip()
        tp_count = int(reasons.isin(["tp", "take_profit", "take profit"]).sum())
        sl_count = int(reasons.isin(["sl", "stop_loss", "stop loss"]).sum())

    return {
        "win_rate": win_rate,
        "total_return": total_return,
        "five_year_return": five_year_return,
        "observed_span_return": observed_span_return,
        "annualized_return": annualized_return,
        "observed_days": observed_days,
        "max_drawdown": max_drawdown,
        "kelly": kelly,
        "profit_factor": profit_factor,
        "trade_count": int(len(values)),
        "tp_count": tp_count,
        "sl_count": sl_count,
        "return_basis": "sequential_compounded_fractional_trade_returns",
        "five_year_verified": False,  # No verified coverage manifest is loaded.
    }


@app.route("/api/metrics")
def get_metrics():
    filters = {name: request.args.get(name) for name in ("strategy", "timeframe", "product")}
    results = []
    if DATA_DIR.is_dir():
        for filepath in sorted(DATA_DIR.iterdir()):
            if filepath.suffix.lower() not in (".csv", ".log"):
                continue
            if filepath.name.startswith("TEST_FIXTURE_ONLY_"):
                continue
            try:
                df = pd.read_csv(filepath)
                # No arbitrary numeric-column fallback: PnL in dollars is not a return.
                return_col = next((c for c in ("return", "returns") if c in df.columns), None)
                if return_col is None or df.empty:
                    continue
                group_cols = [c for c in ("strategy", "timeframe", "product") if c in df.columns]
                groups = df.groupby(group_cols, dropna=False, sort=False) if group_cols else [(None, df)]
                for _, group in groups:
                    name = str(group["strategy"].iloc[0]) if "strategy" in group else filepath.stem.replace("_", " ").title()
                    timeframe = str(group["timeframe"].iloc[0]) if "timeframe" in group else "Unknown"
                    product = str(group["product"].iloc[0]) if "product" in group else "Unknown"
                    if any(value not in (None, "", "All") and value != candidate
                           for value, candidate in ((filters["strategy"], name),
                                                    (filters["timeframe"], timeframe),
                                                    (filters["product"], product))):
                        continue
                    metrics = calculate_metrics(
                        group[return_col].tolist(),
                        group["date"].tolist() if "date" in group else (
                            group["timestamp"].tolist() if "timestamp" in group else None
                        ),
                        group["exit_reason"].tolist() if "exit_reason" in group else None,
                    )
                    results.append({
                        "name": name, "timeframe": timeframe, "product": product,
                        "metrics": metrics, "timeseries": group[return_col].tolist(),
                        "source": filepath.name,
                    })
            except (ValueError, TypeError, KeyError, pd.errors.ParserError, UnicodeError) as exc:
                app.logger.warning("Skipping invalid dataset %s: %s", filepath.name, exc)

    if not results:
        return jsonify({"status": "error", "message": "Datasets unavailable"}), 404
    results.sort(key=lambda item: item["metrics"]["total_return"], reverse=True)
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank
    return jsonify({
        "status": "success",
        "data": {"strategies": results, "top_strategy": results[0],
                 "timeseries": results[0]["timeseries"]},
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
