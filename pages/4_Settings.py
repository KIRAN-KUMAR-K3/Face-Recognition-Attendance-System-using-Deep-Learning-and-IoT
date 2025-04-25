import streamlit as st
import os
import pandas as pd
from datetime import datetime

# Import custom modules
from database import Database
from telegram_utils import TelegramBot
from face_recognition_utils import FaceRecognitionUtils

# Set page configuration
st.set_page_config(
    page_title="Settings - Alva's Attendance System",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# Initialize Telegram bot
@st.cache_resource
def get_telegram_bot():
    return TelegramBot()

telegram_bot = get_telegram_bot()

# Initialize face recognition utilities
@st.cache_resource
def get_face_utils():
    return FaceRecognitionUtils()

face_utils = get_face_utils()

# Session state check
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login to access this page.")
    st.stop()

# Admin check for sensitive settings
is_admin = st.session_state.is_admin

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
    
    # Display college image
    st.markdown("---")
    st.image("https://images.unsplash.com/photo-1728206348193-9b5ae74a7d32", 
            caption="Alva's Institute",
            use_container_width=True)

# Main content
st.title("System Settings")
st.write("Configure the attendance system settings.")

# Settings tabs
tab1, tab2, tab3, tab4 = st.tabs(["General Settings", "Telegram Integration", "Subject Management", "System Info"])

# Tab 1: General Settings
with tab1:
    st.header("General Settings")
    
    # Recognition threshold
    threshold = db.get_setting("attendance_threshold")
    if threshold is None:
        threshold = "0.6"
    
    recognition_threshold = st.slider(
        "Face Recognition Threshold",
        min_value=0.1,
        max_value=1.0,
        value=float(threshold),
        step=0.05,
        help="Lower values are more permissive, higher values are more strict."
    )
    
    if st.button("Save General Settings"):
        db.update_setting("attendance_threshold", str(recognition_threshold))
        st.success("Settings saved successfully.")
    
    # Admin settings
    if is_admin:
        st.markdown("---")
        st.subheader("Administrator Settings")
        
        with st.form("admin_settings"):
            admin_password = db.get_setting("admin_password")
            new_admin_password = st.text_input("Change Admin Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submit_button = st.form_submit_button("Update Admin Password")
            
            if submit_button:
                if new_admin_password != confirm_password:
                    st.error("Passwords do not match.")
                elif not new_admin_password:
                    st.error("Password cannot be empty.")
                else:
                    db.update_setting("admin_password", new_admin_password)
                    st.success("Admin password updated successfully.")
    else:
        st.info("Additional settings are available for administrators.")

# Tab 2: Telegram Integration
with tab2:
    st.header("Telegram Integration")
    st.write("Configure Telegram bot for attendance notifications.")
    
    # Get current settings
    bot_token = db.get_setting("telegram_bot_token") or ""
    chat_id = db.get_setting("telegram_chat_id") or ""
    
    # Settings form
    with st.form("telegram_settings"):
        new_bot_token = st.text_input("Telegram Bot Token", value=bot_token, 
                                    help="Create a bot using BotFather on Telegram to get a token.")
        new_chat_id = st.text_input("Telegram Chat ID", value=chat_id,
                                  help="The ID of the chat (group/channel) where reports should be sent.")
        
        submit_button = st.form_submit_button("Save Telegram Settings")
        
        if submit_button:
            # Update settings
            telegram_bot.update_settings(new_bot_token, new_chat_id)
            st.success("Telegram settings updated successfully.")
    
    # Test connection
    if bot_token and chat_id:
        if st.button("Test Telegram Connection"):
            with st.spinner("Testing connection..."):
                success, message = telegram_bot.test_connection()
                if success:
                    st.success("Telegram connection successful! Check your Telegram for a test message.")
                else:
                    st.error(f"Telegram connection failed: {message}")
    
    # Telegram setup guide
    with st.expander("How to Set Up Telegram Integration"):
        st.markdown("""
        ### Step 1: Create a Telegram Bot
        1. Open Telegram and search for [@BotFather](https://t.me/botfather)
        2. Start a chat with BotFather and send `/newbot`
        3. Follow the instructions to name your bot
        4. Once created, you'll receive a token - copy this token
        
        ### Step 2: Create a Group (optional)
        1. Create a new group in Telegram
        2. Add your bot to the group
        3. Make the bot an administrator (for better functionality)
        
        ### Step 3: Get the Chat ID
        For a group:
        1. Add [@RawDataBot](https://t.me/rawdatabot) to your group
        2. The bot will send a message with group information
        3. Look for `"chat": {"id": -123456789}` and copy the number including the minus sign
        
        For direct messages to a user:
        1. Send a message to [@userinfobot](https://t.me/userinfobot)
        2. It will reply with your user ID
        
        ### Step 4: Enter the Details
        1. Paste the bot token and chat ID in the fields above
        2. Click "Save Telegram Settings"
        3. Test the connection
        """)

# Tab 3: Subject Management
with tab3:
    st.header("Subject Management")
    
    # Two columns layout
    col1, col2 = st.columns(2)
    
    # Column 1: Add new subject
    with col1:
        st.subheader("Add New Subject")
        
        with st.form("add_subject_form"):
            subject_code = st.text_input("Subject Code", 
                                    placeholder="18CS51",
                                    help="Official subject code from Alva's (e.g., 18CS51)")
            subject_name = st.text_input("Subject Name",
                                    placeholder="Management and Entrepreneurship")
            
            branch_options = ["CSE", "ECE", "EEE", "ME", "CE", "ISE"]
            branch = st.selectbox("Branch", branch_options)
            
            semester_options = list(range(1, 9))
            semester = st.selectbox("Semester", semester_options)
            
            # Only admins can assign subjects to any faculty
            if st.session_state.is_admin:
                faculty_name = st.text_input("Faculty Name",
                                       placeholder="Dr. Rajesh Kumar",
                                       help="Name of the faculty teaching this subject")
            else:
                # For non-admin faculty, automatically assign to themselves
                faculty_name = st.session_state.faculty_name
                st.info(f"Subject will be assigned to you: {faculty_name}")
            
            submit_button = st.form_submit_button("Add Subject")
            
            if submit_button:
                if not subject_code or not subject_name:
                    st.error("Subject Code and Name are required.")
                else:
                    # We need to modify the database.py add_subject function to accept faculty_name
                    # Since we've already added the column, we can directly use SQL to add the subject
                    try:
                        conn = db.connect()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO subjects (subject_code, subject_name, branch, semester, faculty_name) VALUES (?, ?, ?, ?, ?)",
                            (subject_code, subject_name, branch, semester, faculty_name)
                        )
                        conn.commit()
                        st.success(f"Successfully added subject: {subject_name} ({subject_code}) assigned to {faculty_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding subject: {str(e)}")
                    finally:
                        db.close()
    
    # Column 2: Manage subjects
    with col2:
        st.subheader("Manage Subjects")
        
        # Get all subjects
        subjects = db.get_subjects()
        
        if subjects:
            # Convert to dataframe for display
            subjects_df = pd.DataFrame(subjects)
            
            # Display subject table
            st.dataframe(
                subjects_df[["subject_code", "subject_name", "branch", "semester"]], 
                use_container_width=True,
                column_config={
                    "subject_code": "Code",
                    "subject_name": "Name",
                    "branch": "Branch",
                    "semester": "Semester"
                }
            )
            
            # Subject actions
            if is_admin:
                st.markdown("### Edit Subject")
                
                selected_subject_id = st.selectbox("Select Subject", 
                                               options=[s["id"] for s in subjects],
                                               format_func=lambda x: next((f"{s['subject_name']} ({s['subject_code']})" for s in subjects if s["id"] == x), ""))
                
                if selected_subject_id:
                    selected_subject = db.get_subject(selected_subject_id)
                    
                    if selected_subject:
                        with st.form("edit_subject_form"):
                            edit_code = st.text_input("Subject Code", value=selected_subject["subject_code"])
                            edit_name = st.text_input("Subject Name", value=selected_subject["subject_name"])
                            
                            branch_options = ["CSE", "ECE", "EEE", "ME", "CE", "ISE"]
                            edit_branch = st.selectbox("Branch", branch_options, 
                                                    index=branch_options.index(selected_subject["branch"]) if selected_subject["branch"] in branch_options else 0)
                            
                            semester_options = list(range(1, 9))
                            edit_semester = st.selectbox("Semester", semester_options, 
                                                      index=semester_options.index(selected_subject["semester"]) if selected_subject["semester"] in semester_options else 0)
                                                      
                            # Add faculty field
                            current_faculty = selected_subject.get("faculty_name", "")
                            edit_faculty = st.text_input("Faculty Name", 
                                                   value=current_faculty,
                                                   placeholder="Dr. Rajesh Kumar",
                                                   help="Name of the faculty teaching this subject")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                update_button = st.form_submit_button("Update Subject")
                            with col2:
                                delete_button = st.form_submit_button("Delete Subject", type="primary")
                            
                            if update_button:
                                try:
                                    conn = db.connect()
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "UPDATE subjects SET subject_code = ?, subject_name = ?, branch = ?, semester = ?, faculty_name = ? WHERE id = ?",
                                        (edit_code, edit_name, edit_branch, edit_semester, edit_faculty, selected_subject_id)
                                    )
                                    conn.commit()
                                    st.success(f"Successfully updated subject: {edit_name} ({edit_code}) assigned to {edit_faculty}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating subject: {str(e)}")
                                finally:
                                    db.close()
                            
                            if delete_button:
                                success, message = db.delete_subject(selected_subject_id)
                                
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
            else:
                st.info("You need administrator privileges to manage subjects. Please contact your administrator.")
        else:
            st.info("No subjects found. Add a new subject using the form on the left.")

