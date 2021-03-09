"""

ref.
https://apiportal.kasikornbank.com/product/public/Information/Slip%20Verification/Try%20API/d519307a-6d82-4e77-b9f4-dc74e542c742
"""
import uuid
from datetime import datetime
from typing import Optional, Dict

import httpx
import pytz
from furl import furl
from httpx._types import CertTypes
from httpx_auth import OAuth2ClientCredentials
from loguru import logger

from thanakan.models.bankcode import AnyBankCode
from thanakan.services.base import BankApi

bkk_tz = pytz.timezone("Asia/Bangkok")


class KBankAPI(BankApi):
    creds: Optional[Dict] = None

    def __init__(
        self,
        consumer_id,
        consumer_secret,
        cert: CertTypes,
        base_url="https://openapi.kasikornbank.com",
    ):
        self.consumer_id = consumer_id
        self.consumer_secret = consumer_secret
        self.cert = cert
        self.base_url = furl(base_url)
        auth_url = self.base_url / "oauth/token"
        client = httpx.Client(cert=self.cert)
        # change this to async with https://docs.authlib.org/en/latest/client/httpx.html
        auth = OAuth2ClientCredentials(
            auth_url.url,
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            client=client,
        )
        self.client = httpx.AsyncClient(
            base_url=base_url, cert=self.cert, auth=auth
        )

        self.client_sync = httpx.Client(
            base_url=base_url, cert=self.cert, auth=auth
        )

    async def get_token(self):

        body = {"grant_type": "client_credentials"}

        auth_url = self.base_url / "oauth/token"
        r = httpx.post(
            auth_url.url,
            data=body,
            auth=(self.consumer_id, self.consumer_secret),
            cert=self.cert,
        )

        if r.status_code == 200:
            self.creds = r.json()
            return r.json()
        else:
            return r

    async def verify_slip(self, sending_bank_id, trans_ref, *, raw=True):
        body = {
            "rqUID": uuid.uuid4().hex,
            "rqDt": datetime.now(tz=bkk_tz).isoformat(),
            "data": {"sendingBank": sending_bank_id, "transRef": trans_ref},
        }

        r = await self.client.post("/v1/verslip/kbank/verify", json=body)

        if r.status_code == 200:
            json = r.json()
            if raw:
                return json
            try:
                return VerifyResponse(**json)
            except Exception as e:
                logger.debug("data is {}", json)
                raise e
        else:
            return r

    def verify_slip_sync(self, sending_bank_id, trans_ref, *, raw=True):
        body = {
            "rqUID": uuid.uuid4().hex,
            "rqDt": datetime.now(tz=bkk_tz).isoformat(),
            "data": {"sendingBank": sending_bank_id, "transRef": trans_ref},
        }

        r = self.client_sync.post("/v1/verslip/kbank/verify", json=body)

        if r.status_code == 200:
            json = r.json()
            if raw:
                return json
            try:
                return VerifyResponse(**json)
            except Exception as e:
                logger.debug("data is {}", json)
                raise e
        else:
            return r
