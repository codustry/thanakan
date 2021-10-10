"""
ref. https://developer.scb/assets/documents/documentation/qr-payment/extracting-data-from-mini-qr.pdf
beware! the "Sample data on mini QR" is poison, there is no such structure in real world.
"""
from typing import List

from dataclasses import dataclass
from enum import Enum

from crccheck.crc import Crc16CcittFalse
from PIL import Image
from pydantic import BaseModel
from pyzbar.pyzbar import Decoded, decode
from pyzbar.wrapper import ZBarSymbol


class Tag(Enum):
    payload = "00"
    country_code = "51"
    crc = "91"


class SubTag(Enum):
    api_id = "00"
    sending_bank_id = "01"
    transaction_ref_id = "02"


@dataclass
class CodeSection:
    code: str
    is_under_payload: bool = False

    @property
    def tag(self):
        return self.code[:2]

    @property
    def tag_type(self):
        return SubTag(self.tag) if self.is_under_payload else Tag(self.tag)

    @property
    def length(self):
        return int(self.code[2:4])

    @property
    def data(self):
        return self.code[4 : 4 + self.length]

    @property
    def rest(self):
        r = self.code[4 + self.length :]
        if r:
            return r
        else:
            return None


class QrPayload(BaseModel):
    api_id: str
    sending_bank_id: str
    transaction_ref_id: str

    @classmethod
    def create_from_code(cls, code):
        api_id = CodeSection(code, is_under_payload=True)
        if not api_id.tag_type == SubTag.api_id:
            raise not_bank_slip("invalid `api id` code section")

        sending_bank_id = CodeSection(api_id.rest, is_under_payload=True)
        if not sending_bank_id.tag_type == SubTag.sending_bank_id:
            raise not_bank_slip("invalid `sending bank id` code section")

        transaction_ref_id = CodeSection(
            sending_bank_id.rest, is_under_payload=True
        )
        if not transaction_ref_id.tag_type == SubTag.transaction_ref_id:
            raise not_bank_slip("invalid `transaction ref id` code section")

        if not transaction_ref_id.rest is None:
            raise not_bank_slip("unexpected extend code section")

        return cls(
            api_id=api_id.data,
            sending_bank_id=sending_bank_id.data,
            transaction_ref_id=transaction_ref_id.data,
        )


class not_bank_slip(Exception):
    pass


class expect_single_qrcode(Exception):
    pass


class SlipQRData(BaseModel):
    payload: QrPayload
    country_code: str
    crc: str

    @classmethod
    def create_from_code(cls, code: str):
        code = code.strip()

        payload = CodeSection(code=code)
        if not payload.tag_type == Tag.payload:
            raise not_bank_slip("invalid `payload` code section")

        country_code = CodeSection(code=payload.rest)
        if not country_code.tag_type == Tag.country_code:
            raise not_bank_slip("invalid `country code` code section")

        crc = CodeSection(code=country_code.rest)

        if not crc.tag_type == Tag.crc:
            raise not_bank_slip("invalid `crc` code section")

        if not crc.rest is None:
            raise not_bank_slip("unexpected extend code section")

        data_part = code[: -crc.length]
        calc_crc = Crc16CcittFalse.calchex(
            data_part.encode(encoding="ascii")
        ).upper()
        if not calc_crc == crc.data:
            raise not_bank_slip("calculated crc and provided crc are unmatched")

        return cls(
            payload=QrPayload.create_from_code(payload.data),
            country_code=country_code.data,
            crc=crc.data,
        )

    @classmethod
    def create_from_image(cls, pil_image: Image):
        qr_inside: List[Decoded] = decode(
            pil_image, symbols=[ZBarSymbol.QRCODE]
        )
        if len(qr_inside) != 1:
            raise expect_single_qrcode()

        qr_data = qr_inside[0].data.decode("UTF-8")

        return cls.create_from_code(qr_data)
