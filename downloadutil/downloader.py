import os
import logging
import shutil

from downloadutil.download_cache import DownloadCache
from downloadutil.util import (
    download_string, get_temporal_randomized_file_name_suffix
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
            verify_checksum: bool,
            download_parent_dir_path: str) -> str:
        """
        Downloads the given URL and returns the downloaded file path.
        """
        expected_sha256: Optional[str] = None

        cached_download_path: Optional[str] = None

        download_dest_path = os.path.join(download_parent_dir_path, os.path.basename(url))
        download_tmp_dest_path = '%s.%s' % (
            download_dest_path,
            get_temporal_randomized_file_name_suffix()
        )

        need_to_download = True
        if self.cache:
            cached_download_path = self.cache.find_cached_download_path(url)
            if cached_download_path:
                if self.config.verbose:
                    logging.info(
                        f"Found cached download path: {cached_download_path}")
                    # Always verify checksum for files in cache.
                    expected_sha256 = read_sha256_from_file(
                        get_sha256_file_path_or_url(cached_download_path))
                    if self.config.verbose:
                        logging.info(
                            f"Copying cached file {cached_download_path} to "
                            f"{download_tmp_dest_path}")
                    shutil.copyfile(cached_download_path, download_tmp_dest_path)
                    actual_sha256 = compute_file_sha256(download_tmp_dest_path)
                    if actual_sha256 == expected_sha256:
                        need_to_download = False
                    else:
                        logging.warning(
                            f"Checksum mismatch: expected {expected_sha256}, got "
                            f"{actual_sha256} for cached file {cached_download_path}. "
                            "Re-downloading.")
                        os.remove(download_tmp_dest_path)
                        self.cache.invalidate_for_url(url)
                        expected_sha256 = None

            else:
                if self.config.verbose:
                    logging.info(
                        f"Did not find a cached path for {url} in {self.cache}, will download.")

        if verify_checksum and not expected_sha256:
            checksum_url = get_sha256_file_path_or_url(url)
            checksum_file_contents = self.strategy.download_to_memory(
                url=checksum_url,
                max_num_bytes=MAX_CHECKSUM_FILE_SIZE_BYTES
            ).decode('utf-8')
            expected_sha256 = parse_sha256_from_file(checksum_file_contents)

        if need_to_download:
            if self.config.verbose:
                logging.info(f"Downloading URL {url}")
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
            raise IOError("Download failed to create file {download_tmp_dest_path}")

        if not cached_download_path and self.cache:
            self.cache.save_to_cache(url, download_tmp_dest_path, expected_sha256)

        if self.config.verbose:
            logging.info(f"Moving {download_tmp_dest_path} to {download_dest_path}")

        os.rename(download_tmp_dest_path, download_dest_path)
        return download_tmp_dest_path
