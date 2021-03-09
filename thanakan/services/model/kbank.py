from typing import Optional

from fastapi_utils.api_model import APIModel
from loguru import logger
from pydantic import root_validator

from thanakan.services.model.common import SlipData


class VerifyResponse(APIModel):
    rqUID: str
    status_code: str
    status_message: str
    data: Optional[SlipData]

    @root_validator(pre=True)
    def fail_make_data_none(cls, values):
        if values["statusCode"] != "0000":
            logger.warning(
                "request not success, status {}, msg {}",
                values["statusCode"],
                values["statusMessage"],
            )
            logger.debug("This is data. {}", values["data"])
            values["data"] = None
        return values
