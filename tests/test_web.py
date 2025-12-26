from unittest.mock import mock_open, patch

from fastapi.testclient import TestClient

from web.main import app

client = TestClient(app)


def test_read_root_no_data():
    with patch("pathlib.Path.exists", return_value=False):
        response = client.get("/")
        assert response.status_code == 200  # noqa: PLR2004
        assert "Weather data not available yet" in response.text


def test_read_root_with_data():
    mock_data = '{"date": "2025-11-22", "temperature": "-5°C", "last_updated": "2025-11-22T12:30:00+00:00"}'
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch(
                "json.load",
                return_value={"date": "2025-11-22", "temperature": "-5°C", "last_updated": "2025-11-22T12:30:00+00:00"},
            ):
                response = client.get("/")
                assert response.status_code == 200  # noqa: PLR2004

                # Check for the main data points
                assert "2025-11-22" in response.text
                assert "-5°C" in response.text

                # Check that the ISO timestamp is in the HTML
                assert "2025-11-22T12:30:00+00:00" in response.text

                # Check for the script that formats the timestamp
                assert "formatLastUpdated(isoTimestamp)" in response.text


def test_api_data_success():
    mock_data = '{"date": "22.11.2025"}'
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch("json.load", return_value={"date": "22.11.2025"}):
                response = client.get("/api/data")
                assert response.status_code == 200  # noqa: PLR2004
                assert response.json() == {"date": "22.11.2025"}


def test_api_data_not_found():
    error_data = {"error": "Weather data not available yet. Please wait for the scraper to run."}
    with patch("web.main.load_weather_data", return_value=error_data):
        response = client.get("/api/data")
        assert response.status_code == 200  # noqa: PLR2004
        assert "Weather data not available yet" in response.json()["error"]