# Tab 4: System Info
with tab4:
    st.header("System Information")
    
    # System stats
    col1, col2 = st.columns(2)
    
    with col1:
        # Face recognition info
        st.subheader("Face Recognition")
        
        # Count students with face encodings
        encodings_count = len(face_utils.known_face_encodings)
        total_students = len(db.get_students())
        
        st.metric("Enrolled Faces", f"{encodings_count}/{total_students}")
        
        # Recognition accuracy info
        threshold = float(db.get_setting("attendance_threshold") or 0.6)
        
        if threshold < 0.4:
            accuracy_level = "Low (more permissive)"
        elif threshold < 0.7:
            accuracy_level = "Medium (balanced)"
        else:
            accuracy_level = "High (more strict)"
        
        st.metric("Recognition Accuracy", accuracy_level)
        
        # Refresh face encodings
        if st.button("Refresh Face Encodings"):
            with st.spinner("Refreshing face encodings..."):
                count = face_utils.load_known_faces()
                st.success(f"Successfully loaded {count} face encodings.")
    
    with col2:
        # Database info
        st.subheader("Database Statistics")
        
        # Count records
        students_count = len(db.get_students())
        subjects_count = len(db.get_subjects())
        
        # Count attendance records
        attendance_df = db.get_attendance()
        attendance_count = len(attendance_df) if attendance_df is not None else 0
        
        st.metric("Students", students_count)
        st.metric("Subjects", subjects_count)
        st.metric("Attendance Records", attendance_count)
    
    # About the system
    st.markdown("---")
    st.subheader("About Alva's Face Recognition Attendance System")
    
    st.markdown("""
    This attendance system was developed for **Alva's Institute of Engineering and Technology** using state-of-the-art face recognition technology.
    
    ### Features:
    - Real-time face recognition using deep learning
    - Telegram integration for instant attendance reports
    - Comprehensive reporting and analytics
    - Student enrollment with face registration
    - Subject and class management
    - Offline operation with sync capability
    
    ### Technology Stack:
    - Streamlit (Web Interface)
    - face_recognition/dlib (Face Recognition)
    - OpenCV (Image Processing)
    - SQLite (Database)
    - Python Telegram Bot API (Notifications)
    
    ### Version: 1.0.0
    
    &copy; 2023 Alva's Institute of Engineering and Technology
    """)
    
    # Contact information
    st.markdown("---")
    st.markdown("""
    ### Contact Information
    
    For support or inquiries, please contact:
    
    **Alva's Institute of Engineering and Technology**  
    Shobhavana Campus, Mijar, Moodbidri  
    D.K, Karnataka - 574225
    
    Phone: +91 8258 262725, 26  
    Email: principal@aiet.org.in  
    Web: [aiet.org.in](https://www.aiet.org.in)
    """)
