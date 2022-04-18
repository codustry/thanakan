"""
https://developer.scb/#/documents/documentation/qr-payment/payment-confirmation.html
"""

from typing import Literal, Optional, Union

import json
import uuid
from enum import Enum

from fastapi import Body, FastAPI, Request
from fastapi_utils.api_model import APIModel
from pydantic import BaseModel, Field

app = FastAPI()


class PaymentConfirmation(APIModel):
    transaction_id: str = Field(
        ...,
        description="Transaction ID generated by source system",
    )
    amount: str = Field(
        ...,
        description="Amount of Transaction",
    )
    transaction_date_and_time: str = Field(
        ...,
        alias="transactionDateandTime",
        description="Date and Time of transaction in ISO 8601 format SCB EASY App Payment (BP), SCB EASY App Payment (CCFA), SCB EASY App Payment (IPP), QR30, Alipay, WeChatPay : Time in GMT+7 QRCS : Time in GMT",
    )
    currency_code: str = Field(
        ...,
        description="Code to define currency for transaction based on ISO 4217 for transactionAmount. Thai Baht is ‘764’",
    )
    transaction_type: Union[str]

    merchant_id: Optional[str] = None
    terminal_id: Optional[str] = None
    qr_id: Optional[str] = None
    merchant_pan: Optional[str] = None
    consumer_pan: Optional[str] = None
    trace_no: Optional[str] = None
    authorize_code: Optional[str] = None

    payee_proxy_type: Optional[str] = None
    payee_proxy_id: Optional[str] = None
    payee_account_number: Optional[str] = None
    payee_name: Optional[str] = None

    payer_proxy_id: Optional[str] = None
    payer_proxy_type: Optional[str] = None
    payer_name: Optional[str] = None
    payer_account_name: Optional[str] = None
    payer_account_number: Optional[str] = None

    bill_payment_ref1: Optional[str] = None
    bill_payment_ref2: Optional[str] = None
    bill_payment_ref3: Optional[str] = None
    sending_bank_code: Optional[str] = None
    receiving_bank_code: Optional[str] = None
    channel_code: Optional[str] = None

    payment_method: Optional[str] = None
    tenor: Optional[str] = None
    ipp_type: Optional[str] = None
    product_code: Optional[str] = None

    exchange_rate: Optional[str] = None
    equivalent_amount: Optional[str] = None
    equivalent_currency_code: Optional[str] = None
    company_id: Optional[str] = None

    invoice: Optional[str] = None
    note: Optional[str] = None


@app.post("/v1/scb")
async def handle_scb_callback(confirmation: PaymentConfirmation):
    response = {
        "resCode": "00",
        "resDesc ": "success",
        "transactionId": confirmation.transaction_id,
        "confirmId": "abc00confirm",
    }
    with open(f"{uuid.uuid4().hex}_response.json", "w") as f:
        json.dump(response, f)

    with open(f"{uuid.uuid4().hex}_confirmation.json", "w") as f:
        json.dump(confirmation.dict(), f)

    return response


@app.get("/v1/scb")
async def ok():
    """
    see in the UAT dunno what it is for
    """
    return "ok"
