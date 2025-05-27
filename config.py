import pathlib  # To handle folder paths
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# NASA Earthdata Login Credentials
EARTHDATA_USERNAME = os.getenv('EARTHDATA_USERNAME')
EARTHDATA_PASSWORD = os.getenv('EARTHDATA_PASSWORD')

# (Optional) Only import and login to earthaccess when needed in your code
# import earthaccess
# auth = earthaccess.login(username=EARTHDATA_USERNAME, password=EARTHDATA_PASSWORD, persist=True)
# assert auth.authenticated

# Product list to search for
product_list = ["PACE_OCI_L3M_CHL", "PACE_OCI_L3M_FLH"]  # Removed PFT since it's not available

# Create download directory if it doesn't exist
download_dir = os.getenv('DOWNLOAD_DIR', 'downloads')
os.makedirs(download_dir, exist_ok=True)

# Date range for satellite data search
start_date = os.getenv('START_DATE', '2024-12-15')
end_date = os.getenv('END_DATE', '2025-01-07')

# Important event date (to tag 'before'/'after' in database)
iron_release_date = "2024-12-28"

# Area of interest - Bounding box (Falkland Islands)
# Format: (min_lon, min_lat, max_lon, max_lat)
bbox = (-61.5, -53.2, -57.5, -50.9)





# MySQL database connection settings from environment variables
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "25060")),  # Convert port to integer with default value
    "ssl": {"ssl": {}}
}
