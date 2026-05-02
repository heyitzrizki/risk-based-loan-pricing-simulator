import plotly.express as px
import streamlit as st

from utils import (
    load_streamlit_artifacts,
    prepare_policy_display,
    prepare_scenario_display,
)

st.set_page_config(
    page_title="Portfolio Frontier | Loan Pricing Simulator",
    page_icon="📈",
    layout="wide",
)

artifacts = load_streamlit_artifacts()

policy_comparison = artifacts["policy_comparison"]
scenario_policy_summary = artifacts["scenario_policy_summary"]
methodology_notes = artifacts["methodology_notes"]

st.title("Portfolio Frontier")

st.markdown(
    """
    Visualize risk-return trade-offs across approval policies and business scenarios.
    """
)

policy_display = prepare_policy_display(policy_comparison)
scenario_display = prepare_scenario_display(scenario_policy_summary)

st.header("Risk-Return Frontier")

col1, col2 = st.columns(2)

with col1:
    fig = px.scatter(
        policy_display,
        x="actual_default_rate_pct",
        y="portfolio_economic_return_pct",
        size="total_economic_profit_m",
        color="policy",
        hover_name="policy",
        title="Default Rate vs Economic Return",
        labels={
            "actual_default_rate_pct": "Default Rate (%)",
            "portfolio_economic_return_pct": "Economic Return (%)",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.scatter(
        policy_display,
        x="approval_rate_pct",
        y="portfolio_economic_return_pct",
        size="total_economic_profit_m",
        color="policy",
        hover_name="policy",
        title="Approval Rate vs Economic Return",
        labels={
            "approval_rate_pct": "Approval Rate (%)",
            "portfolio_economic_return_pct": "Economic Return (%)",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Scenario Sensitivity")

selected_metric = st.selectbox(
    "Scenario metric",
    options=[
        "portfolio_economic_return_pct",
        "total_economic_profit_m",
        "approval_rate",
        "actual_default_rate",
        "high_risk_share",
        "underpriced_share",
    ],
    index=0,
)

metric_labels = {
    "portfolio_economic_return_pct": "Economic Return (%)",
    "total_economic_profit_m": "Economic Profit ($M)",
    "approval_rate": "Approval Rate",
    "actual_default_rate": "Actual Default Rate",
    "high_risk_share": "High-Risk Share",
    "underpriced_share": "Underpriced Share",
}

scenario_chart = scenario_display.copy()

for col in ["approval_rate", "actual_default_rate", "high_risk_share", "underpriced_share"]:
    if col in scenario_chart.columns:
        scenario_chart[f"{col}_pct"] = scenario_chart[col] * 100

if selected_metric == "approval_rate":
    y_col = "approval_rate_pct"
elif selected_metric == "actual_default_rate":
    y_col = "actual_default_rate_pct"
elif selected_metric == "high_risk_share":
    y_col = "high_risk_share_pct"
elif selected_metric == "underpriced_share":
    y_col = "underpriced_share_pct"
else:
    y_col = selected_metric

fig = px.line(
    scenario_chart,
    x="policy",
    y=y_col,
    color="scenario",
    markers=True,
    title=f"{metric_labels[selected_metric]} Across Scenarios",
    labels={
        "policy": "Policy",
        y_col: metric_labels[selected_metric],
        "scenario": "Scenario",
    },
)
st.plotly_chart(fig, use_container_width=True)

st.header("Loss-Profit Trade-Off")

policy_risk_display = policy_comparison.copy()
policy_risk_display["total_expected_loss_m"] = (
    policy_risk_display["total_expected_loss"] / 1_000_000
)
policy_risk_display["total_economic_profit_m"] = (
    policy_risk_display["total_economic_profit"] / 1_000_000
)
policy_risk_display["high_risk_share_pct"] = policy_risk_display["high_risk_share"] * 100

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        policy_risk_display,
        x="policy",
        y=["total_expected_loss_m", "total_economic_profit_m"],
        barmode="group",
        title="Expected Loss vs Economic Profit",
        labels={
            "policy": "Policy",
            "value": "Amount ($M)",
            "variable": "Metric",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        policy_risk_display,
        x="policy",
        y="high_risk_share_pct",
        title="High-Risk Exposure by Policy",
        labels={
            "policy": "Policy",
            "high_risk_share_pct": "High-Risk Share (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Scenario Table")
st.dataframe(scenario_policy_summary, use_container_width=True)

st.header("Interpretation Guide")

st.markdown(
    """
    - **Conservative** keeps risk low but sacrifices scale.
    - **Balanced** is the default operating policy for controlled risk-taking.
    - **Growth** increases scale and profit with higher risk exposure.
    - **Aggressive** maximizes scale but creates the highest risk concentration.
    """
)

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