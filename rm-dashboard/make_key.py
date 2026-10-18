"""Create a 2048-bit RSA key pair for Snowflake key-pair authentication.

Writes rsa_key.p8 (private key, keep it on this PC only) and rsa_key.pub,
then prints the ALTER USER statement that registers the public key.
"""
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

HERE = Path(__file__).resolve().parent
priv_path, pub_path = HERE / "rsa_key.p8", HERE / "rsa_key.pub"
if priv_path.exists():
    raise SystemExit(f"{priv_path.name} already exists; not overwriting it.")

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
priv_path.write_bytes(key.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
pub_pem = key.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
pub_path.write_text(pub_pem)

body = "".join(l for l in pub_pem.splitlines() if "-----" not in l)
print(f"ALTER USER \"SAURAV.MOONKA@ONEQUINCE.COM\" SET RSA_PUBLIC_KEY='{body}';")
