import requests
from bs4 import BeautifulSoup
import pdfplumber
import schedule
import time
import json
import os
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_FILE = "/data/weather.json"
TAGES_NEWS_URL = "https://www.altenberg.de/de/p/-de-p-tages-news-zum-download-47003971-/tages-news-zum-download/47003971/"
BASE_URL = "https://www.altenberg.de"

def fetch_pdf_url():
    try:
        logger.info(f"Fetching page: {TAGES_NEWS_URL}")
        response = requests.get(TAGES_NEWS_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the link containing "Tages-News"
        # Based on exploration: [Tages-News 22.11.2025](https://www.altenberg.de/r/622042260?page=media%2Fdownload)
        # The text usually contains "Tages-News" and a date.
        # We'll look for a link where the text contains "Tages-News"
        
        for a in soup.find_all('a', href=True):
            # Look for links that look like the download link
            # Example: https://www.altenberg.de/r/622042260?page=media%2Fdownload
            # Text usually contains "Tages-News" and a date
            text = a.text.strip()
            href = a['href']
            
            if "Tages-News" in text and ("media%2Fdownload" in href or "media/download" in href or "r/" in href):
                link = href
                if not link.startswith('http'):
                    link = BASE_URL + link
                logger.info(f"Found PDF link: {link}")
                return link
                
            # Fallback: Check if text matches the pattern "Tages-News DD.MM.YYYY"
            if "Tages-News" in text and any(char.isdigit() for char in text):
                 link = href
                 if not link.startswith('http'):
                    link = BASE_URL + link
                 logger.info(f"Found PDF link (fallback): {link}")
                 return link
        
        logger.warning("PDF link not found.")
        return None
    except Exception as e:
        logger.error(f"Error fetching PDF URL: {e}")
        return None

def download_pdf(url):
    try:
        logger.info(f"Downloading PDF from: {url}")
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return None

def extract_weather_data(pdf_file):
    try:
        logger.info("Extracting data from PDF...")
        with pdfplumber.open(pdf_file) as pdf:
            page = pdf.pages[0]
            tables = page.extract_tables()
            
            # Based on analysis, the table structure is a bit complex.
            # We'll look for keywords in the table data.
            
            data = {
                "date": "Unknown",
                "temperature": "Unknown",
                "weather_condition": "Unknown",
                "snow_depth": "Unknown",
                "snow_type": "Unknown",
                "last_snowfall": "Unknown",
                "update_time": "Unknown"
            }
            
            # Flatten the table to search for keys
            # The table from analysis looked like:
            # [['TAGES-NEWS - Samstag, 22. November 2025'], ['Uhrzeit: 08:15Uhr\nTemperatur\n-7°C...']]
            
            # Let's try to parse the text directly or the table cells
            
            text = page.extract_text()
            
            # Simple parsing strategy based on the text output we saw
            lines = text.split('\n')
            for line in lines:
                if "TAGES-NEWS" in line:
                    data["date"] = line.replace("TAGES-NEWS - ", "").strip()
                if "Uhrzeit:" in line:
                    data["update_time"] = line.split("Uhrzeit:")[1].strip().split("Uhr")[0] + " Uhr"
                if "Temperatur" in line and "°C" in line:
                     # This might be on the next line or same line depending on formatting
                     pass
            
            # Using table data might be more reliable if structure is consistent
            for table in tables:
                for row in table:
                    for idx, cell in enumerate(row):
                        if not cell: continue
                        if "TAGES-NEWS" in cell:
                             data["date"] = cell.replace("TAGES-NEWS - ", "").strip()
                        
                        # Check for keys in the cell
                        if "Temperatur" in cell:
                            # Value might be in the next cell
                            if idx + 1 < len(row) and row[idx+1]:
                                val = row[idx+1].strip()
                                if "°C" in val:
                                    data["temperature"] = val
                            
                            # Or in the same cell on a new line
                            if data["temperature"] == "Unknown":
                                lines = cell.split('\n')
                                for i, line in enumerate(lines):
                                    if "Temperatur" in line and i+1 < len(lines):
                                         candidate = lines[i+1].strip()
                                         if "°C" in candidate:
                                             data["temperature"] = candidate

                        if "Uhrzeit:" in cell:
                             # Might be "Uhrzeit: 08:15Uhr" in same cell
                             if "Uhrzeit:" in cell and "Uhr" in cell.split("Uhrzeit:")[1]:
                                 data["update_time"] = cell.split("Uhrzeit:")[1].strip()
                             elif idx + 1 < len(row) and row[idx+1]:
                                 data["update_time"] = row[idx+1].strip()

                        if "Wetterlage:" in cell:
                            if idx + 1 < len(row) and row[idx+1]:
                                data["weather_condition"] = row[idx+1].strip()
                            else:
                                data["weather_condition"] = cell.split("Wetterlage:")[1].strip() if "Wetterlage:" in cell and len(cell.split("Wetterlage:")) > 1 else "Unknown"

                        if "durchschnittliche Schneehöhe" in cell:
                             if idx + 1 < len(row) and row[idx+1]:
                                 data["snow_depth"] = row[idx+1].strip()
                             else:
                                 lines = cell.split('\n')
                                 for i, line in enumerate(lines):
                                     if "durchschnittliche Schneehöhe" in line and i+1 < len(lines):
                                         data["snow_depth"] = lines[i+1].strip()

                        if "Schneeart:" in cell:
                             if idx + 1 < len(row) and row[idx+1]:
                                 data["snow_type"] = row[idx+1].strip()
                             else:
                                 data["snow_type"] = cell.split("Schneeart:")[1].strip() if "Schneeart:" in cell and len(cell.split("Schneeart:")) > 1 else "Unknown"

                        if "letzter Schneefall:" in cell:
                             if idx + 1 < len(row) and row[idx+1]:
                                 data["last_snowfall"] = row[idx+1].strip()
                             else:
                                 data["last_snowfall"] = cell.split("letzter Schneefall:")[1].strip() if "letzter Schneefall:" in cell and len(cell.split("letzter Schneefall:")) > 1 else "Unknown"

            logger.info(f"Extracted data: {data}")
            return data
    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        return None

def job():
    logger.info("Starting scraper job...")
    pdf_url = fetch_pdf_url()
    if pdf_url:
        pdf_file = download_pdf(pdf_url)
        if pdf_file:
            data = extract_weather_data(pdf_file)
            if data:
                os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
                with open(DATA_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info("Data saved successfully.")

if __name__ == "__main__":
    # Run once immediately
    job()
    
    # Schedule every 4 hours
    schedule.every(4).hours.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
