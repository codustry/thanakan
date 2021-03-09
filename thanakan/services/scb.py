import uuid
from decimal import Decimal
from typing import Literal, Optional

import httpx
from furl import furl
from httpx._types import CertTypes
from pydantic import constr, validate_arguments

from services.base import BankApi
from services.model.scb import BaseResponse, CreateQR30Response, SCBCredentialsResponse, StatusCode, \
    TransactionInquiryResponse, VerifyResponse

SANDBOX_BASE_URL = "https://api-sandbox.partners.scb/partners/sandbox/"


class SCBAPI(BankApi):
    creds: Optional[SCBCredentialsResponse] = None

    def __init__(
        self,
        application_key,
        application_secret,
        cert: Optional[CertTypes] = None,
        base_url=SANDBOX_BASE_URL
    ):
        self.application_key = application_key
        self.application_secret = application_secret
        self.cert = cert
        self.base_url = furl(base_url)
        auth_url = self.base_url / "oauth/token"
        client = httpx.Client(cert=self.cert)
        # auth = OAuth2ClientCredentials(
        #     auth_url.url,
        #     client_id=self.consumer_id,
        #     client_secret=self.consumer_secret,
        #     client=client,
        # )
        self.client = httpx.AsyncClient(
            base_url=base_url, cert=self.cert,
            # auth=auth
        )

        self.client_sync = httpx.Client(
            base_url=base_url, cert=self.cert,
            # auth=auth
        )

    async def get_token(self):
        """ get access_token from scb """
        # TODO: turn this into a  custom auth engine
        body = {
            "applicationKey": self.application_key,
            "applicationSecret": self.application_secret
        }
        headers = {
            'Content-Type': 'application/json',
            'resourceOwnerId': self.application_key,
            'requestUId': uuid.uuid4().hex,
            'accept-language': 'EN',
        }

        auth_url = self.base_url / "v1/oauth/token"
        r = httpx.post(
            auth_url.url,
            json=body,
            headers=headers,
            # auth=(self.consumer_id, self.consumer_secret),
            cert=self.cert,
        )

        if r.status_code == 200:
            self.creds = SCBCredentialsResponse.parse_raw(r.content)
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
        headers = {
            'Content-Type': 'application/json',
            'authorization': f'Bearer {self.creds.data.access_token}',
            'resourceOwnerId': self.application_key,
            'requestUId': uuid.uuid4().hex,
            'accept-language': 'EN',
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
            parsed_response = CreateQR30Response.parse_raw(r.content)
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
            'authorization': f'Bearer {self.creds.data.access_token}',
            'resourceOwnerId': self.application_key,
            'requestUId': uuid.uuid4().hex,
            'accept-language': 'EN',
        }

        the_furl = furl('/v1/payment/billpayment/transactions') / transaction_ref_id
        the_furl.args['sendingBank'] = sending_bank_id

        r = await self.client.get(the_furl.url, headers=headers)

        if r.status_code == 200:
            parsed_response = VerifyResponse.parse_raw(r.content)
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
        reference2: str,
        transaction_date: constr(regex=r"\d{4}-\d{2}-\d{2}"),
        amount: Decimal,
        event_code: Literal['00300100', '00300104'] = '00300100',
    ):

        the_furl = furl('/v1/payment/billpayment/inquiry')
        the_furl.add(args={
            'eventCode': event_code,
            'billerId': biller_id,
            'reference1': reference1,
            'reference2': reference2,
            'amount': f"{amount:.2f}",
            'transactionDate': transaction_date
        })


        headers = {
            'authorization': f'Bearer {self.creds.data.access_token}',
            'resourceOwnerId': self.application_key,
            'requestUId': uuid.uuid4().hex,
            'accept-language': 'EN',
        }

        r = await self.client.get(the_furl.url, headers=headers)

        if r.status_code == 200:
            # TODO: parse into specific object
            parsed_response = TransactionInquiryResponse.parse_raw(r.content)
            if parsed_response.status.code == StatusCode.success:
                return parsed_response
            else:
                raise ConnectionError(parsed_response.status.description)
        else:
            raise ConnectionError(r.json())

    @validate_arguments
    async def create_deeplink(
        self,

    ):
        import requests

        url = "https://api-sandbox.partners.scb/partners/sandbox/v3/deeplink/transactions"

        payload = "{\n\t\"transactionType\": \"PURCHASE\",\n\t\"transactionSubType\": [\"BP\", \"CCFA\", \"CCIPP\"],\n\t\"sessionValidityPeriod\": 60,\n\t\"sessionValidUntil\": \"\",\n\t\"billPayment\": {\n\t\t\"paymentAmount\": 100,\n\t\t\"accountTo\": \"123456789012345\",\n\t\t\"accountFrom\": \"123451234567890\",\n\t\t\"ref1\": \"ABCDEFGHIJ1234567890\",\n\t\t\"ref2\": \"ABCDEFGHIJ1234567890\",\n\t\t\"ref3\": \"ABCDEFGHIJ1234567890\"\n\t},\n\t\"creditCardFullAmount\": {\n\t\t\"merchantId\": \"1234567890ABCDEF\",\n\t\t\"terminalId\": \"1234ABCD\",\n\t\t\"orderReference\": \"12345678\",\n\t\t\"paymentAmount\": 100\n\t},\n\t\"installmentPaymentPlan\": {\n\t\t\"merchantId\": \"4218170000000160\",\n\t\t\"terminalId\": \"56200004\",\n\t\t\"orderReference\": \"AA100001\",\n\t\t\"paymentAmount\": 10000.00,\n\t\t\"tenor\": \"12\",\n\t\t\"ippType\": \"3\",\n\t\t\"prodCode\": \"1001\"\n\t},\n\t\"merchantMetaData\": {\n\t\t\"callbackUrl\": \"\",\n\t\t\"merchantInfo\": {\n\t\t\t\"name\": \"SANDBOX MERCHANT NAME\"\n\t\t},\n\t\t\"extraData\": {},\n\t\t\"paymentInfo\": [\n\t\t\t{\n\t\t\t\t\"type\": \"TEXT_WITH_IMAGE\",\n\t\t\t\t\"title\": \"\",\n\t\t\t\t\"header\": \"\",\n\t\t\t\t\"description\": \"\",\n\t\t\t\t\"imageUrl\": \"\"\n\t\t\t},\n\t\t\t{\n\t\t\t\t\"type\": \"TEXT\",\n\t\t\t\t\"title\": \"\",\n\t\t\t\t\"header\": \"\",\n\t\t\t\t\"description\": \"\"\n\t\t\t}\n\t\t]\n\t}\n}"
        payload2 = {
            "transactionType": "PURCHASE",
            "transactionSubType": ["BP", "CCFA", "CCIPP"],
            "sessionValidityPeriod": 60,
            "sessionValidUntil": "",
            "billPayment": {
                "paymentAmount": 100,
                "accountTo": "123456789012345",
                "accountFrom": "123451234567890",
                "ref1": "ABCDEFGHIJ1234567890",
                "ref2": "ABCDEFGHIJ1234567890",
                "ref3": "ABCDEFGHIJ1234567890"
            },
            "creditCardFullAmount": {
                "merchantId": "1234567890ABCDEF",
                "terminalId": "1234ABCD",
                "orderReference": "12345678",
                "paymentAmount": 100
            },
            "installmentPaymentPlan": {
                "merchantId": "4218170000000160",
                "terminalId": "56200004",
                "orderReference": "AA100001",
                "paymentAmount": 10000.00,
                "tenor": "12",
                "ippType": "3",
                "prodCode": "1001"
            },
            "merchantMetaData": {
                "callbackUrl": "",
                "merchantInfo": {
                    "name": "SANDBOX MERCHANT NAME"
                },
                "extraData": {},
                "paymentInfo": [
                    {
                        "type": "TEXT_WITH_IMAGE",
                        "title": "",
                        "header": "",
                        "description": "",
                        "imageUrl": ""
                    },
                    {
                        "type": "TEXT",
                        "title": "",
                        "header": "",
                        "description": ""
                    }
                ]
            }
        }
        headers = {
            'Content-Type': 'application/json',
            'authorization': 'Bearer <Your Access Token>',
            'resourceOwnerId': '<Your API Key>',
            'requestUId': 'fe2f0e21-361b-44fd-85e8-75734184eb34',
            'channel': 'scbeasy',
            'accept-language': 'EN',
            'Cookie': 'TS01e7ba6b=01e76b033c782fc88aa5838c33fda6eb0cf563d307a7b3cb6f17b84b610aecd9e7ef0d4e0fef15be922efd3884bc2a1fa1eb1404da'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)

    @validate_arguments
    async def get_deeplink(
        self,
        transaction_ref_id: str
    ):
        import requests

        url = "https://api-sandbox.partners.scb/partners/sandbox/v2/transactions/9ed5caf2-0a38-4f5a-80b1-20e76f26b2a6"

        payload = {}
        headers = {
            'authorization': 'Bearer ',
            'resourceOwnerId': '',
            'requestUId': 'd03b9b3b-a275-4f78-a7c4-1475a9e65ff6',
            'accept-language': 'EN',
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)

