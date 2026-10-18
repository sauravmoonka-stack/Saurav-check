#!/usr/bin/env python3
"""Query ASC warehouse returns by disposition - quantity as distinct line items"""

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
        warehouse="DEV_COMPUTE_WH"
    )

    cursor = conn.cursor()
    cursor.execute("USE DATABASE DL_PROD")

    print("=" * 70)
    print("ASC Warehouse (Location 472) - Quantity Returned by Grade")
    print("=" * 70)
    print()

    # Query: Using WAREHOUSE_INVENTORY_HISTORY
    # Quantity = distinct count of return_id (not return unit id since that's not in the table)
    query = """
    SELECT
        wih.DISPOSITION as GRADE,
        COUNT(DISTINCT wih.RETURN_ID) as QUANTITY_RETURNED_DISTINCT,
        COUNT(*) as TOTAL_ITEMS,
        COUNT(DISTINCT wih.RETURN_ID) as RETURN_COUNT
    FROM WAREHOUSE_INVENTORY_HISTORY wih
    WHERE wih.WAREHOUSE_LOCATION_ID = 472
        AND wih.DISPOSITION IN ('A', 'B')
    GROUP BY wih.DISPOSITION
    ORDER BY wih.DISPOSITION
    """

    print("Query: Distinct count of returns by disposition (grade)\n")

    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        print("Grade | Quantity Returned (Distinct) | Total Items | Return Count")
        print("------|------------------------------|-------------|-------------")
        for grade, qty_distinct, total, return_count in results:
            print(f"{str(grade):5} | {qty_distinct:28} | {total:11} | {return_count}")
        print()
        print("Summary:")
        total_qty = sum(row[1] for row in results)
        print(f"  Total Quantity (Grade A + B): {total_qty}")
    else:
        print("No data found for grades A and B")
        print("\nChecking all available grades...")

        query_all = """
        SELECT DISTINCT DISPOSITION FROM WAREHOUSE_INVENTORY_HISTORY
        WHERE WAREHOUSE_LOCATION_ID = 472
        ORDER BY DISPOSITION
        """

        cursor.execute(query_all)
        all_grades = cursor.fetchall()

        if all_grades:
            print("\nAvailable dispositions in ASC warehouse (472):")
            for grade in all_grades:
                print(f"  - {grade[0]}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
