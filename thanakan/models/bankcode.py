from enum import Enum

from pydantic.types import constr


class BankCode(Enum):
    """
    https://www.bot.or.th/Thai/Statistics/DataManagementSystem/Standard/StandardCode/Pages/default.aspx
    """
    BBL = "002"
    KBANK = "004"


AnyBankCode = constr(min_length=3, max_length=3)
