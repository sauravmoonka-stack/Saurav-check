#!/usr/bin/env python3
"""Query ASC warehouse (location 472) returns by grade"""

import snowflake.connector
import configparser
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

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
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase,
            backend=default_backend()
        )

    conn = snowflake.connector.connect(
        user=user,
        private_key=private_key,
        account="YLEFPTS-QDP_EU",
        warehouse="DEV_COMPUTE_WH",
        database="DL_PROD"
    )

    cursor = conn.cursor()

    print("Querying quantity returned in ASC warehouse (location 472) by grade A, B...\n")

    # Query using warehouse location 472
    query = """
    SELECT
        wp.BIN_GRADE as GRADE,
        COUNT(*) as QUANTITY_RETURNED,
        COUNT(DISTINCT wp.RETURN_LINE_ITEM_ID) as RETURN_COUNT
    FROM DL_PROD.WAREHOUSE_PROCESSING wp
    WHERE wp.LOCATION_ID = 472
        AND wp.BIN_GRADE IN ('A', 'B')
        AND wp.STATUS NOT IN ('CANCELLED', 'REJECTED')
    GROUP BY wp.BIN_GRADE
    ORDER BY wp.BIN_GRADE
    """

    try:
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print("ASC Warehouse (Location 472) - Quantity Returned by Grade:\n")
            print("Grade | Quantity Returned | Return Count")
            print("------|-------------------|-------------")
            for grade, qty, count in results:
                print(f"{grade:5} | {qty:17} | {count}")
        else:
            print("No data found with that query. Trying alternative approach...\n")

            # Alternative: use Hevo tables if available
            alt_query = """
            SELECT
                'A' as GRADE,
                COUNT(*) as QUANTITY
            FROM DL_PROD.WAREHOUSE_RETURN wr
            WHERE wr.WAREHOUSE_LOCATION_ID = 472
            """

            cursor.execute(alt_query)
            alt_results = cursor.fetchall()
            if alt_results:
                print("Data from alternative query:")
                for row in alt_results:
                    print(row)

    except Exception as query_error:
        print(f"Query error: {query_error}")
        print("\nTrying to identify correct table structure...\n")

        # Check what tables are available
        cursor.execute("""
        SELECT TABLE_NAME
        FROM DL_PROD.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME ILIKE '%WAREHOUSE%'
           OR TABLE_NAME ILIKE '%HEVO%'
        LIMIT 20
        """)

        tables = cursor.fetchall()
        print("Available warehouse-related tables:")
        for table in tables:
            print(f"  - {table[0]}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Connection error: {e}")
    import traceback
    traceback.print_exc()
