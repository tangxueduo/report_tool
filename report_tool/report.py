import base64
import io
import math
import os
import time
from typing import Any, Tuple
from uuid import uuid4

import numpy as np
import pydicom
from common_uitls import dicom
from loguru import logger
from PIL import Image
from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian

from report_tool.constants import (
    DATA_PATH,
    PRODUCT_SSR_RESULT_TYPE,
    REPORT_IMAGE_PATH_MAP,
    ImageItem,
)
from report_tool.utils.imgdb import ImageDB, abs_to_rel
from report_tool.utils.repacs import get_ai_result, save_result


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
    db.init_save_path(item.product)
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


def _base64_to_film(item: ImageItem) -> None:
    """Convert base64 to dcm and update feedback ssr api
    Args:
        refer to:https://wiki.infervision.com/pages/viewpage.action?pageId=543399339
    """
    series_iuid = item.series_iuid
    # convert base64 to image
    base64_decoded = base64.b64decode(item.image)
    image = Image.open(io.BytesIO(base64_decoded))
    image_arr = np.array(resize_custom(image, 512))

    # 取一张原图做样本
    # TODO　这里直接从request　接口取可能更合适

    series_path = "/tmp/"
    # sample_dcm_path = os.path.join(
    #     extra_info.series_path, os.listdir(extra_info.series_path)[0]
    # )
    sample_dcm_path = os.path.join(series_path, os.listdir(series_path)[0])
    sample_dataset = pydicom.read_file(sample_dcm_path, force=True)  # type:ignore

    # init_path
    # TODO: 每个产线初始化文件夹的路径应该不一样, 要做一个映射兼容，目前考虑骨密度, MRA
    screenshot_dcm_dir = screenshot_dir_by_product(item.product, item.series_iuid)
    file_name = f"{uuid4()}.dcm"
    dcm_path = os.path.join(screenshot_dcm_dir, file_name)

    # 落盘
    array_to_dicom(
        origin_ds=sample_dataset,
        np_array=image_arr,
        filename=dcm_path,
        is_vr=True,
        instance_number=1,
    )
    # update_ssr
    update_ssr(series_iuid, dcm_path, item.product, add=True)


def screenshot_dir_by_product(product_name: str, series_iuid: str) -> str:
    """"""
    ssr_path = os.path.join(DATA_PATH, f"RESULT/ssr/{product_name}", series_iuid)
    screenshot_dcm_dir = os.path.join(ssr_path, "dcm/screenshots")
    os.makedirs(screenshot_dcm_dir, exist_ok=True)
    return screenshot_dcm_dir


def update_ssr(
    series_iuid: str, dcm_path: str, product: str, add: bool = False
) -> None:
    """Tool to update ssr images and api result.
    Args:
        dcm_path: dicom图像的绝对路径
        add: true 表示增加, false 表示删除
    """
    for result_type in PRODUCT_SSR_RESULT_TYPE[product]:
        ssr_result = get_ai_result(result_type, series_iuid, True)
        image_type = "seriesImages" if "series" in result_type else "filmImages"
        dcm_path = abs_to_rel(dcm_path)

        # 　TODO: 兼容不同产线的不同结构，
        custom_res = ssr_result[image_type].get("Custom")
        if not custom_res:
            custom_res = [] if product in ("mr_head") else {}
        if isinstance(custom_res, list):
            if add:
                # 更新custom到ssr结果中
                if ssr_result:
                    custom_res.append(dcm_path)
                else:
                    ssr_result[image_type] = {}
                    custom_res = [dcm_path]

            else:
                # 删除custom结果
                custom_res.remove(dcm_path)
                # 删除文件
                try:
                    os.remove(dcm_path)
                except (FileExistsError, OSError):
                    logger.warning(f"{dcm_path} not exists")
        elif isinstance(custom_res, dict):
            pass
        save_result(ssr_result, result_type, series_iuid)


