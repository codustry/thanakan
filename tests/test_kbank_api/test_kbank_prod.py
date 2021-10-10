import json
from pathlib import Path

import pytest
from PIL import Image
from thanakan import SlipQRData
from thanakan.services.kbank import KBankAPI


@pytest.mark.xfail
@pytest.mark.parametrize(
    "file", [f for f in Path("tests/test_kbank_api/slip-test").glob("*.jpg")]
)
@pytest.mark.asyncio
async def test_main(cert, consumer_id, consumer_secret, file):
    api = KBankAPI(
        consumer_id=consumer_id,
        consumer_secret=consumer_secret,
        cert=cert,
        base_url="https://openapi.kasikornbank.com",
    )
    result_path = Path("tests/test_kbank_api/result")
    result_path.mkdir(exist_ok=True)

    qr_data = SlipQRData.create_from_image(Image.open(file))

    response = await api.verify_slip(
        qr_data.payload.sending_bank_id, qr_data.payload.transaction_ref_id
    )

    output_path = result_path / (file.stem + ".json")
    with output_path.open("w") as f:
        f.write(json.dumps(response.dict(), indent=10))
