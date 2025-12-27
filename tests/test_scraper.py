import io
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

from scraper.scraper import SkiWeatherScraper


@pytest.fixture
def scraper():
    return SkiWeatherScraper(data_file="test_weather.json")


def test_fetch_pdf_url_success(scraper):
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = b'<html><a href="/r/123?page=media%2Fdownload">Tages-News 22.11.2025</a></html>'
        mock_get.return_value = mock_response

        url = scraper.fetch_pdf_url()
        assert url == "https://www.altenberg.de/r/123?page=media%2Fdownload"


def test_fetch_pdf_url_not_found(scraper):
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = b'<html><a href="/other">Other Link</a></html>'
        mock_get.return_value = mock_response

        url = scraper.fetch_pdf_url()
        assert url is None


def test_download_pdf_success(scraper):
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = b"%PDF-1.4..."
        mock_get.return_value = mock_response

        pdf_data = scraper.download_pdf("http://example.com/file.pdf")
        assert isinstance(pdf_data, io.BytesIO)
        assert pdf_data.getvalue() == b"%PDF-1.4..."


def test_extract_weather_data_success(scraper):
    # Mock pdfplumber
    with patch("pdfplumber.open") as mock_open_pdf:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdf.pages = [mock_page]

        # Mock table extraction
        mock_page.extract_tables.return_value = [
            [
                ["TAGES-NEWS - 22.11.2025"],
                ["Temperatur", "-5°C"],
                ["Wetterlage:", "sonnig"],
                ["Schneeart:", "Pulver"],
                ["durchschnittliche Schneehöhe", "20 cm"],
                ["letzter Schneefall:", "20.11.2025"],
                ["Uhrzeit: 08:00Uhr"],
            ]
        ]

        mock_open_pdf.return_value.__enter__.return_value = mock_pdf

        data = scraper.extract_weather_data(io.BytesIO(b"fake pdf"))

        assert data["date"] == "2025-11-22"
        assert data["temperature"] == "-5°C"
        assert data["weather_condition"] == "sonnig"
        assert data["snow_type"] == "Pulver"
        assert data["snow_depth"] == "20 cm"
        assert data["last_snowfall"] == "20.11.2025"
        assert data["update_time"] == "08:00Uhr"


def test_save_data(scraper):
    """Test that data is saved correctly with a `last_updated` timestamp."""
    data = {"test": "data", "last_updated": "old_timestamp"}  # The old timestamp should be overwritten.
    m = mock_open()
    with patch("builtins.open", m):
        with patch("json.dump") as mock_json_dump:
            with patch("os.makedirs"):
                scraper.save_data(data)

                # Get the data that was passed to json.dump
                args, _ = mock_json_dump.call_args
                saved_data = args[0]

                # Assert that 'last_updated' is present and is a valid ISO 8601 timestamp
                assert "last_updated" in saved_data
                try:
                    datetime.fromisoformat(saved_data["last_updated"])
                except (ValueError, TypeError):
                    pytest.fail("last_updated is not a valid ISO 8601 timestamp.")

                # Assert that the original data is preserved
                assert saved_data["test"] == "data"


def test_fetch_pdf_url_handles_dynamic_link_text(scraper: SkiWeatherScraper):
    """Test that the scraper correctly finds the PDF URL when the link text is dynamic."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = """
        <html>
            <body>
                <div class="abo-download-area">
                    <a href="/r/91329422?page=media/download" target="_blank" class="abo-download-link">
                        Tages-News Statischer Link für Leistungsträger
                    </a>
                    <a href="/r/622108495?page=media%2Fdownload" target="_blank" class="abo-download-link">
                        Tages-News 24.11.2025
                    </a>
                </div>
            </body>
        </html>
        """.encode()
        mock_get.return_value = mock_response
        url = scraper.fetch_pdf_url()
        assert url == "https://www.altenberg.de/r/622108495?page=media%2Fdownload"


def test_fetch_pdf_url_no_date_in_link(scraper: SkiWeatherScraper):
    """Test that the scraper does not pick up a link with no date."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = """
        <html>
            <body>
                <div class="abo-download-area">
                    <a href="/r/91329422?page=media/download" target="_blank" class="abo-download-link">
                        Tages-News Statischer Link für Leistungsträger
                    </a>
                </div>
            </body>
        </html>
        """.encode()
        mock_get.return_value = mock_response
        url = scraper.fetch_pdf_url()
        assert url is None
