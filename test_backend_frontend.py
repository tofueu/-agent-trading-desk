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
    assert 'fetch(`http://localhost:5000/api/metrics' in content

def test_backend_api():
    # Start the backend server as a subprocess for this test
    backend_process = subprocess.Popen(["python3", "backend/app.py"])

    try:
        # Wait a bit for the server to start
        time.sleep(2)

        response = requests.get('http://localhost:5000/api/metrics')
        assert response.status_code == 200

        data = response.json()
        assert data.get('status') == 'success'

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
