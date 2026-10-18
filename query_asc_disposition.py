#!/usr/bin/env python3
"""Query ASC warehouse (location 472) returns by disposition grade"""

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

    print("=" * 60)
    print("ASC Warehouse (Location 472) - Quantity Returned")
    print("=" * 60)
    print()

    # Query 1: Using WAREHOUSE_INVENTORY_HISTORY
    query1 = """
    SELECT
        wih.DISPOSITION as GRADE,
        COUNT(*) as QUANTITY_RETURNED,
        COUNT(DISTINCT wih.RETURN_ID) as RETURN_COUNT
    FROM DL_PROD.WAREHOUSE_INVENTORY_HISTORY wih
    WHERE wih.WAREHOUSE_LOCATION_ID = 472
        AND wih.DISPOSITION IN ('A', 'B')
    GROUP BY wih.DISPOSITION
    ORDER BY wih.DISPOSITION
    """

    print("Query 1: Using WAREHOUSE_INVENTORY_HISTORY table\n")

    cursor.execute(query1)
    results1 = cursor.fetchall()

    if results1:
        print("Grade | Quantity Returned | Return Count")
        print("------|-------------------|-------------")
        for grade, qty, count in results1:
            print(f"{grade:5} | {qty:17} | {count}")
    else:
        print("No data found in WAREHOUSE_INVENTORY_HISTORY")

    print("\n" + "=" * 60)
    print("Query 2: Using WAREHOUSE_PROCESSING table\n")

    # Query 2: Using WAREHOUSE_PROCESSING (if available)
    query2 = """
    SELECT
        wp.STATUS as STEP,
        COUNT(*) as COUNT
    FROM DL_PROD.WAREHOUSE_PROCESSING wp
    WHERE wp.LOCATION_ID = 472
    GROUP BY wp.STATUS
    LIMIT 10
    """

    try:
        cursor.execute(query2)
        results2 = cursor.fetchall()

        if results2:
            print("WAREHOUSE_PROCESSING data by status:")
            for status, count in results2:
                print(f"  {status}: {count}")
        else:
            print("No data in WAREHOUSE_PROCESSING")
    except Exception as e:
        print(f"Could not query WAREHOUSE_PROCESSING: {e}")

    print("\n" + "=" * 60)
    print("Query 3: Check all dispositions available\n")

    # Query 3: See all unique dispositions for ASC warehouse
    query3 = """
    SELECT DISTINCT
        wih.DISPOSITION,
        COUNT(*) as COUNT
    FROM DL_PROD.WAREHOUSE_INVENTORY_HISTORY wih
    WHERE wih.WAREHOUSE_LOCATION_ID = 472
    GROUP BY wih.DISPOSITION
    ORDER BY wih.DISPOSITION
    """

    cursor.execute(query3)
    results3 = cursor.fetchall()

    if results3:
        print("All dispositions in ASC warehouse (472):")
        print("\nDisposition | Count")
        print("------------|------")
        for disp, count in results3:
            print(f"{str(disp):11} | {count}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
