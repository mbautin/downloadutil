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

import os
import shutil
import pathlib
import logging

from downloadutil.download_config import DownloadConfig
from downloadutil.checksum_util import (
    compute_string_sha256,
    SHA256_CHECKSUM_FILE_SUFFIX,
    get_sha256_file_path_or_url,
    validate_sha256sum,
    compute_file_sha256,
)
from downloadutil.util import (
    remove_ignoring_errors,
    add_suffix_before_archive_extension,
)

from typing import Optional


class CacheEntry:
    url: str
    sha256: str
    content_file_name: str

    def __init__(self, url: str, sha256: str, content_file_name: str) -> None:
        self.url = url
        self.sha256 = sha256
        self.content_file_name = content_file_name


class DownloadCache:
    config: DownloadConfig
    cache_dir_path: str

    """
    A directory containing downloaded files and their checksum files.
    """
    def __init__(self, config: DownloadConfig) -> None:
        self.config = config
        assert config.cache_dir_path
        self.cache_dir_path = os.path.abspath(config.cache_dir_path)

    def ensure_cache_dir_exists(self) -> None:
        pathlib.Path(self.cache_dir_path).mkdir(parents=True, exist_ok=True)

    def cached_path_for_url(self, url: str) -> str:
        url_basename = os.path.basename(url)
        return os.path.join(
            self.cache_dir_path,
            add_suffix_before_archive_extension(
                url_basename,
                f"urlsha256={compute_string_sha256(url)}"
            ))

    def find_cached_download_path(self, url: str) -> Optional[str]:
        cached_path = self.cached_path_for_url(url)
        cached_checksum_path = get_sha256_file_path_or_url(cached_path)
        if os.path.exists(cached_path) and os.path.exists(cached_checksum_path):
            return cached_path
        return None

    def invalidate_for_url(self, url: str) -> None:
        cached_path = self.find_cached_download_path(url)
        if cached_path:
            cached_checksum_path = get_sha256_file_path_or_url(cached_path)
            remove_ignoring_errors(cached_path)
            remove_ignoring_errors(cached_checksum_path)

    def save_to_cache(
            self,
            url: str,
            downloaded_path: str,
            expected_sha256: Optional[str],
            move_file: bool) -> None:
        self.ensure_cache_dir_exists()
        cached_path = self.cached_path_for_url(url)
        if expected_sha256:
            validate_sha256sum(expected_sha256)
        else:
            if self.config.verbose:
                logging.info(f"Computing SHA256 checksum of {downloaded_path}")
            expected_sha256 = compute_file_sha256(downloaded_path)

        if move_file:
            if self.config.verbose:
                logging.info(f"Moving file {downloaded_path} to cache at {cached_path}")
            os.rename(downloaded_path, cached_path)
        else:
            if self.config.verbose:
                logging.info(
                    f"Copying downloaded file {downloaded_path} to cache at {cached_path}")
            shutil.copyfile(downloaded_path, cached_path)

        cached_sha256_path = get_sha256_file_path_or_url(cached_path)
        if self.config.verbose:
            logging.info(
                f"Writing expected SHA256 checksum {expected_sha256} to {cached_sha256_path}")
        with open(cached_sha256_path, 'w') as sha256_file:
            sha256_file.write(expected_sha256 + '\n')

    def __str__(self) -> str:
        return f'download cache at {self.cache_dir_path}'
