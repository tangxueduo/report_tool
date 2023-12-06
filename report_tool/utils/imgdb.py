import base64
import json
import os
import shutil
from typing import Any

from report_tool.constants import DATA_PATH


class ImageDB:
    """Report image tool for save and read"""

    def __init__(self, series_iuid: str, sub_dir: str, extra_info: Any) -> None:
        self.sub_dir = sub_dir
        self.series_iuid = series_iuid
        self.extra_info = extra_info

    def init_save_path(self, product: str) -> None:
        self.sub_dir = os.path.join(
            self.extra_info.data_path,
            f"{product}_report",
            self.sub_dir,
            self.series_iuid,
        )
        os.makedirs(self.sub_dir, exist_ok=True)

    def save_cache(self, file_path: str, content: Any) -> None:
        with open(file_path, "w") as f:
            f.write(json.dumps(content))

    def save_png(self, file_path: str, content: Any) -> None:
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(content))

    def load(self, file_path: str) -> str:
        with open(file_path) as f:
            return json.load(f)

    def remove(self, file_path: str) -> None:
        """Tool to delete a file or a dir
        Args:
            file_path: abs path for a file or a dir
        Return:
            None
        """
        if os.path.isdir(file_path):
            shutil.rmtree(file_path, ignore_errors=True)
        elif os.path.isfile(file_path):
            os.remove(file_path)


# TODO : DATA_PATH 由os.getenv()获取？
def abs_to_rel(path: str, ref: str = DATA_PATH) -> str:
    """Absolute path to relative path"""
    return path.replace(os.path.realpath(ref), "").strip("/")


def rel_to_abs(path: str, ref: str = DATA_PATH) -> str:
    """Relative path to absolute path"""
    return os.path.join(ref, path)
