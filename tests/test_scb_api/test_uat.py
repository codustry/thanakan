import pytest

from thanakan import SCBAPI, SCBBaseURL


@pytest.mark.asyncio
async def test_get_token(scb_api):
    token = await scb_api.get_token()
    print(token)

@pytest.mark.asyncio
async def test_qr30(scb_api):
    out = await scb_api.create_qr30(
        pp_id='311040039475180',
        amount=3210.00,
        ref1='ABC',
        ref2='0992866666',
        ref3='COT'
    )
    print(out)

@pytest.mark.asyncio
async def test_slip_vert(scb_api):
    out = await scb_api.verify_slip(
        transaction_ref_id='202110268HbTUKyFqZ5vKxiUx',
        sending_bank_id='014'
    )
    print(out)

@pytest.mark.asyncio
async def test_create_deeplink(scb_api, deeplink_payload):
    out = await scb_api.create_deeplink(
        payload=deeplink_payload
    )
    print(out)

@pytest.mark.asyncio
async def test_query_deeplink(scb_api,deeplink_payload):
    out = await scb_api.create_deeplink(
        payload=deeplink_payload
    )

    out = await scb_api.get_deeplink(
        transaction_ref_id=out.data.transaction_id
    )
    print(out)

@pytest.mark.asyncio
async def test_query_qr30(scb_api):
    out = await scb_api.query_transaction(
        biller_id=311040039475180,
        reference1='ABC',
        transaction_date="2021-10-26"
    )

    print(out)
