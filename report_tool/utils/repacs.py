from typing import Any

import requests

from report_tool.constants import REPACS_HOST, REPACS_PORT

PREFIX_URL = f"http://{REPACS_HOST}:{REPACS_PORT}"


def get_series_info(series_iuid: str) -> Any:
    url = f"{PREFIX_URL}/series/{series_iuid}"
    resp = requests.get(url, timeout=3)
    return resp.json()
