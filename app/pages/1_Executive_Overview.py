import plotly.express as px
import streamlit as st

from utils import (
    GRADE_ORDER,
    fmt_currency,
    fmt_int,
    fmt_pct,
    load_streamlit_artifacts,
    prepare_grade_display,
    prepare_policy_display,
    pricing_status_counts,
)

st.set_page_config(
    page_title="Executive Overview | Loan Pricing Simulator",
    page_icon="📊",
    layout="wide",
)

artifacts = load_streamlit_artifacts()

portfolio_kpi = artifacts["portfolio_kpi"]
grade_profitability = artifacts["grade_profitability"]
policy_comparison = artifacts["policy_comparison"]
pricing_sample = artifacts["pricing_sample"]
metadata = artifacts["metadata"]

st.title("Executive Overview")

st.markdown(
    """
    High-level summary of the loan pricing engine, portfolio risk, economic profit,
    and approval policy trade-offs.
    """
)

with st.expander("Project Metadata", expanded=False):
    st.json(metadata)

st.header("Portfolio Snapshot")

kpi = portfolio_kpi.iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Loans", fmt_int(kpi["n_loans"]))
col2.metric("Total EAD", fmt_currency(kpi["total_ead"]))
col3.metric("Average PD", fmt_pct(kpi["avg_pd"]))
col4.metric("Actual Default Rate", fmt_pct(kpi["actual_default_rate"]))

col5, col6, col7, col8 = st.columns(4)
col5.metric("Expected Loss", fmt_currency(kpi["total_expected_loss"]))
col6.metric("Expected Profit", fmt_currency(kpi["total_expected_profit"]))
col7.metric("Economic Profit", fmt_currency(kpi["total_economic_profit"]))
col8.metric("Economic Return", fmt_pct(kpi["portfolio_economic_return"]))

st.caption(
    "Economic profit adjusts accounting-style expected profit by subtracting capital charge, "
    "collection cost, and nonlinear tail-risk penalty."
)

st.header("Executive Charts")

pricing_counts = pricing_status_counts(pricing_sample)
policy_display = prepare_policy_display(policy_comparison)
grade_display = prepare_grade_display(grade_profitability)

col1, col2 = st.columns(2)

with col1:
    fig = px.pie(
        pricing_counts,
        names="pricing_status",
        values="count",
        title="Pricing Status Distribution",
        hole=0.35,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.scatter(
        policy_display,
        x="approval_rate_pct",
        y="actual_default_rate_pct",
        size="total_economic_profit_m",
        hover_name="policy",
        color="policy",
        title="Approval Rate vs Default Rate",
        labels={
            "approval_rate_pct": "Approval Rate (%)",
            "actual_default_rate_pct": "Actual Default Rate (%)",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    fig = px.bar(
        grade_display,
        x="internal_grade",
        y="actual_default_rate_pct",
        title="Default Rate by Internal Grade",
        category_orders={"internal_grade": GRADE_ORDER},
        labels={
            "internal_grade": "Internal Grade",
            "actual_default_rate_pct": "Default Rate (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    fig = px.bar(
        policy_display,
        x="policy",
        y="total_economic_profit_m",
        title="Economic Profit by Policy",
        labels={
            "policy": "Policy",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Policy Snapshot")
compact_policy_cols = [
    "policy",
    "approval_rate",
    "actual_default_rate",
    "avg_pd",
    "total_economic_profit",
    "portfolio_economic_return",
    "high_risk_share",
]

compact_policy_cols = [col for col in compact_policy_cols if col in policy_comparison.columns]
st.dataframe(policy_comparison[compact_policy_cols], use_container_width=True)