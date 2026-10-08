import os
from playwright.sync_api import sync_playwright

def verify():
    abs_path = os.path.abspath("index.html")
    url = f"file://{abs_path}"

    os.makedirs("/home/jules/verification", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Desktop view
        context = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = context.new_page()
        page.goto(url)

        # Take screenshot of AI Control Center Desktop
        page.screenshot(path="/home/jules/verification/ai_center_desktop.png")

        # Click on Trading Console tab
        page.click("#tabTrading")
        page.wait_for_timeout(300)
        page.screenshot(path="/home/jules/verification/trading_console_desktop.png")

        # Switch back to AI center and dispatch a task
        page.click("#tabAiCenter")
        page.fill("#taskTitleInput", "Playwright 網頁響應式驗證與單元測試")
        page.click("#dispatchForm button[type='submit']")
        page.wait_for_timeout(300)
        page.screenshot(path="/home/jules/verification/ai_center_task_dispatched.png")

        # Mobile view
        mobile_context = browser.new_context(viewport={'width': 390, 'height': 844})
        mobile_page = mobile_context.new_page()
        mobile_page.goto(url)
        mobile_page.screenshot(path="/home/jules/verification/ai_center_mobile.png")

        browser.close()
        print("Frontend verification screenshots generated successfully.")

if __name__ == '__main__':
    verify()
