import os
import subprocess
import logging
import shlex

from downloadutil.download_config import DownloadConfig
from downloadutil.util import log_and_check_call, log_and_check_output

from typing import Optional, List


class MaxDownloadSizeExceeded(IOError):
    def __init__(self, url: str, max_num_bytes: int) -> None:
        super(IOError, self).__init__(
            f"When downloading URL {url}, maximum download size exceeded: {max_num_bytes}"
        )


class DownloadStrategy:
    config: DownloadConfig

    def download_to_file(
            self,
            url: str,
            dest_path: str,
            max_num_bytes: Optional[int]) -> None:
        raise NotImplementedError()

    def download_to_memory(self, url: str, max_num_bytes: Optional[int]) -> bytes:
        raise NotImplementedError()


class CurlDownloadStrategy(DownloadStrategy):
    CURL_CMD_LINE_PREFIX = [
        'curl',
        '--location',  # Follow links.
        '--silent',
        '--show-error',
    ]

    def __init__(self, config: DownloadConfig) -> None:
        self.config = config

    def _get_curl_cmd_line(
            self,
            url: str,
            dest_path: Optional[str] = None,
            max_num_bytes: Optional[int] = None) -> List[str]:
        cmd_line = list(CurlDownloadStrategy.CURL_CMD_LINE_PREFIX)
        if dest_path:
            cmd_line.extend(['-o', dest_path])
        if max_num_bytes:
            # Add one to max size so we can detect if we go over.
            cmd_line.extend(['--max-filesize', str(max_num_bytes + 1)])
        cmd_line.append(url)
        return cmd_line

    def download_to_file(
            self,
            url: str,
            dest_path: str,
            max_num_bytes: Optional[int] = None) -> None:
        cmd_line = self._get_curl_cmd_line(
            url=url,
            dest_path=dest_path,
            max_num_bytes=max_num_bytes)
        log_and_check_call(cmd_line, self.config.verbose)
        if max_num_bytes:
            actual_file_size = os.path.getsize(dest_path)
            if actual_file_size > max_num_bytes:
                raise MaxDownloadSizeExceeded(url, max_num_bytes)

    def download_to_memory(self, url: str, max_num_bytes: Optional[int]) -> bytes:
        result: bytes = log_and_check_output(
            self._get_curl_cmd_line(url, max_num_bytes=max_num_bytes),
            self.config.verbose)
        if max_num_bytes and len(result) > max_num_bytes:
            raise MaxDownloadSizeExceeded(url, max_num_bytes)
        return result
