import io
import json
import logging
import os
import time

import pdfplumber
import requests
import schedule
import yaml
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SkiWeatherScraper:
    """Scrapes ski weather data from the Altenberg website PDF."""

    BASE_URL = "https://www.altenberg.de"
    TAGES_NEWS_URL = (
        "https://www.altenberg.de/de/p/-de-p-tages-news-zum-download-47003971-/tages-news-zum-download/47003971/"
    )

    def __init__(self, data_file: str = "/data/weather.json"):
        """Initialize the scraper.

        Args:
            data_file: Path to save the extracted JSON data.
        """
        self.data_file = data_file

    def fetch_pdf_url(self) -> str | None:
        """Fetches the URL of the daily PDF.

        Returns:
            The absolute URL of the PDF, or None if not found.
        """
        try:
            logger.info(f"Fetching page: {self.TAGES_NEWS_URL}")
            response = requests.get(self.TAGES_NEWS_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            for a in soup.find_all("a", href=True):
                text = a.text.strip()
                href = a["href"]

                # Look for links that look like the download link
                if "Tages-News" in text and ("media%2Fdownload" in href or "media/download" in href or "r/" in href):
                    link = href
                    if not link.startswith("http"):
                        link = self.BASE_URL + link
                    logger.info(f"Found PDF link: {link}")
                    return link

                # Fallback: Check if text matches the pattern "Tages-News DD.MM.YYYY"
                if "Tages-News" in text and any(char.isdigit() for char in text):
                    link = href
                    if not link.startswith("http"):
                        link = self.BASE_URL + link
                    logger.info(f"Found PDF link (fallback): {link}")
                    return link

            logger.warning("PDF link not found.")
            return None
        except Exception as e:
            logger.error(f"Error fetching PDF URL: {e}")
            return None

    def download_pdf(self, url: str) -> io.BytesIO | None:
        """Downloads the PDF from the given URL.

        Args:
            url: The URL of the PDF.

        Returns:
            A BytesIO object containing the PDF data, or None on failure.
        """
        try:
            logger.info(f"Downloading PDF from: {url}")
            response = requests.get(url)
            response.raise_for_status()
            return io.BytesIO(response.content)
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None

    def _extract_from_cell(self, cell: str, idx: int, row: list[str], data: dict[str, str]) -> None:  # noqa: PLR0912
        """Helper to extract data from a single cell."""
        if "TAGES-NEWS" in cell:
            data["date"] = cell.replace("TAGES-NEWS - ", "").strip()

        if "Temperatur" in cell:
            # Value might be in the next cell
            if idx + 1 < len(row) and row[idx + 1]:
                val = row[idx + 1].strip()
                if "°C" in val:
                    data["temperature"] = val

            # Or in the same cell on a new line
            if data["temperature"] == "Unknown":
                lines = cell.split("\n")
                for i, line in enumerate(lines):
                    if "Temperatur" in line and i + 1 < len(lines):
                        candidate = lines[i + 1].strip()
                        if "°C" in candidate:
                            data["temperature"] = candidate

        if "Uhrzeit:" in cell:
            if "Uhrzeit:" in cell and "Uhr" in cell.split("Uhrzeit:")[1]:
                data["update_time"] = cell.split("Uhrzeit:")[1].strip()
            elif idx + 1 < len(row) and row[idx + 1]:
                data["update_time"] = row[idx + 1].strip()

        if "Wetterlage:" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                data["weather_condition"] = row[idx + 1].strip()
            else:
                parts = cell.split("Wetterlage:")
                if len(parts) > 1:
                    data["weather_condition"] = parts[1].strip()

        if "durchschnittliche Schneehöhe" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                data["snow_depth"] = row[idx + 1].strip()
            else:
                lines = cell.split("\n")
                for i, line in enumerate(lines):
                    if "durchschnittliche Schneehöhe" in line and i + 1 < len(lines):
                        data["snow_depth"] = lines[i + 1].strip()

        if "Schneeart:" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                data["snow_type"] = row[idx + 1].strip()
            else:
                parts = cell.split("Schneeart:")
                if len(parts) > 1:
                    data["snow_type"] = parts[1].strip()

        if "letzter Schneefall:" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                data["last_snowfall"] = row[idx + 1].strip()
            else:
                parts = cell.split("letzter Schneefall:")
                if len(parts) > 1:
                    data["last_snowfall"] = parts[1].strip()

    def extract_weather_data(self, pdf_file: io.BytesIO) -> dict[str, str] | None:
        """Extracts weather data from the PDF file.

        Args:
            pdf_file: The PDF file object.

        Returns:
            A dictionary containing weather data, or None on failure.
        """
        try:
            logger.info("Extracting data from PDF...")
            with pdfplumber.open(pdf_file) as pdf:
                if not pdf.pages:
                    logger.error("PDF has no pages.")
                    return None

                page = pdf.pages[0]
                tables = page.extract_tables()

                data: dict[str, str] = {
                    "date": "Unknown",
                    "temperature": "Unknown",
                    "weather_condition": "Unknown",
                    "snow_depth": "Unknown",
                    "snow_type": "Unknown",
                    "last_snowfall": "Unknown",
                    "update_time": "Unknown",
                }

                for table in tables:
                    for row in table:
                        for idx, cell in enumerate(row):
                            if not cell:
                                continue
                            self._extract_from_cell(cell, idx, row, data)

                logger.info(f"Extracted data: {data}")
                return data
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            return None

    def save_data(self, data: dict[str, str]) -> None:
        """Saves the weather data to a JSON file.

        Args:
            data: The weather data dictionary.
        """
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Data saved successfully.")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def run(self) -> None:
        """Runs the scraping job."""
        logger.info("Starting scraper job...")
        pdf_url = self.fetch_pdf_url()
        if pdf_url:
            pdf_file = self.download_pdf(pdf_url)
            if pdf_file:
                data = self.extract_weather_data(pdf_file)
                if data:
                    self.save_data(data)


def load_schedule_config(config_file: str = "/data/schedule.yaml") -> dict:
    """Load schedule configuration from YAML file.

    Args:
        config_file: Path to the schedule configuration file.

    Returns:
        Schedule configuration dictionary.
    """
    # Default configuration
    default_config = {"default": {"interval": 4, "unit": "hours"}}

    if not os.path.exists(config_file):
        logger.warning(f"Schedule config not found at {config_file}, using default (every 4 hours)")
        return default_config

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
            if not config:
                logger.warning("Empty schedule config, using default")
                return default_config
            logger.info(f"Loaded schedule config from {config_file}")
            return config
    except Exception as e:
        logger.error(f"Error loading schedule config: {e}, using default")
        return default_config


def setup_schedule(scraper: SkiWeatherScraper, config: dict) -> None:
    """Set up the scraper schedule based on configuration.

    Args:
        scraper: The scraper instance.
        config: Schedule configuration dictionary.
    """
    # Find the active schedule (first non-commented key)
    active_schedule = None
    for key, value in config.items():
        if value:  # Skip None/empty values
            active_schedule = (key, value)
            break

    if not active_schedule:
        logger.warning("No active schedule found, using default")
        schedule.every(4).hours.do(scraper.run)
        return

    schedule_name, schedule_config = active_schedule
    logger.info(f"Setting up schedule: {schedule_name}")

    # Handle interval-based schedules
    if "interval" in schedule_config and "unit" in schedule_config:
        interval = schedule_config["interval"]
        unit = schedule_config["unit"]

        if unit == "hours":
            schedule.every(interval).hours.do(scraper.run)
            logger.info(f"Scheduled to run every {interval} hour(s)")
        elif unit == "minutes":
            schedule.every(interval).minutes.do(scraper.run)
            logger.info(f"Scheduled to run every {interval} minute(s)")
        elif unit == "days":
            schedule.every(interval).days.do(scraper.run)
            logger.info(f"Scheduled to run every {interval} day(s)")
        else:
            logger.warning(f"Unknown unit: {unit}, using default")
            schedule.every(4).hours.do(scraper.run)

    # Handle time-based schedules
    elif "times" in schedule_config:
        times = schedule_config["times"]
        for time_str in times:
            schedule.every().day.at(time_str).do(scraper.run)
        logger.info(f"Scheduled to run at {len(times)} specific times per day")

    else:
        logger.warning("Invalid schedule config, using default")
        schedule.every(4).hours.do(scraper.run)


def main() -> None:
    scraper = SkiWeatherScraper()

    # Run once immediately
    scraper.run()

    # Load and set up schedule
    config = load_schedule_config()
    setup_schedule(scraper, config)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
