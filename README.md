# SecureFile - Secure File Management System

A comprehensive, enterprise-grade file management platform with end-to-end encryption, role-based access control, threat detection, and AI-powered file insights.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Project Requirements](#project-requirements)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Security Architecture](#security-architecture)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

### What is SecureFile?

SecureFile is a modern, secure file management and collaboration platform designed for individuals and organizations that prioritize data security and privacy. It enables users to upload, encrypt, store, and securely share files with others while maintaining complete control over access permissions.

Unlike traditional cloud storage solutions, SecureFile implements **end-to-end encryption** by default—files are encrypted on your device before transmission and remain encrypted at rest. The system includes intelligent threat detection, comprehensive audit logging, and role-based access control to prevent unauthorized access.

### Who Should Use SecureFile?

- **Professionals**: Store and share sensitive documents (contracts, financial reports, proposals)
- **Organizations**: Secure internal file management with role-based permissions
- **Privacy-Conscious Users**: Full control over encryption keys and file access
- **Compliance Teams**: Built-in audit trails and permission management for regulatory requirements

### Core Product Benefits

✅ **End-to-End Encryption** - All files encrypted before leaving your device  
✅ **Granular Access Control** - Share files with specific permissions (read-only or edit)  
✅ **Threat Detection** - Automatic scanning for malware, injection attacks, and suspicious files  
✅ **Audit Logging** - Complete history of all file operations and access attempts  
✅ **AI-Powered Insights** - Automatic file summarization, keyword extraction, and sensitivity scoring  
✅ **Two-Factor Authentication** - Account protection with 6-digit PIN verification  
✅ **Role-Based Access** - Admin, User, and Viewer roles with specific capabilities  
✅ **File Preview** - Native preview for documents, spreadsheets, PDFs, images, and more  
✅ **Intelligent Bot Assistant** - AI-powered chatbot for guidance and file operations  
✅ **Share History** - Complete tracking of who has access to each file and when permissions changed

---

## Key Features

### Authentication & Security
- **User Registration** with password complexity requirements (uppercase, lowercase, digit, special character)
- **Secure Login** with bcrypt password hashing (12-round salt)
- **Two-Factor Authentication** using 6-digit PIN for account lockdown
- **JWT-based Sessions** with configurable expiration
- **Session Management** with automatic timeout

### File Management
- **Upload Files** with automatic encryption
- **Download Files** with on-demand decryption
- **Update File Content** while maintaining encryption
- **Delete Files** with secure removal
- **File Preview** for multiple formats (PDF, Word, Excel, PowerPoint, images, text)
- **Bulk Operations** support for advanced workflows

### Sharing & Collaboration
- **Fine-Grained Permissions** - Share with read-only or edit access
- **User-Specific Sharing** - Target specific users or groups
- **Revoke Access** - Instantly remove shared permissions
- **Share History** - Track who accessed what and when
- **Permission Management** - View and modify access at any time

### Security & Protection
- **AES Encryption** - Military-grade encryption for all stored files
- **Malware Scanning** - Detect suspicious files before storage
- **Injection Detection** - Prevent SQL injection, XSS, and path traversal attacks
- **Buffer Overflow Protection** - Validate input length limits
- **Extension Filtering** - Block executable and dangerous file types
- **Rate Limiting** - Prevent abuse and API quota exhaustion

### Audit & Compliance
- **Comprehensive Audit Log** - Every action logged with timestamp and user info
- **Access Tracking** - See exactly who accessed which files and when
- **Audit Reports** - Generate compliance reports for regulatory requirements
- **IP Logging** - Track login attempts from different locations
- **Action History** - Full timeline of uploads, downloads, shares, and deletions

### AI & Intelligence
- **File Insights** - Automatic summarization of file content
- **Keyword Extraction** - Identify important terms and concepts
- **Sensitivity Scoring** - Detect sensitive data (passwords, credit cards, PII)
- **Content Analysis** - Classify files and suggest tags
- **AI Bot Assistant** - Conversational guidance for file operations and troubleshooting

### User Interface
- **Dark & Light Themes** - Switch between appearance modes
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Intuitive Dashboard** - One-click access to files, sharing, and security settings
- **Real-Time Feedback** - Instant confirmation of actions
- **Error Messages** - Clear guidance on any issues

---

## Project Requirements

### System Requirements

#### Minimum Hardware
- **Processor**: Intel/AMD 2GHz dual-core or equivalent
- **RAM**: 2 GB
- **Storage**: 5 GB (20 GB recommended for file storage)
- **Network**: 100 Mbps internet connection (1 Gbps recommended)

#### Operating System
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)

