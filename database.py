# 📁 database.py
import pymysql
from config import db_config

# Function to insert the processed satellite data into MySQL
def insert_metrics(df):
    drop_table_sql = """DROP TABLE IF EXISTS satellite_metrics_simple;"""          # DELETE EXISTING DATA IN DB IF ALREADY EXISTING - AVOID DUPLICATION/ SCHMEA CONFLICTS

    columns_with_types = ", ".join([f"{col} TEXT" for col in df.columns])

                                                                                # CREATE TABLE WITH PK AS DATATYPE TO TEXT 
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS satellite_metrics_simple (         
        id INT AUTO_INCREMENT PRIMARY KEY,
        {columns_with_types}                                    
    );
    """

    column_list = ", ".join(df.columns)                          #??
    placeholder_list = ", ".join(["%s"] * len(df.columns))   #placeholder values for each columns , these will be filled with actual values later 

    insert_sql = f"""
    INSERT INTO satellite_metrics_simple ({column_list})     #??????
    VALUES ({placeholder_list});
    """

    conn, cur = None, None

    try:
        conn = pymysql.connect(**db_config)    # CONNECTS TO MYSQL DB WITH CONFIG SETTINGS
        cur = conn.cursor()

        cur.execute(drop_table_sql)      #DELETES EXISTING TABLE
        conn.commit()

        cur.execute(create_table_sql)   # CREATE NEW TABLE WITH DATA
        conn.commit()

        rows = [tuple(row) for row in df.values]   # CONVERT DF TO TUPLE SO MYSWL CAN INSERT DATA

        cur.executemany(insert_sql, rows)     #ITNERS ROWS TO DB AND SAVES IT
        conn.commit()

        print(f"✅ Inserted {len(rows)} rows into MySQL")

    except Exception as e:
        print(f"❌ DB error: {e}")

    finally:
        if cur:
            cur.close()                # CLSOES DB CONNECTION 
        if conn:
            conn.close()
        print("🧹 DB cleanup complete")
