import pytest
from playwright.sync_api import sync_playwright
import argparse
import sys
import os

# To run this test with Vivaldi, you need to provide the path to the Vivaldi executable.
# Example: pytest visual_test.py --browser-path /usr/bin/vivaldi

def test_ski_weather_dashboard():
    # Get browser path from environment variable or default to None (Playwright's bundled Chromium)
    browser_path = os.environ.get("BROWSER_PATH")
    
    with sync_playwright() as p:
        if browser_path:
            print(f"Launching browser from: {browser_path}")
            browser = p.chromium.launch(executable_path=browser_path, headless=False)
        else:
            print("Launching bundled Chromium")
            browser = p.chromium.launch(headless=True)
            
        page = browser.new_page()
        
        # Navigate to the app
        # Assuming the app is running on localhost:8000
        try:
            page.goto("http://localhost:8000")
            
            # Wait for the content to load
            page.wait_for_selector(".glass-card")
            
            # Verify title
            assert "Skiwetter Altenberg" in page.title()
            
            # Verify header
            assert page.is_visible("h1")
            header_text = page.inner_text("h1")
            assert "Altenberg Skiwetter" in header_text
            
            # Take a screenshot
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path="screenshots/dashboard.png", full_page=True)
            print("Screenshot saved to screenshots/dashboard.png")
            
        except Exception as e:
            print(f"Test failed: {e}")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    # Simple wrapper to run without pytest if needed
    test_ski_weather_dashboard()
