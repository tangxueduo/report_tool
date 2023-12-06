from typing import Any

import requests
from loguru import logger

from report_tool.constants import REPACS_HOST, REPACS_PORT

PREFIX_URL = f"http://{REPACS_HOST}:{REPACS_PORT}"


def get_series_info(series_iuid: str) -> Any:
    url = f"{PREFIX_URL}/series/{series_iuid}"
    resp = requests.get(url, timeout=3)
    return resp.json()


def get_ai_result(
    result_type: str, series_iuid: str, ignore_error: bool = False
) -> Any:
    try:
        url = f"{PREFIX_URL}/series/{series_iuid}/{result_type}"
        resp = requests.get(url, timeout=7)
        resp.raise_for_status()
        result = resp.json()
        logger.info(f"Get {result_type} result successful of {series_iuid}")
    except Exception:
        if ignore_error:
            result = {}
            logger.warning(
                f"Failed to get {result_type} result of {series_iuid}, url : {url}"
            )
        else:
            raise
    return result


def save_result(result: str, result_type: str, series_iuid: str) -> None:
    url = f"{PREFIX_URL}/series/{series_iuid}/{result_type}"
    resp = requests.put(url, json=result, timeout=7)
    resp.raise_for_status()
    logger.info(f"Save {result_type} result of {series_iuid} to repacs")
