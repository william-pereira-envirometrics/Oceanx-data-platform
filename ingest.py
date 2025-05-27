import os  # For file operations like deleting files
import xarray as xr  # For handling NetCDF files (scientific data format)
import pandas as pd  
import numpy as np  
from config import product_list, download_dir, iron_release_date, start_date, end_date, bbox  # Import settings from config file
import earthaccess  
from pathlib import Path  # Safer file path operations
from database import insert_metrics  # Function to insert data into database
 
# ===============================
# ✅ PIPELINE SUMMARY (STEP-BY-STEP)
# ===============================
#
# [Filter & download satellite data from Earthaccess API]
#     ⬇
# [Filter downloaded files for daily 4km resolution]
#     ⬇
# [Open file as NetCDF (.nc)]
#     ⬇
# [Load data as xarray.Dataset]
#     ⬇
# [Loop through variables (e.g. chlor_a, nflh)]
#     ⬇
# [Subset by bounding box (lat/lon) using .sel()]
#     ⬇
# [Convert xarray → pandas DataFrame (lat/lon/value)]
#     ⬇
# [Clean, label metadata, and stack rows]
#     ⬇
# [Save as CSV and insert into database]
#
# ===============================
 
 
 
# Main function that handles the entire data processing pipeline
def fetch_and_process():
    all_metrics = []  # Empty list to store all processed data
 
    # Loop through each satellite product we want to analyze
    for product in product_list:
        print(f"🔍 Searching for granules for: {product}")
 
        #SEARCH CRITERIA (PRODUCT/ DATE/ LOCATION)
        results = earthaccess.search_data(                                  
            short_name=product,                                            # Product name (e.g., chlorophyll data)
            temporal=(start_date, end_date),                              # Date range to search
            bounding_box=bbox,                                            # Geographic area to search
            granule_name="*.DAY.*.4km.*"                                  # Filter for daily 4km resolution files
        )
 
        # Skip if no data found for this product
        if not results:
            print(f"⚠️ No granules found for {product}")
            continue
 
        print(f"📥 Attempting to download {len(results)} granules...")
 
        # Try to download the satellite data files
        try:
            paths = earthaccess.download(results, download_dir)  # Download files to our download directory      #DOWNLOAD DATA BASED OF CRITERIA  
        except Exception as e:
            print(f"❌ Download failed: {e}")
            paths = []
 
        # Process each downloaded file
        for file_path in paths:
            file_path = Path(file_path)
            print(f"📂 Opening file: {file_path.name}")
 
            # Only process daily 4km resolution files
            if not "4km.nc" in file_path.name:                               # Simplified check
                print(f"⏭️ Skipping non-4km file: {file_path.name}")
                continue
 
            try:
                # Open the NetCDF dataset
                with xr.open_dataset(file_path) as ds:
                    # Extract date from filename
                    date_raw = file_path.name.split(".")[1][:8]
                    try:
                        date = pd.to_datetime(date_raw)
                    except Exception:
                        date = None
 
                    # Process each variable in the dataset
                    for var_name, var_data in ds.data_vars.items():
                        # Skip unnecessary variables
                        if var_name.lower() == 'palette' or var_name.lower() not in ['chlor_a', 'nflh']:
                            continue
 
                        # Get units from variable attributes
                        units = var_data.attrs.get('units', None)
 
                        # Use xarray's sel to subset the data to region of interest
                        bounds = {
                            'lon': slice(bbox[0], bbox[2]),      
                            'lat': slice(bbox[3], bbox[1])  # Reversed order for decreasing latitude values
                        }
                       
                        # Subset the data using xarray's sel
                        subset = var_data.sel(bounds)            
                       
                        # Stack coordinates and convert to DataFrame
                        df = subset.to_dataframe().reset_index()                    
                       
                        # Add metadata columns
                        df['product'] = product
                        df['filename'] = file_path.name
                        df['date'] = date
                        df['period'] = "before" if date and date.strftime("%Y%m%d") < iron_release_date.replace("-", "") else "after"
                        df['variable'] = var_name
                        df['units'] = units
                       
                        # Rename columns to match expected schema
                        df = df.rename(columns={
                            'lat': 'latitude',
                            'lon': 'longitude',
                            var_name: 'value'
                        })
 
                        # Remove rows with missing values
                        df = df.dropna(subset=['value'])      
                       
                        # Add DataFrame to list
                        all_metrics.append(df)
 
            except Exception as e:
                print(f"⚠️ Failed to process {file_path.name}: {e}")
 
            # Print progress information
            print(f"\n📈 Metrics collected for {file_path.name}:")
            total_rows = sum(len(df) for df in all_metrics)
            print(f"Total records: {total_rows}")
            if all_metrics:
                print("Sample of last 5 records:")
                print(pd.concat(all_metrics[-1:]).tail())
            print("\n")
 
            # Clean up by deleting the downloaded file
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path.name}: {e}")
 
    # Combine all DataFrames
    expected_columns = ["product", "filename", "date", "period", "variable", "latitude", "longitude", "value", "units"]
    df = pd.concat(all_metrics, ignore_index=True)
    df = df.where(pd.notna(df), None)  # Replace NaN with None for database compatibility
 
    # Save data to CSV file for inspection
    df.to_csv('satellite_data.csv', index=False)
    print(f"💾 Data saved to satellite_data.csv for viewing in Data Wrangler")
 
    print(f"📊 Total rows prepared: {len(df)}")
    return df
 
# This code runs when the script is executed directly (not imported)
if __name__ == "__main__":   #????
    df = fetch_and_process()
    if df.empty:
        print("⚠️ No data extracted.")
    else:
        insert_metrics(df)  # Insert data into database
        print("✅ Pipeline complete")
 
