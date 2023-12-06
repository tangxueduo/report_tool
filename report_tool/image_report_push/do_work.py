import os
import traceback

from common_utils.pacs_postman import file_io_utils, push_image
from loguru import logger

from report_tool import constants
from report_tool.image_report_push import report_generator


def report_push(item: constants.ImageTextPushReq) -> dict:
    # 创建push_task_json
    push_task_dir = os.path.join(constants.DATA_PATH, f"{item.product}_report")
    os.makedirs(push_task_dir, exist_ok=True)

    re_gen = report_generator.ReportGenerator(item)

    # 获取dicom图片路径
    image_ds_path, report_ds_path = re_gen.generate()

    # dicom图片重组
    images = [{"path": image_path} for image_path in image_ds_path]
    reports = [{"path": report_path} for report_path in report_ds_path]
    if not images and not reports:
        logger.warning(
            f"{item.series_iuid} Cannot push report {reports} and image {images}"
        )
        return {}

    # pacs_postman 环境变量
    envs = {
        "MEDIUM_TYPE": constants.MEDIUM_TYPE,
        "LEFT_INFO": constants.LEFT_INFO,
        "RIGHT_INFO": constants.RIGHT_INFO,
        "BOTTOM_INFO": constants.BOTTOM_INFO,
        "FONT_SIZE": constants.FONT_SIZE,
        "LETTER_SPACING": constants.LETTER_SPACING,
        "IS_CUSTOM_FILM_FORMAT": constants.CUSTOM_FILM_FORMAT,
        "UNVALIDATED_AE_TITLES": constants.UNVALIDATED_AE_TITLES.split(","),
    }

    for ae_info in item.pacs:
        # 某张图失败，整个任务不算失败
        image_rst = "ok"
        report_rst = "ok"
        tmp_ae_info = {
            "server_ae": ae_info.pacs_client_aet,
            "server_ip": ae_info.pacs_sevrer_ip,
            "server_port": ae_info.pacs_server_port,
        }

        series_number = file_io_utils.get_series_number(
            item.study_iuid, constants.DATA_PATH
        )

        # 推送
        if images:
            try:
                push_image(
                    images,
                    tmp_ae_info,
                    constants.PACS_SERVER_AET,
                    get_series_desc("image"),
                    series_number=series_number,
                    **envs,
                )
            except Exception:
                logger.error(f"图文报告,图片推送失败。 失败原因：{traceback.format_exc()}")
                image_rst = "error"

        if reports:
            try:
                push_image(
                    reports,
                    tmp_ae_info,
                    constants.PACS_SERVER_AET,
                    get_series_desc("report"),
                    series_number=series_number,
                    **envs,
                )
            except Exception:
                logger.error(f"图文报告,报告推送失败。失败原因： {traceback.format_exc()}")
                report_rst = "error"

    return {"image": image_rst, "report": report_rst}


def get_series_desc(target_type: str) -> str:
    """Get report image series desc."""
    if target_type == "report":
        desc = "TX Push Report"
    elif target_type == "image":
        desc = "TX Push Image"
    return desc
