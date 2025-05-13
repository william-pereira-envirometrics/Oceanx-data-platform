import os  # For file operations like deleting files
import xarray as xr  # For handling NetCDF files (scientific data format)
import pandas as pd  
import numpy as np  
from config import product_list, download_dir, iron_release_date, start_date, end_date, bbox  # Import settings from config file
import earthaccess  
from pathlib import Path  # Safer file path operations
from database import insert_metrics  # Function to insert data into database

# Main function that handles the entire data processing pipeline
def fetch_and_process():
    all_metrics = []  # Empty list to store all processed data

    # Loop through each satellite product we want to analyze
    for product in product_list:
        print(f"🔍 Searching for granules for: {product}")

        # Search NASA Earthdata for satellite data matching our criteria                                              #SEARCH CRITERIA (PRODUCT/ DATE/ LOCATION)
        results = earthaccess.search_data(                                  
            short_name=product,                                            # Product name (e.g., chlorophyll data)
            temporal=(start_date, end_date),                              # Date range to search
            bounding_box=bbox                                             # Geographic area to search
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
            if not ("DAY" in file_path.name and "4km.nc" in file_path.name):                               # FITLER (4KM / DAY) BY FILENAME 
                print(f"⏭️ Skipping non-daily or non-4km file: {file_path.name}")
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
                        # Create a dictionary of coordinate bounds
                        bounds = {
                            'lon': slice(bbox[0], bbox[2]),
                            'lat': slice(bbox[1], bbox[3])
                        }
                        
                        # Subset the data using xarray's sel
                        subset = var_data.sel(bounds)
                        
                        # Stack coordinates and convert to DataFrame in one step
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

                        # Remove any missing values
                        df = df.dropna(subset=['value'])
                        
                        # Add to metrics list
                        all_metrics.extend(df.to_dict('records'))

            except Exception as e:
                print(f"⚠️ Failed to process {file_path.name}: {e}")

            # Print progress information
            print(f"\n📈 Metrics collected for {file_path.name}:")
            print(f"Total records: {len(all_metrics)}")
            if all_metrics:
                print("Sample of last 5 records:")
                print(pd.DataFrame(all_metrics[-5:]))
            print("\n")

            # Clean up by deleting the downloaded file
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path.name}: {e}")

    # Convert all collected data to a DataFrame                                    # CONVERTS TO LIST TO DF 
    expected_columns = ["product", "filename", "date", "period", "variable", "latitude", "longitude", "value", "units"]
    df = pd.DataFrame(all_metrics, columns=expected_columns)
    df = df.where(pd.notna(df), None)  # Replaces all NaN values (used in pandas for missing data) with Python's None, which is more compatible with SQL-style databases

    # Save data to CSV file for inspection
    df.to_csv('satellite_data.csv', index=False)
    print(f"💾 Data saved to satellite_data.csv for viewing in Data Wrangler")

    print(f"📊 Total rows prepared: {len(df)}")
    return df

# This code runs when the script is executed directly (not imported)
if __name__ == "__main__":
    df = fetch_and_process()
    if df.empty:
        print("⚠️ No data extracted.")
    else:
        insert_metrics(df)  # Insert data into database
        print("✅ Pipeline complete")
