# from cryptography.fernet import Fernet
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib


# FERET - Requires C compiler-------------------------------------------------------------------------

# def prepare_key(encryption_key):
#     if(len(encryption_key) < 32):
#         encryption_key = (int((32 / len(encryption_key)))+1 )*encryption_key

#     key_bytearray  = bytearray(encryption_key[:32], 'ASCII')

#     return base64.urlsafe_b64encode(key_bytearray)    
    

# def encrypt_data(data, encryption_key):
    
#     fernet = Fernet(prepare_key(encryption_key))
    
#     # then use the Fernet class instance 
#     # to encrypt the string string must
#     # be encoded to byte string before encryption
#     encrypted_data = fernet.encrypt(data.encode())
#     return encrypted_data

# def decrypt_data(data, encryption_key):
    
    
#     fernet = Fernet(prepare_key(encryption_key))
    
#     # decrypt the encrypted string with the 
#     # Fernet instance of the key,
#     # that was used for encrypting the string
#     # encoded byte string is returned by decrypt method,
#     # so decode it to string with decode methods
#     decrypted_data = fernet.decrypt(data).decode()
#     return decrypted_data


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
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv + ct

def decrypt_data(data, encryption_key):
    key = prepare_key(encryption_key)
    iv = base64.b64decode(data[:24])
    ct = base64.b64decode(data[24:])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode('utf-8')