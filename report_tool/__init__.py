"""
report_tool
=========

A simple tool to convert base64 to jpg, png, and Numpy array.


Basic usage:
    report_tool.b642png()

"""
from report_tool.constants import ImageItem
from report_tool.report import _base64_to_report

__version__ = "1.0.0"


def b642png(item: ImageItem) -> None:
    """convert base64 to png"""
    _base64_to_report(item)


def b642film() -> None:
    """"""
    pass
