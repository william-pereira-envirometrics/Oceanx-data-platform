import os  # For file operations like deleting files
import xarray as xr  # For handling NetCDF files
import pandas as pd  # For tabular data manipulation
import numpy as np  # For numerical operations
from config import product_list, download_dir, iron_release_date, start_date, end_date, bbox  # Project settings
import earthaccess  # NASA Earthdata API wrapper
from pathlib import Path  # Safer file path operations
from database import insert_metrics  # Database insertion function



# Function to search, download, crop, extract and prepare satellite data
def fetch_and_process():
    all_metrics = []  # Final list of rows to go into our DataFrame

    for product in product_list:
        print(f"🔍 Searching for granules for: {product}")

        results = earthaccess.search_data(                                  # Search NASA Earthdata for the product over the specified time range
            short_name=product,                                            # The product ID/name we want to search for (e.g. "PACE_OCI_L3M_CHL")
            temporal=(start_date, end_date),                              # Date range to search within (from config.py)
            bounding_box=bbox                                             # Geographic bounding box to limit search area (from config.py)
        )

        if not results:
            print(f"⚠️ No granules found for {product}")
            continue

        print(f"📥 Attempting to download {len(results)} granules...")

        try:
            paths = earthaccess.download(results, download_dir)  # Download granules
        except Exception as e:
            print(f"❌ Download failed: {e}")
            paths = []

        for file_path in paths:
            file_path = Path(file_path)
            print(f"📂 Opening file: {file_path.name}")

            if not ("DAY" in file_path.name and "4km.nc" in file_path.name):                 # Skip files that are not daily or not 4km resolution
                print(f"⏭️ Skipping non-daily or non-4km file: {file_path.name}")
                continue

            try:
                # Open the dataset safely
                with xr.open_dataset(file_path) as ds:
                    # Extract the date from the filename
                    date_raw = file_path.name.split(".")[1][:8]
                    try:
                        date = pd.to_datetime(date_raw)
                    except Exception:
                        date = None

                    # Loop through all data variables
                    for var_name, var_data in ds.data_vars.items():
                        # Skip 'palette' variable and only process specific variables
                        if var_name.lower() == 'palette' or var_name.lower() not in ['chlor_a', 'nflh']:
                            continue
                        latitudes = ds['lat'].values
                        longitudes = ds['lon'].values
                        values = var_data.values
                        units = var_data.attrs.get('units', None)

                        # Debug: print shapes
                        print(f"Shapes for {file_path.name} - var: {var_name}")
                        print(f"  latitudes: {latitudes.shape}, longitudes: {longitudes.shape}, values: {values.shape}")

                        # Check if values shape matches (lat, lon)
                        if values.shape != (len(latitudes), len(longitudes)):
                            print(f"⚠️ Skipping variable '{var_name}' in {file_path.name}: shape mismatch {values.shape} vs ({len(latitudes)}, {len(longitudes)})")
                            continue

                        # Create meshgrid
                        lat_grid, lon_grid = np.meshgrid(latitudes, longitudes, indexing='ij')
                        flat_lat = lat_grid.flatten()
                        flat_lon = lon_grid.flatten()
                        flat_values = values.flatten()

                        # Check all arrays are the same length
                        if not (len(flat_lat) == len(flat_lon) == len(flat_values)):
                            print(f"⚠️ Skipping variable '{var_name}' in {file_path.name}: flattened arrays not same length")
                            continue

                        # Create DataFrame
                        df = pd.DataFrame({
                            "product": product,
                            "filename": file_path.name,
                            "date": date,
                            "period": "before" if date and date.strftime("%Y%m%d") < iron_release_date.replace("-", "") else "after",
                            "variable": var_name,
                            "latitude": flat_lat,
                            "longitude": flat_lon,
                            "value": flat_values,
                            "units": units
                        })

                        # Filter for points within the Falkland Islands bbox
                        mask = (
                            (df['longitude'] >= bbox[0]) &  # min_lon
                            (df['longitude'] <= bbox[2]) &  # max_lon
                            (df['latitude'] >= bbox[1]) &   # min_lat
                            (df['latitude'] <= bbox[3])     # max_lat
                        )
                        df = df[mask]

                        # Remove NaN values
                        df = df[~np.isnan(df['value'])]
                        all_metrics.extend(df.to_dict('records'))

            except Exception as e:
                print(f"⚠️ Failed to process {file_path.name}: {e}")

            # Print metrics collected so far
            print(f"\n📈 Metrics collected for {file_path.name}:")
            print(f"Total records: {len(all_metrics)}")
            if all_metrics:
                print("Sample of last 5 records:")
                print(pd.DataFrame(all_metrics[-5:]))
            print("\n")

            # Delete the downloaded file to save space
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path.name}: {e}")

    # Convert list to DataFrame with consistent column order
    expected_columns = ["product", "filename", "date", "period", "variable", "latitude", "longitude", "value", "units"]
    df = pd.DataFrame(all_metrics, columns=expected_columns)
    df = df.where(pd.notna(df), None)  # Replace NaN with None for DB compatibility

    # Save to CSV for viewing in Data Wrangler
    df.to_csv('satellite_data.csv', index=False)
    print(f"💾 Data saved to satellite_data.csv for viewing in Data Wrangler")

    print(f"📊 Total rows prepared: {len(df)}")
    return df

# Main block to run when script is executed directly
if __name__ == "__main__":
    df = fetch_and_process()
    if df.empty:
        print("⚠️ No data extracted.")
    else:
        insert_metrics(df)
        print("✅ Pipeline complete")
