#!/usr/bin/env python3
"""Find relevant tables in Snowflake"""

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

    # List databases
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()

    print("📊 Available Databases:")
    db_names = []
    for db in databases[:15]:
        db_name = db[1]
        db_names.append(db_name)
        print(f"  - {db_name}")

    print("\n" + "="*60)
    print("🔍 Searching for relevant tables...\n")

    # Search for tables with relevant keywords in each database
    keywords = ['return', 'warehouse', 'asc', 'grade']

    for db in db_names[:3]:  # Check first 3 databases
        try:
            cursor.execute(f"""
                SELECT TABLE_NAME
                FROM {db}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                LIMIT 30
            """)

            tables = cursor.fetchall()
            if tables:
                print(f"📦 {db} - Tables found ({len(tables)}):")
                for table in tables:
                    print(f"    - {table[0]}")
                print()
        except:
            pass

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
