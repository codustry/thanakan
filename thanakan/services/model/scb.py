from typing import Dict, List, Literal, Union

from dataclasses import Field
from datetime import datetime
from decimal import Decimal
from enum import IntEnum

from fastapi_utils.api_model import APIModel
from thanakan.models.bankcode import AnyBankCode, BankCode
from thanakan.services.model.common import ProxyType, SlipData


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
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    expires_at: int


class BaseResponse(APIModel):
    status: Status
    data: Dict


class SCBCredentialsResponse(BaseResponse):
    data: CredentialsData


class QR30Data(APIModel):
    qr_raw_data: str
    qr_image: str  # seems like a base64 string


class CreateQR30Response(BaseResponse):
    data: QR30Data


class VerifyResponse(BaseResponse):
    data: SlipData


class TransactionInquiryResponse(BaseResponse):
    data: List[Dict]


class WebhookBody(APIModel):
    transaction_date_and_time: datetime
    sending_bank_code: Union[BankCode, AnyBankCode]
    payer_name: str
    payer_proxy_type: ProxyType
    payer_proxy_id: str
    payer_account_number: str
    receiving_bank_code: Union[BankCode, AnyBankCode]
    payee_name: str
    payee_proxy_type: ProxyType
    payee_proxy_id: str
    payee_account_number: str
    amount: Decimal
    currency_code: str  # wtf "764" thb?
    transaction_id: str
    transaction_type: str
    bill_payment_ref1: str
    bill_payment_ref2: str
    bill_payment_ref3: str
    channel_code: str

    class Config:
        schema_extra = {
            "example": {
                "transactionDateandTime": "2021-02-24T11:10:12+07:00",
                "sendingBankCode": "014",
                "payerName": "Susophida Khunnawut",
                "payerProxyType": "ACCOUNT",
                "payerProxyId": "1502830001",
                "payerAccountNumber": "1502830001",
                "receivingBankCode": "014",
                "payeeName": "TestBiller1608347078",
                "payeeProxyType": "BILLERID",
                "payeeProxyId": "925244165291982",
                "payeeAccountNumber": "0987654321",
                "amount": "100",
                "currencyCode": "764",
                "transactionId": "9ed5caf2-0a38-4f5a-80b1-20e76f26b2a6",
                "transactionType": "Domestic Transfers",
                "billPaymentRef1": "ABCDEFGHIJ1234567890",
                "billPaymentRef2": "ABCDEFGHIJ1234567890",
                "billPaymentRef3": "YQH",
                "channelCode": "PMH",
            }
        }
