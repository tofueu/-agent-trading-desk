import pytest
import os
import requests
import json
import time
import subprocess

def test_index_html_structure():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for IDs added for dynamic updates
    assert 'id="kpiKelly"' in content
    assert 'id="kpiWinRate"' in content
    assert 'id="kpiProfitFactor"' in content
    assert 'id="kpiMaxDrawdown"' in content
    assert 'id="totalPnL"' in content
    assert 'id="totalPnLSub"' in content
    assert 'id="extraMetrics"' in content
    assert 'strategyFilter' in content
    assert 'timeframeFilter' in content
    assert 'productFilter' in content

    # Check for fetchMetrics function
    assert 'fetchMetrics()' in content
    assert 'fetch(`http://127.0.0.1:5000/api/metrics' in content

def test_missing_datasets_response():
    # Temporarily hide datasets if any
    hidden = []
    if os.path.exists('data'):
        for f in os.listdir('data'):
            if f.endswith('.csv') and not f.startswith('TEST_FIXTURE_ONLY_'):
                os.rename(f'data/{f}', f'data/{f}.bak')
                hidden.append(f)

    backend_process = subprocess.Popen(["python3", "backend/app.py"])
    try:
        time.sleep(2)
        response = requests.get('http://127.0.0.1:5000/api/metrics')
        assert response.status_code == 404
        data = response.json()
        assert data.get('status') == 'error'
        assert data.get('message') == 'Datasets unavailable'
    finally:
        backend_process.terminate()
        backend_process.wait()
        for f in hidden:
            os.rename(f'data/{f}.bak', f'data/{f}')

def test_csv_metrics_parsing():
    if not os.path.exists('data'):
        os.makedirs('data')
    test_file = 'data/test_run.csv'
    with open(test_file, 'w') as f:
        f.write("timeframe,product,return\n1H,BTC/USD,0.01\n1H,BTC/USD,-0.005")

    backend_process = subprocess.Popen(["python3", "backend/app.py"])
    try:
        time.sleep(2)
        response = requests.get('http://127.0.0.1:5000/api/metrics')
        assert response.status_code == 200

        data = response.json()
        assert data.get('status') == 'success'
        assert 'Test Run' in data.get('data', {}).get('top_strategy', {}).get('name', '')

        metrics = data.get('data', {}).get('top_strategy', {}).get('metrics', {})
        assert 'win_rate' in metrics
        assert 'total_return' in metrics
        assert 'five_year_return' in metrics
        assert 'annualized_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'kelly' in metrics
        assert 'profit_factor' in metrics
        assert 'trade_count' in metrics
        assert 'tp_count' in metrics
        assert 'sl_count' in metrics
        assert metrics['trade_count'] > 0

    finally:
        backend_process.terminate()
        backend_process.wait()
        if os.path.exists(test_file):
            os.remove(test_file)