### Software Requirements

#### Backend
- **Python**: 3.8 or higher
- **pip**: Latest version (for package management)
- **Git**: 2.0+ (for cloning the repository)

#### Frontend
- **Modern Web Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **JavaScript**: ES6 support (no special requirements—vanilla JavaScript)

#### Optional for Development
- **Node.js**: 14+ (for frontend development server)
- **npm**: 6+ (for package management)
- **pytest**: For running automated tests

### Python Dependencies

All dependencies are listed in `requirements.txt`:

```
Flask==3.0.0                    # Web framework
Flask-JWT-Extended==4.6.0       # JWT authentication
bcrypt==4.1.2                   # Password hashing
cryptography==41.0.7            # Fernet encryption
python-docx==1.1.2              # Word document parsing
openpyxl==3.1.5                 # Excel parsing
python-pptx==0.6.23             # PowerPoint parsing
pypdf==4.3.1                    # PDF text extraction
Pillow==10.4.0                  # Image processing
groq==0.11.0                    # Groq LLM API
pywin32==306                    # Windows utilities
```

---

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Hariom-Pandey/SecureFile.git
cd SecureFile
```

### Step 2: Create Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (Optional)

Create a `.env` file in the project root with the following variables:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Flask Configuration
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here

# Groq LLM Settings
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
GROQ_MAX_INPUT_CHARS=2500
GROQ_REQUIRE_SUCCESS=false

# Rate Limiting
AI_RATE_LIMIT_PER_MINUTE=30
BOT_RATE_LIMIT_WINDOW_SECONDS=60

# File Storage
UPLOAD_MAX_SIZE=52428800  # 50 MB in bytes

# Security
MAX_INPUT_LENGTH=10000
```

**Note**: If `.env` is not provided, the system will:
- Auto-generate `SECRET_KEY` and `JWT_SECRET_KEY` on first run
- Store them in `.data/` directory for persistence
- Use default values for other settings

### Step 5: Run the Application

#### Option 1: Direct Python Execution
```bash
cd project
python main.py
```

The application will start at `http://127.0.0.1:5000`

#### Option 2: Using npm (if package.json configured)
```bash
npm run server      # Starts Python backend
npm run dev         # Starts frontend dev server
npm start           # Runs both simultaneously
```

#### Option 3: Using Node.js HTTP Server (Frontend Development)
```bash
cd project
npx http-server -p 3000
```

Frontend will be available at `http://127.0.0.1:3000`

### Step 6: Access the Application

1. Open browser to `http://127.0.0.1:5000/login` (or `http://127.0.0.1:3000` if using dev server)
2. Register a new account with username and password
3. Complete password complexity requirements (uppercase, lowercase, digit, special char)
4. Login with your credentials
5. Start uploading and managing files

### Step 7: Setup AI Features (Optional)

To enable AI-powered file insights and bot assistant:

1. Get a free Groq API key: https://console.groq.com
2. Add to `.env` or environment variables:
   ```bash
   export GROQ_API_KEY=your_api_key_here
   ```
3. Restart the application
4. AI features will automatically activate

---

## Usage

### Register a New Account

1. Navigate to **Register** page
2. Enter username (3-30 characters, alphanumeric + underscore)
3. Enter password (must include uppercase, lowercase, digit, special character)
4. Click **Register**
5. Redirected to login page
6. Enter credentials to login

### Enable Two-Factor Authentication

1. After login, go to **Security** section
2. Click **Enable PIN Lock**
3. Enter a 6-digit PIN
4. Click **Confirm**
5. Next login will require PIN verification

