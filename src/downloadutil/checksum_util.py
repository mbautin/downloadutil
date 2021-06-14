import os
from downloadutil.util import BUFFER_SIZE_BYTES
from typing import Any

import re
import hashlib


SHA256_CHECKSUM_RE = re.compile(r'^[0-9a-f]{64}$')
SHA256_CHECKSUM_FILE_SUFFIX = '.sha256'


def validate_sha256sum(checksum_str: str) -> None:
    """
    Validtes the given SHA256 checksum. Raises an exception if it is invalid.
    """
    if not SHA256_CHECKSUM_RE.match(checksum_str):
        raise ValueError(
            "Invalid SHA256 checksum: '%s', expected 64 hex characters" % checksum_str)


def update_hash_with_file(hash: Any, filename: str, block_size: int = BUFFER_SIZE_BYTES) -> str:
    """
    Compute the hash sun of a file by updating the existing hash object.
    """
    # TODO: use a more precise argument type for hash.
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hash.update(block)
    return hash.hexdigest()


def compute_file_sha256(path: str) -> str:
    return update_hash_with_file(hashlib.sha256(), path)


def compute_string_sha256(s: str) -> str:
    hash = hashlib.sha256()
    hash.update(s.encode('utf-8'))
    return hash.hexdigest()


def parse_sha256_from_file(checksum_file_contents: str) -> str:
    sha256_from_file = checksum_file_contents.strip().split()[0]
    validate_sha256sum(sha256_from_file)
    return sha256_from_file


def read_sha256_from_file(checksum_file_path: str) -> str:
    with open(checksum_file_path) as checksum_file:
        return parse_sha256_from_file(checksum_file.readline())


def get_sha256_file_path_or_url(original_path_or_url: str) -> str:
    if original_path_or_url.endswith(SHA256_CHECKSUM_FILE_SUFFIX):
        raise ValueError(
            f"File path or URL already ends with {SHA256_CHECKSUM_FILE_SUFFIX}: "
            f"{original_path_or_url}, will not add the same suffix again.")
    return original_path_or_url + SHA256_CHECKSUM_FILE_SUFFIX
