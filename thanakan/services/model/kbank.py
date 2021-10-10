from typing import Optional

from fastapi_utils.api_model import APIModel
from loguru import logger
from pydantic import root_validator
from thanakan.services.model.common import SlipData


class KbankSlipVerifyResponse(APIModel):

    rqUID: str
    status_code: str
    status_message: str
    data: Optional[SlipData]

    @property
    def status(self):
        return f"{self.status_code}: {self.status_message}"

    @root_validator(pre=True)
    def fail_make_data_none(cls, values):
        """
        This is to prevent expected consequnece validations fail in the `SlipData` .
        """
        if values["statusCode"] != "0000":
            logger.warning(
                "request not success, with Error {}: {}",
                values["statusCode"],
                values["statusMessage"],
            )
            logger.debug("This is data. {}", values["data"])
            values["data"] = None
        return values
