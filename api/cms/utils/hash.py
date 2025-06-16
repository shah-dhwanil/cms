from hashlib import sha3_256

__all__ = ["hash_string", "verify_hash"]


def hash_string(input_string: str) -> str:
    return sha3_256(input_string.encode("utf-8")).hexdigest()


def verify_hash(input_string: str, hash_value: str) -> bool:
    return hash_string(input_string) == hash_value
