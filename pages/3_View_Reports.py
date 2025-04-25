import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import io
import base64

# Import custom modules
from database import Database
from report_generator import ReportGenerator

# Set page configuration
st.set_page_config(
    page_title="View Reports - Alva's Attendance System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# Initialize report generator
@st.cache_resource
def get_report_generator():
    return ReportGenerator()

report_generator = get_report_generator()

# Session state check
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login to access this page.")
    st.stop()

# Sidebar
with st.sidebar:
    st.image("assets/alvas_logo.svg", width=150)
    st.write(f"Welcome, **{st.session_state.faculty_name}**!")
    st.markdown("---")
    
    # Navigation
    st.markdown("### Navigation")
    st.page_link("app.py", label="🏠 Home", icon="🏠")
    st.page_link("pages/1_Student_Enrollment.py", label="Student Enrollment", icon="👤")
    st.page_link("pages/2_Take_Attendance.py", label="Take Attendance", icon="📷")
    st.page_link("pages/3_View_Reports.py", label="View Reports", icon="📊")
    st.page_link("pages/4_Settings.py", label="Settings", icon="⚙️")
    
    # Filters
    st.markdown("### Report Filters")
    
    # Date range options
    date_options = [
        "Today",
        "Yesterday",
        "Last 7 Days",
        "Last 30 Days",
        "This Month",
        "Custom Range"
    ]
    
    date_range = st.selectbox("Date Range", date_options)
    
    # Custom date range
    custom_start_date = None
    custom_end_date = None
    
    if date_range == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            custom_start_date = st.date_input("Start Date", date.today() - timedelta(days=7))
        with col2:
            custom_end_date = st.date_input("End Date", date.today())
    
    # Subject selection
    all_subjects = db.get_subjects()
    
    # If not admin, filter subjects by faculty name
    if not st.session_state.is_admin:
        faculty_subjects = [s for s in all_subjects if s.get("faculty_name") == st.session_state.faculty_name]
        subjects = faculty_subjects
        if not subjects:
            st.warning(f"No subjects assigned to you ({st.session_state.faculty_name}). Please contact an administrator.")
    else:
        subjects = all_subjects
    
    subject_options = [(0, "All Subjects")] + [(s["id"], f"{s['subject_name']} ({s['subject_code']})") for s in subjects]
    
    selected_subject_id = st.selectbox(
        "Subject",
        options=[s[0] for s in subject_options],
        format_func=lambda x: next((s[1] for s in subject_options if s[0] == x), ""),
        key="report_subject"
    )
    
    if selected_subject_id == 0:
        selected_subject_id = None
    
    # Branch, Semester, Section filters
    branch_options = ["All"] + ["CSE", "ECE", "EEE", "ME", "CE", "ISE"]
    selected_branch = st.selectbox("Branch", branch_options)
    
    semester_options = ["All"] + list(range(1, 9))
    selected_semester = st.selectbox("Semester", semester_options)
    
    section_options = ["All"] + ["A", "B", "C", "D"]
    selected_section = st.selectbox("Section", section_options)
    
    # Convert "All" to None for filtering
    branch_filter = None if selected_branch == "All" else selected_branch
    semester_filter = None if selected_semester == "All" else selected_semester
    section_filter = None if selected_section == "All" else selected_section
    
    # Display college image
    st.markdown("---")
    st.image("https://images.unsplash.com/photo-1602133187081-4874fdbd555c", 
            caption="Faculty",
            use_container_width=True)

# Main content
st.title("Attendance Reports")
st.write("View and analyze attendance data with detailed reports.")

# Determine date filter based on selection
date_filter = None

if date_range == "Today":
    date_filter = date.today().isoformat()
    st.subheader(f"Attendance Report for {date.today().strftime('%B %d, %Y')}")
elif date_range == "Yesterday":
    date_filter = (date.today() - timedelta(days=1)).isoformat()
    st.subheader(f"Attendance Report for {(date.today() - timedelta(days=1)).strftime('%B %d, %Y')}")
elif date_range == "Custom Range":
    if custom_start_date and custom_end_date:
        if custom_start_date > custom_end_date:
            st.error("Start date cannot be after end date.")
        else:
            st.subheader(f"Attendance Report from {custom_start_date.strftime('%B %d, %Y')} to {custom_end_date.strftime('%B %d, %Y')}")
else:
    if date_range == "Last 7 Days":
        st.subheader(f"Attendance Report for the Last 7 Days")
    elif date_range == "Last 30 Days":
        st.subheader(f"Attendance Report for the Last 30 Days")
    elif date_range == "This Month":
        st.subheader(f"Attendance Report for {date.today().strftime('%B %Y')}")

# Fetch attendance data based on filters
attendance_df = None

if date_range == "Custom Range" and custom_start_date and custom_end_date and custom_start_date <= custom_end_date:
    # For custom date range, we need to fetch data for each date and concatenate
    all_data = []
    current_date = custom_start_date
    
    while current_date <= custom_end_date:
        # Get data for this date
        day_data = db.get_attendance(
            date_filter=current_date.isoformat(),
            subject_id=selected_subject_id,
            branch=branch_filter,
            semester=semester_filter,
            section=section_filter
        )
        
        if not day_data.empty:
            all_data.append(day_data)
        
        # Move to the next day
        current_date += timedelta(days=1)
    
    if all_data:
        attendance_df = pd.concat(all_data, ignore_index=True)
    else:
        attendance_df = pd.DataFrame()
else:
    # For other date ranges, we can directly filter by the specific date
    attendance_df = db.get_attendance(
        date_filter=date_filter,
        subject_id=selected_subject_id,
        branch=branch_filter,
        semester=semester_filter,
        section=section_filter
    )

# Display attendance data if available
if attendance_df is not None and not attendance_df.empty:
    # Summary statistics
    total_records = len(attendance_df)
    present_count = len(attendance_df[attendance_df["status"] == "present"])
    absent_count = len(attendance_df[attendance_df["status"] == "absent"])
    presence_rate = round(present_count / total_records * 100, 2) if total_records > 0 else 0
    
    # Display summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", total_records)
    
    with col2:
        st.metric("Present", present_count)
    
    with col3:
        st.metric("Absent", absent_count)
    
    with col4:
        st.metric("Presence Rate", f"{presence_rate}%")
    
    # Display attendance data table
    st.markdown("### Attendance Records")
    st.dataframe(
        attendance_df[["date", "time", "roll_no", "student_name", "status", "subject_name", "branch", "semester", "section"]], 
        use_container_width=True,
        column_config={
            "date": "Date",
            "time": "Time",
            "roll_no": "Roll No",
            "student_name": "Student Name",
            "status": "Status",
            "subject_name": "Subject",
            "branch": "Branch",
            "semester": "Semester",
            "section": "Section"
        }
    )
    
    # Export options
    st.markdown("### Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Generate CSV
        csv_data, error = report_generator.generate_csv(attendance_df)
        
        if csv_data and not error:
            st.download_button(
                label="Download CSV Report",
                data=csv_data,
                file_name=f"attendance_report_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.error(f"Failed to generate CSV: {error}")
    
    with col2:
        # Generate PDF
        pdf_data, error = report_generator.generate_pdf(attendance_df)
        
        if pdf_data and not error:
            st.download_button(
                label="Download PDF Report",
                data=pdf_data,
                file_name=f"attendance_report_{date.today().isoformat()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error(f"Failed to generate PDF: {error}")
    
    # Visualizations
    st.markdown("### Attendance Analysis")
    
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Attendance by Day", "Attendance by Subject", "Attendance by Branch"])
    
    with viz_tab1:
        # Attendance by day visualization
        if "date" in attendance_df.columns:
            # Group by date and count present/absent
            date_grouped = attendance_df.groupby(["date", "status"]).size().unstack().fillna(0)
            
            if not date_grouped.empty and "present" in date_grouped.columns:
                # Calculate attendance percentage
                if "absent" not in date_grouped.columns:
                    date_grouped["absent"] = 0
                
                date_grouped["total"] = date_grouped["present"] + date_grouped["absent"]
                date_grouped["percentage"] = (date_grouped["present"] / date_grouped["total"] * 100).round(2)
                
                # Create a figure with two subplots
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})
                
                # Plot bar chart for present/absent
                date_grouped[["present", "absent"]].plot(kind="bar", stacked=True, ax=ax1, 
                                                      color=["#1E88E5", "#EF5350"])
                ax1.set_title("Daily Attendance Count")
                ax1.set_xlabel("")
                ax1.set_ylabel("Number of Students")
                ax1.legend(["Present", "Absent"])
                
                # Plot line chart for percentage
                date_grouped["percentage"].plot(kind="line", marker="o", ax=ax2, color="#4CAF50")
                ax2.set_title("Daily Attendance Percentage")
                ax2.set_xlabel("Date")
                ax2.set_ylabel("Percentage (%)")
                ax2.set_ylim(0, 100)
                ax2.grid(True, linestyle="--", alpha=0.7)
                
                # Adjust layout
                plt.tight_layout()
                
                # Display the plot
                st.pyplot(fig)
            else:
                st.info("Not enough data to visualize attendance by day.")
        else:
            st.info("Date information not available in the data.")
    
    with viz_tab2:
        # Attendance by subject visualization
        if "subject_name" in attendance_df.columns:
            # Group by subject and count present/absent
            subject_grouped = attendance_df.groupby(["subject_name", "status"]).size().unstack().fillna(0)
            
            if not subject_grouped.empty and "present" in subject_grouped.columns:
                # Calculate attendance percentage
                if "absent" not in subject_grouped.columns:
                    subject_grouped["absent"] = 0
                
                subject_grouped["total"] = subject_grouped["present"] + subject_grouped["absent"]
                subject_grouped["percentage"] = (subject_grouped["present"] / subject_grouped["total"] * 100).round(2)
                
                # Create a figure
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Sort by percentage
                subject_grouped = subject_grouped.sort_values("percentage", ascending=False)
                
                # Create a horizontal bar chart
                bars = ax.barh(subject_grouped.index, subject_grouped["percentage"], color="#1E88E5")
                
                # Add percentage labels
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                          f"{width:.1f}%", va="center")
                
                ax.set_title("Attendance Percentage by Subject")
                ax.set_xlabel("Percentage (%)")
                ax.set_xlim(0, 100)
                ax.grid(True, linestyle="--", alpha=0.7, axis="x")
                
                # Adjust layout
                plt.tight_layout()
                
                # Display the plot
                st.pyplot(fig)
            else:
                st.info("Not enough data to visualize attendance by subject.")
        else:
            st.info("Subject information not available in the data.")
    
    with viz_tab3:
        # Attendance by branch visualization
        if "branch" in attendance_df.columns:
            # Group by branch and count present/absent
            branch_grouped = attendance_df.groupby(["branch", "status"]).size().unstack().fillna(0)
            
            if not branch_grouped.empty and "present" in branch_grouped.columns:
                # Calculate attendance percentage
                if "absent" not in branch_grouped.columns:
                    branch_grouped["absent"] = 0
                
                branch_grouped["total"] = branch_grouped["present"] + branch_grouped["absent"]
                branch_grouped["percentage"] = (branch_grouped["present"] / branch_grouped["total"] * 100).round(2)
                
                # Create a figure
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Create a pie chart
                ax.pie(branch_grouped["percentage"], labels=branch_grouped.index, autopct="%1.1f%%",
                     startangle=90, shadow=False, wedgeprops={"edgecolor": "w"})
                
                ax.set_title("Attendance Percentage by Branch")
                
                # Equal aspect ratio ensures that pie is drawn as a circle
                ax.axis("equal")
                
                # Display the plot
                st.pyplot(fig)
            else:
                st.info("Not enough data to visualize attendance by branch.")
        else:
            st.info("Branch information not available in the data.")
else:
    st.info("No attendance data found for the selected filters.")

# Additional analysis section
st.markdown("---")
st.subheader("Additional Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Attendance Trends")
    st.markdown("""
    Analyze long-term attendance patterns to identify:
    - Days with high absenteeism
    - Subjects with low attendance
    - Students requiring attention
    
    Regular monitoring helps improve overall attendance rates and identifies areas needing intervention.
    """)
    
    st.image("https://images.unsplash.com/photo-1460518451285-97b6aa326961", 
            caption="Student Engagement",
            use_container_width=True)

with col2:
    st.markdown("### Recommendations")
    st.markdown("""
    Based on attendance analysis:
    
    1. **Follow-up with absent students** - Reach out to students with consistently low attendance
    2. **Evaluate challenging subjects** - Identify subjects with lower attendance for curriculum review
    3. **Recognize high performers** - Acknowledge students with excellent attendance records
    4. **Schedule optimization** - Analyze attendance patterns by day/time to optimize class scheduling
    """)
    
    st.image("https://images.unsplash.com/photo-1494883759339-0b042055a4ee", 
            caption="Student Success",
            use_container_width=True)
