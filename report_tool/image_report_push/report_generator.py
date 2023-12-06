import base64
import os
import shutil
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pydicom
from common_utils import dicom, numpy2dcm
from loguru import logger
from PIL import Image

from report_tool import constants
from report_tool.utils.repacs import get_series_info


class ReportGenerator:
    def __init__(self, task_info: constants.ImageTextPushReq):
        self._task_info = task_info

        self._base_path = (
            Path(constants.DATA_PATH)
            / f"{self._task_info.product}_report"
            / "FB_TMP"
            / self._task_info.series_iuid
        )

        self._img_dir = os.path.join(self._base_path, "img_png")

    def __del__(self) -> None:
        shutil.rmtree(self._base_path, ignore_errors=True)

    def _get_img(self, image_path: str, filename: str) -> None:
        Path(self._img_dir).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(self._img_dir, filename)
        img_path = os.path.join(constants.DATA_PATH, image_path.lstrip("/"))
        shutil.copy(img_path, file_path)

    def _get_rep_img(self, report_info: bytes, filename: str) -> None:
        Path(self._img_dir).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(self._img_dir, filename)
        with open(file_path, "wb+") as file:
            file.write(base64.b64decode(report_info))

    # 获取当下series_iuid下的一张dicom图像
    def _get_series_dicom_path(self) -> str:
        """根据 series_iuid 获取 DICOM 下载路径"""

        series_info = get_series_info(self._task_info.series_iuid)
        dicom_path = series_info["images"][0]["storagePath"]
        dicom_path = os.path.join(constants.DATA_PATH, dicom_path)
        if not os.path.isfile(dicom_path):
            logger.info(f"路径 {dicom_path} 下文件不存在")
        return dicom_path

    def _convert_img_to_dicom(self, filename: str) -> str:
        """用于png图片转为dicom图片并保存（临时保存，后续不需要保存）"""
        std_filename = self._get_series_dicom_path()
        src_filename = os.path.join(self._img_dir, f"{filename}.png")

        std_ds = pydicom.dcmread(std_filename)
        im_frame = Image.open(src_filename)

        im_array = np.array(im_frame.getdata(), dtype=np.uint8)[:, :3]
        new_ds = numpy2dcm.array_to_dicom(
            std_ds, im_array, True, 1, row=im_frame.height, col=im_frame.width
        )

        # 添加个性化tag
        new_ds.StudyInstanceUID = self._task_info.study_iuid
        new_ds.PatientID = self._task_info.patient_id

        # TODO: (dwenzhe) 这里由于目前pacs_postman只接收路径，因此这里需要临时落盘一下，后续会对
        # pacs_postman 进行修改，让其可以接收路径和ds，这里就不需要临时存储了。
        new_ds.SeriesInstanceUID = dicom.gen_suid()
        rst_dcm_path = os.path.join(self._base_path, new_ds.SeriesInstanceUID)
        Path(rst_dcm_path).mkdir(parents=True, exist_ok=True)
        dcm_path = (Path(rst_dcm_path) / f"{new_ds.SeriesInstanceUID}.dcm").as_posix()
        new_ds.save_as(dcm_path, False)

        return dcm_path

    def generate(self) -> Tuple[List[str], List[str]]:
        """生成要推送的dicom图片"""
        # TODO: (dwenzhe) 这里的变量名也做临时修改   all_ds_path, ds_path
        image_ds_path = []
        report_ds_path = []
        if self._task_info.image:
            for idx, image_path in enumerate(self._task_info.image):
                self._get_img(image_path, f"{idx}_img.png")
                ds_path = self._convert_img_to_dicom(f"{idx}_img")
                image_ds_path.append(ds_path)

        if self._task_info.report:
            for idx, report_info in enumerate(self._task_info.report):
                self._get_rep_img(str.encode(report_info), f"{idx}_rep.png")
                ds_path = self._convert_img_to_dicom(f"{idx}_rep")
                report_ds_path.append(ds_path)

        return image_ds_path, report_ds_path
