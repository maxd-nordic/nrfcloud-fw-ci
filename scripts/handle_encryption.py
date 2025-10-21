import os
import secrets
import argparse
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization, constant_time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


MAGIC_HEADER = b"ECCFV100"  # file format identifier V1.0.0

# default public key
PUBKEY = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE9cGzSB4vdeG1GjdH4Ej7hikkfjNp
3lhpqsUQ89d6hSkIiFn+VxTh2LcvsTlzpFMrItcOj2boGwEWmisO8Tv4+A==
-----END PUBLIC KEY-----
"""

# --- Key loading ---
def load_key_with_type(filename, need_private=False):
    """Load a key file and return both the key object and its type."""
    with open(filename, "rb") as f:
        data = f.read()

    # Try to load as private key first
    try:
        private_key = serialization.load_pem_private_key(data, password=None)
        if need_private:
            return private_key
        else:
            return private_key.public_key()
    except ValueError:
        # If that fails, try as public key
        try:
            public_key = serialization.load_pem_public_key(data)
            if not need_private:
                return public_key
            else:
                raise ValueError(f"File {filename} does not contain a private key")
        except ValueError:
            raise ValueError(f"File {filename} does not contain a valid PEM key")

# --- Encryption ---
def encrypt_file(input_file, output_file, recipient_pubkey):
    # Generate ephemeral key pair for this encryption
    ephemeral_private = ec.generate_private_key(ec.SECP256R1())
    ephemeral_public = ephemeral_private.public_key()

    # Perform ECDH to get shared secret
    shared_secret = ephemeral_private.exchange(ec.ECDH(), recipient_pubkey)

    # Derive encryption key from shared secret
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None, # OK: shared_secret is unique each time
        info=b"ecies-file-encryption",
    ).derive(shared_secret)

    # Generate nonce for file encryption
    file_nonce = secrets.token_bytes(12)

    # Encrypt file content directly using derived key
    aesgcm = AESGCM(derived_key)
    with open(input_file, "rb") as f:
        plaintext = f.read()
    ciphertext = aesgcm.encrypt(file_nonce, plaintext, None)

    # Serialize ephemeral public key for transmission
    eph_pub_bytes = ephemeral_public.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # Construct simplified header
    header = (
        MAGIC_HEADER
        + len(eph_pub_bytes).to_bytes(4, "big")
        + eph_pub_bytes
        + file_nonce
    )

    with open(output_file, "wb") as f:
        f.write(header)
        f.write(ciphertext)

    print(f"Encrypted: {input_file} -> {output_file}")


# --- Decryption ---
def decrypt_file(input_file, output_file, recipient_privkey):
    with open(input_file, "rb") as f:
        magic = f.read(len(MAGIC_HEADER))
        if magic != MAGIC_HEADER:
            raise ValueError("Not a valid encrypted file")

        eph_pub_len = int.from_bytes(f.read(4), "big")
        eph_pub_bytes = f.read(eph_pub_len)

        # Reconstruct ephemeral public key from bytes
        ephemeral_public = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), eph_pub_bytes
        )

        file_nonce = f.read(12)
        ciphertext = f.read()

    # Perform ECDH with the ephemeral public key using our private key
    shared_secret = recipient_privkey.exchange(ec.ECDH(), ephemeral_public)

    # Derive the same encryption key
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"ecies-file-encryption",
    ).derive(shared_secret)

    # Decrypt file directly using derived key
    aesgcm = AESGCM(derived_key)
    plaintext = aesgcm.decrypt(file_nonce, ciphertext, None)

    with open(output_file, "wb") as f:
        f.write(plaintext)

    print(f"Decrypted: {input_file} -> {output_file}")


# --- Auto mode ---
def auto_process(input_file, output_file, key_file=None):
    """Auto-detect whether to encrypt or decrypt based on the file header."""
    with open(input_file, "rb") as f:
        magic = f.read(len(MAGIC_HEADER))

    if magic == MAGIC_HEADER:
        if not key_file:
            raise ValueError("Private key file required for decryption")

        # Load key and verify it's actually a private key
        key = load_key_with_type(key_file, need_private=True)

        decrypt_file(input_file, output_file, key)
    else:
        # Otherwise -> encrypt
        if key_file:
            key = load_key_with_type(key_file)
        else:
            key = serialization.load_pem_public_key(PUBKEY.encode())
        encrypt_file(input_file, output_file, key)


# --- CLI ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Hybrid ECC file encryption/decryption tool. Automatically detects encrypt/decrypt mode based on file header and key type."
    )

    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")
    parser.add_argument(
        "--key",
        help="Key file (private key for decryption, public/private key for encryption). If not provided, uses default public key for encryption."
    )

    args = parser.parse_args()

    auto_process(args.input, args.output, args.key)
