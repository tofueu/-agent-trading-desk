import os
import io
import pandas as pd
from flask import Flask, request, jsonify, send_file
import datetime

app = Flask(__name__)

def calculate_metrics(df, strategy_name):
    # Sort by timestamp
    df = df.sort_values('timestamp')

    total_trades = len(df)

    if total_trades == 0:
        return {
            'strategy_name': strategy_name,
            'total_trades': 0,
            'win_loss_ratio': 0.0,
            'max_drawdown': 0.0,
            'annualized_return': 0.0,
            'kelly': 0.0,
            '3y_annualized': 'N/A',
            '5y_annualized': 'N/A',
            'pnl_history': []
        }

    wins = df[df['pnl'] > 0]
    losses = df[df['pnl'] < 0]
    num_wins = len(wins)
    num_losses = len(losses)

    win_loss_ratio = num_wins / num_losses if num_losses > 0 else float('inf')

    win_rate = num_wins / total_trades if total_trades > 0 else 0

    avg_win = wins['return_pct'].mean() if num_wins > 0 else 0
    avg_loss = abs(losses['return_pct'].mean()) if num_losses > 0 else 0

    kelly = 0
    if avg_win > 0 and avg_loss > 0:
        b = avg_win / avg_loss
        kelly = win_rate - ((1 - win_rate) / b)

    # Calculate cumulative returns and drawdown
    df['cumulative_return'] = (1 + df['return_pct']).cumprod()
    df['peak'] = df['cumulative_return'].cummax()
    df['drawdown'] = (df['cumulative_return'] - df['peak']) / df['peak']
    max_drawdown = df['drawdown'].min()

    # Calculate annualized return
    start_date = df['timestamp'].iloc[0]
    end_date = df['timestamp'].iloc[-1]

    days_span = (end_date - start_date).days
    years_span = days_span / 365.25 if days_span > 0 else 0

    total_return = df['cumulative_return'].iloc[-1] - 1

    if years_span > 0:
        annualized_return = (1 + total_return) ** (1 / years_span) - 1
    else:
        annualized_return = total_return

    metrics = {
        'strategy_name': strategy_name,
        'total_trades': total_trades,
        'win_loss_ratio': round(win_loss_ratio, 4) if win_loss_ratio != float('inf') else 'inf',
        'max_drawdown': round(max_drawdown * 100, 2), # %
        'annualized_return': round(annualized_return * 100, 2), # %
        'kelly': round(kelly, 4),
        '3y_annualized': 'N/A',
        '5y_annualized': 'N/A',
        'pnl_history': df[['timestamp', 'pnl']].assign(timestamp=df['timestamp'].astype(str)).to_dict(orient='records')
    }

    if years_span >= 3:
        three_years_ago = end_date - pd.DateOffset(years=3)
        df_3y = df[df['timestamp'] >= three_years_ago]
        if not df_3y.empty:
            start_3y = df_3y['timestamp'].iloc[0]
            days_3y = (end_date - start_3y).days
            years_3y = days_3y / 365.25

            # calculate cumulative return from the first point in 3y period
            # to make it accurate we should re-base to 1
            if len(df_3y) > 0:
                ret_3y_series = df_3y['return_pct']
                cum_ret_3y = (1 + ret_3y_series).cumprod().iloc[-1] - 1
                if years_3y > 0:
                    ann_ret_3y = (1 + cum_ret_3y) ** (1 / years_3y) - 1
                else:
                    ann_ret_3y = cum_ret_3y
                metrics['3y_annualized'] = round(ann_ret_3y * 100, 2)

    if years_span >= 5:
        five_years_ago = end_date - pd.DateOffset(years=5)
        df_5y = df[df['timestamp'] >= five_years_ago]
        if not df_5y.empty:
            start_5y = df_5y['timestamp'].iloc[0]
            days_5y = (end_date - start_5y).days
            years_5y = days_5y / 365.25
            if len(df_5y) > 0:
                ret_5y_series = df_5y['return_pct']
                cum_ret_5y = (1 + ret_5y_series).cumprod().iloc[-1] - 1
                if years_5y > 0:
                    ann_ret_5y = (1 + cum_ret_5y) ** (1 / years_5y) - 1
                else:
                    ann_ret_5y = cum_ret_5y
                metrics['5y_annualized'] = round(ann_ret_5y * 100, 2)

    return metrics


@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not file.filename.endswith('.csv'):
         return jsonify({'error': 'File must be CSV'}), 400

    try:
        content = file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(content))

        # Schema validation
        required_cols = {'strategy_name', 'timestamp', 'pnl', 'return_pct'}
        if not required_cols.issubset(df.columns):
            return jsonify({'error': f'Missing required columns. Expected: {required_cols}'}), 400

        # Parse timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Enforce timezone awareness
        if not df.empty and df['timestamp'].dt.tz is None:
            return jsonify({'error': 'Timestamps must be timezone-aware (e.g., UTC)'}), 400

        strategy_name = df['strategy_name'].iloc[0] if not df.empty else "Unknown"

        metrics = calculate_metrics(df, strategy_name)

        return jsonify({'status': 'ok', 'data': metrics}), 200

    except pd.errors.ParserError:
        return jsonify({'error': 'Invalid CSV format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
