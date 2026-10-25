import pytest
import multiprocessing
import time
from playwright.sync_api import Page, expect
import os

@pytest.fixture(scope="session", autouse=True)
def start_server():
    from app import app
    def run_app():
        app.run(port=5000, use_reloader=False)

    p = multiprocessing.Process(target=run_app)
    p.start()
    time.sleep(1) # wait for server to start
    yield
    p.terminate()
    p.join()

def test_initial_render(page: Page):
    page.goto("http://localhost:5000")
    expect(page.locator("h1")).to_have_text("Trading operations console")
    expect(page.locator("#uploadBtn")).to_be_visible()

def test_upload_missing_file_error(page: Page):
    page.goto("http://localhost:5000")
    page.click("#uploadBtn")
    toast = page.locator("#toast")
    expect(toast).to_be_visible()
    expect(toast).to_contain_text("Please select a CSV file first.")

def test_upload_valid_csv(page: Page, tmp_path):
    csv_content = """strategy_name,timestamp,pnl,return_pct
TestStrat,2023-01-01T00:00:00Z,10,0.01
TestStrat,2023-01-02T00:00:00Z,-5,-0.005"""
    file_path = tmp_path / "valid.csv"
    file_path.write_text(csv_content)

    page.goto("http://localhost:5000")
    page.set_input_files("#csvUpload", str(file_path))
    page.click("#uploadBtn")

    # Wait for success toast
    toast = page.locator("#toast")
    expect(toast).to_be_visible()
    expect(toast).to_contain_text("successfully")

    # Check if strategy card is added
    card = page.locator(".strategy-card").first
    expect(card).to_be_visible()
    expect(card.locator(".strategy-title")).to_have_text("TestStrat")
    expect(card.locator("text=Total Trades").locator("xpath=..").locator(".s-val")).to_have_text("2")
    expect(card.locator("text=3Y Annualized").locator("xpath=..").locator(".s-val")).to_have_text("N/A")

def test_upload_invalid_csv_schema(page: Page, tmp_path):
    csv_content = """strategy_name,time,pnl
TestStrat,2023-01-01T00:00:00Z,10"""
    file_path = tmp_path / "invalid.csv"
    file_path.write_text(csv_content)

    page.goto("http://localhost:5000")
    page.set_input_files("#csvUpload", str(file_path))
    page.click("#uploadBtn")

    toast = page.locator("#toast")
    expect(toast).to_be_visible()
    expect(toast).to_contain_text("Missing required columns")
