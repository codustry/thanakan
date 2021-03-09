"""
ref. https://developer.scb/assets/documents/documentation/qr-payment/extracting-data-from-mini-qr.pdf
beware! the "Sample data on mini QR" is poison, there is no such structure in real world.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List

from PIL import Image
from crccheck.crc import Crc16CcittFalse
from pydantic import BaseModel
from pyzbar.pyzbar import decode, Decoded
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
        assert api_id.tag_type == SubTag.api_id

        sending_bank_id = CodeSection(api_id.rest, is_under_payload=True)
        assert sending_bank_id.tag_type == SubTag.sending_bank_id

        transaction_ref_id = CodeSection(
            sending_bank_id.rest, is_under_payload=True
        )
        assert transaction_ref_id.tag_type == SubTag.transaction_ref_id
        assert transaction_ref_id.rest is None

        return cls(
            api_id=api_id.data,
            sending_bank_id=sending_bank_id.data,
            transaction_ref_id=transaction_ref_id.data,
        )


class not_bank_slip(BaseException):
    pass


class QRData(BaseModel):
    payload: QrPayload
    country_code: str
    crc: str

    @classmethod
    def create_from_code(cls, code: str):
        code = code.strip()

        payload = CodeSection(code=code)
        assert payload.tag_type == Tag.payload

        country_code = CodeSection(code=payload.rest)
        assert country_code.tag_type == Tag.country_code

        crc = CodeSection(code=country_code.rest)
        assert crc.tag_type == Tag.crc
        assert crc.rest is None

        data_part = code[: -crc.length]
        calc_crc = Crc16CcittFalse.calchex(
            data_part.encode(encoding="ascii")
        ).upper()
        assert calc_crc == crc.data

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
            raise not_bank_slip("Expect only 1 qr in image.")

        qr_data = qr_inside[0].data.decode("UTF-8")

        return cls.create_from_code(qr_data)
