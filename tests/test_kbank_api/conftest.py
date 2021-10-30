import os
import tempfile
from pathlib import Path

import pytest
from google.cloud import secretmanager_v1


@pytest.fixture
def cert():
    client = secretmanager_v1.SecretManagerServiceClient()

    with tempfile.NamedTemporaryFile(
        "w", prefix="certificate", suffix=".crt", delete=False
    ) as cert_file:
        response = client.access_secret_version(
            request={
                "name": "projects/911343863113/secrets/cert-cert-crt/versions/1"
            }
        )
        payload = response.payload.data.decode("UTF-8")
        cert_file.write(payload)
    with tempfile.NamedTemporaryFile(
        "w", prefix="private", suffix=".key", delete=False
    ) as private_key_file:
        response = client.access_secret_version(
            request={
                "name": "projects/911343863113/secrets/cert-private-key/versions/3"
            }
        )
        payload = response.payload.data.decode("UTF-8")
        private_key_file.write(payload)

    cert_file = Path(cert_file.name)
    private_key_file = Path(private_key_file.name)

    yield (
        str(cert_file.absolute()),
        str(private_key_file.absolute()),
    )

    cert_file.unlink()
    private_key_file.unlink()


@pytest.fixture
def consumer_id():
    return os.getenv("KBANK_CONSUMER_ID")


@pytest.fixture
def consumer_secret():
    return os.getenv("KBANK_CONSUMER_SECRET")

@pytest.fixture
def deeplink_payload():
    return {
        "transactionType": "PURCHASE",
        "transactionSubType": ["BP"],
        "sessionValidityPeriod": 1800,
        "billPayment": {
            "paymentAmount": 3120.00,
            "accountTo": "311040039475180",
            "accountFrom": "123451234567890",
            "ref1": "ABC",
            "ref2": "0992866666",
            "ref3": "COD"
        },
        "merchantMetaData": {
            "callbackUrl": "https://1b1b5d84-513c-40d0-b5f4-c6469142f156.mock.pstmn.io/post",
            "merchantInfo": {
                "name": "Gebwai (เก็บไว้)",
                "urlLogo": "https://ik.imagekit.io/codustry/gebwai/webapp/09122021/hero-greeting_-WTYLgJcb.png?updatedAt=1631423833025"
            },
            "extraData": {},
            "paymentInfo": [
                {
                    "type": "TEXT",
                    "title": "เก็บไว้ขอบคุณครับ",
                    "description": "พวกเราจะพัฒนาระบบอย่างต่อเนื่อง"
                }
            ]
        }
    }
