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

from downloadutil import Downloader, DownloadConfig


class TestDownloadUtil(unittest.TestCase):
    def test_something(self) -> None:
        with tempfile.TemporaryDirectory(prefix='download_util_test_') as tmp_dir:
            config = DownloadConfig()
            downloader = Downloader(config=config)
            print("Temp dir: %s" % tmp_dir)
            downloader.download_url(
                'https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc',
                download_parent_dir_path=tmp_dir,
                verify_checksum=False)


if __name__ == '__main__':
    unittest.main()
