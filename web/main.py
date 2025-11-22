from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

DATA_FILE = "/data/weather.json"

@app.get("/")
async def read_root(request: Request):
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading data file: {e}")
            data = {"error": "Could not load weather data."}
    else:
        data = {"error": "Weather data not available yet. Please wait for the scraper to run."}
    
    return templates.TemplateResponse("index.html", {"request": request, "weather": data})

@app.get("/api/data")
async def get_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            return JSONResponse(content=data)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    return JSONResponse(content={"error": "Data not found"}, status_code=404)