### Upload a File

1. Go to **Files** section
2. Click **Upload File** button
3. Select file from your computer
4. Confirm upload
5. File is encrypted and stored securely

### Share a File

1. In **Files** section, find desired file
2. Click **Share** icon
3. Enter username of recipient
4. Choose permission level:
   - **Read**: Recipient can view/download file
   - **Write**: Recipient can also edit file
5. Click **Share**
6. Recipient sees file in **Shared With Me** section

### View File Insights

1. In **Files** section, find desired file
2. Click **AI Insights** button
3. System analyzes file and displays:
   - Summary of content
   - Extracted keywords
   - Sensitivity score
   - Suggested tags
4. Insights appear in modal window

### Chat with AI Bot

1. Click **Bot Assistant** widget (bottom right)
2. Type your question or select quick prompt
3. Bot responds with guidance and suggested actions
4. Click action buttons to execute operations

### View Audit Log

1. Go to **Audit Log** section
2. See all actions performed on account:
   - Logins and logouts
   - File uploads and downloads
   - Shares and revocations
   - Permission changes
   - Failed security attempts
3. Each entry shows timestamp and IP address

---

## API Documentation

### Authentication Endpoints

```
POST   /api/auth/register          # Register new user
POST   /api/auth/login             # Login with username/password
POST   /api/auth/verify-2fa        # Verify 6-digit PIN
POST   /api/auth/setup-2fa         # Enable PIN lock
POST   /api/auth/disable-2fa       # Disable PIN lock
GET    /api/auth/me                # Get current user profile
GET    /api/auth/audit-log         # Get user's audit log
```

### File Management Endpoints

```
POST   /api/files/upload           # Upload file
GET    /api/files/                 # List user's files
GET    /api/files/<id>             # Download file
PUT    /api/files/<id>             # Update file
DELETE /api/files/<id>             # Delete file
GET    /api/files/<id>/metadata    # Get file metadata
GET    /api/files/<id>/insights    # Generate AI insights
GET    /api/files/<id>/preview     # Get HTML preview
POST   /api/files/<id>/share       # Share file with user
POST   /api/files/<id>/revoke      # Revoke user access
```

### Bot & AI Endpoints

```
POST   /api/bot/message            # Send message to bot
GET    /api/bot/capabilities       # Get bot capabilities
```

### Example API Calls

**Register User:**
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "SecurePass123!"}'
```

**Login:**
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "SecurePass123!"}'
```

**Upload File:**
```bash
curl -X POST http://127.0.0.1:5000/api/files/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf"
```

**Share File:**
```bash
curl -X POST http://127.0.0.1:5000/api/files/1/share \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "jane_doe", "permission": "read"}'
```

---

## Security Architecture

### Encryption

- **Algorithm**: Fernet (AES-128-CBC with HMAC)
- **Key Management**: Single master key stored with restricted permissions
- **File Storage**: All files encrypted before storage
- **Transmission**: Files encrypted client-side and in transit

### Authentication

- **Password Hashing**: bcrypt with 12-round salt (~300ms per hash)
- **JWT Tokens**: Signed with HS256, 1-hour expiration
- **2FA**: 6-digit PIN verification on login
- **Session Management**: Stateless JWT-based authentication

### Access Control

- **RBAC**: Three roles (Admin, User, Viewer)
- **File Permissions**: Owner, Read, Write levels
- **Access Checks**: Multi-layer permission verification

### Threat Detection

- **Malware Scanning**: EICAR signature detection
- **Injection Prevention**: SQL, XSS, path traversal pattern matching
- **Buffer Overflow Protection**: Input length validation
- **Extension Filtering**: Blocked and allowed file type lists

### Audit & Logging

- **Comprehensive Logging**: All actions recorded with timestamp
- **User Tracking**: IP address and user context logged
- **Immutable Records**: Audit logs never modified or deleted
- **Compliance**: Supports regulatory requirements (GDPR, HIPAA, SOC2)

---

## Testing

### Run All Tests

