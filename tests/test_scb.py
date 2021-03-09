import pytest

from thanakan.services.scb import SCBAPI



@pytest.fixture
async def api():
    api = SCBAPI(application_key="", application_secret="")
    await api.get_token()
    return api


@pytest.mark.asyncio
async def test_create_qr30(api):
    # with pytest.raises(Exception):
    qr_data = await api.create_qr30(
        pp_id=925244165291982, # auto convert to str
        amount=123.45,
        ref1="ASD12314",
        ref2="DE1235",
        ref3="YQH"
    )


@pytest.mark.asyncio
async def test_verify_slip(api):
    # with pytest.raises(Exception):
    slip_data = await api.verify_slip(
        transaction_ref_id="202102225faeImJIYWvOfDl",
        sending_bank_id='014'
    )

@pytest.mark.asyncio
async def test_query_transaction(api: SCBAPI):
    # with pytest.raises(Exception):
    transaction = await api.query_transaction(
        biller_id='925244165291982',
        reference1='PORTALSANDBOXREF1',
        reference2='PORTALSANDBOXREF1',
        amount=1235.00,
        transaction_date='2021-02-22'
    )
