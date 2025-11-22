from unittest.mock import mock_open, patch

from fastapi.testclient import TestClient

from web.main import app

client = TestClient(app)


def test_read_root_no_data():
    with patch("os.path.exists", return_value=False):
        response = client.get("/")
        assert response.status_code == 200  # noqa: PLR2004
        assert "Weather data not available yet" in response.text


def test_read_root_with_data():
    mock_data = '{"date": "22.11.2025", "temperature": "-5°C"}'
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch("json.load", return_value={"date": "22.11.2025", "temperature": "-5°C"}):
                response = client.get("/")
                assert response.status_code == 200  # noqa: PLR2004
                assert "22.11.2025" in response.text
                assert "-5°C" in response.text


def test_api_data_success():
    mock_data = '{"date": "22.11.2025"}'
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch("json.load", return_value={"date": "22.11.2025"}):
                response = client.get("/api/data")
                assert response.status_code == 200  # noqa: PLR2004
                assert response.json() == {"date": "22.11.2025"}


def test_api_data_not_found():
    with patch("os.path.exists", return_value=False):
        response = client.get("/api/data")
        assert response.status_code == 200  # noqa: PLR2004
        assert "Weather data not available yet" in response.json()["error"]
