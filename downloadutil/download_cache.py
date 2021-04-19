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
from downloadutil.util import remove_ignoring_errors

from typing import Optional


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
        return os.path.join(
            self.cache_dir_path,
            f"{os.path.basename(url)}-urlsha256={compute_string_sha256(url)}")

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

    def save_to_cache(self, url: str, downloaded_path: str, expected_sha256: Optional[str]) -> None:
        self.ensure_cache_dir_exists()
        cached_path = self.cached_path_for_url(url)
        if expected_sha256:
            validate_sha256sum(expected_sha256)
        else:
            if self.config.verbose:
                logging.info(f"Computing SHA256 checksum of {downloaded_path}")
            expected_sha256 = compute_file_sha256(downloaded_path)
        if self.config.verbose:
            logging.info(f"Copying downloaded file {downloaded_path} to cache at {cached_path}.")
        shutil.copyfile(downloaded_path, cached_path)
        cached_sha256_path = get_sha256_file_path_or_url(cached_path)
        if self.config.verbose:
            logging.info(
                f"Writing expected SHA256 checksum {expected_sha256} to {cached_sha256_path}")
        with open(cached_sha256_path, 'w') as sha256_file:
            sha256_file.write(expected_sha256 + '\n')

    def __str__(self) -> str:
        return f'download cache at {self.cache_dir_path}'
