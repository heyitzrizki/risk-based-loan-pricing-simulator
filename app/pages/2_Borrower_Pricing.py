import plotly.express as px
import streamlit as st

from utils import (
    GRADE_ORDER,
    filter_pricing_sample,
    fmt_currency,
    fmt_pct,
    get_available_grades,
    load_streamlit_artifacts,
)

st.set_page_config(
    page_title="Borrower Pricing | Loan Pricing Simulator",
    page_icon="💳",
    layout="wide",
)

artifacts = load_streamlit_artifacts()
pricing_sample = artifacts["pricing_sample"]
lgd_assumptions = artifacts["lgd_assumptions"]
methodology_notes = artifacts["methodology_notes"]

st.title("Borrower-Level Pricing Explorer")

st.markdown(
    """
    This page explores individual loan-level pricing outputs:
    predicted default risk, internal grade, expected loss, required rate,
    pricing gap, and economic profit.
    """
)

st.caption(
    "The loan-level table uses a stratified deployment sample for fast interaction. "
    "Portfolio-level KPIs in the executive page are computed from the full holdout test set."
)

st.sidebar.title("Borrower Pricing Filters")

available_grades = get_available_grades(pricing_sample)

selected_grades = st.sidebar.multiselect(
    "Internal Grade",
    options=available_grades,
    default=available_grades,
)

available_pricing_status = pricing_sample["pricing_status"].dropna().unique().tolist()

selected_pricing_status = st.sidebar.multiselect(
    "Pricing Status",
    options=available_pricing_status,
    default=available_pricing_status,
)

available_decisions = pricing_sample["pricing_decision"].dropna().unique().tolist()

selected_decisions = st.sidebar.multiselect(
    "Pricing Decision",
    options=available_decisions,
    default=available_decisions,
)

pd_min = float(pricing_sample["calibrated_pd"].min())
pd_max = float(pricing_sample["calibrated_pd"].max())

selected_pd_range = st.sidebar.slider(
    "PD Range",
    min_value=pd_min,
    max_value=pd_max,
    value=(pd_min, pd_max),
    step=0.01,
)

loan_min = int(pricing_sample["loan_amnt"].min())
loan_max = int(pricing_sample["loan_amnt"].max())

selected_loan_range = st.sidebar.slider(
    "Loan Amount Range",
    min_value=loan_min,
    max_value=loan_max,
    value=(loan_min, loan_max),
    step=500,
)

filtered = filter_pricing_sample(
    pricing_sample,
    selected_grades=selected_grades,
    selected_pricing_status=selected_pricing_status,
)

filtered = filtered[
    filtered["pricing_decision"].isin(selected_decisions)
    & filtered["calibrated_pd"].between(selected_pd_range[0], selected_pd_range[1])
    & filtered["loan_amnt"].between(selected_loan_range[0], selected_loan_range[1])
].copy()

st.header("Filtered Loan Pool Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Loans", f"{len(filtered):,.0f}")
col2.metric("Total EAD", fmt_currency(filtered["ead"].sum()))
col3.metric("Average PD", fmt_pct(filtered["calibrated_pd"].mean()))
col4.metric("Average Economic Return", fmt_pct(filtered["economic_return"].mean()))

col5, col6, col7, col8 = st.columns(4)

col5.metric("Expected Loss", fmt_currency(filtered["expected_loss"].sum()))
col6.metric("Expected Profit", fmt_currency(filtered["expected_profit"].sum()))
col7.metric("Economic Profit", fmt_currency(filtered["economic_profit"].sum()))
col8.metric(
    "Underpriced Share",
    fmt_pct((filtered["pricing_status"] == "Underpriced").mean())
    if len(filtered) > 0
    else "N/A",
)

st.header("Borrower Pricing Diagnostics")

if len(filtered) == 0:
    st.warning("No loans match the selected filters.")
else:
    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            filtered,
            x="calibrated_pd",
            color="internal_grade",
            nbins=40,
            title="PD Distribution by Internal Grade",
            category_orders={"internal_grade": GRADE_ORDER},
            labels={
                "calibrated_pd": "Predicted Default Probability",
                "internal_grade": "Internal Grade",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(
            filtered,
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
            title="Actual Rate vs Required Risk-Based Rate",
            labels={
                "required_rate": "Required Rate",
                "actual_rate": "Actual Rate",
                "pricing_status": "Pricing Status",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        grade_summary = (
            filtered
            .groupby("internal_grade")
            .agg(
                n_loans=("loan_amnt", "size"),
                avg_pd=("calibrated_pd", "mean"),
                avg_pricing_gap=("pricing_gap", "mean"),
                total_economic_profit=("economic_profit", "sum"),
            )
            .reset_index()
        )

        fig = px.bar(
            grade_summary,
            x="internal_grade",
            y="total_economic_profit",
            title="Economic Profit by Internal Grade",
            category_orders={"internal_grade": GRADE_ORDER},
            labels={
                "internal_grade": "Internal Grade",
                "total_economic_profit": "Economic Profit",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        fig = px.box(
            filtered,
            x="internal_grade",
            y="pricing_gap",
            category_orders={"internal_grade": GRADE_ORDER},
            title="Pricing Gap Distribution by Internal Grade",
            labels={
                "internal_grade": "Internal Grade",
                "pricing_gap": "Pricing Gap",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

st.header("Loan-Level Pricing Table")

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
    "pricing_decision",
    "expected_loss",
    "expected_profit",
    "capital_charge",
    "collection_cost",
    "tail_risk_penalty",
    "economic_profit",
    "economic_return",
    "strategy_approved",
    "grade",
    "sub_grade",
]

table_cols = [col for col in table_cols if col in filtered.columns]

st.dataframe(
    filtered[table_cols].sort_values("calibrated_pd", ascending=False),
    use_container_width=True,
    height=500,
)

st.header("Pricing Methodology")

with st.expander("LGD assumptions", expanded=False):
    st.dataframe(lgd_assumptions, use_container_width=True)

with st.expander("Methodology notes", expanded=False):
    for _, row in methodology_notes.iterrows():
        st.markdown(f"**{row['section']}**")
        st.write(row["note"])