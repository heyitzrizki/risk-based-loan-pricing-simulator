import streamlit as st

st.set_page_config(
    page_title="Risk-Based Loan Pricing Simulator",
    page_icon="💰",
    layout="wide"
)

st.title("Risk-Based Loan Pricing & Profitability Simulator")

st.markdown(
    """
    This Streamlit application will simulate how borrower-level credit risk can be translated into:

    - risk-based interest rates,
    - expected loss,
    - expected profitability,
    - approval and repricing decisions,
    - portfolio profitability frontier.

    The dashboard is currently under development.
    """
)
