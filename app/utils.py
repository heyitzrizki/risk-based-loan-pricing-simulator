import json
from pathlib import Path

import pandas as pd
import streamlit as st


# Path helpers

def get_project_root() -> Path:
    """
    Return project root assuming this file is located under app/.
    """
    return Path(__file__).resolve().parents[1]


def get_artifact_dir() -> Path:
    """
    Return Streamlit artifact directory.
    """
    return get_project_root() / "artifacts" / "streamlit"


# Data loading

@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    """
    Load CSV artifact from artifacts/streamlit.
    """
    path = get_artifact_dir() / filename

    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")

    return pd.read_csv(path)


@st.cache_data
def load_json(filename: str) -> dict:
    """
    Load JSON artifact from artifacts/streamlit.
    """
    path = get_artifact_dir() / filename

    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_streamlit_artifacts() -> dict:
    """
    Load all artifacts required by the Streamlit dashboard.
    """
    return {
        "portfolio_kpi": load_csv("streamlit_portfolio_kpi.csv"),
        "kpi_cards": load_csv("streamlit_kpi_cards.csv"),
        "grade_profitability": load_csv("streamlit_grade_profitability.csv"),
        "policy_comparison": load_csv("streamlit_policy_comparison.csv"),
        "scenario_policy_summary": load_csv("streamlit_scenario_policy_summary.csv"),
        "approval_summary": load_csv("streamlit_approval_summary.csv"),
        "pricing_sample": load_csv("streamlit_pricing_sample.csv"),
        "lgd_assumptions": load_csv("streamlit_lgd_assumptions.csv"),
        "methodology_notes": load_csv("streamlit_methodology_notes.csv"),
        "metadata": load_json("streamlit_metadata.json"),
    }


# Formatting helpers

def fmt_currency(value) -> str:
    """
    Format a numeric value as currency.
    """
    if pd.isna(value):
        return "N/A"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.2f}K"

    return f"${value:,.0f}"


def fmt_pct(value) -> str:
    """
    Format a decimal value as percentage.
    """
    if pd.isna(value):
        return "N/A"

    return f"{float(value) * 100:,.2f}%"


def fmt_int(value) -> str:
    """
    Format a numeric value as integer.
    """
    if pd.isna(value):
        return "N/A"

    return f"{float(value):,.0f}"


def add_percent_column(df: pd.DataFrame, source_col: str, new_col: str) -> pd.DataFrame:
    """
    Add percentage column by multiplying a decimal column by 100.
    """
    out = df.copy()

    if source_col in out.columns:
        out[new_col] = out[source_col] * 100

    return out


def add_million_column(df: pd.DataFrame, source_col: str, new_col: str) -> pd.DataFrame:
    """
    Add million-scale column from numeric currency column.
    """
    out = df.copy()

    if source_col in out.columns:
        out[new_col] = out[source_col] / 1_000_000

    return out


# Data transformation helpers

GRADE_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]


def get_available_grades(df: pd.DataFrame, grade_col: str = "internal_grade") -> list:
    """
    Return grades ordered by predefined internal grade order.
    """
    if grade_col not in df.columns:
        return []

    available = df[grade_col].dropna().unique().tolist()

    return [grade for grade in GRADE_ORDER if grade in available]


def filter_pricing_sample(
    df: pd.DataFrame,
    selected_grades: list,
    selected_pricing_status: list,
) -> pd.DataFrame:
    """
    Filter pricing sample by internal grade and pricing status.
    """
    out = df.copy()

    if selected_grades and "internal_grade" in out.columns:
        out = out[out["internal_grade"].isin(selected_grades)]

    if selected_pricing_status and "pricing_status" in out.columns:
        out = out[out["pricing_status"].isin(selected_pricing_status)]

    return out


def prepare_policy_display(policy_comparison: pd.DataFrame) -> pd.DataFrame:
    """
    Add chart-friendly columns to policy comparison table.
    """
    out = policy_comparison.copy()

    if "approval_rate" in out.columns:
        out["approval_rate_pct"] = out["approval_rate"] * 100

    if "actual_default_rate" in out.columns:
        out["actual_default_rate_pct"] = out["actual_default_rate"] * 100

    if "portfolio_economic_return" in out.columns:
        out["portfolio_economic_return_pct"] = out["portfolio_economic_return"] * 100

    if "total_economic_profit" in out.columns:
        out["total_economic_profit_m"] = out["total_economic_profit"] / 1_000_000

    return out


def prepare_grade_display(grade_profitability: pd.DataFrame) -> pd.DataFrame:
    """
    Add chart-friendly columns to grade profitability table.
    """
    out = grade_profitability.copy()

    if "actual_default_rate" in out.columns:
        out["actual_default_rate_pct"] = out["actual_default_rate"] * 100

    if "avg_economic_return" in out.columns:
        out["avg_economic_return_pct"] = out["avg_economic_return"] * 100

    if "total_economic_profit" in out.columns:
        out["total_economic_profit_m"] = out["total_economic_profit"] / 1_000_000

    return out


