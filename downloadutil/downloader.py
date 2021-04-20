import os
import logging
import shutil

from downloadutil.download_cache import DownloadCache
from downloadutil.util import (
    download_string, append_random_tmp_suffix
)
from downloadutil.checksum_util import (
    validate_sha256sum,
    compute_file_sha256,
    SHA256_CHECKSUM_FILE_SUFFIX,
    parse_sha256_from_file,
    read_sha256_from_file,
    get_sha256_file_path_or_url
)
from downloadutil.download_strategy import DownloadStrategy, CurlDownloadStrategy
from downloadutil.download_config import DownloadConfig

from typing import Optional


MAX_CHECKSUM_FILE_SIZE_BYTES = 65536


class Downloader:
    cache: Optional[DownloadCache]
    strategy: DownloadStrategy
    config: DownloadConfig

    def __init__(self, config: DownloadConfig) -> None:
        self.cache = None
        self.config = config
        if config.cache_dir_path:
            self.cache = DownloadCache(config)

        self.strategy = CurlDownloadStrategy(config)

    def download_url(
            self,
            url: str,
            download_parent_dir_path: Optional[str],
            verify_checksum: bool) -> str:
        """
        Downloads the given URL and returns the downloaded file path.

        :param url: The URL to download
        :param download_parent_dir_path: where to put the resulting file. This is allowed to be None
            only in case we are using a cache directory, and in that case the path to the cached
            file is returned.
        :param verify_checksum: Whether to download a special checksum file from a URL that is the
            same as the given URL but with an .sha256 appended, and to verify the file checksum
            using the expected SHA256 checksum in that file.
        """
        use_only_cache_directory: bool
        if download_parent_dir_path:
            use_only_cache_directory = False
            download_dest_path = os.path.join(download_parent_dir_path, os.path.basename(url))
        elif self.cache:
            # We will download directly to cache.
            use_only_cache_directory = True
            download_dest_path = self.cache.cached_path_for_url(url)
        else:
            raise ValueError(
                "No download parent directory path or cache directory is configured. "
                f"Not sure where to download URL {url}.")
        download_tmp_dest_path = append_random_tmp_suffix(download_dest_path)

        cached_download_path: Optional[str] = None
        expected_sha256: Optional[str] = None
        if self.cache:
            cached_download_path = self.cache.find_cached_download_path(url)
            if cached_download_path:
                if self.config.verbose:
                    logging.info(f"Found cached download path: {cached_download_path}")

                # Always verify checksum for files in cache.
                expected_sha256 = read_sha256_from_file(
                    get_sha256_file_path_or_url(cached_download_path))

                actual_sha256 = compute_file_sha256(cached_download_path)
                if actual_sha256 == expected_sha256:
                    if use_only_cache_directory:
                        # Not copying the file to a user-specified directory. Just returning the
                        # path in our cache.
                        return cached_download_path

                    if self.config.verbose:
                        logging.info(
                            f"Copying cached file {cached_download_path} to "
                            f"{download_tmp_dest_path}")
                    shutil.copyfile(cached_download_path, download_tmp_dest_path)
                    return cached_download_path

                logging.warning(
                    f"Checksum mismatch: expected {expected_sha256}, got "
                    f"{actual_sha256} for cached file {cached_download_path}. "
                    "Invalidating the cache entry and re-downloading.")
                self.cache.invalidate_for_url(url)

            else:
                if self.config.verbose:
                    logging.info(
                        f"Did not find a cached path for {url} in {self.cache}, will download.")

        expected_sha256 = None
        if verify_checksum:
            checksum_url = get_sha256_file_path_or_url(url)
            checksum_file_contents = self.strategy.download_to_memory(
                url=checksum_url,
                max_num_bytes=MAX_CHECKSUM_FILE_SIZE_BYTES
            ).decode('utf-8')
            expected_sha256 = parse_sha256_from_file(checksum_file_contents)

        if self.config.verbose:
            logging.info(f"Downloading URL {url} to {download_tmp_dest_path}")
        try:
            self.strategy.download_to_file(
                url=url,
                dest_path=download_tmp_dest_path,
                max_num_bytes=None)
        except Exception as ex:
            if os.path.exists(download_tmp_dest_path):
                os.remove(download_tmp_dest_path)
            raise ex

        if not os.path.exists(download_tmp_dest_path):
            raise IOError(f"Failed to download {url} to file {download_tmp_dest_path}")

        if verify_checksum:
            actual_sha256 = compute_file_sha256(download_tmp_dest_path)
            if actual_sha256 != expected_sha256:
                os.remove(download_tmp_dest_path)
                raise IOError(
                    f"Invalid checksum: {actual_sha256}, expected {expected_sha256} for file "
                    f"{download_tmp_dest_path} downloaded from {url}")

        if self.cache:
            self.cache.save_to_cache(
                url,
                download_tmp_dest_path,
                expected_sha256,
                move_file=use_only_cache_directory)

        if not use_only_cache_directory:
            if self.config.verbose:
                logging.info(f"Moving {download_tmp_dest_path} to {download_dest_path}")
            os.rename(download_tmp_dest_path, download_dest_path)

        return download_dest_path