def array_to_dicom(
    origin_ds: pydicom.dataset.FileDataset,
    np_array: np.ndarray,
    filename: str,
    is_vr: bool,
    instance_number: int,
    full_tag: bool = False,
) -> None:
    """将一个 numpy array 转换为一张 dicom 并存储

    Args:
        origin_ds: 原始 dicom 摸一张图的 dataset
        np_array: 待转换的 numpy array
        filename: 存储路径
        is_vr: TODO update desc
        instance_number: new dicom instance number
    """
    creation_date = time.strftime("%Y%m%d", time.localtime(time.time()))
    creation_time = time.strftime("%H%M%S", time.localtime(time.time()))
    ds = origin_ds.copy()
    # edit tags
    ds.file_meta.TransferSyntaxUID = (
        ImplicitVRLittleEndian if origin_ds.is_implicit_VR else ExplicitVRLittleEndian
    )
    ds.Rows, ds.Columns = np_array.shape[:2]
    # ds.Rows, ds.Columns = 512, 512
    ds.InstanceNumber = instance_number
    ds.ImageComments = origin_ds.SeriesDescription
    ds.SeriesInstanceUID = dicom.gen_suid(origin_ds.SeriesInstanceUID)
    ds.InstanceCreationDate = creation_date
    ds.InstanceCreationTime = creation_time
    ds.ContentDate = creation_date
    ds.ContentTime = creation_time
    ds.PresentationCreationDate = creation_date
    ds.PresentationCreationTime = creation_time
    ds.RescaleIntercept = 0
    ds.RescaleSlope = 1
    ds["PixelData"].is_undefined_length = False
    ds.SOPInstanceUID = dicom.gen_uuid()
    ds.file_meta.MediaStorageSOPInstanceUID = origin_ds.SOPInstanceUID
    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    if not ds.SeriesNumber:
        ds.SeriesNumber = "991"
    elif not str(ds.SeriesNumber).startswith("99"):
        ds.SeriesNumber = "99" + str(ds.SeriesNumber)
    ds.ContentLabel = "UNNAMED"
    ds.ContentDescription = "UNNAMED"
    ds.ContentCreatorName = "Infervision"
    if not full_tag:
        dicom.remove_extra_tags(ds)
    if is_vr:
        ds.BitsStored = 8
        ds.BitsAllocated = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.WindowWidth = 255
        ds.WindowCenter = 127
        ds.PhotometricInterpretation = "RGB"
        ds.SamplesPerPixel = 3
        ds.PlanarConfiguration = 0
    else:
        ds.BitsStored = 16
        ds.BitsAllocated = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 1
        ds.WindowWidth = 800
        ds.WindowCenter = 300
    ds.PixelData = np_array.tobytes()
    ds.save_as(filename)


def round_aspect(number: float, key: Any) -> int:
    return max(min(math.floor(number), math.ceil(number), key=key), 1)


def get_new_size(x: int, y: int, aspect: float) -> Tuple[int, int]:
    if x / y >= aspect:
        x = round_aspect(y * aspect, key=lambda n: abs(aspect - n / y))
    else:
        y = round_aspect(x / aspect, key=lambda n: 0 if n == 0 else abs(aspect - x / n))
    return x, y


def resize_custom(im_frame: Image, vr_width: int) -> Image:
    """将截图大小按照宽高比resize 为胶片大小范围内(512, 512)"""
    aspect = im_frame.width / im_frame.height
    x, y = get_new_size(vr_width, vr_width, aspect)
    # TODO: 修改重采样的插值方式，@txueduo,冠脉已经修改
    im_frame = im_frame.resize((x, y), Image.ANTIALIAS)
    image_color = Image.new("RGB", (vr_width, vr_width))
    bw, bh = image_color.size
    lw, lh = im_frame.size
    image_color.paste(im_frame, ((bw - lw) // 2, (bh - lh) // 2))
    return image_color
