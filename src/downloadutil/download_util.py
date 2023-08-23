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

from downloadutil import Downloader, DownloadConfig

import argparse
import logging
import os


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(filename)s:%(lineno)d] %(asctime)s %(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--url', help='URL to download.', required=True)
    parser.add_argument(
        '--dest-dir-parent', help='Parent directory in which to extract the archive')
    parser.add_argument(
        '--cache-dir',
        default=os.path.expanduser('~/.cache/downloads'),
        help='Download cache directory on the locally mounted disk. Must have enough space.')
    parser.add_argument(
        '--no-cache',
        help='Do not use a cache directory',
        action='store_true')
    parser.add_argument(
        '--verify-checksum',
        help='In addition to downloading the given URL, also download the SHA256 checksum file '
             'from the URL obtained by appending an .sha256 suffix, and verifying the checksum.',
        action='store_true')

    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    args = parser.parse_args()
    config = DownloadConfig(
        verbose=args.verbose,
        cache_dir_path=None if args.no_cache else args.cache_dir)
    downloader = Downloader(config=config)
    result_path = downloader.download_url(
        args.url,
        verify_checksum=args.verify_checksum,
        download_parent_dir_path=args.dest_dir_parent)
    logging.info(f"Downloaded: {result_path}")


if __name__ == '__main__':
    main()
