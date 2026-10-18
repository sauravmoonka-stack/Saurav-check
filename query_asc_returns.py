#!/usr/bin/env python3
"""Query quantity returned in ASC warehouse by grade A, B"""

import snowflake.connector
import configparser
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

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
    cursor.execute("USE DATABASE DL_INTEG")

    print("Querying quantity returned in ASC warehouse by grade A, B...\n")

    # Query to get quantity returned from ASC warehouse
    query = """
    SELECT
        wl.DISPLAY_NAME as WAREHOUSE_NAME,
        wa.BIN_GRADE as GRADE,
        COUNT(DISTINCT wrl.ID) as RETURN_COUNT,
        COUNT(*) as TOTAL_ITEMS
    FROM WAREHOUSE_RETURN_LINE_ITEM wrl
    JOIN WAREHOUSE_RETURN wr ON wrl.WAREHOUSE_RETURN_ID = wr.ID
    JOIN WAREHOUSE_LOCATIONS wl ON wr.WAREHOUSE_LOCATION_ID = wl.ID
    LEFT JOIN WAREHOUSE_AISLES wa ON wl.ID = wa.WAREHOUSE_LOCATION_ID
    WHERE wl.DISPLAY_NAME ILIKE '%ASC%'
        AND wa.BIN_GRADE IN ('A', 'B')
        AND wrl.WAREHOUSE_RETURN_LINE_ITEM_STATUS NOT IN ('CANCELLED', 'REJECTED')
    GROUP BY wl.DISPLAY_NAME, wa.BIN_GRADE
    ORDER BY wl.DISPLAY_NAME, wa.BIN_GRADE
    """

    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        print(f"Found {len(results)} records:\n")
        for warehouse, grade, return_count, total_items in results:
            print(f"Warehouse: {warehouse}")
            print(f"  Grade: {grade}")
            print(f"  Return Count: {return_count}")
            print(f"  Total Items: {total_items}\n")
    else:
        print("No data found. Checking available warehouses...\n")

        cursor.execute("""
        SELECT DISTINCT DISPLAY_NAME FROM WAREHOUSE_LOCATIONS
        WHERE DISPLAY_NAME IS NOT NULL
        LIMIT 20
        """)

        warehouses = cursor.fetchall()
        print("Available warehouses:")
        for w in warehouses:
            print(f"  - {w[0]}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
