
"""EduPulse AI — Student Performance and Institutional Analytics."""

import streamlit as st

from src.analytics.kpis import calculate_overall_kpis
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
    "Explore academic performance and attendance using validated student data."
)

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

st.markdown("### Institutional analytics")

# Filters are defined before KPI calculations so all metrics use
# the same selected subset of records.
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


if filtered_data.empty:
    st.warning(
        "No student records match the selected filters. "
        "Choose at least one department and one semester."
    )

else:
    # All headline metrics now reflect the same filtered records.
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

    st.markdown("### Attendance monitoring")

    st.metric(
        "Students below attendance threshold",
        kpis["low_attendance_count"],
    )

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

    with st.expander("View filtered student records"):
        st.dataframe(
            filtered_data,
            use_container_width=True,
            hide_index=True,
        )


st.caption(
    "Pass rate uses final_score >= 40. Low attendance means below 75%. "
    "These are configurable project assumptions, not universal policies."
)