def prepare_scenario_display(scenario_policy_summary: pd.DataFrame) -> pd.DataFrame:
    """
    Add chart-friendly columns to scenario table.
    """
    out = scenario_policy_summary.copy()

    if "portfolio_economic_return" in out.columns:
        out["portfolio_economic_return_pct"] = out["portfolio_economic_return"] * 100

    if "total_economic_profit" in out.columns:
        out["total_economic_profit_m"] = out["total_economic_profit"] / 1_000_000

    return out


def pricing_status_counts(pricing_sample: pd.DataFrame) -> pd.DataFrame:
    """
    Return pricing status counts for pie chart.
    """
    if "pricing_status" not in pricing_sample.columns:
        return pd.DataFrame(columns=["pricing_status", "count"])

    counts = pricing_sample["pricing_status"].value_counts().reset_index()
    counts.columns = ["pricing_status", "count"]

    return counts


# Display helpers

def safe_dataframe(df: pd.DataFrame, height: int | None = None):
    """
    Display dataframe with full container width.
    """
    st.dataframe(df, use_container_width=True, height=height)


def get_selected_policy_row(policy_comparison: pd.DataFrame, selected_policy: str) -> pd.Series:
    """
    Return selected policy row. Falls back to first row if selected policy is missing.
    """
    matched = policy_comparison[policy_comparison["policy"].eq(selected_policy)]

    if matched.empty:
        return policy_comparison.iloc[0]

    return matched.iloc[0]

    def calculate_manual_pricing(
    loan_amount: float,
    term_months: int,
    offered_rate: float,
    pd_value: float,
    lgd: float,
    funding_cost_rate: float,
    operating_cost_rate: float,
    target_margin_rate: float,
    capital_cost_rate: float,
    collection_cost_rate: float,
    tail_risk_multiplier: float,
    pricing_tolerance: float = 0.01,
    max_allowed_rate: float = 0.30,
) -> dict:
    term_years = term_months / 12

    ead = loan_amount
    actual_rate = offered_rate

    expected_loss = pd_value * lgd * ead
    lifetime_expected_loss_rate = pd_value * lgd
    annualized_expected_loss_rate = lifetime_expected_loss_rate / term_years

    required_rate = (
        funding_cost_rate
        + operating_cost_rate
        + annualized_expected_loss_rate
        + target_margin_rate
    )

    required_rate_capped = min(required_rate, max_allowed_rate)
    pricing_gap = actual_rate - required_rate

    if pricing_gap < -pricing_tolerance:
        pricing_status = "Underpriced"
    elif pricing_gap <= pricing_tolerance:
        pricing_status = "Fairly Priced"
    else:
        pricing_status = "Overpriced"

    interest_income = ead * actual_rate * term_years
    funding_cost = ead * funding_cost_rate * term_years
    operating_cost = ead * operating_cost_rate * term_years

    expected_profit = (
        interest_income
        - funding_cost
        - operating_cost
        - expected_loss
    )

    risk_adjusted_return = expected_profit / ead if ead else 0

    capital_requirement = ead * pd_value * lgd
    capital_charge = capital_requirement * capital_cost_rate * term_years
    collection_cost = expected_loss * collection_cost_rate
    tail_risk_penalty = ead * (pd_value ** 2) * lgd * tail_risk_multiplier

    economic_profit = (
        expected_profit
        - capital_charge
        - collection_cost
        - tail_risk_penalty
    )

    economic_return = economic_profit / ead if ead else 0

    repriced_interest_income = ead * required_rate_capped * term_years
    repriced_expected_profit = (
        repriced_interest_income
        - funding_cost
        - operating_cost
        - expected_loss
    )

    repriced_economic_profit = (
        repriced_expected_profit
        - capital_charge
        - collection_cost
        - tail_risk_penalty
    )

    repriced_economic_return = repriced_economic_profit / ead if ead else 0

    if economic_profit >= 0 and required_rate <= max_allowed_rate:
        decision = "Approve at Current Rate"
    elif repriced_economic_profit >= 0 and required_rate <= max_allowed_rate:
        decision = "Approve if Repriced"
    elif required_rate > max_allowed_rate and pd_value < 0.35:
        decision = "Manual Review"
    else:
        decision = "Reject"

    return {
        "loan_amount": loan_amount,
        "term_months": term_months,
        "term_years": term_years,
        "pd": pd_value,
        "lgd": lgd,
        "ead": ead,
        "offered_rate": actual_rate,
        "required_rate": required_rate,
        "required_rate_capped": required_rate_capped,
        "pricing_gap": pricing_gap,
        "pricing_status": pricing_status,
        "expected_loss": expected_loss,
        "lifetime_expected_loss_rate": lifetime_expected_loss_rate,
        "annualized_expected_loss_rate": annualized_expected_loss_rate,
        "interest_income": interest_income,
        "funding_cost": funding_cost,
        "operating_cost": operating_cost,
        "expected_profit": expected_profit,
        "risk_adjusted_return": risk_adjusted_return,
        "capital_requirement": capital_requirement,
        "capital_charge": capital_charge,
        "collection_cost": collection_cost,
        "tail_risk_penalty": tail_risk_penalty,
        "economic_profit": economic_profit,
        "economic_return": economic_return,
        "repriced_expected_profit": repriced_expected_profit,
        "repriced_economic_profit": repriced_economic_profit,
        "repriced_economic_return": repriced_economic_return,
        "decision": decision,
    }