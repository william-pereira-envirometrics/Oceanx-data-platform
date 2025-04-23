# 📁 database.py
import pymysql
from config import db_config

def insert_metrics(df):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS satellite_metrics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product TEXT,
        variable TEXT,
        filename TEXT,
        date DATE,
        period TEXT,
        mean FLOAT,
        max FLOAT,
        location TEXT,
        latitude FLOAT,
        longitude FLOAT,
        observation_type TEXT,
        chlorophyll_band TEXT,
        bloom_intensity TEXT,
        pft_type TEXT,
        relative_growth_rate FLOAT,
        dominance_percent FLOAT,
        iron_fertilisation TEXT,
        campaign_id TEXT,
        sensor_name TEXT,
        satellite TEXT
    );
    """

    insert_sql = """
    INSERT INTO satellite_metrics (
        product, variable, filename, date, period, mean, max,
        location, latitude, longitude, observation_type,
        chlorophyll_band, bloom_intensity, pft_type,
        relative_growth_rate, dominance_percent,
        iron_fertilisation, campaign_id, sensor_name, satellite
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s, %s, %s
    );
    """

    conn, cur = None, None
    try:
        conn = pymysql.connect(**db_config)
        cur = conn.cursor()
        cur.execute(create_table_sql)
        conn.commit()

        # ✅ Ensure all expected columns exist, fill with None if missing
        df = df.reindex(columns=[
            "product", "variable", "filename", "date", "period", "mean", "max",
            "location", "latitude", "longitude", "observation_type",
            "chlorophyll_band", "bloom_intensity", "pft_type",
            "relative_growth_rate", "dominance_percent",
            "iron_fertilisation", "campaign_id", "sensor_name", "satellite"
        ], fill_value=None)

        rows = [tuple(row) for row in df.values]
        cur.executemany(insert_sql, rows)
        conn.commit()

        print("✅ Data inserted into MySQL")
    except Exception as e:
        print(f"❌ DB error: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
        print("🧹 Cleanup complete")
