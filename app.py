import streamlit as st
import json
from parse import parse_rfq

st.set_page_config(
    page_title="RFQ Parser",
    page_icon="📦",
    layout="centered"
)

st.title("📦 RFQ Parser")
st.subheader("Packaging Industry Enquiry Extraction")

st.write(
    "Enter a customer enquiry below to extract "
    "the packaging details automatically."
)

rfq_text = st.text_area(
    "Enter RFQ message",
    placeholder="Example: Need 50000 BOPP bags, 90 GSM, delivery to Hyderabad.",
    height=150
)

if st.button("Parse RFQ", type="primary"):
    if rfq_text.strip():
        result = parse_rfq(rfq_text)

        st.success("RFQ parsed successfully!")
        st.subheader("Extracted Information")
        st.json(result)

        st.download_button(
            label="Download JSON",
            data=json.dumps(result, indent=4),
            file_name="rfq_result.json",
            mime="application/json"
        )
    else:
        st.warning("Please enter an RFQ message.")

st.divider()
st.caption("Built with Python and Streamlit")