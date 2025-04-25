# import face_recognition - temporarily disabled
import cv2
import numpy as np
import streamlit as st
from database import Database
from io import BytesIO
from PIL import Image

class FaceRecognitionUtils:
    def __init__(self):
        """Initialize face recognition utilities."""
        self.db = Database()
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known face encodings from the database."""
        students = self.db.get_all_face_encodings()
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
        for student in students:
            self.known_face_encodings.append(student['face_encoding'])
            self.known_face_names.append(f"{student['name']} ({student['roll_no']})")
            self.known_face_ids.append(student['id'])
        
        return len(students)
    
    def detect_faces(self, image):
        """Detect faces in an image using OpenCV's Haar cascade."""
        # Convert the image to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Load the face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Convert to face_recognition style format (top, right, bottom, left)
        face_locations = []
        for (x, y, w, h) in faces:
            face_locations.append((y, x+w, y+h, x))
        
        return face_locations
    
    def recognize_faces(self, image, tolerance=0.6):
        """Mock face recognition (actual implementation would use face_recognition)."""
        # Detect faces using OpenCV
        face_locations = self.detect_faces(image)
        
        # For demo purposes, we'll just return placeholder data
        face_names = ["Student" for _ in face_locations]
        face_ids = [1 for _ in face_locations]  # Default to first student ID
        
        return face_locations, face_names, face_ids
    
    def draw_faces(self, image, face_locations, face_names):
        """Draw boxes and names around detected faces."""
        # Make a copy of the image to draw on
        output_image = image.copy()
        
        # Draw a box around each face and label with the name
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Draw the box
            cv2.rectangle(output_image, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Draw the name
            cv2.rectangle(output_image, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(output_image, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        
        return output_image
    
    def get_face_encoding(self, image):
        """Get a placeholder face encoding."""
        # Detect faces using OpenCV
        face_locations = self.detect_faces(image)
        
        if not face_locations:
            return None, "No face detected in the image"
        
        if len(face_locations) > 1:
            return None, "Multiple faces detected. Please provide an image with a single face."
        
        # Return a placeholder encoding (128-dimensional vector)
        return np.ones(128, dtype=np.float64), None
    
    def process_uploaded_image(self, uploaded_file):
        """Process an uploaded image file."""
        try:
            # Read the image file
            image_bytes = uploaded_file.getvalue()
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return image, None
        except Exception as e:
            return None, f"Error processing image: {str(e)}"
    
    def process_webcam_image(self, img_array):
        """Process an image from the webcam."""
        try:
            image = cv2.imdecode(np.frombuffer(img_array, np.uint8), cv2.IMREAD_COLOR)
            return image, None
        except Exception as e:
            return None, f"Error processing webcam image: {str(e)}"

def capture_face_streamlit():
    """Capture a face using the webcam in Streamlit."""
    st.write("Please position your face in the center of the camera")
    
    # For demo purposes, let's use a sample image instead of webcam
    # as webcam might not be available in the Replit environment
    st.info("Note: In this demo version, webcam capture is simulated. In a production environment, actual webcam would be used.")
    
    # Show an upload option instead
    uploaded_file = st.file_uploader("Upload a photo of your face", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Process the uploaded image
        face_utils = FaceRecognitionUtils()
        image, error = face_utils.process_uploaded_image(uploaded_file)
        
        if error:
            st.error(error)
            return None
        
        # Display the image
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        st.image(image_rgb, caption="Uploaded Image", use_column_width=True)
        
        # Detect faces
        face_locations = face_utils.detect_faces(image)
        
        if not face_locations:
            st.error("No face detected in the uploaded image. Please upload a clear image with a face.")
            return None
        
        if len(face_locations) > 1:
            st.warning("Multiple faces detected. Using the first face for enrollment.")
        
        # Draw rectangle around the face
        output_image = image.copy()
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(output_image, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Show the image with face detection
        output_rgb = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
        st.image(output_rgb, caption="Face Detected", use_column_width=True)
        
        # Get face encoding
        face_encoding, error = face_utils.get_face_encoding(image)
        
        if error:
            st.error(error)
            return None
        
        return image
    
    return None
