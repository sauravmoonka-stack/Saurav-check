#!/usr/bin/env python3
"""Query Snowflake for quantity returned in ASC warehouse by grade"""

import snowflake.connector
import configparser
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import pandas as pd

# Read credentials
config_path = os.path.expanduser("~/.snowflake/credentials/sf.ini")
config = configparser.ConfigParser()
config.read(config_path)

user = config.get('default', 'user')
private_key_path = config.get('default', 'private_key')
passphrase_b64 = config.get('default', 'passphrase', fallback=None)

passphrase = None
if passphrase_b64:
    passphrase = base64.b64decode(passphrase_b64)

try:
    # Load private key and connect
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase,
            backend=default_backend()
        )

    conn = snowflake.connector.connect(
        user=user,
        private_key=private_key,
        account="YLEFPTS-QDP_EU"
    )

    cursor = conn.cursor()

    print("🔍 Exploring Snowflake schema...\n")

    # Find tables with "return" or "warehouse" in the name
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_SCHEMA
        FROM INFORMATION_SCHEMA.TABLES
        WHERE (TABLE_NAME ILIKE '%return%' OR TABLE_NAME ILIKE '%warehouse%' OR TABLE_NAME ILIKE '%asc%')
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        LIMIT 50
    """)

    tables = cursor.fetchall()
    if tables:
        print(f"Found {len(tables)} relevant tables:")
        for schema, table in [(row[1], row[0]) for row in tables]:
            print(f"  - {schema}.{table}")
    else:
        print("No tables found with 'return', 'warehouse', or 'asc' in name.")
        print("\nShowing all available schemas:")
        cursor.execute("SHOW SCHEMAS")
        schemas = cursor.fetchall()
        for schema_info in schemas[:10]:
            print(f"  - {schema_info[1]}")

    # Try to find the right query
    print("\n" + "="*60)
    print("Attempting to query quantity returned by ASC warehouse...\n")

    # Common patterns - try to find the data
    try:
        cursor.execute("""
            SELECT *
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME ILIKE '%return%'
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            schema = result[1]
            table = result[0]
            print(f"Querying from {schema}.{table}...")

            cursor.execute(f"""
                SELECT *
                FROM {schema}.{table}
                WHERE WAREHOUSE ILIKE '%ASC%'
                AND GRADE IN ('A', 'B')
                LIMIT 10
            """)

            rows = cursor.fetchall()
            if rows:
                print(f"\nFound {len(rows)} rows:")
                for row in rows:
                    print(row)
            else:
                print("No data found matching the criteria.")
    except Exception as e:
        print(f"Query attempt failed: {e}")
        print("\nPlease provide the table name and column names for:")
        print("- Warehouse column")
        print("- Grade column")
        print("- Quantity returned column")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
