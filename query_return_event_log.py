#!/usr/bin/env python3
"""Query WAREHOUSE_RETURN_EVENT_LOG for ASC warehouse returns"""

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

    print("=" * 70)
    print("ASC Warehouse (Location 472) - Returns from WAREHOUSE_RETURN_EVENT_LOG")
    print("=" * 70)
    print()

    # First, let's see what columns and data we have
    print("Exploring table structure and data...\n")

    query1 = """
    SELECT
        WAREHOUSE_LOCATION_ID,
        COUNT(DISTINCT LINE_ITEM_ID) as QUANTITY_RETURNED,
        COUNT(DISTINCT RETURN_ID) as RETURN_COUNT,
        COUNT(*) as TOTAL_EVENTS
    FROM WAREHOUSE_RETURN_EVENT_LOG
    WHERE WAREHOUSE_LOCATION_ID = 472
    GROUP BY WAREHOUSE_LOCATION_ID
    """

    cursor.execute(query1)
    result1 = cursor.fetchone()

    if result1:
        loc_id, qty, return_count, events = result1
        print(f"Warehouse Location: {loc_id}")
        print(f"Quantity Returned (Distinct Line Items): {qty}")
        print(f"Return Count: {return_count}")
        print(f"Total Events: {events}")
    else:
        print("No data found for warehouse location 472")

    print("\n" + "=" * 70)
    print("Now querying by grade (disposition) if available...\n")

    # Check if there's a disposition/grade column
    query2 = """
    SELECT *
    FROM WAREHOUSE_RETURN_EVENT_LOG
    WHERE WAREHOUSE_LOCATION_ID = 472
    LIMIT 1
    """

    cursor.execute(query2)
    col_names = [desc[0] for desc in cursor.description]
    print(f"Available columns in WAREHOUSE_RETURN_EVENT_LOG:")
    for col in col_names:
        print(f"  - {col}")

    print("\n" + "=" * 70)
    print("Sample data from ASC warehouse (location 472):\n")

    query3 = """
    SELECT *
    FROM WAREHOUSE_RETURN_EVENT_LOG
    WHERE WAREHOUSE_LOCATION_ID = 472
    LIMIT 5
    """

    cursor.execute(query3)
    rows = cursor.fetchall()

    for i, row in enumerate(rows, 1):
        print(f"Record {i}:")
        for col, val in zip(col_names, row):
            print(f"  {col}: {val}")
        print()

    # Try to find grade/disposition related columns
    print("=" * 70)
    print("Searching for grade/disposition in data...\n")

    # Check if there's grade info in the exception_event_payload or other fields
    query4 = """
    SELECT DISTINCT
        EXCEPTION_TYPE,
        COUNT(*) as COUNT
    FROM WAREHOUSE_RETURN_EVENT_LOG
    WHERE WAREHOUSE_LOCATION_ID = 472
    GROUP BY EXCEPTION_TYPE
    LIMIT 10
    """

    cursor.execute(query4)
    rows4 = cursor.fetchall()

    if rows4:
        print("Exception types found:")
        for exc_type, count in rows4:
            print(f"  {exc_type}: {count}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
