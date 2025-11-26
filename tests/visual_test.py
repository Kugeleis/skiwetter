import os
import re

from playwright.sync_api import sync_playwright

# To run this test with Vivaldi, you need to provide the path to the Vivaldi executable.
# Example: pytest visual_test.py --browser-path /usr/bin/vivaldi


def test_ski_weather_dashboard():
    # Get browser path from environment variable or default to None (Playwright's bundled Chromium)
    browser_path = os.environ.get("BROWSER_PATH")

    with sync_playwright() as p:
        if browser_path:
            print(f"Launching browser from: {browser_path}")
            browser = p.chromium.launch(executable_path=browser_path, headless=True)
        else:
            print("Launching bundled Chromium")
            browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        # Capture console messages
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

        # Navigate to the app
        # Assuming the app is running on localhost:8000
        try:
            page.goto("http://localhost:8000", wait_until="networkidle")

            # Wait for the date element to be updated by the script
            date_element = page.wait_for_selector("#date-value", timeout=5000)

            # Check if the date has the correct format e.g. "Montag, 24.11.25"
            date_text = date_element.inner_text()
            assert re.match(r"\w+, \d{2}\.\d{2}\.\d{2}", date_text), f"Date format is incorrect: {date_text}"

            # Verify title
            assert "Skiwetter Altenberg" in page.title()

            # Verify header
            assert page.is_visible("h1")
            header_text = page.inner_text("h1")
            assert "Altenberg Skiwetter" in header_text

            # Verify that the notes section is visible and contains the correct text
            notes_section = page.wait_for_selector(".notes-section", timeout=5000)
            assert notes_section.is_visible()
            notes_text = notes_section.inner_text()
            assert "anmerkungen" in notes_text.lower()
            assert "Der erste Neuschnee" in notes_text

            # Take a screenshot
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path="screenshots/dashboard.png", full_page=True)
            print("Screenshot saved to screenshots/dashboard.png")

        except Exception as e:
            print(f"Test failed: {e}")
            raise e
        finally:
            browser.close()


def test_mobile_layout():
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

        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        # Navigate to the app
        try:
            page.goto("http://localhost:8000", wait_until="networkidle")

            # Wait for the date element to be updated by the script
            page.wait_for_selector("#date-value", timeout=5000)

            # Verify that the notes section is visible
            notes_section = page.wait_for_selector(".notes-section", timeout=5000)
            assert notes_section.is_visible()

            # Take a screenshot
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path="screenshots/dashboard-mobile.png", full_page=True)
            print("Screenshot saved to screenshots/dashboard-mobile.png")

        except Exception as e:
            print(f"Mobile test failed: {e}")
            raise e
        finally:
            browser.close()


if __name__ == "__main__":
    # Simple wrapper to run without pytest if needed
    test_ski_weather_dashboard()
    test_mobile_layout()
