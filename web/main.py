import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from common.helpers import get_data_file_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ski Weather Dashboard")

# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Get data file path (works both locally and in Docker)
DATA_FILE = get_data_file_path("weather.json")


def load_weather_data(file_path: Path | str) -> dict[str, Any]:
    """Loads weather data from the JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        A dictionary containing weather data or an error message.
    """
    file_path = Path(file_path)
    if file_path.exists():
        try:
            with open(file_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading data file: {e}")
            return {"error": "Could not load weather data."}
    else:
        return {"error": "Weather data not available yet. Please wait for the scraper to run."}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """Renders the main dashboard page.

    Args:
        request: The incoming request.

    Returns:
        The rendered HTML page.
    """
    data = load_weather_data(DATA_FILE)
    return templates.TemplateResponse(request=request, name="index.html", context={"weather": data})


@app.get("/api/data", response_class=JSONResponse)
async def get_data() -> JSONResponse:
    """Returns the raw weather data as JSON.

    Returns:
        A JSON response containing the weather data or an error.
    """
    data = load_weather_data(DATA_FILE)
    if "error" in data and "scraper" not in data.get("error", ""):
        # If it's a file not found error (scraper hasn't run), return 404?
        # Actually the load_weather_data returns a dict with error key.
        # Let's check if file exists logic again.
        if not DATA_FILE.exists():
            return JSONResponse(content=data, status_code=404)
        return JSONResponse(content=data, status_code=500)

    return JSONResponse(content=data)
