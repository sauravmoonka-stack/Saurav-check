#!/usr/bin/env python3
"""Query Snowflake using credentials from ~/.snowflake/credentials/sf.ini"""

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

# Decode passphrase
passphrase = None
if passphrase_b64:
    passphrase = base64.b64decode(passphrase_b64)

print(f"Connecting to Snowflake as {user}...\n")

try:
    # Load private key
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase,
            backend=default_backend()
        )

    # Connect
    conn = snowflake.connector.connect(
        user=user,
        private_key=private_key,
        account="YLEFPTS-QDP_EU"
    )

    # Run query
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE()")
    result = cursor.fetchone()

    print("✅ Connected successfully!")
    print(f"User: {result[0]}")
    print(f"Account: {result[1]}")
    print(f"Warehouse: {result[2]}\n")

    # Example query - show available databases
    print("Running example query...")
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    print(f"Available databases ({len(databases)} total):")
    for db in databases[:5]:
        print(f"  - {db[1]}")
    if len(databases) > 5:
        print(f"  ... and {len(databases) - 5} more")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
