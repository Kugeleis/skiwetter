"""
This script generates a static HTML page from a Jinja2 template and a JSON data file.
It's used to create a static version of the website for deployment on platforms like GitHub Pages.
"""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Use absolute paths to run this script from anywhere in the project
# Get the project root directory (assuming this script is in `scripts/`)
ROOT_DIR = Path(__file__).parent.parent
DATA_FILE = ROOT_DIR / "data" / "weather.json"
TEMPLATE_DIR = ROOT_DIR / "web" / "templates"
TEMPLATE_NAME = "index.html"
OUTPUT_DIR = ROOT_DIR / "docs"
OUTPUT_FILE = OUTPUT_DIR / "index.html"


def generate_static_page():
    """
    Generates a static HTML page from a template and data file.
    """
    # 1. Load data
    weather_data = {}
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, encoding="utf-8") as f:
                weather_data = json.load(f)
                logger.info("Successfully loaded weather data.")
        else:
            weather_data = {"error": "Weather data not available yet."}
            logger.warning("Weather data file not found.")
    except json.JSONDecodeError as e:
        weather_data = {"error": "Failed to decode weather data."}
        logger.error(f"Error decoding JSON: {e}")
    except Exception as e:
        weather_data = {"error": "An unexpected error occurred."}
        logger.error(f"Error loading data: {e}")

    # 2. Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_NAME)

    # 3. Render the template
    try:
        rendered_html = template.render(weather=weather_data)
        logger.info("Successfully rendered HTML template.")
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        # Create a fallback HTML in case of rendering failure
        rendered_html = f"<html><body><h1>Error rendering page</h1><p>{e}</p></body></html>"

    # 4. Write the output file
    try:
        # Ensure the output directory exists
        OUTPUT_DIR.mkdir(exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        logger.info(f"Static page successfully generated at: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Error writing to output file: {e}")


if __name__ == "__main__":
    generate_static_page()
