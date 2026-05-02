import plotly.express as px
import streamlit as st

from utils import (
    fmt_currency,
    fmt_pct,
    get_selected_policy_row,
    load_streamlit_artifacts,
    prepare_policy_display,
)

st.set_page_config(
    page_title="Approval Strategy | Loan Pricing Simulator",
    page_icon="✅",
    layout="wide",
)

artifacts = load_streamlit_artifacts()

policy_comparison = artifacts["policy_comparison"]
approval_summary = artifacts["approval_summary"]
methodology_notes = artifacts["methodology_notes"]

st.title("Approval Strategy")

st.markdown(
    """
    Compare approval policies using approval rate, default rate, high-risk exposure,
    expected loss, economic profit, and economic return.
    """
)

available_policies = policy_comparison["policy"].dropna().tolist()
default_policy_index = (
    available_policies.index("Balanced")
    if "Balanced" in available_policies
    else 0
)

selected_policy = st.sidebar.selectbox(
    "Selected Policy",
    options=available_policies,
    index=default_policy_index,
)

policy_display = prepare_policy_display(policy_comparison)
selected_policy_row = get_selected_policy_row(policy_comparison, selected_policy)

st.header("Selected Policy Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Approval Rate", fmt_pct(selected_policy_row["approval_rate"]))
col2.metric("Approved EAD", fmt_currency(selected_policy_row["approved_ead"]))
col3.metric("Economic Profit", fmt_currency(selected_policy_row["total_economic_profit"]))
col4.metric("Economic Return", fmt_pct(selected_policy_row["portfolio_economic_return"]))

col5, col6, col7, col8 = st.columns(4)
col5.metric("Average PD", fmt_pct(selected_policy_row["avg_pd"]))
col6.metric("Actual Default Rate", fmt_pct(selected_policy_row["actual_default_rate"]))
col7.metric("Underpriced Share", fmt_pct(selected_policy_row["underpriced_share"]))
col8.metric("High-Risk Share", fmt_pct(selected_policy_row["high_risk_share"]))

st.header("Policy Trade-Offs")

col1, col2 = st.columns(2)

with col1:
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

with col2:
    fig = px.scatter(
        policy_display,
        x="approval_rate_pct",
        y="actual_default_rate_pct",
        size="total_economic_profit_m",
        color="policy",
        hover_name="policy",
        title="Approval Rate vs Default Rate",
        labels={
            "approval_rate_pct": "Approval Rate (%)",
            "actual_default_rate_pct": "Default Rate (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

policy_risk = policy_comparison.copy()
policy_risk["high_risk_share_pct"] = policy_risk["high_risk_share"] * 100
policy_risk["underpriced_share_pct"] = policy_risk["underpriced_share"] * 100

col3, col4 = st.columns(2)

with col3:
    fig = px.bar(
        policy_risk,
        x="policy",
        y="high_risk_share_pct",
        title="High-Risk Exposure by Policy",
        labels={
            "policy": "Policy",
            "high_risk_share_pct": "High-Risk Share (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    fig = px.bar(
        policy_risk,
        x="policy",
        y="underpriced_share_pct",
        title="Underpriced Share by Policy",
        labels={
            "policy": "Policy",
            "underpriced_share_pct": "Underpriced Share (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Approved vs Rejected Portfolio")

approval_display = approval_summary.copy()
approval_display["total_economic_profit_m"] = (
    approval_display["total_economic_profit"] / 1_000_000
)
approval_display["actual_default_rate_pct"] = (
    approval_display["actual_default_rate"] * 100
)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        approval_display,
        x="approval_segment",
        y="total_economic_profit_m",
        title="Economic Profit by Approval Segment",
        labels={
            "approval_segment": "Approval Segment",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        approval_display,
        x="approval_segment",
        y="actual_default_rate_pct",
        title="Default Rate by Approval Segment",
        labels={
            "approval_segment": "Approval Segment",
            "actual_default_rate_pct": "Default Rate (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(approval_summary, use_container_width=True)

st.header("Policy Comparison Table")
st.dataframe(policy_comparison, use_container_width=True)

st.header("Policy Methodology")

policy_notes = methodology_notes[
    methodology_notes["section"].isin(
        [
            "Policy Comparison",
            "Economic Profit",
            "Limitation",
        ]
    )
].copy()

for _, row in policy_notes.iterrows():
    with st.expander(str(row["section"])):
        st.write(row["note"])