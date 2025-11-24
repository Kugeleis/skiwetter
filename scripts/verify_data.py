import json
import sys
from datetime import datetime
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from common.helpers import get_data_file_path  # noqa: E402


def main() -> None:
    """Check if the scraped data is from today.

    Exits with a non-zero status code if the date in the data file
    does not match the current date.
    """
    data_file = get_data_file_path()
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        sys.exit(1)

    with open(data_file) as f:
        data = json.load(f)

    data_date_str = data.get("date")
    if not data_date_str:
        print("Error: 'date' field missing in data file.")
        sys.exit(1)

    try:
        data_date = datetime.strptime(data_date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"Error: Could not parse date '{data_date_str}'. Expected YYYY-MM-DD.")
        sys.exit(1)

    today = datetime.now().date()

    if data_date != today:
        print(f"Error: Scraped data is not from today. Expected {today}, found {data_date}.")
        sys.exit(1)
    else:
        print(f"Data verification successful. Data date ({data_date}) matches today's date ({today}).")
        sys.exit(0)


if __name__ == "__main__":
    main()
