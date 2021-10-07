import pytest
import os
import tempfile
from pathlib import Path

from google.cloud import secretmanager_v1

@pytest.fixture
def cert():
    client = secretmanager_v1.SecretManagerServiceClient()

    with tempfile.NamedTemporaryFile('w', prefix='certificate', suffix='.crt', delete=False) as cert_file:
        response = client.access_secret_version(request={"name": "projects/911343863113/secrets/cert-cert-crt/versions/1"})
        payload = response.payload.data.decode("UTF-8")
        cert_file.write(payload)
    with tempfile.NamedTemporaryFile('w', prefix='private',suffix='.key', delete=False) as private_key_file:
        response = client.access_secret_version(request={"name": "projects/911343863113/secrets/cert-private-key/versions/3"})
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
    return os.getenv('KBANK_CONSUMER_ID')

@pytest.fixture
def consumer_secret():
    return os.getenv('KBANK_CONSUMER_SECRET')