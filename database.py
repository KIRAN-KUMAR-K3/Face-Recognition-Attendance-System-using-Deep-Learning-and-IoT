import os
import sqlite3
import pandas as pd
from datetime import datetime, date
import json

class Database:
    def __init__(self, db_path="attendance_system.db"):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = None
        self.create_tables()
    
    def connect(self):
        """Create a database connection."""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            branch TEXT NOT NULL,
            semester INTEGER NOT NULL,
            section TEXT NOT NULL,
            email TEXT,
            face_encoding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create subjects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE NOT NULL,
            subject_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            semester INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create attendance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            status TEXT NOT NULL,
            synced BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
        ''')
        
        # Create faculty table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Insert default settings if they don't exist
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                    ("telegram_bot_token", ""))
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                    ("telegram_chat_id", ""))
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                    ("attendance_threshold", "0.6"))
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                    ("admin_password", "admin123"))
        
        # Create an admin user if not exists
        cursor.execute("INSERT OR IGNORE INTO faculty (faculty_id, name, password, is_admin) VALUES (?, ?, ?, ?)",
                    ("admin", "Administrator", "admin123", True))
        
        conn.commit()
        self.close()
    
    def add_student(self, roll_no, name, branch, semester, section, email, face_encoding=None):
        """Add a new student to the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Convert numpy array to binary for storage
            face_encoding_binary = None
            if face_encoding is not None:
                face_encoding_binary = json.dumps(face_encoding.tolist()).encode()
            
            cursor.execute('''
            INSERT INTO students (roll_no, name, branch, semester, section, email, face_encoding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (roll_no, name, branch, semester, section, email, face_encoding_binary))
            
            conn.commit()
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Roll number already exists"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()
    
    def update_student(self, student_id, roll_no, name, branch, semester, section, email, face_encoding=None):
        """Update an existing student in the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # If face encoding is provided, update it along with other details
            if face_encoding is not None:
                face_encoding_binary = json.dumps(face_encoding.tolist()).encode()
                cursor.execute('''
                UPDATE students
                SET roll_no = ?, name = ?, branch = ?, semester = ?, section = ?, email = ?, face_encoding = ?
                WHERE id = ?
                ''', (roll_no, name, branch, semester, section, email, face_encoding_binary, student_id))
            else:
                # Otherwise, update only the other details
                cursor.execute('''
                UPDATE students
                SET roll_no = ?, name = ?, branch = ?, semester = ?, section = ?, email = ?
                WHERE id = ?
                ''', (roll_no, name, branch, semester, section, email, student_id))
            
            conn.commit()
            return True, "Student updated successfully"
        except sqlite3.IntegrityError:
            return False, "Roll number already exists"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()
    
    def delete_student(self, student_id):
        """Delete a student from the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            return True, "Student deleted successfully"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()
    
    def get_student(self, student_id):
        """Get a student's details by ID."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT id, roll_no, name, branch, semester, section, email, face_encoding
            FROM students
            WHERE id = ?
            ''', (student_id,))
            
            result = cursor.fetchone()
            if result:
                student = {
                    'id': result[0],
                    'roll_no': result[1],
                    'name': result[2],
                    'branch': result[3],
                    'semester': result[4],
                    'section': result[5],
                    'email': result[6],
                    'face_encoding': None
                }
                
                # Convert stored face encoding back to numpy array if it exists
                if result[7]:
                    import numpy as np
                    try:
                        # If it's binary data (from older entries)
                        if isinstance(result[7], bytes):
                            student['face_encoding'] = np.array(json.loads(result[7].decode()))
                        # If it's a JSON string (from newer entries or our sample data)
                        else:
                            student['face_encoding'] = np.array(json.loads(result[7]))
                    except Exception as e:
                        print(f"Error decoding face encoding: {e}")
                        student['face_encoding'] = np.ones(128, dtype=np.float64)  # Use a default encoding
                
                return student
            return None
        except Exception as e:
            print(f"Error getting student: {e}")
            return None
        finally:
            self.close()
    
    def get_students(self, branch=None, semester=None, section=None):
        """Get all students, optionally filtered by branch, semester, and section."""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = '''
        SELECT id, roll_no, name, branch, semester, section, email
        FROM students
        '''
        
        conditions = []
        params = []
        
        if branch:
            conditions.append("branch = ?")
            params.append(branch)
        
        if semester:
            conditions.append("semester = ?")
            params.append(semester)
        
        if section:
            conditions.append("section = ?")
            params.append(section)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY roll_no"
        
        try:
            cursor.execute(query, params)
            
            students = []
            for row in cursor.fetchall():
                students.append({
                    'id': row[0],
                    'roll_no': row[1],
                    'name': row[2],
                    'branch': row[3],
                    'semester': row[4],
                    'section': row[5],
                    'email': row[6]
                })
            
            return students
        except Exception as e:
            print(f"Error getting students: {e}")
            return []
        finally:
            self.close()
    
    def get_all_face_encodings(self):
        """Get all students with their face encodings."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT id, roll_no, name, face_encoding
            FROM students
            WHERE face_encoding IS NOT NULL
            ''')
            
            import numpy as np
            students = []
            for row in cursor.fetchall():
                try:
                    # Handle different types of stored face encodings
                    if isinstance(row[3], bytes):
                        face_encoding = np.array(json.loads(row[3].decode()))
                    else:
                        face_encoding = np.array(json.loads(row[3]))
                except Exception as e:
                    print(f"Error decoding face encoding: {e}")
                    face_encoding = np.ones(128, dtype=np.float64)  # Use a default encoding
                
                students.append({
                    'id': row[0],
                    'roll_no': row[1],
                    'name': row[2],
                    'face_encoding': face_encoding
                })
            
            return students
        except Exception as e:
            print(f"Error getting face encodings: {e}")
            return []
        finally:
            self.close()
    
    def add_subject(self, subject_code, subject_name, branch, semester):
        """Add a new subject to the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO subjects (subject_code, subject_name, branch, semester)
            VALUES (?, ?, ?, ?)
            ''', (subject_code, subject_name, branch, semester))
            
            conn.commit()
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Subject code already exists"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()
    
    def update_subject(self, subject_id, subject_code, subject_name, branch, semester):
        """Update an existing subject in the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE subjects
            SET subject_code = ?, subject_name = ?, branch = ?, semester = ?
            WHERE id = ?
            ''', (subject_code, subject_name, branch, semester, subject_id))
            
            conn.commit()
            return True, "Subject updated successfully"
        except sqlite3.IntegrityError:
            return False, "Subject code already exists"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()
    
    def delete_subject(self, subject_id):
        """Delete a subject from the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
            conn.commit()
            return True, "Subject deleted successfully"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()
    
    def get_subject(self, subject_id):
        """Get a subject's details by ID."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT id, subject_code, subject_name, branch, semester
            FROM subjects
            WHERE id = ?
            ''', (subject_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'subject_code': result[1],
                    'subject_name': result[2],
                    'branch': result[3],
                    'semester': result[4]
                }
            return None
        except Exception as e:
            print(f"Error getting subject: {e}")
            return None
        finally:
            self.close()
    
    def get_subjects(self, branch=None, semester=None):
        """Get all subjects, optionally filtered by branch and semester."""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = '''
        SELECT id, subject_code, subject_name, branch, semester
        FROM subjects
        '''
        
        conditions = []
        params = []
        
        if branch:
            conditions.append("branch = ?")
            params.append(branch)
        
        if semester:
            conditions.append("semester = ?")
            params.append(semester)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY subject_code"
        
        try:
            cursor.execute(query, params)
            
            subjects = []
            for row in cursor.fetchall():
                subjects.append({
                    'id': row[0],
                    'subject_code': row[1],
                    'subject_name': row[2],
                    'branch': row[3],
                    'semester': row[4]
                })
            
            return subjects
        except Exception as e:
            print(f"Error getting subjects: {e}")
            return []
        finally:
            self.close()
    
    def mark_attendance(self, student_id, subject_id, status="present", sync=True):
        """Mark attendance for a student."""
        conn = self.connect()
        cursor = conn.cursor()
        
        current_date = date.today().isoformat()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        try:
            # Check if the student already has attendance for this subject and date
            cursor.execute('''
            SELECT id FROM attendance
            WHERE student_id = ? AND subject_id = ? AND date = ?
            ''', (student_id, subject_id, current_date))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update the existing attendance
                cursor.execute('''
                UPDATE attendance
                SET time = ?, status = ?, synced = ?
                WHERE id = ?
                ''', (current_time, status, sync, existing[0]))
            else:
                # Create a new attendance record
                cursor.execute('''
                INSERT INTO attendance (student_id, subject_id, date, time, status, synced)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (student_id, subject_id, current_date, current_time, status, sync))
            
            conn.commit()
            return True, "Attendance marked successfully"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()
    
    def get_attendance(self, date_filter=None, subject_id=None, student_id=None, branch=None, semester=None, section=None):
        """Get attendance records with various filters."""
        conn = self.connect()
        
        query = '''
        SELECT a.id, a.date, a.time, a.status, a.synced,
               s.id, s.roll_no, s.name, s.branch, s.semester, s.section,
               sub.id, sub.subject_code, sub.subject_name
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN subjects sub ON a.subject_id = sub.id
        '''
        
        conditions = []
        params = []
        
        if date_filter:
            conditions.append("a.date = ?")
            params.append(date_filter)
        
        if subject_id:
            conditions.append("a.subject_id = ?")
            params.append(subject_id)
        
        if student_id:
            conditions.append("a.student_id = ?")
            params.append(student_id)
        
        if branch:
            conditions.append("s.branch = ?")
            params.append(branch)
        
        if semester:
            conditions.append("s.semester = ?")
            params.append(semester)
        
        if section:
            conditions.append("s.section = ?")
            params.append(section)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY a.date DESC, a.time DESC"
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            
            # Rename columns for clarity
            df.columns = [
                'id', 'date', 'time', 'status', 'synced',
                'student_id', 'roll_no', 'student_name', 'branch', 'semester', 'section',
                'subject_id', 'subject_code', 'subject_name'
            ]
            
            return df
        except Exception as e:
            print(f"Error getting attendance: {e}")
            return pd.DataFrame()
        finally:
            self.close()
    
    def get_unsynced_attendance(self):
        """Get attendance records that haven't been synced with Telegram."""
        conn = self.connect()
        
        query = '''
        SELECT a.id, a.date, a.time, a.status,
               s.id, s.roll_no, s.name, s.branch, s.semester, s.section,
               sub.id, sub.subject_code, sub.subject_name
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN subjects sub ON a.subject_id = sub.id
        WHERE a.synced = FALSE
        ORDER BY a.date DESC, a.time DESC
        '''
        
        try:
            df = pd.read_sql_query(query, conn)
            
            # Rename columns for clarity
            df.columns = [
                'id', 'date', 'time', 'status',
                'student_id', 'roll_no', 'student_name', 'branch', 'semester', 'section',
                'subject_id', 'subject_code', 'subject_name'
            ]
            
            return df
        except Exception as e:
            print(f"Error getting unsynced attendance: {e}")
            return pd.DataFrame()
        finally:
            self.close()
    
    def mark_attendance_synced(self, attendance_id):
        """Mark attendance as synced with Telegram."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE attendance
            SET synced = TRUE
            WHERE id = ?
            ''', (attendance_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error marking attendance as synced: {e}")
            return False
        finally:
            self.close()
    
    def get_setting(self, key):
        """Get a setting value by key."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return None
        except Exception as e:
            print(f"Error getting setting: {e}")
            return None
        finally:
            self.close()
    
    def update_setting(self, key, value):
        """Update a setting value."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE settings
            SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = ?
            ''', (value, key))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating setting: {e}")
            return False
        finally:
            self.close()
    
    def verify_credentials(self, faculty_id, password):
        """Verify faculty login credentials."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT id, name, is_admin
            FROM faculty
            WHERE faculty_id = ? AND password = ?
            ''', (faculty_id, password))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'is_admin': bool(result[2])
                }
            return None
        except Exception as e:
            print(f"Error verifying credentials: {e}")
            return None
        finally:
            self.close()
    
    def get_attendance_stats(self, date_filter=None, subject_id=None, branch=None, semester=None, section=None):
        """Get attendance statistics."""
        conn = self.connect()
        
        try:
            # Base conditions for the query
            conditions = []
            params = []
            
            if date_filter:
                conditions.append("a.date = ?")
                params.append(date_filter)
            
            if subject_id:
                conditions.append("a.subject_id = ?")
                params.append(subject_id)
            
            if branch:
                conditions.append("s.branch = ?")
                params.append(branch)
            
            if semester:
                conditions.append("s.semester = ?")
                params.append(semester)
            
            if section:
                conditions.append("s.section = ?")
                params.append(section)
            
            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
            
            # Get total enrolled students
            total_query = f'''
            SELECT COUNT(DISTINCT s.id)
            FROM students s
            '''
            
            if branch or semester or section:
                student_conditions = []
                if branch:
                    student_conditions.append("s.branch = ?")
                if semester:
                    student_conditions.append("s.semester = ?")
                if section:
                    student_conditions.append("s.section = ?")
                
                if student_conditions:
                    total_query += " WHERE " + " AND ".join(student_conditions)
            
            total_df = pd.read_sql_query(total_query, conn, params=[p for p in params if p in [branch, semester, section]])
            total_students = total_df.iloc[0, 0]
            
            # Get present students
            present_query = f'''
            SELECT COUNT(DISTINCT a.student_id)
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            {where_clause}
            AND a.status = 'present'
            '''
            
            present_df = pd.read_sql_query(present_query, conn, params=params)
            present_students = present_df.iloc[0, 0]
            
            # Calculate absent students
            absent_students = total_students - present_students
            
            # Get attendance by branch
            branch_query = f'''
            SELECT s.branch, COUNT(DISTINCT a.student_id) as present_count
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            {where_clause}
            AND a.status = 'present'
            GROUP BY s.branch
            '''
            
            branch_df = pd.read_sql_query(branch_query, conn, params=params)
            
            # Get attendance by subject
            subject_query = f'''
            SELECT sub.subject_name, COUNT(DISTINCT a.student_id) as present_count
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN subjects sub ON a.subject_id = sub.id
            {where_clause}
            AND a.status = 'present'
            GROUP BY sub.subject_name
            '''
            
            subject_df = pd.read_sql_query(subject_query, conn, params=params)
            
            return {
                'total': int(total_students),
                'present': int(present_students),
                'absent': int(absent_students),
                'attendance_by_branch': branch_df,
                'attendance_by_subject': subject_df
            }
        except Exception as e:
            print(f"Error getting attendance stats: {e}")
            return {
                'total': 0,
                'present': 0,
                'absent': 0,
                'attendance_by_branch': pd.DataFrame(),
                'attendance_by_subject': pd.DataFrame()
            }
        finally:
            self.close()
