# 📁 ingest.py
import os
import xarray as xr
import pandas as pd
from config import product_list, bounding_box, download_dir, iron_release_date, start_date, end_date
import earthaccess
from pathlib import Path
from database import insert_metrics

def fetch_and_process():
    all_metrics = []  # Store all processed results

    for product in product_list:
        print(f"🔍 Searching for granules for: {product}")

        # Search for granules using Earthaccess
        results = earthaccess.search_data(
            short_name=product,
            temporal=(start_date, end_date),
            bounding_box=bounding_box
        )

        if not results:
            print(f"⚠️ No granules found for {product}")
            continue

        print(f"📥 Attempting to download {len(results)} granules...")
        try:
            paths = earthaccess.download(results, download_dir)
        except Exception as e:
            print(f"❌ Download failed for {product}: {e}")
            paths = []

        for file_path in paths:
            try:
                file_path = Path(file_path)  # Ensure it's a Path object
                date = file_path.name.split(".")[1][:8]
                period = "before" if date < iron_release_date.replace("-", "") else "after"

                # Open NetCDF file safely
                with xr.open_dataset(file_path, engine="netcdf4") as ds:
                    for var in ds.data_vars:
                        data = ds[var]
                        all_metrics.append({
                            "product": product,
                            "variable": var,
                            "filename": file_path.name,
                            "date": pd.to_datetime(date),
                            "period": period,
                            "mean": float(data.mean(skipna=True).values),
                            "max": float(data.max(skipna=True).values)
                        })

            except Exception as e:
                print(f"⚠️ Failed to process {file_path.name}: {e}")

            # Cleanup after reading
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path.name}: {e}")

    return pd.DataFrame(all_metrics)

if __name__ == "__main__":
    df = fetch_and_process()
    print(df.head())  # Preview first few rows
    insert_metrics(df)  # Push to MySQL
