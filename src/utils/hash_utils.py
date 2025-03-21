from _hashlib import HASH as Hash
import hashlib
import os


def hash_dir(path: str) -> Hash:
    h = hashlib.md5()
    for root, _, files in os.walk(path):
        for file in files:
            with open(os.path.join(root, file), 'rb') as f:
                h.update(f.read())
    return h


def hash_file(path: str) -> Hash:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' not found!")

    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h
