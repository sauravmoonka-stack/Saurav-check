#!/usr/bin/env python3
"""Query CDP_DW for ASC warehouse returns"""

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
        database="CDP_DW"
    )

    cursor = conn.cursor()

    print("=" * 70)
    print("Querying VW_MIXPANEL_RETURN_ORDERS from CDP_DW")
    print("=" * 70)
    print()

    # Query the Mixpanel return orders view
    query = """
    SELECT
        COUNT(*) as TOTAL_RETURNS,
        SUM(QUANTITY_RETURNED) as TOTAL_QUANTITY_RETURNED
    FROM CDP.VW_MIXPANEL_RETURN_ORDERS
    WHERE RETURN_DATE >= DATEADD(month, -1, CURRENT_DATE())
    """

    print("Recent returns (last 30 days):\n")
    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        total_returns, total_qty = result
        print(f"Total Returns: {total_returns}")
        print(f"Total Quantity Returned: {total_qty}")
    else:
        print("No data found")

    print("\n" + "=" * 70)
    print("Exploring available columns in VW_MIXPANEL_RETURN_ORDERS...\n")

    # Check what columns are available
    query_explore = """
    SELECT * FROM CDP.VW_MIXPANEL_RETURN_ORDERS
    LIMIT 1
    """

    cursor.execute(query_explore)
    col_names = [desc[0] for desc in cursor.description]

    print("Available columns:")
    for col in col_names:
        print(f"  - {col}")

    cursor.close()
    conn.close()

    print("\nBased on available columns, what specific data do you need?")
    print("Can you provide the:")
    print("  1. Column name for warehouse/location")
    print("  2. Column name for grade")
    print("  3. Confirmation on QUANTITY_RETURNED column")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
