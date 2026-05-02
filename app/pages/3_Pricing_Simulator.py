import pandas as pd
import streamlit as st

from utils import (
    calculate_manual_pricing,
    fmt_currency,
    fmt_pct,
    load_streamlit_artifacts,
)

st.set_page_config(
    page_title="Manual Pricing Simulator | Loan Pricing Simulator",
    page_icon="🧮",
    layout="wide",
)

artifacts = load_streamlit_artifacts()

grade_profitability = artifacts["grade_profitability"]
lgd_assumptions = artifacts["lgd_assumptions"]
methodology_notes = artifacts["methodology_notes"]

st.title("Manual Risk-Based Pricing Simulator")

st.markdown(
    """
    Simulate pricing for a new loan using PD, LGD, loan amount, offered rate,
    funding cost, operating cost, target margin, and economic risk assumptions.
    """
)

grade_options = grade_profitability["internal_grade"].dropna().tolist()

grade_reference = grade_profitability[
    [
        "internal_grade",
        "avg_pd",
        "avg_lgd",
        "avg_actual_rate",
        "avg_required_rate",
        "actual_default_rate",
    ]
].copy()

st.sidebar.title("Simulation Mode")

pd_mode = st.sidebar.radio(
    "PD input mode",
    options=["Use internal grade average PD", "Enter manual PD"],
)

st.header("Loan Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    loan_amount = st.number_input(
        "Loan Amount",
        min_value=500.0,
        max_value=100000.0,
        value=15000.0,
        step=500.0,
    )

with col2:
    term_months = st.selectbox(
        "Loan Term",
        options=[36, 60],
        index=0,
    )

with col3:
    offered_rate = st.number_input(
        "Offered Annual Interest Rate (%)",
        min_value=0.0,
        max_value=40.0,
        value=13.5,
        step=0.25,
    ) / 100

st.header("Risk Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    selected_grade = st.selectbox(
        "Internal Grade",
        options=grade_options,
        index=grade_options.index("BBB") if "BBB" in grade_options else 0,
    )

grade_row = grade_profitability[
    grade_profitability["internal_grade"].eq(selected_grade)
].iloc[0]

lgd_row = lgd_assumptions[
    lgd_assumptions["internal_grade"].eq(selected_grade)
]

default_lgd = (
    float(lgd_row["lgd_assumption"].iloc[0])
    if not lgd_row.empty and "lgd_assumption" in lgd_row.columns
    else float(grade_row.get("avg_lgd", 0.4))
)

default_pd = float(grade_row["avg_pd"])

with col2:
    if pd_mode == "Use internal grade average PD":
        pd_value = st.number_input(
            "PD",
            min_value=0.0,
            max_value=1.0,
            value=default_pd,
            step=0.01,
            disabled=True,
        )
    else:
        pd_value = st.number_input(
            "Manual PD",
            min_value=0.0,
            max_value=1.0,
            value=default_pd,
            step=0.01,
        )

with col3:
    lgd = st.number_input(
        "LGD",
        min_value=0.0,
        max_value=1.0,
        value=default_lgd,
        step=0.01,
    )

st.header("Business Assumptions")

col1, col2, col3 = st.columns(3)

with col1:
    funding_cost_rate = st.number_input(
        "Funding Cost (%)",
        min_value=0.0,
        max_value=25.0,
        value=4.0,
        step=0.25,
    ) / 100

with col2:
    operating_cost_rate = st.number_input(
        "Operating Cost (%)",
        min_value=0.0,
        max_value=25.0,
        value=2.0,
        step=0.25,
    ) / 100

with col3:
    target_margin_rate = st.number_input(
        "Target Margin (%)",
        min_value=0.0,
        max_value=30.0,
        value=5.0,
        step=0.25,
    ) / 100

st.header("Economic Risk Assumptions")

col1, col2, col3 = st.columns(3)

with col1:
    capital_cost_rate = st.number_input(
        "Capital Cost (%)",
        min_value=0.0,
        max_value=30.0,
        value=8.0,
        step=0.25,
    ) / 100

