#!/usr/bin/env python3
"""Query quantity returned using Hevo warehouse tables"""

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
        account="YLEFPTS-QDP_EU"
    )

    cursor = conn.cursor()

    print("Searching for Hevo warehouse tables...\n")

    # First, find Hevo tables
    cursor.execute("""
    SELECT TABLE_NAME
    FROM DL_INTEG.INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME ILIKE '%HEVO%' OR TABLE_NAME ILIKE '%warehouse%'
    AND TABLE_TYPE = 'BASE TABLE'
    LIMIT 50
    """)

    tables = cursor.fetchall()
    if tables:
        print(f"Found {len(tables)} Hevo/warehouse related tables:")
        for table in tables:
            print(f"  - {table[0]}")
        print("\nTo query the correct data, I need the exact table names.")
        print("\nWhich of these tables contains the quantity returned data?")
        print("Also, which columns contain:")
        print("  - Warehouse/Location name")
        print("  - Grade (A, B, etc.)")
        print("  - Quantity returned")
    else:
        print("No Hevo-specific tables found.")
        print("\nPlease provide:")
        print("1. Database name")
        print("2. Table name(s)")
        print("3. Column names for warehouse, grade, and quantity")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
