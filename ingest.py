import os  # To interact with the operating system (e.g., deleting files)
import xarray as xr  # For opening and working with NetCDF files
import pandas as pd  # For working with dataframes
from config import product_list, download_dir, iron_release_date, start_date, end_date, bbox  # Importing necessary settings from config
import earthaccess  # For accessing Earth data
from pathlib import Path  # For handling file paths
from database import insert_metrics  # For inserting the data into the database

# Function to search, download, crop, and prepare data
def fetch_and_process():
    all_metrics = []  # Empty list to store extracted records

    for product in product_list:  # Loop through each product
        print(f"🔍 Searching for granules for: {product}")

        # Search for available granules in date range
        results = earthaccess.search_data(                                     # SEARCH FOR x3 PRODUCTs within DATE period
            short_name=product,  # Use product name from the config
            temporal=(start_date, end_date)  # Set date range for the search
        )

        if not results:  # If no results are found, skip this product
            print(f"⚠️ No granules found for {product}")
            continue  # Move on to the next product

        print(f"📥 Attempting to download {len(results)} granules...")

        # Download all found granules
        try:
            paths = earthaccess.download(results, download_dir)  # Download the files             # DOWNLOAD SEARCH RESULTS
        except Exception as e:
            print(f"❌ Download failed: {e}")
            paths = []  # If download fails, set paths to empty list

        # Process each downloaded file
        for file_path in paths:
            file_path = Path(file_path)  # Convert file path to a Path object for easier manipulation            # OPEN EACH FILE
            print(f"📂 Opening file: {file_path.name}")

            try:
                with xr.open_dataset(file_path) as ds:  # Open the dataset (NetCDF file)
                    # Crop the dataset to Falklands bounding box (using lon and lat)
                    cropped_ds = ds.sel(
                        lon=slice(bbox[0], bbox[2]),  # Select longitude within the bounding box            # FILTER DATA IN FILE BY
                        lat=slice(bbox[1], bbox[3])   # Select latitude within the bounding box
                    )

                    # Extract date from the file name (assuming the date is in a specific format)
                    date_raw = file_path.name.split(".")[1][:8]  # Extract date from filename (e.g., '20241201')
                    try:
                        date = pd.to_datetime(date_raw)  # Convert the extracted string to a pandas datetime object
                    except Exception:
                        date = None  # Set date to None if conversion fails

                    # Loop through each variable in the cropped dataset (no filter for specific variables)
                    for var_name, var_data in cropped_ds.data_vars.items():  # Loop through all variables
                        flat_values = var_data.values.flatten()  # Flatten the variable data into a 1D array

                        # Save every value, no filtering based on variable type (store all variables)
                        for val in flat_values:
                            all_metrics.append({
                                "product": product,  # Store the product name (e.g., PACE_OCI_L3M_CHL)
                                "filename": file_path.name,  # Store the filename (for tracking and debugging)       # SAVED COLUMNS 
                                "date": date,  # Store the date extracted from the filename
                                "period": "before" if date and date.strftime("%Y%m%d") < iron_release_date.replace("-", "") else "after",  # Period before or after iron release
                                "variable": var_name,  # Store the variable name (metric)
                                "value": float(val) if pd.notna(val) else None  # Store the value, convert NaN to None for SQL compatibility
                            })

            except Exception as e:
                print(f"⚠️ Failed to process {file_path.name}: {e}")  # Error handling for dataset processing

            # Clean up local file to save space
            try:
                os.remove(file_path)  # Delete the file after processing
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path.name}: {e}")  # Error handling for file deletion

    # Convert list of dictionaries into a pandas DataFrame
    df = pd.DataFrame(all_metrics)  # Convert the list of records into a structured DataFrame            # CONVERT TO DF 

    # Replace NaN values with None for SQL compatibility (necessary for inserting into MySQL)
    df = df.where(pd.notna(df), None)  # Replace NaN values with None

    print(f"📊 Total rows prepared: {len(df)}")  # Print how many rows were processed
    return df  # Return the DataFrame for further processing (insertion into the database)

# Main script logic
if __name__ == "__main__":
    df = fetch_and_process()  # Fetch and process data

    if df.empty:  # Check if no data was extracted
        print("⚠️ No data extracted.")  # Print warning if no data
    else:
        insert_metrics(df)  # Insert data into the database
        print("✅ Pipeline complete")  # Print confirmation when the pipeline is complete
