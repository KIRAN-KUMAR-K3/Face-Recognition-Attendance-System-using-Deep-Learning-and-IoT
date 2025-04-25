import streamlit as st
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
from face_recognition_utils import FaceRecognitionUtils
from telegram_utils import TelegramBot

# Set page configuration
st.set_page_config(
    page_title="Take Attendance - Alva's Attendance System",
    page_icon="📷",
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

# Session state check
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login to access this page.")
    st.stop()

# Initialize session state for attendance
if 'recognized_students' not in st.session_state:
    st.session_state.recognized_students = set()

if 'attendance_df' not in st.session_state:
    st.session_state.attendance_df = pd.DataFrame()

if 'capture_active' not in st.session_state:
    st.session_state.capture_active = False

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
    
    # Subject selection
    st.markdown("### Class Information")
    
    # Get all subjects
    all_subjects = db.get_subjects()
    
    # If not admin, filter subjects by faculty name
    if not st.session_state.is_admin:
        faculty_subjects = [s for s in all_subjects if s.get("faculty_name") == st.session_state.faculty_name]
        subjects = faculty_subjects
        if not subjects:
            st.warning(f"No subjects assigned to you ({st.session_state.faculty_name}). Please contact an administrator.")
    else:
        subjects = all_subjects
    
    subject_options = [(s["id"], f"{s['subject_name']} ({s['subject_code']})") for s in subjects]
    
    if subject_options:
        selected_subject_id = st.selectbox(
            "Select Subject",
            options=[s[0] for s in subject_options],
            format_func=lambda x: next((s[1] for s in subject_options if s[0] == x), ""),
            key="take_attendance_subject"
        )
    else:
        st.error("No subjects found. Please add subjects in the settings.")
        selected_subject_id = None
    
    # Attendance threshold
    threshold = db.get_setting("attendance_threshold")
    if threshold is None:
        threshold = "0.6"
    
    recognition_threshold = st.slider(
        "Recognition Threshold",
        min_value=0.1,
        max_value=1.0,
        value=float(threshold),
        step=0.05,
        help="Lower values are more permissive, higher values are more strict."
    )
    
    # Update the threshold setting
    if float(threshold) != recognition_threshold:
        db.update_setting("attendance_threshold", str(recognition_threshold))
    
    # Display teacher image
    st.markdown("---")
    st.image("https://images.unsplash.com/photo-1511629091441-ee46146481b6", 
            caption="Faculty",
            use_container_width=True)

# Main content
st.title("Take Attendance")
st.write("Use face recognition to take attendance for your class.")

# Stats display
if selected_subject_id:
    subject = db.get_subject(selected_subject_id)
    if subject:
        st.markdown(f"### Subject: {subject['subject_name']} ({subject['subject_code']})")
        
        # Display attendance stats
        stats = db.get_attendance_stats(date_filter=date.today().isoformat(), subject_id=selected_subject_id)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Present", stats['present'])
        with col2:
            st.metric("Absent", stats['absent'])
        with col3:
            st.metric("Total", stats['total'])

# Attendance mode selection
attendance_mode = st.radio("Select Attendance Mode", ["Webcam", "Upload Image"])

if attendance_mode == "Webcam":
    # Webcam capture mode
    st.markdown("### Webcam Attendance")
    
    # Start/Stop button
    if not st.session_state.capture_active:
        if st.button("Start Capturing", key="start_webcam"):
            st.session_state.capture_active = True
            st.session_state.recognized_students = set()
            st.session_state.attendance_df = pd.DataFrame()
            st.rerun()
    else:
        if st.button("Stop Capturing", key="stop_webcam"):
            st.session_state.capture_active = False
            st.rerun()
    
    # Display webcam feed when active
    if st.session_state.capture_active:
        if not selected_subject_id:
            st.error("Please select a subject before taking attendance.")
            st.session_state.capture_active = False
            st.rerun()
        
        # Create a placeholder for the video feed
        video_placeholder = st.empty()
        info_placeholder = st.empty()
        
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("Could not open webcam. Please make sure your webcam is connected and not being used by another application.")
            st.session_state.capture_active = False
            st.rerun()
        
        try:
            # Keep capturing until the user stops
            while st.session_state.capture_active:
                # Capture frame-by-frame
                ret, frame = cap.read()
                
                if not ret:
                    st.error("Could not read from webcam. Please try again.")
                    break
                
                # Process frame for face recognition
                face_locations, face_names, face_ids = face_utils.recognize_faces(frame, tolerance=recognition_threshold)
                
                # Draw boxes and names
                output_frame = face_utils.draw_faces(frame, face_locations, face_names)
                
                # Convert to RGB for display
                output_rgb = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
                
                # Display the frame
                video_placeholder.image(output_rgb, channels="RGB", use_container_width=True)
                
                # Update recognized students
                for face_id, face_name in zip(face_ids, face_names):
                    if face_id and face_id not in st.session_state.recognized_students:
                        # Mark attendance for this student
                        success, message = db.mark_attendance(face_id, selected_subject_id, "present", False)
                        if success:
                            st.session_state.recognized_students.add(face_id)
                            # Get student details
                            student = db.get_student(face_id)
                            info_placeholder.success(f"✅ Attendance marked for {student['name']} ({student['roll_no']})")
                
                # Wait a bit before the next frame
                time.sleep(0.1)
                
                # Check if the stop button has been pressed
                if not st.session_state.capture_active:
                    break
        
        finally:
            # Release the webcam
            cap.release()
            
            # Reload the attendance data
            attendance_df = db.get_attendance(date_filter=date.today().isoformat(), subject_id=selected_subject_id)
            st.session_state.attendance_df = attendance_df
    
    # Display recognized students
    if len(st.session_state.recognized_students) > 0:
        st.markdown("### Recognized Students")
        
        # Filter attendance for today and the selected subject
        attendance_df = db.get_attendance(date_filter=date.today().isoformat(), subject_id=selected_subject_id)
        
        if not attendance_df.empty:
            # Display the attendance data
            st.dataframe(attendance_df[["roll_no", "student_name", "status", "time", "synced"]], use_container_width=True)
            
            # Sync with Telegram
            if st.button("Send Attendance Report to Telegram"):
                with st.spinner("Sending attendance report..."):
                    success, message = telegram_bot.send_attendance_report(attendance_df)
                    if success:
                        st.success("Attendance report sent successfully.")
                    else:
                        st.error(f"Error sending attendance report: {message}")

elif attendance_mode == "Upload Image":
    # Image upload mode
    st.markdown("### Upload Class Image")
    
    uploaded_file = st.file_uploader("Upload a class photo to take attendance", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        if not selected_subject_id:
            st.error("Please select a subject before taking attendance.")
        else:
            # Process the uploaded image
            image_bytes = uploaded_file.getvalue()
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Process for face recognition
            face_locations, face_names, face_ids = face_utils.recognize_faces(image, tolerance=recognition_threshold)
            
            # Draw boxes and names
            output_image = face_utils.draw_faces(image, face_locations, face_names)
            
            # Convert to RGB for display
            output_rgb = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
            
            # Display the processed image
            st.image(output_rgb, caption="Processed Image", use_container_width=True)
            
            # Mark attendance for recognized students
            st.markdown("### Recognition Results")
            
            recognized_count = 0
            unknown_count = 0
            
            for face_id, face_name in zip(face_ids, face_names):
                if face_id:
                    # Mark attendance for this student
                    success, message = db.mark_attendance(face_id, selected_subject_id, "present", False)
                    if success:
                        recognized_count += 1
                else:
                    unknown_count += 1
            
            # Display summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Recognized Students", recognized_count)
            with col2:
                st.metric("Unknown Faces", unknown_count)
            
            # Show attendance data
            attendance_df = db.get_attendance(date_filter=date.today().isoformat(), subject_id=selected_subject_id)
            
            if not attendance_df.empty:
                st.markdown("### Attendance Data")
                st.dataframe(attendance_df[["roll_no", "student_name", "status", "time", "synced"]], use_container_width=True)
                
                # Sync with Telegram
                if st.button("Send Attendance Report to Telegram"):
                    with st.spinner("Sending attendance report..."):
                        success, message = telegram_bot.send_attendance_report(attendance_df)
                        if success:
                            st.success("Attendance report sent successfully.")
                        else:
                            st.error(f"Error sending attendance report: {message}")

# Display student gallery at the bottom
st.markdown("---")
st.markdown("### Student Gallery")

# Display a gallery of sample student images
gallery_cols = st.columns(4)
student_images = [
    "https://images.unsplash.com/photo-1460518451285-97b6aa326961",
    "https://images.unsplash.com/photo-1494883759339-0b042055a4ee",
    "https://images.unsplash.com/photo-1473492201326-7c01dd2e596b",
    "https://images.unsplash.com/photo-1598981457915-aea220950616"
]

for i, col in enumerate(gallery_cols):
    if i < len(student_images):
        col.image(student_images[i], use_container_width=True)
