import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
# import face_recognition - temporarily disabled
import time
import base64
import io

# Import custom modules
from database import Database
from face_recognition_utils import FaceRecognitionUtils, capture_face_streamlit

# Set page configuration
st.set_page_config(
    page_title="Student Enrollment - Alva's Attendance System",
    page_icon="👤",
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
    
    # Display college image
    st.markdown("---")
    st.image("https://images.unsplash.com/photo-1728206348193-9b5ae74a7d32", 
            caption="Alva's Institute",
            use_container_width=True)

# Main content
st.title("Student Enrollment")
st.write("Add new students or manage existing student records.")

# Tabs for enrollment options
tab1, tab2 = st.tabs(["Add New Student", "Manage Students"])

# Tab 1: Add New Student
with tab1:
    st.header("Add New Student")
    
    # Form for student details
    with st.form("enrollment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            roll_no = st.text_input("USN (e.g., 4AL22CS001)", 
                                key="enroll_roll", 
                                placeholder="4AL22CS001",
                                help="University Seat Number format: 4AL[YY][DEPT][NUMBER]")
            name = st.text_input("Student Name", key="enroll_name")
            email = st.text_input("Email", key="enroll_email")
        
        with col2:
            branch_options = ["CSE", "ECE", "EEE", "ME", "CE", "ISE"]
            branch = st.selectbox("Branch", branch_options, key="enroll_branch")
            
            semester_options = list(range(1, 9))
            semester = st.selectbox("Semester", semester_options, key="enroll_semester")
            
            section_options = ["A", "B", "C", "D"]
            section = st.selectbox("Section", section_options, key="enroll_section")
        
        st.markdown("### Face Image")
        image_source = st.radio("Select Image Source", ["Upload Image", "Capture from Webcam"])
        
        uploaded_file = None
        if image_source == "Upload Image":
            uploaded_file = st.file_uploader("Upload Student Image", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                image_bytes = uploaded_file.getvalue()
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Display the uploaded image
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                st.image(image_rgb, caption="Uploaded Image", use_container_width=True)
                
                # Check if a face is detected
                face_locations = face_utils.detect_faces(image)
                if not face_locations:
                    st.warning("No face detected in the uploaded image. Please upload a clear image with a face.")
                elif len(face_locations) > 1:
                    st.warning("Multiple faces detected. Please upload an image with a single face.")
        
        submit_button = st.form_submit_button("Enroll Student")
    
    # Handle form submission
    if submit_button:
        if not roll_no or not name:
            st.error("Roll Number and Student Name are required.")
        else:
            # Process the face image
            face_image = None
            face_encoding = None
            error_message = None
            
            if image_source == "Upload Image" and uploaded_file:
                image_bytes = uploaded_file.getvalue()
                nparr = np.frombuffer(image_bytes, np.uint8)
                face_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif image_source == "Capture from Webcam":
                face_image = capture_face_streamlit()
            
            if face_image is not None:
                # Get face encoding
                face_encoding, error = face_utils.get_face_encoding(face_image)
                
                if error:
                    st.error(error)
                else:
                    # Add student to database
                    success, result = db.add_student(roll_no, name, branch, semester, section, email, face_encoding)
                    
                    if success:
                        st.success(f"Successfully enrolled student: {name} ({roll_no})")
                        # Reload face encodings
                        face_utils.load_known_faces()
                        # Clear form
                        st.rerun()
                    else:
                        st.error(f"Error enrolling student: {result}")
            else:
                st.error("No face image provided. Please upload an image or capture from webcam.")

# Tab 2: Manage Students
with tab2:
    st.header("Manage Students")
    
    # Filters for student list
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_branch = st.selectbox("Filter by Branch", ["All"] + ["CSE", "ECE", "EEE", "ME", "CE", "ISE"])
    
    with col2:
        filter_semester = st.selectbox("Filter by Semester", ["All"] + list(range(1, 9)))
    
    with col3:
        filter_section = st.selectbox("Filter by Section", ["All"] + ["A", "B", "C", "D"])
    
    # Get students based on filters
    branch_filter = None if filter_branch == "All" else filter_branch
    semester_filter = None if filter_semester == "All" else filter_semester
    section_filter = None if filter_section == "All" else filter_section
    
    students = db.get_students(branch=branch_filter, semester=semester_filter, section=section_filter)
    
    if students:
        # Convert to dataframe for display
        students_df = pd.DataFrame(students)
        
        # Display student table with selection
        selected_indices = st.dataframe(
            students_df[["roll_no", "name", "branch", "semester", "section", "email"]], 
            use_container_width=True,
            column_config={
                "roll_no": "Roll No",
                "name": "Name",
                "branch": "Branch",
                "semester": "Semester",
                "section": "Section",
                "email": "Email"
            }
        )
        
        # Student details and actions
        if st.session_state.is_admin:
            st.subheader("Student Actions")
            
            selected_student_id = st.selectbox("Select Student", 
                                            options=[s["id"] for s in students],
                                            format_func=lambda x: next((f"{s['name']} ({s['roll_no']})" for s in students if s["id"] == x), ""))
            
            if selected_student_id:
                selected_student = db.get_student(selected_student_id)
                
                if selected_student:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Update Student")
                        
                        with st.form("update_form"):
                            roll_no = st.text_input("USN", 
                                                value=selected_student["roll_no"],
                                                placeholder="4AL22CS001",
                                                help="University Seat Number format: 4AL[YY][DEPT][NUMBER]")
                            name = st.text_input("Name", value=selected_student["name"])
                            email = st.text_input("Email", value=selected_student["email"] or "")
                            
                            branch_options = ["CSE", "ECE", "EEE", "ME", "CE", "ISE"]
                            branch = st.selectbox("Branch", branch_options, index=branch_options.index(selected_student["branch"]) if selected_student["branch"] in branch_options else 0)
                            
                            semester_options = list(range(1, 9))
                            semester = st.selectbox("Semester", semester_options, index=semester_options.index(selected_student["semester"]) if selected_student["semester"] in semester_options else 0)
                            
                            section_options = ["A", "B", "C", "D"]
                            section = st.selectbox("Section", section_options, index=section_options.index(selected_student["section"]) if selected_student["section"] in section_options else 0)
                            
                            update_button = st.form_submit_button("Update Student")
                            
                            if update_button:
                                success, message = db.update_student(selected_student_id, roll_no, name, branch, semester, section, email)
                                
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                    
                    with col2:
                        st.markdown("### Update Face Image")
                        
                        # Display current face image status
                        if selected_student["face_encoding"] is not None:
                            st.info("Face image is already registered. Updating will replace the existing image.")
                        else:
                            st.warning("No face image registered for this student.")
                        
                        # Options to add or update face image
                        image_source = st.radio("Select Image Source", ["Upload Image", "Capture from Webcam"], key="update_source")
                        
                        if image_source == "Upload Image":
                            uploaded_file = st.file_uploader("Upload Student Image", type=["jpg", "jpeg", "png"], key="update_upload")
                            
                            if uploaded_file:
                                # Process the uploaded image
                                image_bytes = uploaded_file.getvalue()
                                nparr = np.frombuffer(image_bytes, np.uint8)
                                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                                
                                # Display the uploaded image
                                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                                st.image(image_rgb, caption="Uploaded Image", use_container_width=True)
                                
                                # Check if a face is detected
                                face_locations = face_utils.detect_faces(image)
                                if not face_locations:
                                    st.warning("No face detected in the uploaded image.")
                                elif len(face_locations) > 1:
                                    st.warning("Multiple faces detected. Please upload an image with a single face.")
                                else:
                                    # Get face encoding
                                    face_encoding, error = face_utils.get_face_encoding(image)
                                    
                                    if error:
                                        st.error(error)
                                    else:
                                        if st.button("Update Face Image"):
                                            # Update student with new face encoding
                                            success, message = db.update_student(
                                                selected_student_id, 
                                                selected_student["roll_no"], 
                                                selected_student["name"], 
                                                selected_student["branch"], 
                                                selected_student["semester"], 
                                                selected_student["section"], 
                                                selected_student["email"], 
                                                face_encoding
                                            )
                                            
                                            if success:
                                                st.success("Face image updated successfully.")
                                                face_utils.load_known_faces()
                                            else:
                                                st.error(f"Error updating face image: {message}")
                        
                        elif image_source == "Capture from Webcam":
                            st.write("Click the button below to capture a face image.")
                            
                            if st.button("Capture Face Image"):
                                face_image = capture_face_streamlit()
                                
                                if face_image is not None:
                                    # Get face encoding
                                    face_encoding, error = face_utils.get_face_encoding(face_image)
                                    
                                    if error:
                                        st.error(error)
                                    else:
                                        # Update student with new face encoding
                                        success, message = db.update_student(
                                            selected_student_id, 
                                            selected_student["roll_no"], 
                                            selected_student["name"], 
                                            selected_student["branch"], 
                                            selected_student["semester"], 
                                            selected_student["section"], 
                                            selected_student["email"], 
                                            face_encoding
                                        )
                                        
                                        if success:
                                            st.success("Face image updated successfully.")
                                            face_utils.load_known_faces()
                                        else:
                                            st.error(f"Error updating face image: {message}")
                        
                        # Delete button (danger zone)
                        st.markdown("---")
                        st.markdown("### Danger Zone")
                        
                        if st.button("Delete Student", type="primary"):
                            # Confirm deletion
                            if st.checkbox("I understand this action cannot be undone."):
                                success, message = db.delete_student(selected_student_id)
                                
                                if success:
                                    st.success(message)
                                    face_utils.load_known_faces()
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting student: {message}")
        else:
            st.info("You need administrator privileges to manage students. Please contact your administrator.")
    else:
        st.info("No students found. Add new students using the 'Add New Student' tab.")

# Display sample student images at the bottom
st.markdown("---")
st.subheader("Sample Student Profiles")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.image("https://images.unsplash.com/photo-1516534775068-ba3e7458af70", caption="Student 1", use_container_width=True)

with col2:
    st.image("https://images.unsplash.com/photo-1503676382389-4809596d5290", caption="Student 2", use_container_width=True)

with col3:
    st.image("https://images.unsplash.com/photo-1530099486328-e021101a494a", caption="Student 3", use_container_width=True)

with col4:
    st.image("https://images.unsplash.com/photo-1456406644174-8ddd4cd52a06", caption="Student 4", use_container_width=True)
