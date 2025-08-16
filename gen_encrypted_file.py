from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# 1MB of random plaintext
plaintext = os.urandom(1024 * 1024)  # 1MB

# AES key and IV (random)
key = os.urandom(32)  # AES-256
iv = os.urandom(16)

# Encrypt using AES-CBC
cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
encryptor = cipher.encryptor()

# Pad to 16 bytes (AES block size)
pad_len = 16 - (len(plaintext) % 16)
padded = plaintext + bytes([pad_len] * pad_len)

# Encrypt
ciphertext = encryptor.update(padded) + encryptor.finalize()

# Save to file
with open("./test_files/encrypted_files/encrypted_1MB_1.bin", "wb") as f:
    f.write(ciphertext)
