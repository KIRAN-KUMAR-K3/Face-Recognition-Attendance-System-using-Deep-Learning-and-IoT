import asyncio
# import telegram - temporarily disabled
import os
from database import Database
from datetime import datetime
import pandas as pd

class TelegramBot:
    def __init__(self):
        """Initialize the Telegram bot."""
        self.db = Database()
        self.bot_token = self.db.get_setting("telegram_bot_token")
        self.chat_id = self.db.get_setting("telegram_chat_id")
        self.bot = None
        
        # In the actual implementation, we would initialize the Telegram bot here
        # For demo purposes, we'll use a simplified version
    
    async def send_message(self, message):
        """Send a message to the Telegram chat."""
        if not self.bot_token or not self.chat_id or self.chat_id.strip() == "":
            print("Telegram bot not configured")
            return False, "Telegram bot not configured"
        
        # In a real implementation, this would actually send the message
        print(f"Would send message to Telegram: {message}")
        return True, "Message sent successfully (demo mode)"
    
    def send_message_sync(self, message):
        """Send a message to the Telegram chat synchronously."""
        # For demo purposes, just simulate sending a message
        print(f"Simulated sending: {message}")
        return True, "Message sent successfully (demo mode)"
    
    def send_attendance_report(self, attendance_data):
        """Send an attendance report to the Telegram chat."""
        if attendance_data.empty:
            return False, "No attendance data to send"
        
        # Format the attendance data as a message
        date_str = attendance_data["date"].iloc[0]
        subject_name = attendance_data["subject_name"].iloc[0]
        subject_code = attendance_data["subject_code"].iloc[0]
        
        # Calculate total, present, and absent students
        total_students = attendance_data.shape[0]
        present_students = attendance_data[attendance_data["status"] == "present"].shape[0]
        absent_students = total_students - present_students
        
        # Format the message
        message = f"<b>📊 ATTENDANCE REPORT</b>\n\n"
        message += f"<b>Date:</b> {date_str}\n"
        message += f"<b>Subject:</b> {subject_name} ({subject_code})\n\n"
        message += f"<b>📈 SUMMARY</b>\n"
        message += f"Total Students: {total_students}\n"
        message += f"Present: {present_students}\n"
        message += f"Absent: {absent_students}\n"
        message += f"Attendance: {(present_students / total_students * 100):.2f}%\n\n"
        
        message += f"<b>👥 PRESENT STUDENTS</b>\n"
        present_df = attendance_data[attendance_data["status"] == "present"]
        if not present_df.empty:
            for idx, row in present_df.iterrows():
                message += f"- {row['student_name']} ({row['roll_no']})\n"
        else:
            message += "No students present\n"
        
        message += f"\n<b>👥 ABSENT STUDENTS</b>\n"
        absent_df = attendance_data[attendance_data["status"] == "absent"]
        if not absent_df.empty:
            for idx, row in absent_df.iterrows():
                message += f"- {row['student_name']} ({row['roll_no']})\n"
        else:
            message += "No students absent\n"
        
        message += f"\n<b>⏰ Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += f"\n<b>📍 ALVA'S INSTITUTE OF ENGINEERING AND TECHNOLOGY</b>"
        
        # Send the message
        success, error = self.send_message_sync(message)
        
        if success:
            # Mark the attendance as synced
            for idx, row in attendance_data.iterrows():
                self.db.mark_attendance_synced(row["id"])
        
        return success, error
    
    def sync_pending_attendance(self):
        """Sync pending attendance reports with Telegram."""
        unsynced_attendance = self.db.get_unsynced_attendance()
        
        if unsynced_attendance.empty:
            return True, "No pending attendance to sync"
        
        # Group by date and subject
        grouped = unsynced_attendance.groupby(["date", "subject_id"])
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for (date, subject_id), group in grouped:
            success, error = self.send_attendance_report(group)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                error_messages.append(error)
        
        if error_count == 0:
            return True, f"Successfully synced {success_count} attendance reports"
        else:
            return False, f"Synced {success_count} reports, {error_count} failed: {', '.join(error_messages)}"
    
    def test_connection(self):
        """Test the connection to the Telegram bot."""
        if not self.bot_token or self.bot_token.strip() == "":
            return False, "Bot token is not configured"
        
        if not self.chat_id or self.chat_id.strip() == "":
            return False, "Chat ID is not configured"
        
        message = f"🔄 Test message from Alva's Attendance System\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return self.send_message_sync(message)
    
    def update_settings(self, bot_token=None, chat_id=None):
        """Update the Telegram bot settings."""
        if bot_token:
            success = self.db.update_setting("telegram_bot_token", bot_token)
            if not success:
                return False, "Failed to update bot token"
            self.bot_token = bot_token
        
        if chat_id:
            success = self.db.update_setting("telegram_chat_id", chat_id)
            if not success:
                return False, "Failed to update chat ID"
            self.chat_id = chat_id
        
        # Re-initialize the bot with the new settings (demo mode)
        try:
            if self.bot_token and self.bot_token.strip() != "":
                # In a real implementation, we would initialize the bot here
                # self.bot = telegram.Bot(token=self.bot_token)
                return True, "Settings updated successfully (demo mode)"
            else:
                self.bot = None
                return True, "Bot token cleared"
        except Exception as e:
            return False, f"Error initializing Telegram bot: {e}"
