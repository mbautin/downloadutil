import logging
import os
import hashlib
import urllib.request
import datetime
import random
import shlex
import getpass
import subprocess

from typing import List


BUFFER_SIZE_BYTES = 128 * 1024

# Some servers need this header in order to allow the download.
REQUEST_HEADERS = {'user-agent': 'Mozilla'}


def download_file(url: str, dest_path: str) -> str:
    """
    Download a file to the given path and return its SHA256 sum. Note that this downloads directly
    to the destination path, without usinga temporary file.
    """
    try:
        with open(dest_path, 'wb') as dest_file:
            req = urllib.request.Request(url, headers=REQUEST_HEADERS)
            with urllib.request.urlopen(req) as remote_stream:
                sha256_hash = hashlib.sha256()
                for byte_block in iter(lambda: remote_stream.read(BUFFER_SIZE_BYTES), b""):
                    sha256_hash.update(byte_block)
                    dest_file.write(byte_block)
                return sha256_hash.hexdigest()
    except:  # noqa
        if os.path.exists(dest_path):
            logging.warn("Deleting an unfinished download: %s", dest_path)
            os.remove(dest_path)
        raise


def download_string(url: str, max_bytes: int) -> str:
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(req) as remote_stream:
        bytes_downloaded = 0
        max_bytes_left = max_bytes + 1
        result = bytearray()
        for byte_block in iter(
                lambda: remote_stream.read(min(max_bytes_left, BUFFER_SIZE_BYTES)), b""):
            assert len(byte_block) <= max_bytes_left
            result.extend(byte_block)
            bytes_downloaded += len(byte_block)
        if bytes_downloaded > max_bytes:
            raise IOError(
                "The file at %s is too large (more than %d bytes)", url, max_bytes)
        return byte_block.decode('utf-8')


def check_dir_exists_and_is_writable(dir_path: str, description: str) -> None:
    """
    Check if the given directory exists and is writable. Raises an exception otherwise.
    """
    if not os.path.isdir(dir_path):
        raise IOError("%s directory %s does not exist" % (description, dir_path))
    if not os.access(dir_path, os.W_OK):
        raise IOError("%s directory %s is not writable by current user (%s)" % (
            description, dir_path, getpass.getuser()))


def get_temporal_randomized_file_name_suffix() -> str:
    return "%s.%s" % (
        datetime.datetime.now().strftime('%Y-%m-%dT%H_%M_%S'),
        ''.join([str(random.randint(0, 10)) for i in range(10)])
    )


def cmd_args_to_str(cmd_line_args: List[str]) -> str:
    return ' '.join([shlex.quote(arg) for arg in cmd_line_args])


def log_and_check_call(args: List[str], verbose: bool) -> None:
    args_as_str = cmd_args_to_str(args)
    if verbose:
        logging.info("Running command: %s", args_as_str)
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError as ex:
        logging.exception("Error when executing command: %s", args_as_str)
        raise ex


def log_and_check_output(args: List[str], verbose: bool) -> bytes:
    args_as_str = cmd_args_to_str(args)
    if verbose:
        logging.info("Running command: %s", args_as_str)
    try:
        return subprocess.check_output(args)
    except subprocess.CalledProcessError as ex:
        logging.exception("Error when executing command: %s", args_as_str)
        raise ex


def remove_ignoring_errors(path: str) -> None:
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError as ex:
            logging.exception(f"Ignoring an error while removing file {path}")
