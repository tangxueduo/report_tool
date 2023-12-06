import os
import time
from uuid import uuid4

from report_tool.constants import REPORT_IMAGE_PATH_MAP, ImageItem
from report_tool.utils.imgdb import ImageDB, abs_to_rel


def _base64_to_report(item: ImageItem) -> None:
    """base64 编码的图像存储为 png 图像， 使用 ImageDB 记录图像路径，使用 ReportImage 记录图文报告图像信息
    Args:
        series_iuid: str = ""
        image: str = ""  # base64 encode png
        predict_type: str = ""  # ct_bmd
        target: str = "report,film"  # 图像应用场景， 包括 report, film. 用 , 间隔表示支持多种使用场景
        report_image_type: ReportImageType = (
            None  # 图文报告中图像分类, 包括 preset, screenshot, upload
        )
        option: Any = None  # 前端用于记录图像信息, 仅用于图文报告
        extra: Any = None
    Return:
        None
    """
    db = ImageDB(
        item.series_iuid,
        sub_dir=REPORT_IMAGE_PATH_MAP[item.report_image_type.value],
        extra_info=None,
    )
    db.init_save_path(item.predict_type)
    suffix = f"{uuid4()}.png"
    image_file = os.path.join(db.sub_dir, suffix)
    db.save_png(image_file, item.image)

    # 存储cache.json文件 与 png 同名的文件
    cache_name = os.path.join(db.sub_dir, suffix.replace(".png", ".cache.json"))
    option_dict = {"timestamp": time.time()}
    if item.option:
        option_dict.update(item.option)

    # TODO: 这里所有产线的存储结构一致
    content = {
        "report_image_type": item.report_image_type.value,
        "series_iuid": item.series_iuid,
        "option": {"desc": "", "id": 1, "imageId": "", "timestamp": time.time()},
        "path": abs_to_rel(image_file),
    }

    db.save_cache(cache_name, content)


def _base64_to_film() -> None:
    pass
