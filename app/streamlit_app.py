import plotly.express as px
import streamlit as st

from utils import (
    GRADE_ORDER,
    filter_pricing_sample,
    fmt_currency,
    fmt_int,
    fmt_pct,
    get_available_grades,
    get_selected_policy_row,
    load_streamlit_artifacts,
    prepare_grade_display,
    prepare_policy_display,
    prepare_scenario_display,
    pricing_status_counts,
)

# Page configuration

st.set_page_config(
    page_title="Risk-Based Loan Pricing Simulator",
    page_icon="💰",
    layout="wide",
)

# Load artifacts

artifacts = load_streamlit_artifacts()

portfolio_kpi = artifacts["portfolio_kpi"]
kpi_cards = artifacts["kpi_cards"]
grade_profitability = artifacts["grade_profitability"]
policy_comparison = artifacts["policy_comparison"]
scenario_policy_summary = artifacts["scenario_policy_summary"]
approval_summary = artifacts["approval_summary"]
pricing_sample = artifacts["pricing_sample"]
lgd_assumptions = artifacts["lgd_assumptions"]
methodology_notes = artifacts["methodology_notes"]
metadata = artifacts["metadata"]

# Sidebar controls

st.sidebar.title("Controls")

available_policies = policy_comparison["policy"].dropna().tolist()
default_policy_index = (
    available_policies.index("Balanced")
    if "Balanced" in available_policies
    else 0
)

selected_policy = st.sidebar.selectbox(
    "Approval Policy",
    options=available_policies,
    index=default_policy_index,
)

available_scenarios = scenario_policy_summary["scenario"].dropna().unique().tolist()

selected_scenario = st.sidebar.selectbox(
    "Scenario",
    options=available_scenarios,
    index=0,
)

grade_order = GRADE_ORDER
available_grades = get_available_grades(pricing_sample)

selected_grades = st.sidebar.multiselect(
    "Internal Grade Filter",
    options=available_grades,
    default=available_grades,
)

available_pricing_status = pricing_sample["pricing_status"].dropna().unique().tolist()

selected_pricing_status = st.sidebar.multiselect(
    "Pricing Status Filter",
    options=available_pricing_status,
    default=available_pricing_status,
)

filtered_sample = filter_pricing_sample(
    pricing_sample,
    selected_grades=selected_grades,
    selected_pricing_status=selected_pricing_status,
)

# Header

st.title("Risk-Based Loan Pricing & Portfolio Profitability Simulator")

st.markdown(
    """
    This dashboard translates borrower-level default risk into **risk-based pricing**,
    **expected loss**, **economic profit**, and **approval policy simulation**.

    The simulator uses a PD model, internal risk grades, LGD assumptions,
    required-rate logic, and economic profit adjustments to support credit
    portfolio decision-making.
    """
)

with st.expander("Project Metadata", expanded=False):
    st.json(metadata)

# Executive overview

st.header("1. Executive Overview")

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
    "Economic profit adjusts expected profit by subtracting capital charge, "
    "collection cost, and nonlinear tail-risk penalty."
)

# Pricing overview

st.header("2. Pricing Overview")

pricing_counts = pricing_status_counts(pricing_sample)

approval_display = approval_summary.copy()
approval_display["total_economic_profit_m"] = (
    approval_display["total_economic_profit"] / 1_000_000
)

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

st.subheader("Approved vs Rejected Portfolio Summary")
st.dataframe(approval_summary, use_container_width=True)

# Policy comparison

st.header("3. Approval Policy Comparison")

policy_display = prepare_policy_display(policy_comparison)

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
        hover_name="policy",
        title="Approval Rate vs Default Rate",
        labels={
            "approval_rate_pct": "Approval Rate (%)",
            "actual_default_rate_pct": "Actual Default Rate (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

selected_policy_row = get_selected_policy_row(policy_comparison, selected_policy)

st.subheader(f"Selected Policy: {selected_policy}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Approval Rate", fmt_pct(selected_policy_row["approval_rate"]))
col2.metric("Approved EAD", fmt_currency(selected_policy_row["approved_ead"]))
col3.metric("Economic Profit", fmt_currency(selected_policy_row["total_economic_profit"]))
col4.metric("Economic Return", fmt_pct(selected_policy_row["portfolio_economic_return"]))

st.dataframe(policy_comparison, use_container_width=True)


# Grade profitability

st.header("4. Internal Grade Profitability")

grade_display = prepare_grade_display(grade_profitability)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        grade_display,
        x="internal_grade",
        y="actual_default_rate_pct",
        title="Actual Default Rate by Internal Grade",
        category_orders={"internal_grade": grade_order},
        labels={
            "internal_grade": "Internal Grade",
            "actual_default_rate_pct": "Default Rate (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        grade_display,
        x="internal_grade",
        y="total_economic_profit_m",
        title="Economic Profit by Internal Grade",
        category_orders={"internal_grade": grade_order},
        labels={
            "internal_grade": "Internal Grade",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(grade_profitability, use_container_width=True)

# Scenario sensitivity

st.header("5. Scenario Sensitivity")

scenario_all_display = prepare_scenario_display(scenario_policy_summary)

scenario_filtered = scenario_all_display[
    scenario_all_display["scenario"].eq(selected_scenario)
].copy()

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        scenario_filtered,
        x="policy",
        y="total_economic_profit_m",
        title=f"Economic Profit by Policy — {selected_scenario}",
        labels={
            "policy": "Policy",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.line(
        scenario_all_display,
        x="policy",
        y="portfolio_economic_return_pct",
        color="scenario",
        markers=True,
        title="Economic Return Across Scenarios",
        labels={
            "policy": "Policy",
            "portfolio_economic_return_pct": "Economic Return (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(scenario_policy_summary, use_container_width=True)

# Loan-level explorer

st.header("6. Loan-Level Explorer")

st.caption(
    "This table uses a stratified deployment sample for fast interaction. "
    "Portfolio-level KPIs are computed from the full holdout test set."
)

loan_display_cols = [
    "loan_amnt",
    "term_months",
    "int_rate",
    "calibrated_pd",
    "internal_grade",
    "actual_rate",
    "required_rate",
    "pricing_gap",
    "pricing_status",
    "expected_loss",
    "expected_profit",
    "economic_profit",
    "economic_return",
    "strategy_approved",
    "grade",
    "sub_grade",
]

loan_display_cols = [
    col for col in loan_display_cols
    if col in filtered_sample.columns
]

st.dataframe(
    filtered_sample[loan_display_cols].sort_values(
        "calibrated_pd",
        ascending=False,
    ),
    use_container_width=True,
    height=450,
)

# Methodology

st.header("7. Methodology Notes")

for _, row in methodology_notes.iterrows():
    with st.expander(str(row["section"])):
        st.write(row["note"])

st.subheader("LGD Assumptions")
st.dataframe(lgd_assumptions, use_container_width=True)