with col2:
    collection_cost_rate = st.number_input(
        "Collection Cost on EL (%)",
        min_value=0.0,
        max_value=50.0,
        value=10.0,
        step=1.0,
    ) / 100

with col3:
    tail_risk_multiplier = st.number_input(
        "Tail-Risk Multiplier",
        min_value=0.0,
        max_value=2.0,
        value=0.35,
        step=0.05,
    )

result = calculate_manual_pricing(
    loan_amount=loan_amount,
    term_months=term_months,
    offered_rate=offered_rate,
    pd_value=pd_value,
    lgd=lgd,
    funding_cost_rate=funding_cost_rate,
    operating_cost_rate=operating_cost_rate,
    target_margin_rate=target_margin_rate,
    capital_cost_rate=capital_cost_rate,
    collection_cost_rate=collection_cost_rate,
    tail_risk_multiplier=tail_risk_multiplier,
)

st.header("Simulation Output")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Required Rate", fmt_pct(result["required_rate"]))
col2.metric("Offered Rate", fmt_pct(result["offered_rate"]))
col3.metric("Pricing Gap", fmt_pct(result["pricing_gap"]))
col4.metric("Pricing Status", result["pricing_status"])

col5, col6, col7, col8 = st.columns(4)
col5.metric("Expected Loss", fmt_currency(result["expected_loss"]))
col6.metric("Expected Profit", fmt_currency(result["expected_profit"]))
col7.metric("Economic Profit", fmt_currency(result["economic_profit"]))
col8.metric("Economic Return", fmt_pct(result["economic_return"]))

st.subheader("Decision Recommendation")

decision = result["decision"]

if decision == "Approve at Current Rate":
    st.success(decision)
elif decision == "Approve if Repriced":
    st.info(decision)
elif decision == "Manual Review":
    st.warning(decision)
else:
    st.error(decision)

st.subheader("Detailed Calculation")

result_table = pd.DataFrame(
    [
        {"metric": "Expected Loss", "value": result["expected_loss"], "format": "currency"},
        {"metric": "Lifetime EL Rate", "value": result["lifetime_expected_loss_rate"], "format": "percent"},
        {"metric": "Annualized EL Rate", "value": result["annualized_expected_loss_rate"], "format": "percent"},
        {"metric": "Interest Income", "value": result["interest_income"], "format": "currency"},
        {"metric": "Funding Cost", "value": result["funding_cost"], "format": "currency"},
        {"metric": "Operating Cost", "value": result["operating_cost"], "format": "currency"},
        {"metric": "Capital Charge", "value": result["capital_charge"], "format": "currency"},
        {"metric": "Collection Cost", "value": result["collection_cost"], "format": "currency"},
        {"metric": "Tail-Risk Penalty", "value": result["tail_risk_penalty"], "format": "currency"},
        {"metric": "Repriced Economic Profit", "value": result["repriced_economic_profit"], "format": "currency"},
        {"metric": "Repriced Economic Return", "value": result["repriced_economic_return"], "format": "percent"},
    ]
)

def format_result(row):
    if row["format"] == "currency":
        return fmt_currency(row["value"])
    if row["format"] == "percent":
        return fmt_pct(row["value"])
    return row["value"]

result_table["display_value"] = result_table.apply(format_result, axis=1)

st.dataframe(
    result_table[["metric", "display_value"]],
    use_container_width=True,
)

st.header("Grade Reference")

st.dataframe(grade_reference, use_container_width=True)

st.header("Methodology Notes")

selected_sections = [
    "Expected Loss",
    "LGD",
    "Required Rate",
    "Pricing Gap",
    "Economic Profit",
    "Policy Comparison",
]

notes = methodology_notes[
    methodology_notes["section"].isin(selected_sections)
].copy()

for _, row in notes.iterrows():
    with st.expander(str(row["section"])):
        st.write(row["note"])