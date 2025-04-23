# 📁 config.py
import pathlib

# Earthaccess will handle authentication
username = "will_pereira108"
password = "Envirometrics2025?!"

# This will prompt once and store credentials in ~/.netrc
import earthaccess
auth = earthaccess.login(persist=True)

# Region of interest: Chesapeake Bay area (guaranteed to have data)    
bounding_box = (-61.5, -53.2, -57.5, -50.9)  # CONFIRM THIS !!
start_date = "2024-12-15" 
end_date = "2025-01-07"
iron_release_date = "2024-12-30"  # just for tagging 'before'/'after'

# Specific OCI L3M chlorophyll product
product_list = ["PACE_OCI_L3M_CHL_NRT"] 


# Output directory for downloads
download_dir = pathlib.Path("downloads")
download_dir.mkdir(exist_ok=True)

# Cloud cover range (optional filter)
#cloud_cover = (0, 50)    #CHANGE THIS!

# MySQL DB config (DigitalOcean)
db_config = {
    "host": "db-mysql-lon1-78576-do-user-18592894-0.h.db.ondigitalocean.com",
    "user": "doadmin",
    "password": "AVNS_5d24Ut_RiknfWJtv9d6",
    "database": "defaultdb",
    "port": 25060,
    "ssl": {"ssl": {}}
}