#!/usr/bin/env python3
"""Test script to verify Snowflake connection"""

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

private_key_path = r"C:\Users\SauravMoonka\marketing_ro_user.p8"

print("Connecting to Snowflake...")
print(f"User: saurav.moonka@onequince.com")
print(f"Account: TD05366 (locator)")
print(f"Private Key: {private_key_path}\n")

try:
    # Load the unencrypted private key
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    # Try with account locator
    conn = snowflake.connector.connect(
        user="saurav.moonka@onequince.com",
        private_key=private_key,
        account="TD05366"
    )

    # Execute a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE()")
    result = cursor.fetchone()

    print("✅ Connection successful!")
    print(f"Current User: {result[0]}")
    print(f"Current Account: {result[1]}")
    print(f"Current Warehouse: {result[2]}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTrying with different account formats...")

    # Try again with full account identifier
    try:
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

        conn = snowflake.connector.connect(
            user="saurav.moonka@onequince.com",
            private_key=private_key,
            account="YLEFPTS-QDP_EU"
        )

        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()

        print("✅ Connection successful with YLEFPTS-QDP_EU!")
        print(f"Current User: {result[0]}")
        print(f"Current Account: {result[1]}")
        print(f"Current Warehouse: {result[2]}")

        cursor.close()
        conn.close()

    except Exception as e2:
        print(f"Also failed: {e2}")
