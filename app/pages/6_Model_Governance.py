import plotly.express as px
import streamlit as st

from utils import (
    GRADE_ORDER,
    fmt_currency,
    fmt_pct,
    load_streamlit_artifacts,
    prepare_grade_display,
)

st.set_page_config(
    page_title="Model Governance | Loan Pricing Simulator",
    page_icon="🛡️",
    layout="wide",
)

artifacts = load_streamlit_artifacts()

portfolio_kpi = artifacts["portfolio_kpi"]
grade_profitability = artifacts["grade_profitability"]
lgd_assumptions = artifacts["lgd_assumptions"]
methodology_notes = artifacts["methodology_notes"]
metadata = artifacts["metadata"]

st.title("Model Governance")

st.markdown(
    """
    Documentation of model design, assumptions, risk controls, limitations,
    and future governance requirements.
    """
)

st.header("System Metadata")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Project Information")
    st.json(metadata)

with col2:
    st.subheader("Core Modeling Flow")
    st.markdown(
        """
        1. Loan-level preprocessing  
        2. PD modeling using XGBoost  
        3. Calibration check and final PD selection  
        4. Internal grade binning  
        5. Expected loss calculation  
        6. Required rate estimation  
        7. Economic profit adjustment  
        8. Policy-based approval simulation  
        """
    )

st.header("Governance Snapshot")

kpi = portfolio_kpi.iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Average PD", fmt_pct(kpi["avg_pd"]))
col2.metric("Actual Default Rate", fmt_pct(kpi["actual_default_rate"]))
col3.metric("Expected Loss", fmt_currency(kpi["total_expected_loss"]))
col4.metric("Economic Profit", fmt_currency(kpi["total_economic_profit"]))

st.header("Internal Grade Validation")

grade_display = prepare_grade_display(grade_profitability)

fig = px.bar(
    grade_display,
    x="internal_grade",
    y="actual_default_rate_pct",
    title="Monotonic Default Rate by Internal Grade",
    category_orders={"internal_grade": GRADE_ORDER},
    labels={
        "internal_grade": "Internal Grade",
        "actual_default_rate_pct": "Actual Default Rate (%)",
    },
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(grade_profitability, use_container_width=True)

st.header("Key Assumptions")

st.subheader("LGD Assumptions")
st.dataframe(lgd_assumptions, use_container_width=True)

st.subheader("Economic Profit Adjustment")

st.markdown(
    """
    The simulator separates accounting-style expected profit from risk-adjusted
    economic profit.
    
    Economic profit subtracts:
    
    - capital charge,
    - collection cost,
    - nonlinear tail-risk penalty.
    
    This prevents high-interest, high-risk loans from appearing automatically
    attractive based only on nominal interest income.
    """
)

st.header("Methodology Notes")

for _, row in methodology_notes.iterrows():
    with st.expander(str(row["section"])):
        st.write(row["note"])

st.header("Limitations")

st.warning(
    """
    This simulator is a portfolio analytics prototype, not a production regulatory
    credit decisioning system. LGD, capital cost, collection cost, and tail-risk
    penalty are simulation assumptions. A production system would require recovery
    data, reject inference, regulatory capital treatment, fairness testing,
    monitoring, and model risk management approval.
    """
)

st.header("Recommended Future Improvements")

st.markdown(
    """
    - Estimate LGD using real recovery data.
    - Add reject inference if rejected applications become available.
    - Monitor PD calibration drift over time.
    - Add fairness and adverse impact analysis.
    - Replace assumption-based capital charge with a formal capital model.
    - Add prepayment and vintage effects into profitability simulation.
    - Add PSI, calibration drift, and policy performance monitoring.
    """
)