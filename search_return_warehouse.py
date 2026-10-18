#!/usr/bin/env python3
"""Search for return and warehouse related tables"""

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

    # Search for columns containing 'return', 'warehouse', 'grade', 'asc'
    databases = ['DL_INTEG', 'DL_PROD', 'CDP_DW', 'DW_PROD']

    print("🔎 Searching for relevant columns...\n")

    for db in databases:
        try:
            cursor.execute(f"""
                SELECT TABLE_NAME, COLUMN_NAME
                FROM {db}.INFORMATION_SCHEMA.COLUMNS
                WHERE COLUMN_NAME ILIKE '%return%'
                   OR COLUMN_NAME ILIKE '%warehouse%'
                   OR COLUMN_NAME ILIKE '%grade%'
                   OR COLUMN_NAME ILIKE '%asc%'
            """)

            columns = cursor.fetchall()
            if columns:
                print(f"📍 {db}:")
                for table, col in columns:
                    print(f"  - {table}.{col}")
                print()
        except:
            pass

    # Also try to find tables by name
    print("\n" + "="*60)
    print("📋 Tables with relevant keywords:\n")

    for db in databases:
        try:
            cursor.execute(f"""
                SELECT TABLE_NAME
                FROM {db}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME ILIKE '%return%'
                   OR TABLE_NAME ILIKE '%exchange%'
                   OR TABLE_NAME ILIKE '%inventory%'
                   OR TABLE_NAME ILIKE '%warehouse%'
            """)

            tables = cursor.fetchall()
            if tables:
                print(f"🏢 {db}:")
                for table in tables:
                    print(f"  - {table[0]}")
                    # Show columns for this table
                    cursor.execute(f"""
                        SELECT COLUMN_NAME
                        FROM {db}.INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = '{table[0]}'
                        LIMIT 20
                    """)
                    columns = cursor.fetchall()
                    for col in columns:
                        print(f"      • {col[0]}")
                print()
        except:
            pass

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
