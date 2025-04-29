from ingest import fetch_and_process  # Function to fetch data
from database import insert_metrics  # Function to insert into DB

# Main script entry
if __name__ == "__main__":
    print("🚀 Starting satellite data pipeline...")
    df = fetch_and_process()

    if df.empty:
        print("⚠️ No data extracted.")
    else:
        insert_metrics(df)
        print("✅ Pipeline complete")
