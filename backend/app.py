from flask import Flask, jsonify, request
import pandas as pd
import numpy as np
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def calculate_metrics(returns):
    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
    total_return = returns.sum()

    # Calculate cumulative returns and max drawdown
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.cummax()
    drawdowns = (cum_returns - running_max) / running_max
    max_drawdown = drawdowns.min()

    # Kelly fraction approximation
    mean_return = returns.mean()
    var_return = returns.var()
    kelly = mean_return / var_return if var_return > 0 else 0

    # Profit factor
    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    # Annualized return (assuming 252 trading days and 1 data point = 1 day for simplicity in this demo, though timeframe varies)
    # The prompt requests "five-year return" and "annualized return". We'll mock a 5-year factor for the demo calculation
    annualized_return = (1 + total_return) ** (252 / (len(returns) * 5)) - 1 if len(returns) > 0 else 0
    five_year_return = total_return * 5 # Simplified projection for the metric

    return {
        "win_rate": float(win_rate),
        "total_return": float(total_return),
        "five_year_return": float(five_year_return),
        "annualized_return": float(annualized_return),
        "max_drawdown": float(max_drawdown),
        "kelly": float(kelly),
        "profit_factor": float(profit_factor),
        "trade_count": int(len(returns)),
        "tp_count": int((returns > 0).sum()),
        "sl_count": int((returns < 0).sum())
    }

@app.route('/api/metrics')
def get_metrics():
    strategy_filter = request.args.get('strategy')
    timeframe_filter = request.args.get('timeframe')
    product_filter = request.args.get('product')

    try:
        with open('data/backtests.json', 'r') as f:
            datasets = json.load(f)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Dataset not found"}), 404

    # Calculate metrics for all and rank them by total return
    results = []
    for data in datasets:
        # Apply filters
        if strategy_filter and strategy_filter != "All" and data['strategy'] != strategy_filter: continue
        if timeframe_filter and timeframe_filter != "All" and data['timeframe'] != timeframe_filter: continue
        if product_filter and product_filter != "All" and data['product'] != product_filter: continue

        returns_series = pd.Series(data['returns'])
        metrics = calculate_metrics(returns_series)
        results.append({
            "name": data['strategy'],
            "timeframe": data['timeframe'],
            "product": data['product'],
            "metrics": metrics,
            "timeseries": data['returns']
        })

    if not results:
        return jsonify({"status": "success", "data": {"strategies": [], "top_strategy": None}})

    # Rank strategies by total return descending
    results.sort(key=lambda x: x['metrics']['total_return'], reverse=True)

    # Assign ranks
    for i, res in enumerate(results):
        res['rank'] = i + 1

    top_strategy = results[0]

    return jsonify({
        "status": "success",
        "data": {
            "strategies": results,
            "top_strategy": top_strategy,
            "timeseries": top_strategy['timeseries']
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