```bash
pytest project/tests/ -v
```

### Run Specific Test Suite

```bash
pytest project/tests/test_auth.py -v
pytest project/tests/test_encryption.py -v
pytest project/tests/test_access_control.py -v
pytest project/tests/test_threat_detection.py -v
pytest project/tests/test_file_operations.py -v
```

### Run Specific Test

```bash
pytest project/tests/test_auth.py::test_register -v
```

---

## Project Structure

```
SecureFile/
├── main.py                          # Application entry point
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── PROJECT_COMPREHENSIVE_ANALYSIS.md # Detailed technical documentation
│
├── project/
│   ├── main.py                      # Flask app factory
│   ├── config.py                    # Configuration constants
│   ├── data/                        # Persistent data directory
│   │   ├── .secret_key              # Flask secret (auto-generated)
│   │   ├── .jwt_secret_key          # JWT secret (auto-generated)
│   │   ├── master.key               # Encryption master key
│   │   └── secure_files.db          # SQLite database
│   │
│   ├── app/
│   │   ├── auth/                    # Authentication module
│   │   │   ├── authentication.py    # User registration & login
│   │   │   └── two_factor.py        # 2FA PIN verification
│   │   │
│   │   ├── protection/              # Security & encryption
│   │   │   ├── encryption.py        # Fernet encryption
│   │   │   └── access_control.py    # RBAC & permissions
│   │   │
│   │   ├── detection/               # Threat detection
│   │   │   └── threat_detector.py   # Malware, injection, overflow scanning
│   │   │
│   │   ├── files/                   # File operations
│   │   │   ├── file_operations.py   # CRUD operations
│   │   │   ├── bot_service.py       # AI chatbot
│   │   │   ├── intelligence.py      # AI file insights
│   │   │   └── preview_converter.py # File preview conversion
│   │   │
│   │   ├── models/                  # Database models
│   │   │   ├── database.py          # SQLite setup
│   │   │   ├── user.py              # User model
│   │   │   ├── file_record.py       # File model
│   │   │   ├── audit_log.py         # Audit logging
│   │   │   └── share_history.py     # Share tracking
│   │   │
│   │   ├── routes/                  # API endpoints
│   │   │   ├── auth_routes.py       # Auth endpoints
│   │   │   └── file_routes.py       # File endpoints
│   │   │
│   │   └── __init__.py
│   │
│   ├── storage/                     # Encrypted file storage
│   │   └── *.enc                    # Encrypted files
│   │
│   ├── templates/                   # HTML templates
│   │   ├── dashboard.html           # Main dashboard
│   │   ├── login.html               # Login page
│   │   └── register.html            # Registration page
│   │
│   ├── static/                      # Frontend assets
│   │   ├── css/
│   │   │   └── style.css            # Unified styling (dark/light theme)
│   │   ├── js/
│   │   │   ├── api.js               # API communication
│   │   │   ├── dashboard.js         # Dashboard logic
│   │   │   └── login.js             # Auth UI
│   │   └── images/                  # Icons and logos
│   │
│   └── tests/                       # Test suite
│       ├── test_auth.py             # Authentication tests
│       ├── test_encryption.py       # Encryption tests
│       ├── test_access_control.py   # RBAC tests
│       ├── test_threat_detection.py # Threat detection tests
│       └── test_file_operations.py  # File operation tests
│
└── .venv/                           # Python virtual environment
```

---

## Troubleshooting

### Issue: Port 5000 Already in Use

```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use different port
python main.py --port 8000
```

### Issue: File Upload Fails

1. Check file size (max 50 MB)
2. Verify file extension is allowed
3. Check storage directory exists: `project/storage/`
4. Ensure write permissions on storage directory

### Issue: Encryption Key Missing

The system auto-generates encryption key on first run. If missing:
1. Check `.data/master.key` exists
2. If deleted, encrypted files cannot be recovered
3. Always backup `.data/` directory

### Issue: AI Insights Not Working

1. Verify `GROQ_API_KEY` is set in environment
2. Check Groq API quota at https://console.groq.com
3. Verify internet connection
4. Check `GROQ_REQUIRE_SUCCESS=false` to enable fallback

