# Copyright (c) YugabyteDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations
# under the License.

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

ARCHIVE_EXTENSIONS = ['.tar.gz', '.tar.bz2', '.zip']


def download_file(url: str, dest_path: str) -> str:
    """
    Download a file to the given path and return its SHA256 sum. Note that this downloads directly
    to the destination path, without using a temporary file.
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
    """
    Download the given URL as a string, up the the given number of bytes. If more bytes are
    downloaded, raises an IOError.
    """
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(req) as remote_stream:
        max_bytes_left = max_bytes + 1
        result = bytearray()
        for byte_block in iter(
                lambda: remote_stream.read(min(max_bytes_left, BUFFER_SIZE_BYTES)), b""):
            assert len(byte_block) <= max_bytes_left
            max_bytes_left -= len(byte_block)
            result.extend(byte_block)
            if max_bytes_left == 0:
                break
        if len(result) > max_bytes:
            raise IOError(
                "The file at %s is too large (at least %d bytes, more than %d bytes)" % (
                    url, len(result), max_bytes))
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


def add_optional_dash_and_suffix(prefix: str, suffix: str) -> str:
    """
    Adds an optional dash (if the prefix does not already end with a dash) and the given suffix.
    If the suffix or the prefix are empty, does not add any dashes.

    >>> add_optional_dash_and_suffix('foo-', 'bar')
    'foo-bar'
    >>> add_optional_dash_and_suffix('foo', 'bar')
    'foo-bar'
    >>> add_optional_dash_and_suffix('foo', '-bar')
    'foo-bar'
    >>> add_optional_dash_and_suffix('foo-', '-bar')
    'foo--bar'
    >>> add_optional_dash_and_suffix('foo', '')
    'foo'
    >>> add_optional_dash_and_suffix('', 'foo')
    'foo'
    """
    if suffix == '':
        return prefix
    if prefix == '':
        return suffix
    if prefix.endswith('-') or suffix.startswith('-'):
        return prefix + suffix

    return f'{prefix}-{suffix}'


def add_suffix_before_archive_extension(file_name: str, suffix: str) -> str:
    """
    Adds a dash and the given suffix before the archive extension, such as .tar.gz. If the extension
    is not one of the recognized archive extensions, the suffix is added at the very end.

    >>> add_suffix_before_archive_extension('some/dir/foo.bar.tar.gz', 'mysuffix')
    'some/dir/foo.bar-mysuffix.tar.gz'
    >>> add_suffix_before_archive_extension('some/dir/myfile.zip', 'mysuffix')
    'some/dir/myfile-mysuffix.zip'
    >>> add_suffix_before_archive_extension('some/dir/myfile.tar.bz2', 'mysuffix')
    'some/dir/myfile-mysuffix.tar.bz2'
    """
    for extension in ARCHIVE_EXTENSIONS:
        if file_name.endswith(extension):
            return add_optional_dash_and_suffix(file_name[:-len(extension)], suffix) + extension

    return add_optional_dash_and_suffix(file_name, suffix)


def append_random_tmp_suffix(path: str) -> str:
    return '%s.%s' % (path, get_temporal_randomized_file_name_suffix())
