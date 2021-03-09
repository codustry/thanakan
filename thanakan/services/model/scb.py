from enum import IntEnum
from typing import Dict, List, Literal, Union

from fastapi_utils.api_model import APIModel

from services.model.common import SlipData


class StatusCode(IntEnum):
    """
    only known status codes
    """
    success = 1000


class Status(APIModel):
    code: Union[StatusCode, int]
    description: str


class CredentialsData(APIModel):
    access_token: str
    token_type: Literal['Bearer'] = 'Bearer'
    expires_in: int
    expires_at: int


class BaseResponse(APIModel):
    status: Status
    data: Dict


class SCBCredentialsResponse(BaseResponse):
    data: CredentialsData


class QR30Data(APIModel):
    qr_raw_data: str
    qr_image: str # seems like a base64 string


class CreateQR30Response(BaseResponse):
    data: QR30Data

class VerifyResponse(BaseResponse):
    data: SlipData

class TransactionInquiryResponse(BaseResponse):
    data: List[Dict]
