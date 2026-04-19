# SecureFile

Secure file management with **end-to-end encryption**, **role-based access control**, **threat detection**, and **AI-powered insights**.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📋 Quick Links

- 📖 [**Installation Guide**](INSTALLATION.md) - Setup in 4 steps
- ✨ [**Features**](FEATURES.md) - What you get
- 🔌 [**API**](API_DOCUMENTATION.md) - All endpoints

---

## ⚡ Quick Start (4 Steps)

```bash
# 1. Clone
git clone https://github.com/Hariom-Pandey/SecureFile.git && cd SecureFile

# 2. Setup
python -m venv .venv && .venv\Scripts\Activate.ps1

# 3. Install
pip install -r project/requirements.txt && cd project

# 4. Run
python main.py  # → http://127.0.0.1:5000/login
```

👉 [Full setup guide →](INSTALLATION.md)

---

## 🔑 Core Features

🔒 **AES-128 Encryption** • 👤 **JWT + 2FA** • 📤 **Permissions** • 🔍 **Threat Detection** • 📊 **Audit Logs** • 🤖 **AI Assistant** • 🎨 **Dark/Light Mode**

👉 [Complete features →](FEATURES.md)

---

## 🔌 API Quick Example

```bash
# Register user
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "Pass123!"}'

# Upload file (need token)
curl -X POST http://127.0.0.1:5000/api/files/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf"
```

👉 [All endpoints →](API_DOCUMENTATION.md)

---

## 🧪 Testing

```bash
# Run all tests
pytest project/tests/ -v

# Specific test
pytest project/tests/test_auth.py -v
```

**Status**: 15/15 file operations tests passing ✅

---

## 🛡️ Security

- **Passwords**: Bcrypt (12-round salt, ~300ms per hash)
- **Encryption**: Fernet (AES-128-CBC + HMAC)
- **Access**: Role-based control (Admin/User/Viewer)
- **Threats**: Malware + injection + buffer overflow detection
- **Audit**: Immutable action logging

---

## 📂 Project Structure

```
SecureFile/
├── project/
│   ├── app/
│   │   ├── auth/              # Authentication
│   │   ├── files/             # File operations & AI
│   │   ├── protection/        # Encryption & access control
│   │   ├── detection/         # Threat detection
│   │   ├── models/            # Database models
│   │   └── routes/            # API endpoints
│   ├── static/                # Frontend (CSS, JS)
│   ├── templates/             # HTML pages
│   ├── tests/                 # Test suite
│   ├── config.py              # Configuration
│   └── main.py                # Entry point
├── INSTALLATION.md            # Setup guide
├── FEATURES.md                # Feature list
├── API_DOCUMENTATION.md       # API reference
├── LICENSE.md                 # MIT License
└── README.md                  # This file
```

---

## 🚀 Getting Started

1. **[Installation](INSTALLATION.md)** - Setup in 4 steps
2. **[Features](FEATURES.md)** - What's included
3. **[API Docs](API_DOCUMENTATION.md)** - All endpoints

---

## 📝 License

MIT License - See [LICENSE.md](LICENSE.md)

---

**Secure. Simple. Scalable.** ✨
