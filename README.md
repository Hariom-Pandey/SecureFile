# SecureFile

Secure file management with **end-to-end encryption**, **role-based access control**, **threat detection**, and **AI-powered insights**.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📋 Quick Links

- 📖 [**Installation Guide**](INSTALLATION.md) - Setup instructions
- ✨ [**Features**](FEATURES.md) - Complete feature list
- 🔌 [**API Documentation**](API_DOCUMENTATION.md) - Endpoint reference
- ⚖️ [**License**](LICENSE.md) - MIT License
- 📚 [**Technical Docs**](PROJECT_COMPREHENSIVE_ANALYSIS.md) - Deep dive architecture

---

## 🎯 What is SecureFile?

SecureFile enables **secure file management and collaboration** with:

- 🔐 **End-to-End Encryption** - Files encrypted before transmission
- 👥 **Fine-Grained Sharing** - Control who accesses what and when
- 🛡️ **Threat Detection** - Malware scanning, injection prevention
- 📊 **AI Insights** - Automatic summarization and keyword extraction
- 📝 **Audit Trails** - Complete history of all file operations
- 🤖 **AI Bot** - Conversational guidance for file operations

---

## ⚡ Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/Hariom-Pandey/SecureFile.git
cd SecureFile
```

### 2. Setup Virtual Environment
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate       # macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r project/requirements.txt
```

### 4. Run Application
```bash
cd project
python main.py
```

**Access at:** `http://127.0.0.1:5000/login`

📖 See [**INSTALLATION.md**](INSTALLATION.md) for detailed setup instructions.

---

## 🔑 Key Features

| Feature | Description |
|---------|-------------|
| 🔒 **Encryption** | AES-128 encryption at rest |
| 👤 **Auth** | JWT + 2FA (6-digit PIN) |
| 📤 **Share** | Fine-grained permissions (read/write) |
| 🔍 **Detect** | Malware scanning + injection prevention |
| 📊 **Audit** | Complete action logging |
| 🤖 **AI** | File insights + bot assistant |
| 🎨 **Themes** | Dark & light mode support |

📚 See [**FEATURES.md**](FEATURES.md) for complete feature list.

---

## 🔌 API Example

### Register User
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "SecurePass123!"}'
```

### Upload File
```bash
curl -X POST http://127.0.0.1:5000/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

🔌 See [**API_DOCUMENTATION.md**](API_DOCUMENTATION.md) for all endpoints.

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

📚 See [**PROJECT_COMPREHENSIVE_ANALYSIS.md**](PROJECT_COMPREHENSIVE_ANALYSIS.md) for security details.

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

## 🚀 Next Steps

1. **[Install Now](INSTALLATION.md)** - Get started in 5 minutes
2. **[Explore Features](FEATURES.md)** - See what SecureFile can do
3. **[Check API Docs](API_DOCUMENTATION.md)** - Integrate with your app
4. **[Read Technical Docs](PROJECT_COMPREHENSIVE_ANALYSIS.md)** - Understand architecture

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

---

## 📝 License

Licensed under the **[MIT License](LICENSE.md)** - free to use commercially.

---

## 📞 Support

- 📖 Check [INSTALLATION.md](INSTALLATION.md) for setup issues
- 🐛 Report bugs via GitHub issues
- 💡 Request features via GitHub discussions

---

**Made by [Hariom Pandey](https://github.com/Hariom-Pandey)**  
*Secure. Simple. Scalable.*
