# 🎓 Face Recognition Attendance System using Deep Learning & IoT

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-ff69b4)](https://streamlit.io)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux%20|%20Replit-lightgrey)](#)

An advanced and modular **Face Recognition-Based Attendance System** designed for academic institutions. Built with **Python**, **OpenCV**, **Streamlit**, and **SQLite**, this system offers **real-time attendance**, **secure user roles**, **automated reports**, and **Telegram integration** — all optimized for deployment on environments like **Kali Linux** or **Replit**.

---

## 🚀 Key Features

### 🔐 User Authentication & Roles
- Faculty login system with secure password management
- Role-based access (Admin vs Regular Faculty)
- Session and privilege management

### 👨‍🎓 Student Management
- Add/edit/delete student records
- Register face images linked to student profiles
- Branch, semester, and section categorization

### 📸 Face Recognition Attendance
- Real-time face recognition via webcam or image upload
- Batch face detection and attendance marking
- Adjustable recognition confidence thresholds

### 📚 Subject Management
- Create/manage subjects with metadata
- Assign subjects to faculty
- Map subjects to specific branches and semesters

### 📈 Attendance Reporting & Analytics
- Detailed reports with date, subject, and student filters
- Export attendance as **PDF** or **CSV**
- Graphs and charts for trends, stats, and comparisons

### 📲 Telegram Integration
- Real-time attendance notifications
- Auto-report generation and sharing
- Sync logs and status messages via bot

### 💻 Modern Web Interface
- Responsive and intuitive Streamlit UI
- Light/Dark mode toggle
- Real-time UI status updates and quick access

### 💾 Data Management
- SQLite backend with automatic syncing
- Face encoding storage and lookup
- Periodic data backup and restore utilities

---

## 📁 Project Structure

```
Face-Recognition-Attendance-System/
│
├── app.py                    # Main Streamlit app
├── database.py               # SQLite logic & queries
├── face_recognition_utils.py # Face encoding, detection, recognition
├── telegram_utils.py         # Telegram bot notifications
├── report_generator.py       # Report export (PDF, CSV)
├── pages/                    # Modular app pages
├── assets/                   # Static images, icons
├── attendance_system.db      # SQLite database file
├── requirements.txt          # Dependencies
├── pyproject.toml            # Project metadata
├── uv.lock                   # Poetry/venv lock file
└── README.md                 # This file
```

---

## ⚙️ Installation & Setup

### 🔧 1. Clone the Repository

```bash
git clone https://github.com/KIRAN-KUMAR-K3/Face-Recognition-Attendance-System-using-Deep-Learning-and-IoT.git
cd Face-Recognition-Attendance-System-using-Deep-Learning-and-IoT
```

### 🐍 2. Set Up a Virtual Environment

```bash
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
```

### 📦 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### ▶️ 4. Run the Application

```bash
streamlit run app.py
```

---

## 🤖 Telegram Bot Setup (Optional)

To enable notifications:
1. Use [@BotFather](https://t.me/BotFather) on Telegram to create a bot.
2. Copy the **Bot Token** and **Chat ID**.
3. Open `telegram_utils.py` and update:
   ```python
   TELEGRAM_API_KEY = 'your_api_key'
   TELEGRAM_CHAT_ID = 'your_chat_id'
   ```

---

## 📊 Reporting & Export

- View reports by date, subject, or student
- Download as **CSV** or **PDF**
- Visual graphs show:
  - Daily attendance %
  - Branch/subject-wise trends
  - Student-wise analytics

---

## 🛡️ Security

- Secure password hashing
- Admin-controlled subject access
- Role-based visibility for pages and actions
- Optional logout timeout/session protection

---

## 🧪 Future Enhancements

- Admin dashboard with full control
- OTP-based student verification
- Multi-device face recognition (mobile + web)
- Cloud storage support (Firebase, AWS S3)
- AI-powered duplicate face prevention

---

## 🙌 Contributing

Pull requests are welcome! Please follow standard GitHub practice:

```bash
# Fork the repository
# Create a feature branch
# Commit with clear messages
# Push and create a PR
```

Follow PEP8 formatting and include docstrings for functions.

---

## 📚 Useful Resources

- [Streamlit Docs](https://docs.streamlit.io/)
- [OpenCV Docs](https://docs.opencv.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [SQLite Docs](https://www.sqlite.org/index.html)

---

## 👨‍💻 Author

**Kiran Kumar K**  
🔗 [GitHub](https://github.com/KIRAN-KUMAR-K3)  
🧠 Information Security Intern, IISc Bangalore

---

## 📄 License

Licensed under the **MIT License** — you are free to use, modify, and distribute this project with attribution.

---

> _Built with ❤️ for smarter attendance and intelligent security._
