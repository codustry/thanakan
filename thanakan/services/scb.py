import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple, Literal

import httpx
from furl import furl
from httpx._types import CertTypes
from httpx_auth import OAuth2ClientCredentials, InvalidGrantRequest, GrantNotProvided
from pydantic import validate_arguments, constr

from thanakan.services.base import BankApi
from thanakan.services.model.scb import SCBCredentialsSCBResponse, CreateQR30SCBResponse, StatusCode, VerifySCBResponse, \
    TransactionInquirySCBResponse, SCBDeeplinkResponse, SCBDeeplinkTransactionResponse


# from thanakan.services.model.scb import BaseResponse, CreateQR30Response, SCBCredentialsResponse, StatusCode, \
#     TransactionInquiryResponse, VerifyResponse

class SCBBaseURL(str, Enum):
    sandbox = "https://api-sandbox.partners.scb/partners/sandbox/"
    uat = 'https://api-uat.partners.scb/partners/'
    production = 'https://api.partners.scb/partners/'

class SCBOAuth2ClientCredentials(OAuth2ClientCredentials):
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        **kwargs,
    ):
        super().__init__(token_url, client_id, client_secret, token_field_name='accessToken', **kwargs)
        self.data = {
            "applicationKey": client_id,
            "applicationSecret": client_secret,
        }

    def request_new_grant_with_post_scb_special(
        self, url: str, data, grant_name: str, client: httpx.Client
    ) -> Tuple[str, int]:
        with client:
            header = {
                'Content-Type': 'application/json',
                'resourceOwnerId': self.client_id,
                'requestUId': uuid.uuid4().hex,
                'accept-language': 'EN',
            }
            response = client.post(url, json=data, headers=header)

            if response.is_error:
                # As described in https://tools.ietf.org/html/rfc6749#section-5.2
                raise InvalidGrantRequest(response)

            content = response.json().get('data')

        token = content.get(grant_name)
        if not token:
            raise GrantNotProvided(grant_name, content)
        return token, content.get("expiresIn")

    def request_new_token(self) -> tuple:
        # As described in https://tools.ietf.org/html/rfc6749#section-4.3.3
        token, expires_in = self.request_new_grant_with_post_scb_special(
            self.token_url, self.data, self.token_field_name, self.client
        )
        # Handle both Access and Bearer tokens
        return (
            (self.state, token, expires_in)
            if expires_in
            else (self.state, token)
        )

