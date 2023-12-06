from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel


class ReportImageType(Enum):
    PRESET = "preset"
    SCREENSHOT = "screenshot"
    UPLOAD = "upload"


# Report Image request structure
# TODO: 这里面的字段应该在不同产品线里面做到字段兼容
class ImageItem(BaseModel):
    series_iuid: str = ""
    image: str = ""  # base64 encode png
    predict_type: str = ""  # ct_bmd
    target: Union[str, List[str]]  # 图像应用场景， 包括 report, film. 用 , 间隔表示支持多种使用场景
    report_image_type: ReportImageType  # 图文报告中图像分类, 包括 preset, screenshot, upload
    option: Any = None  # 前端用于记录图像信息, 仅用于图文报告
    extra: Any = None


# 预设图，上传图，截图，子目录映射
REPORT_IMAGE_PATH_MAP = {
    "preset": "image/preset",
    "screenshot": "image/screenshot",
    "upload": "image/upload",
}


# 图文报告需要获取的 PACS 配置
class ImageTextPacsConfig(BaseModel):
    pacs_sevrer_ip: str
    pacs_server_port: int
    pacs_client_aet: str


class ImageTextPushReq(BaseModel):
    series_iuid: str
    study_iuid: str
    patient_id: str
    report: List[str] = []  # 报告回传
    image: List[str] = []  # 图像回传
    pacs: List[ImageTextPacsConfig]
    product: str


class ImageTextPushResp(BaseModel):
    image: Optional[str]
    report: Optional[str]


# 默认
DATA_PATH = "/media/tx-deepocean/Data/DICOMS"
MEDIUM_TYPE = "BLUE FILM"
LEFT_INFO = "PatientName,PatientID,PatientAge+PatientSex,StudyDate,StudyTime"
RIGHT_INFO = "HospitalName,Manufacturer,SeriesDescription"
BOTTOM_INFO = "WindowWidth,WindowCenter"
LETTER_SPACING = 1
CUSTOM_FILM_FORMAT = 0
PACS_SERVER_AET = "TXPACS"
REPACS_HOST = "repacs"
REPACS_PORT = 3333
FONT_SIZE = 15
UNVALIDATED_AE_TITLES = ""
