
"""EduPulse AI — Student Performance and Institutional Analytics."""

import streamlit as st

from src.analytics.department_risk import calculate_department_risk
from src.analytics.kpis import calculate_overall_kpis
from src.analytics.risk import identify_student_risks
from src.components.charts import (
    show_attendance_vs_performance,
    show_department_comparison,
    show_semester_performance,
)
from src.data.loader import load_sample_student_data, load_student_csv


st.set_page_config(
    page_title="EduPulse AI",
    page_icon="🎓",
    layout="wide",
)

st.title("EduPulse AI")
st.subheader("Student Performance & Institutional Analytics")
st.caption(
    "Explore academic performance, attendance, and rule-based "
    "student support indicators using validated student data."
)

# -------------------------------------------------------------------
# Sidebar: data source configuration
# -------------------------------------------------------------------

with st.sidebar:
    st.header("Data source")

    data_source = st.radio(
        "Choose your data source",
        ("Synthetic sample data", "Upload CSV"),
    )

    if data_source == "Synthetic sample data":
        num_students = st.slider(
            "Number of synthetic students",
            min_value=10,
            max_value=1000,
            value=200,
            step=10,
        )

        seed = st.number_input(
            "Random seed",
            min_value=0,
            max_value=1_000_000,
            value=42,
            step=1,
        )

        uploaded_file = None

    else:
        uploaded_file = st.file_uploader(
            "Upload a student CSV file",
            type=["csv"],
            help="The file must contain all required student columns.",
        )


# -------------------------------------------------------------------
# Load and validate data
# -------------------------------------------------------------------

try:
    if data_source == "Synthetic sample data":
        student_data = load_sample_student_data(
            num_students=num_students,
            seed=int(seed),
        )
    else:
        if uploaded_file is None:
            st.info("Upload a CSV file in the sidebar to view your analytics.")
            st.stop()

        student_data = load_student_csv(uploaded_file)

except ValueError as exc:
    st.error(f"Unable to load student data: {exc}")
    st.stop()


st.success(f"Successfully loaded {len(student_data)} student records.")

# -------------------------------------------------------------------
# Filters
# -------------------------------------------------------------------

st.markdown("### Institutional analytics")

filter_col1, filter_col2 = st.columns(2)

departments = sorted(student_data["department"].unique().tolist())
semesters = sorted(student_data["semester"].unique().tolist())

with filter_col1:
    selected_departments = st.multiselect(
        "Filter by department",
        options=departments,
        default=departments,
    )

with filter_col2:
    selected_semesters = st.multiselect(
        "Filter by semester",
        options=semesters,
        default=semesters,
        format_func=lambda value: f"Semester {value}",
    )

filtered_data = student_data.loc[
    student_data["department"].isin(selected_departments)
    & student_data["semester"].isin(selected_semesters)
].copy()


# -------------------------------------------------------------------
# Analytics dashboard
# -------------------------------------------------------------------

if filtered_data.empty:
    st.warning(
        "No student records match the selected filters. "
        "Choose at least one department and one semester."
    )

else:
    # ---------------------------------------------------------------
    # Cohort KPIs
    # ---------------------------------------------------------------

    kpis = calculate_overall_kpis(filtered_data)

    st.caption(
        f"Showing {kpis['total_students']:,} matching student records."
    )

    st.markdown("### Cohort overview")

    metric_columns = st.columns(4)

    metric_columns[0].metric(
        "Total students",
        f"{kpis['total_students']:,}",
    )

    metric_columns[1].metric(
        "Average academic score",
        f"{kpis['average_academic_score']:.2f} / 100",
    )

    metric_columns[2].metric(
        "Average attendance",
        f"{kpis['average_attendance']:.2f}%",
    )

    metric_columns[3].metric(
        "Pass rate",
        f"{kpis['pass_rate']:.2f}%",
    )

    # ---------------------------------------------------------------
    # Attendance monitoring
    # ---------------------------------------------------------------

    st.markdown("### Attendance monitoring")

    st.metric(
        "Students below attendance threshold",
        kpis["low_attendance_count"],
    )

    # ---------------------------------------------------------------
    # Existing performance charts
    # ---------------------------------------------------------------

    chart_tab1, chart_tab2, chart_tab3 = st.tabs(
        [
            "Department comparison",
            "Semester performance",
            "Attendance vs. scores",
        ]
    )

    with chart_tab1:
        show_department_comparison(filtered_data)

    with chart_tab2:
        show_semester_performance(filtered_data)

    with chart_tab3:
        show_attendance_vs_performance(filtered_data)

    # ---------------------------------------------------------------
    # Department risk analytics
    # ---------------------------------------------------------------

    st.markdown("### Department risk analytics")

    department_risk = calculate_department_risk(filtered_data)

    st.caption(
        "Compare the percentage of students with at least one "
        "rule-based support indicator across departments. Results "
        "respect the selected department and semester filters."
    )

    chart_data = department_risk.set_index("department")[
        ["flagged_student_rate"]
    ]

    st.bar_chart(
        chart_data,
        x_label="Department",
        y_label="Students with support indicators (%)",
    )

    with st.expander("View department risk breakdown", expanded=True):
        display_department_risk = department_risk.round(
            {
                "flagged_student_rate": 2,
                "low_attendance_rate": 2,
                "low_final_score_rate": 2,
                "low_average_score_rate": 2,
            }
        )

        st.dataframe(
            display_department_risk,
            use_container_width=True,
            hide_index=True,
        )

    # ---------------------------------------------------------------
    # Student support insights
    # ---------------------------------------------------------------

    st.markdown("### Student support insights")

    risk_data = identify_student_risks(filtered_data)

    flagged_data = risk_data.loc[
        risk_data["risk_indicator_count"] > 0
    ].copy()

    support_col1, support_col2 = st.columns(2)

    with support_col1:
        st.metric(
            "Students with support indicators",
            len(flagged_data),
        )

    with support_col2:
        st.metric(
            "Students with multiple indicators",
            int((risk_data["risk_indicator_count"] >= 2).sum()),
        )

    st.caption(
        "These indicators highlight records for human review. "
        "They are rule-based flags, not predictions or diagnoses."
    )

    priority_options = [
        "All students",
        "Flagged students only",
        "Consider support",
        "Support recommended",
        "Multiple support indicators",
        "No rule-based flag",
    ]

    selected_priority = st.selectbox(
        "Filter student support records",
        options=priority_options,
        index=1,
    )

    if selected_priority == "All students":
        displayed_risk_data = risk_data.copy()

    elif selected_priority == "Flagged students only":
        displayed_risk_data = flagged_data.copy()

    else:
        displayed_risk_data = risk_data.loc[
            risk_data["support_priority"] == selected_priority
        ].copy()

    support_columns = [
        "student_id",
        "student_name",
        "department",
        "semester",
        "average_academic_score",
        "attendance_percentage",
        "final_score",
        "support_priority",
        "support_reasons",
    ]

    st.dataframe(
        displayed_risk_data[support_columns].round(
            {"average_academic_score": 2}
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ---------------------------------------------------------------
    # Complete filtered records
    # ---------------------------------------------------------------

    with st.expander("View filtered student records"):
        st.dataframe(
            filtered_data,
            use_container_width=True,
            hide_index=True,
        )


# -------------------------------------------------------------------
# Methodology note
# -------------------------------------------------------------------

st.caption(
    "Project assumptions: pass mark = 40, low attendance = below 75%, "
    "and low average academic score = below 50. These are configurable "
    "rules, not universal institutional policies. Support indicators "
    "should be reviewed by appropriate staff before any action."
)