### Issue: Database Locked

SQLite locks on concurrent writes:
1. Wait a few seconds and retry
2. For production with many users, migrate to PostgreSQL
3. Restart application if persistent

### Issue: Permission Denied on Login

1. Verify user exists (check registration)
2. Verify password is correct (case-sensitive)
3. If 2FA enabled, verify 6-digit PIN
4. Check audit log for failed attempts

---

## Performance Tips

### For Large Files
- Use SSD for faster encryption/decryption
- Files >50MB may take several seconds to upload
- Consider splitting large files or using compression

### For Many Users
- Current setup supports ~100 concurrent users
- For 1000+ users, migrate to PostgreSQL
- Use reverse proxy (nginx) for load balancing
- Implement caching layer (Redis)

### For Database
- SQLite is limited to single-server deployments
- PostgreSQL recommended for production
- Regular database backups essential

---

## Contributing

We welcome contributions! Here's how to help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with clear commit messages
4. **Test** your changes (`pytest project/tests/ -v`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request with description of changes

### Contribution Guidelines
- Follow PEP 8 for Python code
- Add tests for new features
- Update documentation
- Ensure all tests pass before submitting PR

---

## License

This project is licensed under the **MIT License** - see below for details.

### MIT License

```
MIT License

Copyright (c) 2024-2026 Hariom Pandey

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### What This Means

✅ **You can**:
- Use this software for personal or commercial projects
- Modify and distribute the code
- Include it in proprietary applications

❌ **You must**:
- Include the original license and copyright notice
- Provide a copy of this license with your distribution

---

## Support & Contact

### Getting Help

1. **Check Documentation**: See [PROJECT_COMPREHENSIVE_ANALYSIS.md](PROJECT_COMPREHENSIVE_ANALYSIS.md) for detailed technical docs
2. **Review Examples**: Check API documentation section above
3. **Search Issues**: Look for similar problems in GitHub issues
4. **Create Issue**: Report bugs or request features via GitHub issues

### Contact

- **Author**: Hariom Pandey
- **GitHub**: https://github.com/Hariom-Pandey/SecureFile
- **Email**: Open an issue on GitHub for fastest response

---

## Roadmap

### Short Term
- [ ] Performance optimization for large files
- [ ] Advanced file search and filtering
- [ ] File versioning and history
- [ ] Batch operations (bulk upload/share/delete)

### Medium Term
- [ ] Desktop application (Electron-based)
- [ ] Mobile apps (iOS/Android)
- [ ] Advanced collaboration features
- [ ] Workflow automation and rules

### Long Term
- [ ] Enterprise SSO (SAML/OAuth2)
- [ ] High availability and disaster recovery
- [ ] Advanced compliance reporting (HIPAA, SOC2, ISO 27001)
- [ ] Blockchain-based audit trail (optional)

---

## Changelog

### Version 1.0.0 (Current)

**Features**:
- User registration and authentication
- Two-factor authentication (PIN-based)
- File upload with encryption
- Secure file download and decryption
- Fine-grained file sharing and permissions
- Audit logging of all actions
- Threat detection and malware scanning
- AI-powered file insights and summarization
- Intelligent bot assistant
- Dark/light theme support
- File preview for multiple formats

**Security**:
- AES encryption at rest
- bcrypt password hashing
- JWT-based authentication
- RBAC with multiple roles
- Comprehensive threat detection
- Immutable audit logs

---

## Acknowledgments

- Flask team for excellent web framework
- Cryptography.io for robust encryption library
- Groq for LLM API
- Community contributors and testers

---

## Disclaimer

**Security Notice**: While SecureFile implements strong security practices, no system is 100% secure. Always:
- Keep your encryption key backup safe
- Use strong, unique passwords
- Keep software updated
- Enable two-factor authentication
- Regularly review audit logs

For security vulnerabilities, please report privately to repository maintainers instead of opening public issues.

---

**Made with ❤️ by Hariom Pandey**

*Last Updated: April 19, 2026*
