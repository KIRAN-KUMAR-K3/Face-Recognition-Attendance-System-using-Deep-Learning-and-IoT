import streamlit as st
import os
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, date
from PIL import Image
# import face_recognition - temporarily disabled
import time
import io
import base64

# Import custom modules
from database import Database
from face_recognition_utils import FaceRecognitionUtils, capture_face_streamlit
from telegram_utils import TelegramBot
from report_generator import ReportGenerator

# Set page configuration
st.set_page_config(
    page_title="Alva's Face Recognition Attendance System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# Initialize face recognition utils
@st.cache_resource
def get_face_utils():
    return FaceRecognitionUtils()

face_utils = get_face_utils()

# Initialize Telegram bot
@st.cache_resource
def get_telegram_bot():
    return TelegramBot()

telegram_bot = get_telegram_bot()

# Initialize report generator
@st.cache_resource
def get_report_generator():
    return ReportGenerator()

report_generator = get_report_generator()

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'faculty_name' not in st.session_state:
    st.session_state.faculty_name = ""

if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Login function
def login(faculty_id, password):
    faculty = db.verify_credentials(faculty_id, password)
    if faculty:
        st.session_state.logged_in = True
        st.session_state.faculty_name = faculty['name']
        st.session_state.is_admin = faculty['is_admin']
        return True
    return False

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.faculty_name = ""
    st.session_state.is_admin = False
    st.rerun()

# Login page
def show_login_page():
    # College logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("assets/alvas_logo.svg", width=100)
    with col2:
        st.title("Alva's Face Recognition Attendance System")
        st.subheader("Faculty Login")
    
    # Login form
    with st.form("login_form"):
        faculty_id = st.text_input("Faculty ID")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button:
            if login(faculty_id, password):
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
    
    # About section
    st.markdown("---")
    st.subheader("About the System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        The **Face Recognition Attendance System** uses advanced AI technology to automate student attendance. 
        
        Key features:
        - Real-time face recognition
        - Telegram integration for instant reports
        - Comprehensive attendance analytics
        - Easy student enrollment
        - Offline mode support
        """)
    
    with col2:
        st.image("https://images.unsplash.com/photo-1498243691581-b145c3f54a5a", 
                caption="Alva's Institute of Engineering and Technology",
                use_container_width=True)

# Main application
def main():
    # Sidebar
    with st.sidebar:
        st.image("assets/alvas_logo.svg", width=150)
        st.write(f"Welcome, **{st.session_state.faculty_name}**!")
        st.markdown("---")
        
        st.markdown("### Quick Stats")
        stats = db.get_attendance_stats(date_filter=date.today().isoformat())
        
        # Display today's attendance stats
        st.metric("Today's Attendance", f"{stats['present']}/{stats['total']}")
        
        # Display attendance percentage
        attendance_pct = (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
        st.metric("Attendance Percentage", f"{attendance_pct:.1f}%")
        
        # Show sync status
        unsynced = db.get_unsynced_attendance()
        st.metric("Pending Sync", len(unsynced))
        
        # Sync button
        if len(unsynced) > 0:
            if st.button("Sync Now"):
                with st.spinner("Syncing attendance data..."):
                    success, message = telegram_bot.sync_pending_attendance()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        st.markdown("---")
        if st.button("Logout"):
            logout()

    # Home page content
    st.title("Alva's Face Recognition Attendance System")
    
    # Display today's date
    st.write(f"Today: {datetime.now().strftime('%A, %B %d, %Y')}")
    
    # Statistics cards in a row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div style='border-radius: 10px; background-color: #f0f2f6; padding: 20px; text-align: center;'>
                <h3>Present Students</h3>
                <h1 style='color: green;'>{}</h1>
            </div>
            """.format(stats['present']), 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div style='border-radius: 10px; background-color: #f0f2f6; padding: 20px; text-align: center;'>
                <h3>Absent Students</h3>
                <h1 style='color: red;'>{}</h1>
            </div>
            """.format(stats['absent']), 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div style='border-radius: 10px; background-color: #f0f2f6; padding: 20px; text-align: center;'>
                <h3>Total Students</h3>
                <h1>{}</h1>
            </div>
            """.format(stats['total']), 
            unsafe_allow_html=True
        )
    
    # Quick access buttons
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Take Attendance", use_container_width=True):
            switch_page("2_Take_Attendance")
    
    with col2:
        if st.button("Enroll Student", use_container_width=True):
            switch_page("1_Student_Enrollment")
    
    with col3:
        if st.button("View Reports", use_container_width=True):
            switch_page("3_View_Reports")
    
    # Recent attendance
    st.markdown("### Recent Attendance")
    
    # Get today's attendance
    today_attendance = db.get_attendance(date_filter=date.today().isoformat())
    
    if not today_attendance.empty:
        # Display the attendance data in a table
        st.dataframe(today_attendance[["roll_no", "student_name", "subject_name", "time", "status"]], use_container_width=True)
        
        # Add download buttons
        csv_data, _ = report_generator.generate_csv(today_attendance)
        pdf_data, _ = report_generator.generate_pdf(today_attendance, title="Today's Attendance Report")
        
        col1, col2 = st.columns(2)
        with col1:
            csv_b64 = base64.b64encode(csv_data.encode()).decode()
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"attendance_{date.today().isoformat()}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name=f"attendance_{date.today().isoformat()}.pdf",
                mime="application/pdf"
            )
    else:
        st.info("No attendance records for today. Use the 'Take Attendance' feature to record attendance.")
    
    # Campus images
    st.markdown("### Alva's Institute Campus")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image("https://images.unsplash.com/photo-1519452575417-564c1401ecc0", 
                caption="Campus View",
                use_container_width=True)
    
    with col2:
        st.image("https://images.unsplash.com/photo-1591123120675-6f7f1aae0e5b", 
                caption="Classroom",
                use_container_width=True)

# Helper function to switch pages
def switch_page(page_name):
    # Use st.page_link instead for newer Streamlit versions
    st.page_link(f"pages/{page_name}.py", label=page_name, use_container_width=True)
    st.rerun()

# Run the app
if __name__ == "__main__":
    if st.session_state.logged_in:
        main()
    else:
        show_login_page()
