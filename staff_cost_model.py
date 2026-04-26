"""Interactive staff cost modelling scenario tool.

Run with:
    streamlit run staff_cost_model.py
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

DAYS_IN_YEAR = 365
DEFAULT_BUDGET = 350_000
DEFAULT_ON_COST_RATE = 0.22


def annual_to_daily_cost(annual_salary: float, on_cost_rate: float) -> float:
    """Convert annual salary + on-costs into a daily cost."""
    return (annual_salary * (1 + on_cost_rate)) / DAYS_IN_YEAR


def overlap_days(start: date, end: date, period_start: date, period_end: date) -> int:
    """Inclusive overlap in days for two date ranges."""
    active_start = max(start, period_start)
    active_end = min(end, period_end)
    if active_end < active_start:
        return 0
    return (active_end - active_start).days + 1


def vacancy_cost(
    annual_salary: float,
    on_cost_rate: float,
    start_date: date,
    period_start: date,
    period_end: date,
) -> float:
    """Calculate cost in period from a start date through period end."""
    days = overlap_days(start_date, period_end, period_start, period_end)
    return annual_to_daily_cost(annual_salary, on_cost_rate) * days


def format_currency(amount: float) -> str:
    return f"${amount:,.0f}"


def _default_vacancy_rows(year: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Vacancy": "Engineer",
                "Annual Salary": 110_000,
                "On-cost Rate": DEFAULT_ON_COST_RATE,
                "Budgeted Start": date(year, 1, 15),
                "Scenario Start": date(year, 3, 1),
            },
            {
                "Vacancy": "Analyst",
                "Annual Salary": 85_000,
                "On-cost Rate": DEFAULT_ON_COST_RATE,
                "Budgeted Start": date(year, 2, 1),
                "Scenario Start": date(year, 2, 1),
            },
        ]
    )


def _to_date(value: object) -> date:
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(f"Expected date value, received {type(value).__name__}")


def _build_result_rows(input_df: pd.DataFrame, period_start: date, period_end: date) -> tuple[pd.DataFrame, list[str]]:
    records: list[dict[str, object]] = []
    validation_issues: list[str] = []

    for idx, row in input_df.iterrows():
        vacancy = str(row.get("Vacancy", "")).strip()
        if not vacancy:
            continue

        row_num = idx + 1

        try:
            annual_salary = float(row["Annual Salary"])
            on_cost_rate = float(row["On-cost Rate"])
            budgeted_start = _to_date(row["Budgeted Start"])
            scenario_start = _to_date(row["Scenario Start"])
        except (TypeError, ValueError, KeyError) as exc:
            validation_issues.append(f"Row {row_num} ({vacancy}): {exc}")
            continue

        if annual_salary < 0:
            validation_issues.append(f"Row {row_num} ({vacancy}): Annual Salary cannot be negative.")
            continue

        if on_cost_rate < 0:
            validation_issues.append(f"Row {row_num} ({vacancy}): On-cost Rate cannot be negative.")
            continue

        budget_cost = vacancy_cost(
            annual_salary=annual_salary,
            on_cost_rate=on_cost_rate,
            start_date=budgeted_start,
            period_start=period_start,
            period_end=period_end,
        )
        scenario_cost = vacancy_cost(
            annual_salary=annual_salary,
            on_cost_rate=on_cost_rate,
            start_date=scenario_start,
            period_start=period_start,
            period_end=period_end,
        )

        variance = scenario_cost - budget_cost
        records.append(
            {
                "Vacancy": vacancy,
                "Budgeted Start": budgeted_start,
                "Scenario Start": scenario_start,
                "Budgeted Cost": budget_cost,
                "Scenario Cost": scenario_cost,
                "Variance": variance,
                "Variance %": (variance / budget_cost) if budget_cost else 0.0,
            }
        )

    return pd.DataFrame(records), validation_issues


def main() -> None:
    st.set_page_config(page_title="Staff Cost Modeller", layout="wide")
    st.title("Staff Cost Modelling Scenario Tool")
    st.write(
        "Try different vacancy start dates and instantly compare scenario spend "
        "against your staffing budget and baseline plan."
    )

    st.subheader("Budget Period")
    c1, c2, c3 = st.columns(3)
    with c1:
        period_start = st.date_input("Period start", value=date(date.today().year, 1, 1))
    with c2:
        period_end = st.date_input("Period end", value=date(date.today().year, 12, 31))
    with c3:
        annual_budget = st.number_input(
            "Budget ($)", min_value=0, value=DEFAULT_BUDGET, step=10_000
        )

    if period_end < period_start:
        st.error("Period end must be on or after period start.")
        return

    st.subheader("Vacancy Assumptions")
    st.caption(
        "Update budgeted vs scenario start dates for each vacancy to test timing impacts."
    )

    if "vacancy_rows" not in st.session_state:
        st.session_state["vacancy_rows"] = _default_vacancy_rows(period_start.year)

    input_df = st.data_editor(
        st.session_state["vacancy_rows"],
        num_rows="dynamic",
        use_container_width=True,
        key="vacancy_editor",
        column_config={
            "Vacancy": st.column_config.TextColumn(required=True),
            "Annual Salary": st.column_config.NumberColumn(min_value=0, step=1_000),
            "On-cost Rate": st.column_config.NumberColumn(
                min_value=0.0, max_value=2.0, step=0.01, format="%.2f"
            ),
            "Budgeted Start": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Scenario Start": st.column_config.DateColumn(format="YYYY-MM-DD"),
        },
    )
    st.session_state["vacancy_rows"] = input_df

    if input_df.empty:
        st.info("Add at least one vacancy row to run the model.")
        return

    result_df, validation_issues = _build_result_rows(input_df, period_start, period_end)

    if validation_issues:
        st.warning("Some rows were skipped due to validation issues:")
        for issue in validation_issues:
            st.write(f"- {issue}")

    if result_df.empty:
        st.info("No valid vacancy rows are available to model.")
        return

    totals = result_df[["Budgeted Cost", "Scenario Cost", "Variance"]].sum()
    scenario_vs_budget = float(totals["Scenario Cost"] - annual_budget)

    st.subheader("Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Budget", format_currency(annual_budget))
    m2.metric("Budgeted Vacancy Cost", format_currency(float(totals["Budgeted Cost"])))
    m3.metric("Scenario Vacancy Cost", format_currency(float(totals["Scenario Cost"])))
    m4.metric(
        "Scenario vs Budget",
        format_currency(scenario_vs_budget),
        delta=format_currency(float(totals["Variance"])),
        delta_color="inverse",
    )

    st.caption(
        "Delta above is Scenario vs Budgeted Vacancy Plan (negative means scenario saves money)."
    )

    st.subheader("Vacancy-Level Variance")
    display_df = result_df.copy()
    display_df["Budgeted Cost"] = display_df["Budgeted Cost"].map(format_currency)
    display_df["Scenario Cost"] = display_df["Scenario Cost"].map(format_currency)
    display_df["Variance"] = display_df["Variance"].map(format_currency)
    display_df["Variance %"] = (result_df["Variance %"] * 100).map(lambda x: f"{x:.1f}%")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
