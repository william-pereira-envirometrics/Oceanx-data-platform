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

        results = earthaccess.search_data(  # Search NASA Earthdata for the product over the specified time range
            short_name=product,
            temporal=(start_date, end_date),
            granule_name="*.DAY.*.4km.*",  # Skip files that are not daily or not 4km resolution
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

                    subset_ds = cropped_ds[[i for i in ds if i != "palette"]]
                    subset_da = subset_ds.to_dataarray("variable")
                    subset_da["product"] = product
                    subset_da["filename"] = file_path.name
                    subset_da["date"] = date
                    if date and date.strftime("%Y%m%d") < iron_release_date.replace(
                        "-", ""
                    ):
                        subset_da["period"] = "before"
                    else:
                        subset_da["period"] = "after"
                    subset_df = subset_da.to_dataframe("value").dropna()
                    all_metrics.append(subset_df)

            except Exception as e:
                print(f"⚠️ Failed to process {file_path.name}: {e}")

            # Delete the downloaded file to save space
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path.name}: {e}")

    # Concat list to DataFrame
    df = pd.concat(all_metrics)
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
