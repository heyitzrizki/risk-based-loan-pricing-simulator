import json

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
policy_comparison = artifacts["policy_comparison"]
scenario_policy_summary = artifacts["scenario_policy_summary"]
lgd_assumptions = artifacts["lgd_assumptions"]
methodology_notes = artifacts["methodology_notes"]
metadata = artifacts["metadata"]

st.title("Model Governance")

st.markdown(
    """
    This page documents the model design, assumptions, risk controls,
    limitations, and governance considerations behind the pricing simulator.
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
        1. Loan-level data preprocessing  
        2. PD modeling using XGBoost  
        3. Calibration check and final PD selection  
        4. Internal grade binning  
        5. Expected loss calculation  
        6. Required rate estimation  
        7. Economic profit adjustment  
        8. Policy-based approval simulation  
        """
    )

st.header("Governance Summary")

kpi = portfolio_kpi.iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Average PD", fmt_pct(kpi["avg_pd"]))
col2.metric("Actual Default Rate", fmt_pct(kpi["actual_default_rate"]))
col3.metric("Expected Loss", fmt_currency(kpi["total_expected_loss"]))
col4.metric("Economic Profit", fmt_currency(kpi["total_economic_profit"]))

st.caption(
    "These figures summarize the holdout test portfolio used to generate the Streamlit artifacts."
)

st.header("Internal Grade Validation")

grade_display = prepare_grade_display(grade_profitability)

col1, col2 = st.columns(2)

with col1:
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

with col2:
    fig = px.bar(
        grade_display,
        x="internal_grade",
        y="avg_economic_return_pct",
        title="Economic Return by Internal Grade",
        category_orders={"internal_grade": GRADE_ORDER},
        labels={
            "internal_grade": "Internal Grade",
            "avg_economic_return_pct": "Economic Return (%)",
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
    The simulator separates **accounting-style expected profit** from
    **risk-adjusted economic profit**.
    
    Economic profit is calculated by subtracting:
    
    - capital charge,
    - collection cost,
    - nonlinear tail-risk penalty.
    
    This avoids treating high-interest, high-risk loans as automatically attractive
    simply because their nominal interest income is high.
    """
)

st.header("Policy Governance")

policy_display = policy_comparison.copy()
policy_display["approval_rate_pct"] = policy_display["approval_rate"] * 100
policy_display["actual_default_rate_pct"] = (
    policy_display["actual_default_rate"] * 100
)
policy_display["high_risk_share_pct"] = policy_display["high_risk_share"] * 100
policy_display["portfolio_economic_return_pct"] = (
    policy_display["portfolio_economic_return"] * 100
)

col1, col2 = st.columns(2)

with col1:
    fig = px.scatter(
        policy_display,
        x="approval_rate_pct",
        y="actual_default_rate_pct",
        size="high_risk_share_pct",
        color="policy",
        hover_name="policy",
        title="Policy Risk Appetite View",
        labels={
            "approval_rate_pct": "Approval Rate (%)",
            "actual_default_rate_pct": "Actual Default Rate (%)",
            "high_risk_share_pct": "High-Risk Share (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        policy_display,
        x="policy",
        y="high_risk_share_pct",
        title="High-Risk Exposure by Policy",
        labels={
            "policy": "Policy",
            "high_risk_share_pct": "High-Risk Share (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(policy_comparison, use_container_width=True)

st.header("Scenario Governance")

st.markdown(
    """
    Scenario analysis evaluates whether the approval policies remain robust under
    different funding cost, operating cost, and target margin assumptions.
    """
)

scenario_display = scenario_policy_summary.copy()
scenario_display["portfolio_economic_return_pct"] = (
    scenario_display["portfolio_economic_return"] * 100
)

fig = px.line(
    scenario_display,
    x="policy",
    y="portfolio_economic_return_pct",
    color="scenario",
    markers=True,
    title="Economic Return Stability Across Scenarios",
    labels={
        "policy": "Policy",
        "portfolio_economic_return_pct": "Economic Return (%)",
    },
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(scenario_policy_summary, use_container_width=True)

st.header("Methodology Notes")

for _, row in methodology_notes.iterrows():
    with st.expander(str(row["section"])):
        st.write(row["note"])

st.header("Model Limitations")

st.warning(
    """
    This simulator is a portfolio analytics prototype, not a production regulatory
    credit decisioning system. LGD, capital cost, collection cost, and tail-risk
    penalty are simulation assumptions. A production system would require recovery
    data, reject inference, regulatory capital treatment, fairness testing, monitoring,
    and model risk management approval.
    """
)

st.header("Recommended Future Improvements")

st.markdown(
    """
    - Add true recovery data to estimate LGD empirically.
    - Add borrower-level reject inference if rejected applications become available.
    - Monitor PD calibration drift over time.
    - Add fairness and adverse impact analysis.
    - Replace assumption-based capital charge with regulatory/economic capital model.
    - Add prepayment and vintage effects into profitability simulation.
    - Add model monitoring dashboard for PSI, calibration drift, and policy performance.
    """
)