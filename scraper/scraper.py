import io
import json
import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
import shutil

import pdfplumber
import requests
from bs4 import BeautifulSoup

from common.helpers import get_data_file_path

# Get the data directory using the common helper function.
# This ensures consistency between local and Docker environments.
data_dir = get_data_file_path().parent


def setup_logging(log_file: Path | str = data_dir / "scraper.log") -> logging.Logger:
    """Configure logging with both file and console handlers.

    Sets up a rotating file handler that limits log file size to 1MB
    and keeps 1 backup file. Also configures console output for Docker compatibility.

    Args:
        log_file: Path to the log file.

    Returns:
        Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if function is called multiple times
    if logger.handlers:
        return logger

    # Create formatters
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler with rotation (1MB max size, 1 backup file)
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=1,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console handler for Docker/stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Configure logging
logger = setup_logging()


class SkiWeatherScraper:
    """Scrapes ski weather data from the Altenberg website PDF."""

    BASE_URL = "https://www.altenberg.de"
    TAGES_NEWS_URL = (
        "https://www.altenberg.de/de/p/-de-p-tages-news-zum-download-47003971-/tages-news-zum-download/47003971/"
    )

    def __init__(self, data_file: Path | str = data_dir / "weather.json"):
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

                # Check if the link text contains "Tages-News" and a date in the format DD.MM.YYYY
                if "Tages-News" in text and any(char.isdigit() for char in text):
                    # Further check if the href contains "media/download" or "r/"
                    if "media%2Fdownload" in href or "media/download" in href or "r/" in href:
                        link = href
                        if not link.startswith("http"):
                            link = self.BASE_URL + link
                        logger.info(f"Found PDF link: {link}")
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

    def _format_date_iso(self, date_str: str) -> str | None:
        """Convert date from DD.MM.YYYY to YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None

    def _extract_from_cell(self, cell: str, idx: int, row: list[str | None], data: dict[str, str]) -> None:  # noqa: PLR0912, PLR0915
        """Helper to extract data from a single cell."""
        if "TAGES-NEWS" in cell:
            raw_date = cell.replace("TAGES-NEWS - ", "").strip()
            iso_date = self._format_date_iso(raw_date)
            if iso_date:
                data["date"] = iso_date

        if "Temperatur" in cell:
            # Value might be in the next cell
            if idx + 1 < len(row) and row[idx + 1]:
                val = row[idx + 1]
                assert val is not None  # Type narrowing for mypy
                if "°C" in val:
                    data["temperature"] = val.strip()

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
                val = row[idx + 1]
                assert val is not None  # Type narrowing for mypy
                data["update_time"] = val.strip()

        if "Wetterlage:" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                val = row[idx + 1]
                assert val is not None  # Type narrowing for mypy
                data["weather_condition"] = val.strip()
            else:
                parts = cell.split("Wetterlage:")
                if len(parts) > 1:
                    data["weather_condition"] = parts[1].strip()

        if "durchschnittliche Schneehöhe" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                val = row[idx + 1]
                assert val is not None  # Type narrowing for mypy
                data["snow_depth"] = val.strip()
            else:
                lines = cell.split("\n")
                for i, line in enumerate(lines):
                    if "durchschnittliche Schneehöhe" in line and i + 1 < len(lines):
                        data["snow_depth"] = lines[i + 1].strip()

        if "Schneeart:" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                val = row[idx + 1]
                assert val is not None  # Type narrowing for mypy
                data["snow_type"] = val.strip()
            else:
                parts = cell.split("Schneeart:")
                if len(parts) > 1:
                    data["snow_type"] = parts[1].strip()

        if "letzter Schneefall:" in cell:
            if idx + 1 < len(row) and row[idx + 1]:
                val = row[idx + 1]
                assert val is not None  # Type narrowing for mypy
                data["last_snowfall"] = val.strip()
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
                    # Also copy to docs
                    docs_path = Path("docs/weather.json")
                    if not docs_path.parent.exists():
                        docs_path.parent.mkdir(parents=True)
                    shutil.copy(self.data_file, docs_path)


if __name__ == "__main__":
    scraper = SkiWeatherScraper()
    scraper.run()
