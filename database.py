# 📁 database.py
import pymysql
from config import db_config
import bcrypt  # Add this import at the top with other imports

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

def setup_users_table():
    """Create the users table if it doesn't exist"""
    create_users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(60) NOT NULL,
        email VARCHAR(100) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP NULL
    );
    """
    
    conn, cur = None, None
    try:
        conn = pymysql.connect(**db_config)
        cur = conn.cursor()
        cur.execute(create_users_table_sql)
        conn.commit()
        print("✅ Users table setup complete")
    except Exception as e:
        print(f"❌ Error setting up users table: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def verify_user(username, password):
    """Verify user credentials against the database"""
    conn, cur = None, None
    try:
        conn = pymysql.connect(**db_config)
        cur = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get user from database
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Update last login time
            cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))
            conn.commit()
            return True
        return False
    except Exception as e:
        print(f"❌ Error verifying user: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def create_user(username, password, email=None):
    """Create a new user with hashed password"""
    conn, cur = None, None
    try:
        # Hash the password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        conn = pymysql.connect(**db_config)
        cur = conn.cursor()
        
        # Insert new user
        cur.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
            (username, password_hash.decode('utf-8'), email)
        )
        conn.commit()
        print(f"✅ User {username} created successfully")
        return True
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:  # Duplicate entry error
            print(f"❌ Username {username} already exists")
        else:
            print(f"❌ Error creating user: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Call this when the module is imported to ensure the users table exists
setup_users_table()
