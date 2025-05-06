import pathlib  # To handle folder paths
import earthaccess  # To manage login to NASA Earthdata

# Earthdata login credentials
username = "will_pereira108"
password = "Envirometrics2025?!"

# Login to Earthdata and persist credentials
auth = earthaccess.login(persist=True)
assert auth.authenticated  # Make sure login actually worked

# Define the products you want to search (list)
product_list = ["PACE_OCI_L3M_CHL", "PACE_OCI_L3M_PFT", "PACE_OCI_L3M_FLH"] 

# Create downloads folder if it doesn't exist
download_dir = pathlib.Path("downloads")
download_dir.mkdir(exist_ok=True)

# Set the date range for granules (satellite data) search
start_date = "2024-12-15"
end_date = "2025-01-07"

# Important event date (to tag 'before'/'after' in database)
iron_release_date = "2024-12-30"

# Area of interest - Bounding box (Falkland Islands)
# Format: (min_lon, min_lat, max_lon, max_lat)
bbox = (-61.5, -53.2, -57.5, -50.9)

# MySQL database connection settings
db_config = {
    "host": "db-mysql-lon1-78576-do-user-18592894-0.h.db.ondigitalocean.com",
    "user": "doadmin",
    "password": "AVNS_5d24Ut_RiknfWJtv9d6",
    "database": "defaultdb",
    "port": 25060,
    "ssl": {"ssl": {}}
}
