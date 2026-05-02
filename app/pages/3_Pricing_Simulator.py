import plotly.express as px
import streamlit as st

from utils import (
    GRADE_ORDER,
    fmt_currency,
    fmt_pct,
    load_streamlit_artifacts,
    prepare_grade_display,
    pricing_status_counts,
)

st.set_page_config(
    page_title="Pricing Simulator | Loan Pricing Simulator",
    page_icon="🧮",
    layout="wide",
)

artifacts = load_streamlit_artifacts()

portfolio_kpi = artifacts["portfolio_kpi"]
grade_profitability = artifacts["grade_profitability"]
pricing_sample = artifacts["pricing_sample"]
lgd_assumptions = artifacts["lgd_assumptions"]
methodology_notes = artifacts["methodology_notes"]

st.title("Pricing Simulator")

st.markdown(
    """
    This page focuses on the pricing engine: actual interest rate, required
    risk-based rate, pricing gap, expected loss, and economic profit.
    """
)

kpi = portfolio_kpi.iloc[0]

st.header("Pricing Engine Snapshot")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Average Actual Rate", fmt_pct(kpi["avg_actual_rate"]))
col2.metric("Average Required Rate", fmt_pct(kpi["avg_required_rate"]))
col3.metric("Underpriced Share", fmt_pct(kpi["underpriced_share"]))
col4.metric("Economic Return", fmt_pct(kpi["portfolio_economic_return"]))

col5, col6, col7, col8 = st.columns(4)
col5.metric("Expected Loss", fmt_currency(kpi["total_expected_loss"]))
col6.metric("Expected Profit", fmt_currency(kpi["total_expected_profit"]))
col7.metric("Economic Profit", fmt_currency(kpi["total_economic_profit"]))
col8.metric("Total EAD", fmt_currency(kpi["total_ead"]))

st.caption(
    "Required rate is calculated from funding cost, operating cost, annualized expected loss, "
    "and target margin. Economic profit adjusts expected profit using capital charge, "
    "collection cost, and tail-risk penalty."
)

st.header("Pricing Status Overview")

pricing_counts = pricing_status_counts(pricing_sample)

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
    fig = px.histogram(
        pricing_sample,
        x="pricing_gap",
        color="pricing_status",
        nbins=60,
        title="Pricing Gap Distribution",
        labels={
            "pricing_gap": "Actual Rate - Required Rate",
            "pricing_status": "Pricing Status",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Actual Rate vs Required Rate")

col1, col2 = st.columns(2)

with col1:
    fig = px.scatter(
        pricing_sample,
        x="required_rate",
        y="actual_rate",
        color="pricing_status",
        hover_data=[
            "loan_amnt",
            "term_months",
            "calibrated_pd",
            "internal_grade",
            "pricing_gap",
            "economic_profit",
        ],
        title="Loan-Level Actual Rate vs Required Rate",
        labels={
            "required_rate": "Required Risk-Based Rate",
            "actual_rate": "Actual Interest Rate",
            "pricing_status": "Pricing Status",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.box(
        pricing_sample,
        x="internal_grade",
        y="pricing_gap",
        color="internal_grade",
        category_orders={"internal_grade": GRADE_ORDER},
        title="Pricing Gap by Internal Grade",
        labels={
            "internal_grade": "Internal Grade",
            "pricing_gap": "Pricing Gap",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Pricing by Internal Grade")

grade_display = prepare_grade_display(grade_profitability)

grade_pricing_cols = [
    "internal_grade",
    "n_loans",
    "avg_pd",
    "actual_default_rate",
    "avg_actual_rate",
    "avg_required_rate",
    "avg_pricing_gap",
    "underpriced_share",
    "total_expected_loss",
    "total_expected_profit",
    "total_economic_profit",
    "avg_economic_return",
]

grade_pricing_cols = [
    col for col in grade_pricing_cols
    if col in grade_profitability.columns
]

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        grade_display,
        x="internal_grade",
        y="avg_required_rate",
        category_orders={"internal_grade": GRADE_ORDER},
        title="Average Required Rate by Grade",
        labels={
            "internal_grade": "Internal Grade",
            "avg_required_rate": "Average Required Rate",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        grade_display,
        x="internal_grade",
        y="total_economic_profit_m",
        category_orders={"internal_grade": GRADE_ORDER},
        title="Economic Profit by Grade",
        labels={
            "internal_grade": "Internal Grade",
            "total_economic_profit_m": "Economic Profit ($M)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    grade_profitability[grade_pricing_cols],
    use_container_width=True,
)

st.header("Interactive Pricing Explorer")

selected_status = st.multiselect(
    "Pricing status",
    options=pricing_sample["pricing_status"].dropna().unique().tolist(),
    default=pricing_sample["pricing_status"].dropna().unique().tolist(),
)

selected_grades = st.multiselect(
    "Internal grades",
    options=[g for g in GRADE_ORDER if g in pricing_sample["internal_grade"].unique()],
    default=[g for g in GRADE_ORDER if g in pricing_sample["internal_grade"].unique()],
)

filtered = pricing_sample[
    pricing_sample["pricing_status"].isin(selected_status)
    & pricing_sample["internal_grade"].isin(selected_grades)
].copy()

table_cols = [
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
    "grade",
    "sub_grade",
]

table_cols = [col for col in table_cols if col in filtered.columns]

st.dataframe(
    filtered[table_cols].sort_values("pricing_gap", ascending=True),
    use_container_width=True,
    height=450,
)

st.header("Assumptions")

col1, col2 = st.columns(2)

with col1:
    st.subheader("LGD Assumptions")
    st.dataframe(lgd_assumptions, use_container_width=True)

with col2:
    st.subheader("Relevant Methodology Notes")
    selected_sections = [
        "Expected Loss",
        "LGD",
        "Required Rate",
        "Pricing Gap",
        "Economic Profit",
    ]

    notes = methodology_notes[
        methodology_notes["section"].isin(selected_sections)
    ].copy()

    for _, row in notes.iterrows():
        with st.expander(str(row["section"])):
            st.write(row["note"])