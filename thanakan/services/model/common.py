from typing import Literal, Optional, Union

from decimal import Decimal
from enum import auto

from fastapi_utils.api_model import APIModel
from fastapi_utils.enums import StrEnum
from pydantic import constr, root_validator, validator
from thanakan.models.bankcode import AnyBankCode, BankCode


class ProxyType(StrEnum):
    NATID = auto()
    MSISDN = auto()
    EWALLETID = auto()
    EMAIL = auto()
    BILLERID = auto()

    # SCB
    ACCOUNT = auto()


class Proxy(APIModel):
    type: Optional[ProxyType]
    value: Optional[str]

    @validator("*", pre=True)
    def convert_empty_str_to_none(cls, v):
        if isinstance(v, str) and v == "":
            return None
        else:
            return v


class AccountType(StrEnum):
    BANKAC = auto()
    TOKEN = auto()
    DUMMY = auto()


class Account(APIModel):
    type: Optional[AccountType]
    value: Optional[str]

    @validator("*", pre=True)
    def convert_empty_str_to_none(cls, v):
        if isinstance(v, str) and v == "":
            return None
        else:
            return v


class End(APIModel):
    display_name: Optional[str]
    name: Optional[str]
    proxy: Optional[Proxy]
    account: Optional[Account]

    @validator("proxy", "account")
    def dict_of_all_none_to_none(cls, v):
        if all((y is None for x, y in v)):
            return None
        else:
            return v


class SlipData(APIModel):
    language: Optional[Literal["EN", "TH"]]
    receiving_bank: Optional[Union[BankCode, AnyBankCode]]
    sending_bank: Union[BankCode, AnyBankCode]
    trans_ref: str
    trans_date: str
    trans_time: str
    sender: End
    receiver: End
    amount: Decimal
    paid_local_amount: Optional[Decimal]
    country_code: Optional[constr(min_length=2, max_length=2)]
    trans_fee_amount: Optional[str]
    ref1: Optional[str]
    ref2: Optional[str]
    ref3: Optional[str]
    to_merchant_id: Optional[str]

    @validator("*", pre=True)
    def convert_empty_str_to_none(cls, v):
        if isinstance(v, str) and v == "":
            return None
        else:
            return v
