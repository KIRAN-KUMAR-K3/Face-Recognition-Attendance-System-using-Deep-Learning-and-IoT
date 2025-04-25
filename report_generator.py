import pandas as pd
from database import Database
import io
import base64
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime

class ReportGenerator:
    def __init__(self):
        """Initialize report generator."""
        self.db = Database()
    
    def generate_csv(self, attendance_df):
        """Generate a CSV report from attendance data."""
        if attendance_df.empty:
            return None, "No attendance data to export"
        
        try:
            # Create a CSV string from the dataframe
            csv_buffer = io.StringIO()
            attendance_df.to_csv(csv_buffer, index=False)
            
            return csv_buffer.getvalue(), None
        except Exception as e:
            return None, f"Error generating CSV: {str(e)}"
    
    def generate_pdf(self, attendance_df, title="Attendance Report"):
        """Generate a PDF report from attendance data."""
        if attendance_df.empty:
            return None, "No attendance data to export"
        
        try:
            # Create a PDF buffer
            buffer = io.BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create a list of Flowables (items to add to the PDF)
            elements = []
            
            # Add title
            title_style = styles["Heading1"]
            title_paragraph = Paragraph(f"<b>{title}</b>", title_style)
            elements.append(title_paragraph)
            elements.append(Spacer(1, 0.25 * inch))
            
            # Add Alva's Institute header
            header_style = styles["Heading2"]
            header_paragraph = Paragraph("<b>ALVA'S INSTITUTE OF ENGINEERING AND TECHNOLOGY</b>", header_style)
            elements.append(header_paragraph)
            elements.append(Spacer(1, 0.25 * inch))
            
            # Add report date and time
            date_style = styles["Normal"]
            date_paragraph = Paragraph(f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style)
            elements.append(date_paragraph)
            elements.append(Spacer(1, 0.25 * inch))
            
            # Add summary information if all entries are for the same subject and date
            if len(attendance_df["subject_name"].unique()) == 1 and len(attendance_df["date"].unique()) == 1:
                subject_name = attendance_df["subject_name"].iloc[0]
                subject_code = attendance_df["subject_code"].iloc[0]
                date_str = attendance_df["date"].iloc[0]
                
                summary_style = styles["Normal"]
                summary_paragraph = Paragraph(f"<b>Subject:</b> {subject_name} ({subject_code})<br/>"
                                            f"<b>Date:</b> {date_str}<br/>", summary_style)
                elements.append(summary_paragraph)
                
                # Add attendance statistics
                total_students = attendance_df.shape[0]
                present_students = attendance_df[attendance_df["status"] == "present"].shape[0]
                absent_students = total_students - present_students
                attendance_pct = (present_students / total_students * 100) if total_students > 0 else 0
                
                stats_paragraph = Paragraph(f"<b>Total Students:</b> {total_students}<br/>"
                                          f"<b>Present:</b> {present_students}<br/>"
                                          f"<b>Absent:</b> {absent_students}<br/>"
                                          f"<b>Attendance:</b> {attendance_pct:.2f}%", summary_style)
                elements.append(stats_paragraph)
                elements.append(Spacer(1, 0.25 * inch))
            
            # Prepare data for the table
            # Select and reorder columns for the report
            columns = ["roll_no", "student_name", "status", "time", "subject_name", "date"]
            data = [["Roll No", "Student Name", "Status", "Time", "Subject", "Date"]]  # Header row
            
            # Add data rows
            for _, row in attendance_df.iterrows():
                data_row = [row[col] if col in row else "" for col in columns]
                data.append(data_row)
            
            # Create the table
            table = Table(data, repeatRows=1)
            
            # Add style to the table
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
            
            # Add alternating row colors
            for i in range(1, len(data)):
                if i % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), colors.white)
            
            table.setStyle(table_style)
            elements.append(table)
            
            # Build the PDF
            doc.build(elements)
            
            # Get the value of the BytesIO buffer
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return pdf_data, None
        except Exception as e:
            return None, f"Error generating PDF: {str(e)}"
    
    def get_download_link(self, data, filename, text="Download"):
        """Generate a download link for the given data."""
        b64 = base64.b64encode(data.encode()).decode() if isinstance(data, str) else base64.b64encode(data).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
        return href
