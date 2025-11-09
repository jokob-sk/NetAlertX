from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os
import hashlib
import uuid


# SIMPLE CRYPT - requeres C compiler -------------------------------------------------------------------------

# def prepare_key(encryption_key):
#     if len(encryption_key) < 32:
#         encryption_key = (encryption_key * ((32 // len(encryption_key)) + 1))[:32]
#     return encryption_key

# def encrypt_data(data, encryption_key):
#     key = prepare_key(encryption_key)
#     encrypted_data = encrypt(key, data)
#     return encrypted_data

# def decrypt_data(data, encryption_key):
#     key = prepare_key(encryption_key)
#     decrypted_data = decrypt(key, data).decode('utf-8')
#     return decrypted_data

# pycryptodome -------------------------------------------------------------------------


def prepare_key(encryption_key):
    key = hashlib.sha256(encryption_key.encode()).digest()
    return key


def encrypt_data(data, encryption_key):
    key = prepare_key(encryption_key)
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode("utf-8"), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode("utf-8")
    ct = base64.b64encode(ct_bytes).decode("utf-8")
    return iv + ct


def decrypt_data(data, encryption_key):
    key = prepare_key(encryption_key)
    iv = base64.b64decode(data[:24])
    ct = base64.b64decode(data[24:])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode("utf-8")


# -------------------------------------------------------------------------------
def get_random_bytes(length):
    # Generate random bytes
    random_bytes = os.urandom(length)

    # Convert bytes to hexadecimal string
    hex_string = random_bytes.hex()

    # Format hexadecimal string with hyphens
    formatted_hex = "-".join(
        hex_string[i : i + 2] for i in range(0, len(hex_string), 2)
    )

    return formatted_hex


# -------------------------------------------------------------------------------
def generate_deterministic_guid(plugin, primary_id, secondary_id):
    """Generates a deterministic GUID based on plugin, primary ID, and secondary ID."""
    data = f"{plugin}-{primary_id}-{secondary_id}".encode("utf-8")
    return str(uuid.UUID(hashlib.md5(data).hexdigest()))
