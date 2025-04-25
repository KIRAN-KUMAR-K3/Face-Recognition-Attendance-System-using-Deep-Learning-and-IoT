# 🎓 Face Recognition Attendance System using Deep Learning & IoT

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-ff69b4)](https://streamlit.io)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux%20|%20Replit-lightgrey)](#)

A lightweight and modular **face recognition-based attendance system** powered by **OpenCV** and integrated with **Telegram** for real-time attendance alerts. Designed to work in **resource-constrained** environments like Kali Linux or Replit, without depending on heavy libraries like `dlib`.

---

## 📸 Features

- ✅ Face detection using Haar Cascades (OpenCV)
- ✅ Face recognition using LBPH (training & prediction pipeline ready)
- ✅ Attendance marking with date & time logging
- ✅ SQLite-powered local database
- ✅ Telegram integration for real-time attendance alerts
- ✅ Report generation with CSV export
- ✅ Web UI using Streamlit
- ✅ Image upload support for platforms like Replit

---

## 🖥️ Project Demo

> Coming soon — demo video & screenshots

---

## 📁 Project Structure

```
Face-Recognition-Attendance-System-using-Deep-Learning-and-IoT/
│
├── app.py                    # Main Streamlit app
├── database.py               # SQLite helper functions
├── face_recognition_utils.py # Face detection & recognition logic
├── telegram_utils.py         # Telegram messaging support
├── report_generator.py       # Attendance report functions
├── attendance_system.db      # Local SQLite database
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata
├── uv.lock                   # Lock file (Poetry)
├── pages/                    # Multi-page Streamlit UI
├── assets/                   # Icons, images
└── README.md                 # Project documentation
```

---

## 🚀 Installation & Setup

### 🔧 1. Clone the Repository

```bash
git clone https://github.com/KIRAN-KUMAR-K3/Face-Recognition-Attendance-System-using-Deep-Learning-and-IoT.git
cd Face-Recognition-Attendance-System-using-Deep-Learning-and-IoT
```

### 🐍 2. Create Virtual Environment

```bash
# Kali & Linux
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
```

### 📦 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### ▶️ 4. Run the App

```bash
streamlit run app.py
```

---

## 🤖 Telegram Bot Setup (Optional)

Enable real-time attendance alerts via Telegram:

1. Open [@BotFather](https://t.me/botfather) and create a new bot
2. Copy your **API Token**
3. Update `telegram_utils.py`:
   ```python
   TELEGRAM_API_KEY = 'your_api_key'
   TELEGRAM_CHAT_ID = 'your_chat_id'
   ```
4. Or use demo mode (no message will be sent)

---

## 🧠 How It Works

| Step | Function |
|------|----------|
| Upload Face | User uploads image of their face |
| Detect Face | OpenCV detects face using Haar Cascades |
| Train Model | LBPH model stores face encodings |
| Predict | Matches new input with known faces |
| Log Attendance | Name + Time stored in SQLite DB |
| Notify | Optional Telegram alert sent |

---

## 📊 Attendance Report

- CSV logs stored daily
- Exportable attendance list
- Report summary available in UI

---

## 🧪 Future Enhancements

- 🔐 Admin login & user roles
- 📹 Live webcam capture (local-only)
- 🧠 CNN-based face recognition (via TensorFlow Lite)
- ☁️ Cloud-based database integration
- 📈 Analytics dashboard (attendance trends)

---

## 🤝 Contribution Guidelines

Contributions are welcome! Here's how:

```bash
# Fork the repository
# Clone your fork
# Create a new branch
# Make your changes
# Submit a pull request 🚀
```

Please follow [PEP8](https://pep8.org/) and include comments/documentation.

---

## 📚 Resources

- [OpenCV Documentation](https://docs.opencv.org/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 👨‍💻 Author

**Kiran Kumar K**  
🔗 [GitHub](https://github.com/KIRAN-KUMAR-K3)  
📍 IISc Bangalore (InfoSec Intern)

---

## 📄 License

This project is licensed under the **MIT License**.  
Feel free to use and modify with attribution.

---

> _Built with 💡 by a cybersecurity enthusiast — bridging AI, IoT, and security._
