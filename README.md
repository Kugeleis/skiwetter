# Skiwetter Altenberg

A modern, automated ski weather dashboard that scrapes daily snow conditions from the Altenberg ski resort website and displays them in a beautiful, responsive web interface.

## 🎯 Project Intention

This project was created to provide an easy-to-access, always-up-to-date view of ski conditions at Altenberg, Germany. Instead of manually checking PDF reports on the resort's website, this dashboard:

- **Automatically scrapes** the daily "Tages-News" PDF from [altenberg.de](https://www.altenberg.de)
- **Extracts key metrics** like temperature, snow depth, snow type, and weather conditions
- **Displays the data** in a premium, glassmorphism-styled web interface
- **Updates regularly** throughout the day to ensure fresh information

Perfect for skiers planning their day or checking conditions remotely!

## ✨ Features

- 🔄 Automated PDF scraping and data extraction
- 🎨 Modern, responsive UI with glassmorphism design
- 🐳 Fully Dockerized for easy deployment
- 📊 Real-time weather data display
- ❄️ Animated snowflakes for winter ambiance
- 🔧 Developer-friendly with `uv`, `ruff`, and `pytest`

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) `uv` for local development

### Running with Docker Compose

```bash
# Clone the repository
git clone <your-repo-url>
cd skiwetter

# Start the services
docker compose up -d

# View logs
docker compose logs -f

# Stop the services
docker compose down
```

The dashboard will be available at `http://localhost:8000`.

## 📦 Deployment

### Production Deployment

1. **Clone the repository** on your server:
   ```bash
   git clone <your-repo-url>
   cd skiwetter
   ```

2. **Configure environment** (optional):
   ```bash
   # Create a .env file if you need custom settings
   echo "DATA_FILE=/data/weather.json" > .env
   ```

3. **Start services**:
   ```bash
   docker compose up -d
   ```

4. **Set up reverse proxy** (recommended for production):
   
   Example Nginx configuration:
   ```nginx
   server {
       listen 80;
       server_name skiwetter.yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Enable SSL** with Let's Encrypt:
   ```bash
   certbot --nginx -d skiwetter.yourdomain.com
   ```

### Updating the Application

```bash
cd skiwetter
git pull
docker compose down
docker compose up -d --build
```

## ⏰ Scheduling the Scraper

The scraper schedule is configured via `data/schedule.yaml`. This file is mounted into the Docker container and read at startup.

### Default Schedule

By default, the scraper runs **every 4 hours**. This is defined in `data/schedule.yaml`:

```yaml
default:
  interval: 4
  unit: hours
```

### Customizing the Schedule

Edit `data/schedule.yaml` to change when the scraper runs. The first non-commented schedule in the file will be used.

#### Example: Run Every Morning (7-11 AM, Every 10 Minutes)

Uncomment the `morning_intensive` section in `data/schedule.yaml`:

```yaml
morning_intensive:
  times:
    - "07:00"
    - "07:10"
    - "07:20"
    # ... (all times listed)
    - "11:00"
```

#### Example: Run Every Hour

Uncomment the `hourly` section:

```yaml
hourly:
  interval: 1
  unit: hours
```

#### Example: Run at Specific Times

Uncomment the `specific_times` section:

```yaml
specific_times:
  times:
    - "08:00"
    - "12:00"
    - "16:00"
```

### Applying Schedule Changes

After modifying `data/schedule.yaml`, restart the scraper container:

```bash
docker compose restart scraper
```

The new schedule will be loaded automatically.

### Schedule Configuration Format

**Interval-based schedules:**
```yaml
schedule_name:
  interval: <number>
  unit: hours|minutes|days
```

**Time-based schedules:**
```yaml
schedule_name:
  times:
    - "HH:MM"
    - "HH:MM"
```

## 🛠️ Development

### Local Setup

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Or use the task runner
task check
task format
```

### Project Structure

```
skiwetter/
├── scraper/           # PDF scraping service
│   ├── scraper.py     # Main scraper logic
│   └── __init__.py
├── web/               # FastAPI web service
│   ├── main.py        # API and routing
│   ├── templates/     # Jinja2 templates
│   └── __init__.py
├── tests/             # Test suite
│   ├── test_scraper.py
│   ├── test_web.py
│   └── visual_test.py
├── scripts/           # Utility scripts
│   └── analyze_pdf.py # PDF analysis tool
├── data/              # Runtime data (shared by all containers)
│   ├── schedule.yaml  # Scraper schedule (version controlled)
│   ├── weather.json   # Current weather data (generated)
│   └── tages_news.pdf # Latest downloaded PDF (generated)
├── Dockerfile.scraper # Scraper container
├── Dockerfile.web     # Web container
├── docker-compose.yml # Service orchestration
├── pyproject.toml     # Project config
├── duties.py          # Task automation
└── Taskfile.yml       # Task runner wrapper
```

### Available Tasks

```bash
task check        # Run linting and tests
task format       # Format code
task clean        # Clean build artifacts
task bump-patch   # Bump patch version (0.0.X)
task bump-minor   # Bump minor version (0.X.0)
task bump-major   # Bump major version (X.0.0)
```

### Updating Docker Containers During Development

When you make changes to the code, you need to rebuild the Docker containers to see the changes in action.

**Quick rebuild and restart:**
```bash
# Rebuild and restart all services
docker compose up -d --build

# Rebuild only the scraper
docker compose up -d --build scraper

# Rebuild only the web service
docker compose up -d --build web
```

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f scraper
docker compose logs -f web
```

**Stop and remove containers:**
```bash
# Stop services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

**Development workflow:**
1. Make code changes
2. Run tests locally: `uv run pytest`
3. Rebuild containers: `docker compose up -d --build`
4. Check logs: `docker compose logs -f`
5. Test the application: `http://localhost:8000`

## 📊 Data Fields

The scraper extracts the following information:

- **Date**: Publication date of the report
- **Temperature**: Current temperature at the measurement station
- **Weather Condition**: Current weather (e.g., sunny, cloudy, snowing)
- **Snow Depth**: Average snow depth in the region
- **Snow Type**: Type of snow (e.g., powder, packed)
- **Last Snowfall**: Date of the last snowfall
- **Update Time**: Time when the data was last updated

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=scraper --cov=web

# Run visual tests (requires running web server)
BROWSER_PATH=$(pwd)/vivaldi_wrapper.sh uv run python tests/visual_test.py
```

## 📝 License

This project is for educational and personal use. Please respect the terms of service of altenberg.de when using this scraper.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 🐛 Troubleshooting

**Scraper not finding PDF:**
- Check if the website structure has changed
- Verify the URL in `scraper.py` is still correct

**Web app shows "Data not available":**
- Ensure the scraper has run at least once
- Check scraper logs: `docker compose logs scraper`

**Docker build fails:**
- Ensure you have the latest Docker version
- Try `docker compose build --no-cache`

## 📧 Contact

For issues or questions, please open an issue on GitHub.
