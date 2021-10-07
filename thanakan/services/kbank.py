"""

ref.
https://apiportal.kasikornbank.com/product/public/Information/Slip%20Verification/Try%20API/d519307a-6d82-4e77-b9f4-dc74e542c742
"""
from typing import Dict, Optional, Tuple

import uuid
from datetime import datetime

import httpx
import pytz
from furl import furl
from httpx._types import CertTypes
from httpx_auth import (
    GrantNotProvided,
    InvalidGrantRequest,
    OAuth2ClientCredentials,
)
from loguru import logger
from thanakan.services.base import BankApi
from thanakan.services.model.kbank import VerifyResponse

bkk_tz = pytz.timezone("Asia/Bangkok")


class KBankOAuth2ClientCredentials(OAuth2ClientCredentials):
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        *args,
        **kwargs,
    ):
        super().__init__(token_url, client_id, client_secret, **kwargs)
        self.data = "grant_type=client_credentials"

    def request_new_grant_with_post_kbank_special(
        self, url: str, data, grant_name: str, client: httpx.Client
    ) -> Tuple[str, int]:
        with client:
            header = {"Content-Type": "application/x-www-form-urlencoded"}
            response = client.post(url, data=data, headers=header)

            if response.is_error:
                # As described in https://tools.ietf.org/html/rfc6749#section-5.2
                raise InvalidGrantRequest(response)

            content = response.json()

        token = content.get(grant_name)
        if not token:
            raise GrantNotProvided(grant_name, content)
        return token, content.get("expires_in")

    def request_new_token(self) -> tuple:
        # As described in https://tools.ietf.org/html/rfc6749#section-4.3.3
        token, expires_in = self.request_new_grant_with_post_kbank_special(
            self.token_url, self.data, self.token_field_name, self.client
        )
        # Handle both Access and Bearer tokens
        return (
            (self.state, token, expires_in)
            if expires_in
            else (self.state, token)
        )


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
        auth = KBankOAuth2ClientCredentials(
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
        """
        This is normally handle by `KBankOAuth2ClientCredentials` automatically. This is for dev to call.
        """

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

    async def verify_slip(self, sending_bank_id, trans_ref, *, raw=False):
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
                response = VerifyResponse(**json)
                if response.status_message.strip() != "SUCCESS":
                    logger.warning(
                        "Not Success: {} {}",
                        response.status_code,
                        response.status_message,
                    )
                return response
            except Exception as e:
                logger.debug("data is {}", json)
                raise Exception("Could not parse the json") from e
        else:
            return r

    def verify_slip_sync(self, sending_bank_id, trans_ref, *, raw=False):
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
                response = VerifyResponse(**json)
                if response.status_message.strip() != "SUCCESS":
                    logger.warning(
                        "Not Success: {} {}",
                        response.status_code,
                        response.status_message,
                    )
                return response
            except Exception as e:
                logger.debug("data is {}", json)
                raise Exception("Could not parse the json") from e
        else:
            return r
