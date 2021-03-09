import pytest
from thanakan.services.kbank import KBankAPI


@pytest.mark.asyncio
async def test_main():
    api = KBankAPI(
        consumer_id="",
        consumer_secret="",
        cert=(
            "certificate.crt",
            "private.key",
        ),
        base_url="https://openapi-test.kasikornbank.com",
    )
    # b = await api.get_token()
    a = await api.verify_slip("", "")
    pass
