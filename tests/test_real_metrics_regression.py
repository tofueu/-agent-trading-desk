"""Regression coverage for evidence-based trading dashboard metrics."""
import pytest
from backend import app as backend


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(backend, "DATA_DIR", tmp_path)
    backend.app.config["TESTING"] = True
    return backend.app.test_client(), tmp_path


def test_no_datasets_fails_closed(client):
    api, _ = client
    response = api.get("/api/metrics")
    assert response.status_code == 404
    assert response.json["message"] == "Datasets unavailable"


def test_observed_returns_not_fabricated_five_year(client):
    api, root = client
    (root / "actual.csv").write_text(
        "strategy,timeframe,product,return\n"
        "Alpha,1H,BTCUSDT,0.10\n"
        "Alpha,1H,BTCUSDT,-0.05\n", encoding="utf-8"
    )
    response = api.get("/api/metrics")
    assert response.status_code == 200
    metrics = response.json["data"]["top_strategy"]["metrics"]
    assert metrics["total_return"] == pytest.approx(0.045)
    assert metrics["max_drawdown"] == pytest.approx(-0.05)
    assert metrics["win_rate"] == pytest.approx(0.5)
    assert metrics["kelly"] == pytest.approx(0.25)
    assert metrics["profit_factor"] == pytest.approx(2)
    assert metrics["five_year_return"] is None
    assert metrics["annualized_return"] is None
    assert metrics["tp_count"] is None
    assert metrics["sl_count"] is None
    assert metrics["trade_count"] == 2


def test_pnl_dollars_not_misread_as_fractional_return(client):
    api, root = client
    (root / "dollars.csv").write_text("pnl\n100\n-20\n", encoding="utf-8")
    assert api.get("/api/metrics").status_code == 404


def test_no_fallback_to_arbitrary_numeric_column(client):
    api, root = client
    (root / "volume.csv").write_text("volume\n100\n200\n", encoding="utf-8")
    assert api.get("/api/metrics").status_code == 404


def test_fixture_never_counted_as_real(client):
    api, root = client
    (root / "TEST_FIXTURE_ONLY_smc.csv").write_text("return\n0.5\n", encoding="utf-8")
    assert api.get("/api/metrics").status_code == 404


def test_explicit_exit_reasons_and_observed_dates(client):
    api, root = client
    (root / "observed.csv").write_text(
        "date,return,exit_reason\n"
        "2020-01-01,0.10,tp\n"
        "2025-01-01,-0.05,sl\n", encoding="utf-8"
    )
    response = api.get("/api/metrics")
    assert response.status_code == 200
    m = response.json["data"]["top_strategy"]["metrics"]
    assert m["tp_count"] == 1
    assert m["sl_count"] == 1
    assert m["five_year_return"] == pytest.approx(0.045)
    assert m["annualized_return"] is not None
    assert m["observed_days"] > 365 * 4.9


def test_separate_products_not_mixed(client):
    api, root = client
    (root / "trades.csv").write_text(
        "strategy,timeframe,product,return\n"
        "A,1D,BTC,0.10\n"
        "A,1D,ETH,-0.05\n", encoding="utf-8"
    )
    response = api.get("/api/metrics")
    assert response.status_code == 200
    assert len(response.json["data"]["strategies"]) == 2
    assert api.get("/api/metrics?product=ETH").json["data"]["top_strategy"]["product"] == "ETH"
