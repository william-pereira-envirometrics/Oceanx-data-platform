import os  # For file operations like deleting files
import xarray as xr  # For handling NetCDF files
import pandas as pd  # For tabular data manipulation
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
            short_name=product,
            temporal=(start_date, end_date)
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

            
            if "DAY" not in file_path.name or "4km.nc" not in file_path.name:                 # Skip files that are not daily or not 4km resolution
                print(f"⏭️ Skipping non-daily or non-4km file: {file_path.name}")
                continue

            try:
                with xr.open_dataset(file_path) as ds:                                        # Filter for the bounding box region (location filter)
                    cropped_ds = ds.sel(
                        lon=slice(bbox[0], bbox[2]),
                        lat=slice(bbox[3], bbox[1]),
                    )

                    # Extract the date from the filename
                    date_raw = file_path.name.split(".")[1][:8]
                    try:
                        date = pd.to_datetime(date_raw)
                    except Exception:
                        date = None

                    # Loop through all data variables (e.g. chlor_a, nflh)
                    for var_name, var_data in cropped_ds.data_vars.items():
                        lat = cropped_ds.lat.values  # 1D Array of latitudes
                        lon = cropped_ds.lon.values  # 1D Array of longitudes
                        values = var_data.values    # 2D array of values for this variable

                        # Check if data is (lat, lon) or (lon, lat)
                        is_lat_first = values.shape == (len(lat), len(lon))

                        # Loop through every pixel to extract lat, lon, and value
                        for i, lat_val in enumerate(lat):
                            for j, lon_val in enumerate(lon):
                                try:
                                    val = values[i, j] if is_lat_first else values[j, i]
                                    all_metrics.append({
                                        "product": product,
                                        "filename": file_path.name,
                                        "date": date,
                                        "period": "before" if date and date.strftime("%Y%m%d") < iron_release_date.replace("-", "") else "after",
                                        "variable": var_name,
                                        "latitude": float(lat_val),
                                        "longitude": float(lon_val),
                                        "value": float(val) if pd.notna(val) else None
                                    })
                                except:
                                    continue  # Skip if invalid index or NaN

            except Exception as e:
                print(f"⚠️ Failed to process {file_path.name}: {e}")

            # Delete the downloaded file to save space
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path.name}: {e}")

    # Convert list to DataFrame with consistent column order
    expected_columns = ["product", "filename", "date", "period", "variable", "latitude", "longitude", "value"]
    df = pd.DataFrame(all_metrics, columns=expected_columns)
    df = df.where(pd.notna(df), None)  # Replace NaN with None for DB compatibility

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
