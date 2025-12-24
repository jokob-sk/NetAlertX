import sys
import os

# Connect to the database using environment variable
db_path = os.path.join(
    os.getenv('NETALERTX_DB', '/data/db'),
    'app.db'
)

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import get_temp_db_connection  # noqa: E402 [flake8 lint suppression]

conn = get_temp_db_connection()
cursor = conn.cursor()

# Get the names of all tables (excluding SQLite internal tables)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = cursor.fetchall()

# Disable foreign key constraints temporarily
cursor.execute("PRAGMA foreign_keys = OFF;")

# Delete all rows from each table
for (table_name,) in tables:
    cursor.execute(f"DELETE FROM {table_name};")

# Commit changes and re-enable foreign keys
conn.commit()
cursor.execute("PRAGMA foreign_keys = ON;")

# Vacuum to shrink database file
cursor.execute("VACUUM;")

# Close connection
conn.close()
