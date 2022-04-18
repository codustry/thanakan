import os
from asyncio import run
from pathlib import Path

import streamlit as st
from PIL import Image
from thanakan import SCBAPI, SCBBaseURL, SlipQRData

st.title("Thanakan Slip QR Code Tester for SCB")

scb_api = SCBAPI(
    api_key=st.secrets["SCB_API_KEY"],
    api_secret=st.secrets["SCB_API_SECRET"],
    base_url=SCBBaseURL.production.value,
)


uploaded_file = st.file_uploader(
    "Upload a QR Code bank slip",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=False,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
)

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    s = SlipQRData.create_from_image(img)
    out = run(
        scb_api.verify_slip(
            transaction_ref_id=s.payload.transaction_ref_id,
            sending_bank_id=s.payload.sending_bank_id,
        )
    )
    st.image(uploaded_file)
    st.subheader("Slip QR Code Data")
    st.write(s)
    st.subheader("Transaction Data")
    st.write(out)
