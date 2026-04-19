# SecureFile - Technical Documentation

Complete technical reference for SecureFile architecture, API, features, and deployment.

---

## 🏗️ Architecture Overview

### System Components
- **Backend**: Python Flask with JWT authentication
- **Database**: SQLite with encrypted storage
- **Encryption**: AES-128-CBC with Fernet (symmetric)
- **Frontend**: HTML/CSS/JavaScript with dark/light theme support
- **Threat Detection**: Malware scanning + injection prevention

### Security Layers
- **Passwords**: Bcrypt (12-round salt, ~300ms per hash)
- **Tokens**: JWT with expiration (30 min access, 7-day refresh)
- **2FA**: 6-digit PIN verification
- **Access Control**: Role-based (Admin/User/Viewer)
- **Audit**: Immutable action logging

---

## 📋 Installation & Setup

### System Requirements
- **Python**: 3.8+ (tested on 3.10, 3.11)
- **Node.js**: 16+ (for frontend build tools)
- **Disk**: 500MB minimum
- **RAM**: 2GB recommended
- **OS**: Windows, macOS, Linux

### Quick Start (4 Steps)

```bash
# 1. Clone repository
git clone https://github.com/Hariom-Pandey/SecureFile.git
cd SecureFile

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
source .venv/bin/activate             # macOS/Linux

# 3. Install dependencies
pip install -r project/requirements.txt

# 4. Run application
cd project
python main.py
```

**Access:** `http://127.0.0.1:5000/login`

### Alternative Launch Methods

**Using Flask CLI:**
```bash
cd project
flask --app main run
```

**Using Python module:**
```bash
cd project
python -m flask run
```

**Production with Gunicorn:**
```bash
pip install gunicorn
cd project
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Environment Variables

Create `.env` in `project/` directory:
```env
# Server
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DB_PATH=data/securefile.db

# JWT
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ACCESS_TOKEN_EXPIRES=1800  # 30 minutes

# Groq AI (optional)
GROQ_API_KEY=your-groq-key-here

# File Limits
MAX_FILE_SIZE=104857600  # 100MB
MAX_SHARE_DAYS=365
```

### Troubleshooting

**Port 5000 already in use:**
```bash
python main.py --port 5001
```

**Database locked error:**
- Stop all running instances
- Delete `project/data/securefile.db`
- Restart application

**Module import errors:**
- Reinstall dependencies: `pip install -r project/requirements.txt --force-reinstall`
- Check Python version: `python --version`

---

## ✨ Complete Feature List

### Authentication & Security (Auth Module)
- ✓ User registration with password validation
- ✓ Login with JWT token authentication
- ✓ Two-factor authentication (6-digit PIN)
- ✓ Password strength requirements
- ✓ Session management with token expiration
- ✓ Automatic logout on inactivity

### File Management (Files Module)
- ✓ Upload encrypted files
- ✓ Download with automatic decryption
- ✓ Preview generation for PDFs, images, videos
- ✓ File rename and metadata editing
- ✓ Batch file operations
- ✓ File versioning support
- ✓ Trash/recover deleted files

### Sharing & Collaboration (Share Module)
- ✓ Share files with specific users
- ✓ Fine-grained permissions (read-only, read-write)
- ✓ Time-limited access (set expiry date)
- ✓ Share history tracking
- ✓ Revoke access instantly
- ✓ Public share links (optional)
- ✓ Password-protected shares

### Security & Protection (Protection Module)
- ✓ AES-128 encryption at rest
- ✓ File integrity verification (HMAC)
- ✓ Secure key management
- ✓ Role-based access control (RBAC)
- ✓ Permission inheritance
- ✓ Quarantine suspicious files

### Threat Detection (Detection Module)
- ✓ Malware pattern detection
- ✓ SQL injection prevention
- ✓ Command injection blocking
- ✓ Buffer overflow protection
- ✓ File type validation
- ✓ Content scanning
- ✓ Suspicious activity logging

### Audit & Compliance (Audit Module)
- ✓ Complete action history
- ✓ User activity tracking
- ✓ File operation logging
- ✓ Access attempt recording
- ✓ Immutable audit trail
- ✓ Export audit logs
- ✓ Compliance reporting

### AI & Intelligence (Intelligence Module)
- ✓ Automatic file summarization
- ✓ Keyword extraction
- ✓ Content analysis
- ✓ Document categorization
- ✓ AI-powered bot assistant
- ✓ Natural language queries
- ✓ Smart recommendations

### User Interface
- ✓ Responsive design (mobile-friendly)
- ✓ Dark mode support
- ✓ Light mode support
- ✓ Dashboard overview
- ✓ File browser with search
- ✓ Permission management UI
- ✓ Audit log viewer

### API Features
- ✓ RESTful endpoints for all operations
- ✓ JSON request/response format
- ✓ Authentication via Bearer token
- ✓ Error handling with status codes
- ✓ Rate limiting support
- ✓ CORS enabled for frontend
- ✓ API documentation included

---

## 🔌 API Reference

### Base URL
```
http://localhost:5000/api
```

### Authentication Endpoints

#### Register User
```bash
POST /auth/register
Content-Type: application/json

