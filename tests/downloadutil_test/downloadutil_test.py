# Copyright (c) Yugabyte, Inc.
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
import unittest
import tempfile

from downloadutil import Downloader, DownloadConfig, util


class TestDownloadUtil(unittest.TestCase):
    def test_something(self) -> None:
        with tempfile.TemporaryDirectory(prefix='download_util_test_') as tmp_dir:
            config = DownloadConfig()
            downloader = Downloader(config=config)
            downloader.download_url(
                'https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc',
                download_parent_dir_path=tmp_dir,
                verify_checksum=False)


class TestDirectDownloads(unittest.TestCase):
    def test_download_file(self) -> None:
        url = 'https://github.com/yugabyte/yugabyte-db-thirdparty/releases/download/' \
              'v20230815011048-76449cf143-macos-arm64/yugabyte-db-thirdparty-v20230815011048-' \
              '76449cf143-macos-arm64.tar.gz.sha256'
        expected_result = (
            '5322556c5fabe3c3abe55b23a06386494702af1e0c890494970dbb1688717a23  '
            'yugabyte-db-thirdparty-v20230815011048-76449cf143-macos-arm64.tar.gz\n'
        )
        with tempfile.TemporaryDirectory(prefix='download_util_test_') as tmp_dir:
            dest_path = os.path.join(tmp_dir, 'myfile1')

            result = util.download_file(url, dest_path=dest_path)
            self.assertTrue(os.path.exists(dest_path))

            with open(dest_path) as input_file:
                contents = input_file.read()
            self.assertEqual(expected_result, contents)

        result = util.download_string(url, len(expected_result))
        self.assertEqual(expected_result, result)

        try:
            result = util.download_string(url, len(expected_result) - 1)
            self.fail("Expetected to throw an IOError")
        except IOError as ex:
            if 'too large' not in str(ex):
                raise ex


if __name__ == '__main__':
    unittest.main()
