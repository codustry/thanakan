import pytest

from thanakan.services.kbank import KBankAPI

@pytest.mark.asyncio
async def test_main(cert, consumer_id, consumer_secret):
    api = KBankAPI(
        consumer_id=consumer_id,
        consumer_secret=consumer_secret,
        cert=cert,
        base_url="https://openapi-test.kasikornbank.com",
    )
    a = await api.verify_slip("002", "2020122816575524000933108")
    pass