{
  "username": "john",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered",
  "user_id": "12345"
}
```

#### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "username": "john",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLC...",
  "expires_in": 1800
}
```

#### Verify 2FA
```bash
POST /auth/verify-2fa
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "pin": "123456"
}
```

### File Operations

#### Upload File
```bash
POST /files/upload
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data

file=@document.pdf
```

**Response:**
```json
{
  "success": true,
  "file_id": "abc123",
  "filename": "document.pdf",
  "encrypted": true
}
```

#### Download File
```bash
GET /files/download/{file_id}
Authorization: Bearer YOUR_TOKEN
```

**Response:** File binary data (automatically decrypted)

#### List Files
```bash
GET /files/list
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "file_id": "abc123",
      "filename": "document.pdf",
      "size": 2048576,
      "uploaded": "2026-04-19T10:30:00Z",
      "shared_count": 2
    }
  ]
}
```

#### Delete File
```bash
DELETE /files/delete/{file_id}
Authorization: Bearer YOUR_TOKEN
```

### Sharing Endpoints

#### Share File
```bash
POST /share/create
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "file_id": "abc123",
  "recipient_username": "jane",
  "permission": "read",
  "expires_days": 7
}
```

**Response:**
```json
{
  "success": true,
  "share_id": "share_456",
  "expires": "2026-04-26T10:30:00Z"
}
```

#### List Shared Files
```bash
GET /share/list
Authorization: Bearer YOUR_TOKEN
```

#### Revoke Share
```bash
DELETE /share/{share_id}
Authorization: Bearer YOUR_TOKEN
```

### Threat Detection

#### Scan File
```bash
POST /detect/scan
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "file_id": "abc123"
}
```

**Response:**
```json
{
  "success": true,
  "status": "safe",
  "threats_detected": 0,
  "scanned_at": "2026-04-19T10:30:00Z"
}
```

### Audit Endpoints

#### Get Audit Log
```bash
GET /audit/logs
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "logs": [
    {
      "timestamp": "2026-04-19T10:30:00Z",
      "user": "john",
      "action": "file_upload",
      "resource": "document.pdf",
      "status": "success"
    }
  ]
}
```

### Bot/AI Endpoints

#### Chat with Bot
```bash
POST /bot/chat
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "file_id": "abc123",
  "query": "What is this document about?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "This document contains...",
  "processing_time": 1234
}
```

#### Get File Summary
```bash
GET /bot/summary/{file_id}
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "success": true,
  "summary": "Document summary here...",
  "keywords": ["keyword1", "keyword2"]
}
```

### Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human readable error message",
  "status": 400
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad request
- `401` - Unauthorized (invalid token)
- `403` - Forbidden (permission denied)
- `404` - Not found
- `500` - Server error

---

## 📁 Project Structure

```
SecureFile/
├── project/
│   ├── app/
│   │   ├── auth/              # Authentication & 2FA
│   │   │   ├── authentication.py
│   │   │   └── two_factor.py
│   │   ├── detection/         # Threat detection
│   │   │   └── threat_detector.py
│   │   ├── files/             # File operations & AI
│   │   │   ├── file_operations.py
│   │   │   ├── preview_converter.py
│   │   │   ├── bot_service.py
│   │   │   └── intelligence.py
│   │   ├── models/            # Database models
│   │   │   ├── user.py
│   │   │   ├── file_record.py
│   │   │   ├── audit_log.py
│   │   │   └── share_history.py
│   │   ├── protection/        # Encryption & access control
│   │   │   ├── encryption.py
│   │   │   └── access_control.py
│   │   └── routes/            # API endpoints
│   │       ├── auth_routes.py
│   │       └── file_routes.py
│   ├── static/                # Frontend assets
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── api.js
│   │       └── dashboard.js
│   ├── templates/             # HTML pages
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   └── register.html
│   ├── tests/                 # Test suite
│   │   ├── test_auth.py
│   │   ├── test_encryption.py
│   │   ├── test_file_operations.py
│   │   └── test_threat_detection.py
│   ├── config.py              # Configuration
│   ├── main.py                # Flask app entry point
│   ├── wsgi.py                # Production WSGI
│   └── requirements.txt        # Python dependencies
├── .gitignore                 # Git ignore rules
├── README.md                  # Project overview
├── TECHNICAL.md              # This file
├── LICENSE.md                # MIT License
└── package.json              # Node.js config
```

---

## 🧪 Testing

### Run All Tests
```bash
cd project
pytest tests/ -v
```

### Run Specific Test Suite
```bash
pytest tests/test_auth.py -v
pytest tests/test_encryption.py -v
pytest tests/test_file_operations.py -v
pytest tests/test_threat_detection.py -v
```

### Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html
```

### Test Status
- ✅ Authentication tests: 7/7 passing
- ✅ File operations tests: 15/15 passing
- ✅ Encryption tests: 6/6 passing
- ✅ Threat detection tests: 8/8 passing
- ✅ **Total: 36/36 tests passing**

---

## 🚀 Deployment

### Development Server
```bash
cd project
python main.py
```

### Production with Gunicorn
```bash
pip install gunicorn
cd project
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Production with Nginx
```nginx
upstream securefile {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://securefile;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/SecureFile/project/static;
    }
}
```

### Environment Variables for Production
```bash
export FLASK_ENV=production
export SECRET_KEY=your-strong-secret-key-here
export JWT_SECRET_KEY=your-jwt-secret-here
export DB_PATH=/var/lib/securefile/securefile.db
export GROQ_API_KEY=your-groq-api-key-here
```

---

## 🔒 Security Best Practices

1. **Never commit secrets** - Use `.env` file (included in `.gitignore`)
2. **Use HTTPS** - Deploy with SSL/TLS certificates
3. **Enable 2FA** - Require 2FA for all users
4. **Regular backups** - Backup database and encrypted files daily
5. **Update dependencies** - Run `pip install -r requirements.txt --upgrade` monthly
6. **Monitor logs** - Review audit logs regularly for suspicious activity
7. **Strong passwords** - Enforce password complexity requirements
8. **Principle of least privilege** - Grant minimal necessary permissions

---

## 📞 Support & Documentation

For additional help:
- Check [README.md](README.md) for project overview
- See [LICENSE.md](LICENSE.md) for licensing information
- Review error logs in `project/logs/`
- Open GitHub issue for bug reports

---

**Version:** 1.0.0  
**Last Updated:** 2026-04-19  
**Python:** 3.8+  
**Flask:** 3.0.0+
