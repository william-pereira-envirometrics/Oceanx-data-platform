# 📁 database.py
import pymysql
from config import db_config

# Function to insert the processed satellite data into MySQL
def insert_metrics(df):
    drop_table_sql = """DROP TABLE IF EXISTS satellite_metrics_simple;"""

    columns_with_types = ", ".join([f"{col} TEXT" for col in df.columns])

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS satellite_metrics_simple (
        id INT AUTO_INCREMENT PRIMARY KEY,
        {columns_with_types}
    );
    """

    column_list = ", ".join(df.columns)
    placeholder_list = ", ".join(["%s"] * len(df.columns))

    insert_sql = f"""
    INSERT INTO satellite_metrics_simple ({column_list})
    VALUES ({placeholder_list});
    """

    conn, cur = None, None

    try:
        conn = pymysql.connect(**db_config)
        cur = conn.cursor()

        cur.execute(drop_table_sql)
        conn.commit()

        cur.execute(create_table_sql)
        conn.commit()

        rows = [tuple(row) for row in df.values]

        cur.executemany(insert_sql, rows)
        conn.commit()

        print(f"✅ Inserted {len(rows)} rows into MySQL")

    except Exception as e:
        print(f"❌ DB error: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("🧹 DB cleanup complete")
