from typing import Optional, Any


class DownloadConfig:
    verbose: bool
    cache_dir_path: Optional[str]

    def __init__(
            self,
            verbose: bool = False,
            cache_dir_path: Optional[str] = None) -> None:
        self.verbose = verbose
        self.cache_dir_path = cache_dir_path