class SCBAPI(BankApi):
    creds: Optional[SCBCredentialsSCBResponse] = None

    def __init__(
        self,
        api_key,
        api_secret,
        cert: Optional[CertTypes] = None,
        base_url=SCBBaseURL.sandbox.value
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.cert = cert
        self.base_url = furl(base_url)

        auth_url = self.base_url / "v1/oauth/token"
        client = httpx.Client(cert=self.cert)

        auth = SCBOAuth2ClientCredentials(
            auth_url.url,
            client_id=self.api_key,
            client_secret=self.api_secret,
            client=client,
        )

        common_header = {
            'Content-Type': 'application/json',
            'resourceOwnerId': self.api_key,
            'accept-language': 'EN',
        }
        self.client = httpx.AsyncClient(
            base_url=base_url, cert=self.cert, headers=common_header,
            auth=auth
        )

        self.client_sync = httpx.Client(
            base_url=base_url, cert=self.cert, headers=common_header,
            auth=auth
        )

    async def get_token(self):
        """ get access_token from scb """
        # TODO: turn this into a  custom auth engine
        body = {
            "applicationKey": self.api_key,
            "applicationSecret": self.api_secret
        }
        headers = {
            'Content-Type': 'application/json',
            'resourceOwnerId': self.api_key,
            'requestUId': uuid.uuid4().hex,
            'accept-language': 'EN',
        }

        auth_url = self.base_url / "v1/oauth/token"
        r = httpx.post(
            auth_url.url,
            json=body,
            headers=headers,
            cert=self.cert,
        )

        if r.status_code == 200:
            self.creds = SCBCredentialsSCBResponse.parse_raw(r.content)
            return self.creds
        else:
            raise ConnectionError(r.json())

    @validate_arguments
    async def create_qr30(
        self,
        pp_id: constr(min_length=15, max_length=15),
        amount: Decimal,
        ref1: constr(max_length=20, regex="[A-Z0-9]*"),
        ref2: constr(max_length=20, regex="[A-Z0-9]*"),
        ref3: constr(max_length=20, regex="[A-Z]{3}[A-Z0-9]*"),
        qr_type: Literal['PP'] = "PP",
        pp_type: Literal['BILLERID'] = 'BILLERID',
    ):
        request_unique_id = uuid.uuid4().hex
        headers = {
            'requestUId': request_unique_id,
        }
        payload = {
            'qrType': qr_type,
            'ppType': pp_type,
            'amount': str(amount),
            'ppId': pp_id,
            'ref1': ref1,
            'ref2': ref2,
            'ref3': ref3
        }
        r = await self.client.post('/v1/payment/qrcode/create', json=payload, headers=headers)

        if r.status_code == 200:
            parsed_response = CreateQR30SCBResponse.parse_raw(r.content)

            if parsed_response.status.code == StatusCode.success:
                return parsed_response
            else:
                raise ConnectionError(parsed_response.status.description)
        else:
            raise ConnectionError(r.json())

    @validate_arguments
    async def verify_slip(
        self,
        transaction_ref_id: str,
        sending_bank_id: str,
    ):
        headers = {
            'requestUId': uuid.uuid4().hex,
        }

        the_furl = furl('/v1/payment/billpayment/transactions') / transaction_ref_id
        the_furl.args['sendingBank'] = sending_bank_id

        r = await self.client.get(the_furl.url, headers=headers)

        if r.status_code == 200:
            parsed_response = VerifySCBResponse.parse_raw(r.content)
            if parsed_response.status.code == StatusCode.success:
                return parsed_response
            else:
                raise ConnectionError(parsed_response.status.description)
        else:
            raise ConnectionError(r.json())

    @validate_arguments
    async def query_transaction(
        self,
        biller_id: str,
        reference1: str,
        transaction_date: constr(regex=r"\d{4}-\d{2}-\d{2}"),
        reference2: Optional[str] = None,
        amount: Optional[Decimal]= None,
        event_code: Literal['00300100', '00300104'] = '00300100',
    ):

        the_furl = furl('/v1/payment/billpayment/inquiry')
        args = {
            'eventCode': event_code,
            'billerId': biller_id,
            'reference1': reference1,
            'reference2': reference2,
            'amount': amount,
            'transactionDate': transaction_date
        }
        args = {k:v  for k, v in args.items() if v is not None}


        the_furl.add(args=args)


        headers = {
            'requestUId': uuid.uuid4().hex
        }

        r = await self.client.get(the_furl.url, headers=headers)

        if r.status_code == 200:
            # TODO: parse into specific object
            parsed_response = TransactionInquirySCBResponse.parse_raw(r.content)
            if parsed_response.status.code == StatusCode.success:
                return parsed_response
            else:
                raise ConnectionError(parsed_response.status.description)
        else:
            raise ConnectionError(r.json())

    @validate_arguments
    async def create_deeplink(
        self,
        payload: dict
    ):

        the_furl = furl('/v3/deeplink/transactions')

        headers = {
            'requestUId': uuid.uuid4().hex,
            'channel': 'scbeasy'
        }

        r = await self.client.post(the_furl.url, headers=headers, json=payload)

        if r.status_code == 200 or r.status_code == 201:
            parsed_response = SCBDeeplinkResponse.parse_raw(r.content)
            if parsed_response.status.code == StatusCode.success:
                return parsed_response
            else:
                raise ConnectionError(parsed_response.status.description)
        else:
            raise ConnectionError(r.json())

    @validate_arguments
    async def get_deeplink(
        self,
        transaction_ref_id: str
    ):
        the_furl = furl('/v2/transactions') / transaction_ref_id

        headers = {
            'requestUId': uuid.uuid4().hex,
        }

        r = await self.client.get(the_furl.url, headers=headers)

        if r.status_code == 200:
            parsed_response = SCBDeeplinkTransactionResponse.parse_raw(r.content)
            if parsed_response.status.code == StatusCode.success:
                return parsed_response
            else:
                raise ConnectionError(parsed_response.status.description)
        else:
            raise ConnectionError(r.json())


