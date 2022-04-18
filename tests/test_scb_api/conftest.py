import os
import tempfile
from pathlib import Path

import pytest
from google.cloud import secretmanager_v1
from thanakan import SCBAPI, SCBBaseURL


@pytest.fixture
def api_key():
    return os.getenv("SCB_UAT_API_KEY")


@pytest.fixture
def api_secret():
    return os.getenv("SCB_UAT_API_SECRET")


@pytest.fixture
def scb_api(api_key, api_secret):
    s = SCBAPI(
        api_key=api_key, api_secret=api_secret, base_url=SCBBaseURL.uat.value
    )
    return s
