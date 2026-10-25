import pytest
import io
from app import app, calculate_metrics
import pandas as pd
import numpy as np

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_missing_file_part(client):
    response = client.post('/api/upload')
    assert response.status_code == 400
    assert response.json['error'] == 'No file part'

def test_empty_filename(client):
    data = {'file': (io.BytesIO(b""), '')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.json['error'] == 'No selected file'

def test_invalid_extension(client):
    data = {'file': (io.BytesIO(b"some data"), 'test.txt')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.json['error'] == 'File must be CSV'

def test_missing_columns(client):
    csv_content = "timestamp,pnl\n2023-01-01T00:00:00Z,10"
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert 'Missing required columns' in response.json['error']

def test_missing_timezone(client):
    csv_content = "strategy_name,timestamp,pnl,return_pct\nStrategy1,2023-01-01 00:00:00,10,0.01"
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert 'timezone-aware' in response.json['error']

def test_valid_csv_metrics_calculation(client):
    csv_content = """strategy_name,timestamp,pnl,return_pct
Strat1,2023-01-01T00:00:00Z,10,0.01
Strat1,2023-01-02T00:00:00Z,-5,-0.005
Strat1,2023-01-03T00:00:00Z,20,0.02"""

    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'valid.csv')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    metrics = response.json['data']
    assert metrics['strategy_name'] == 'Strat1'
    assert metrics['total_trades'] == 3
    assert metrics['3y_annualized'] == 'N/A'
    assert metrics['5y_annualized'] == 'N/A'
    assert metrics['win_loss_ratio'] == 2.0
    assert 'win_rate' in metrics
    assert 'kelly' in metrics
    assert 'max_drawdown' in metrics

def test_long_term_metrics_calculation(client):
    # Create 6 years of dummy data
    dates = pd.date_range(start='2017-01-01', end='2023-01-01', freq='D', tz='UTC')
    df = pd.DataFrame({
        'strategy_name': 'LongTerm',
        'timestamp': dates,
        'pnl': np.random.normal(1, 10, len(dates)),
        'return_pct': np.random.normal(0.0001, 0.01, len(dates))
    })

    metrics = calculate_metrics(df, 'LongTerm')
    assert metrics['3y_annualized'] != 'N/A'
    assert metrics['5y_annualized'] != 'N/A'
    assert isinstance(metrics['3y_annualized'], float)
    assert isinstance(metrics['5y_annualized'], float)

def test_empty_csv_data(client):
    csv_content = "strategy_name,timestamp,pnl,return_pct\n"
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'empty_data.csv')}
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    metrics = response.json['data']
    assert metrics['total_trades'] == 0
    assert metrics['win_loss_ratio'] == 0.0
