# Secure File Management System

A secure file management system built with Python and Flask that incorporates authentication, encryption, access control, and threat detection.

## Features

### Authentication
- **Password-based authentication** with bcrypt hashing (12 rounds)
- **Password complexity enforcement**: minimum 8 characters, requires uppercase, lowercase, digit, and special character
- **Account-wise second-step verification (2FA-style)** using a per-user 6-digit PIN lock
- **JWT-based session management** with configurable expiration

### Protection
- **Role-based access control (RBAC)**: Admin, User, and Viewer roles
- **File-level permissions**: Owner, Read, and Write access per user
- **AES encryption at rest** using Fernet (symmetric encryption) for all stored files
- **Audit logging** of all security-relevant actions

### Threat Detection
- **Buffer overflow prevention**: Input length validation on all fields
- **Malware signature scanning**: Files scanned against known malware signatures on upload
- **Injection attack detection**: SQL injection, XSS, path traversal pattern matching
- **File extension filtering**: Blocked (`.exe`, `.bat`, etc.) and allowed extension lists
- **File size limits**: Configurable maximum upload size (default 50 MB)

### File Operations
- **Upload** files (encrypted automatically)
- **Read/Download** files (decrypted on access with permission check)
- **Write/Update** file contents
- **Delete** files (owner/admin only)
- **Share** files with other users (read or write permission)
- **Revoke** shared access
- **View metadata** (size, type, timestamps, permissions)
- **AI file insights** with optional Groq-powered summaries, keywords, tags, and sensitivity scoring
- **Cloud-ready export bundles** for encrypted backup or object-storage upload

## Project Structure

```
project/
├── main.py                          # Application entry point
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
├── app/
│   ├── auth/
│   │   ├── authentication.py        # Password auth & registration
│   │   └── two_factor.py            # TOTP-based 2FA
│   ├── protection/
│   │   ├── access_control.py        # RBAC & file permissions
│   │   └── encryption.py            # AES file encryption
│   ├── detection/
│   │   └── threat_detector.py       # Malware, injection, overflow detection
│   ├── files/
│   │   ├── file_operations.py       # Core file CRUD operations
│   │   └── intelligence.py          # AI-style document insights
│   ├── models/
│   │   ├── database.py              # SQLite database setup
│   │   ├── user.py                  # User model
│   │   ├── file_record.py           # File & permission models
│   │   └── audit_log.py             # Audit logging model
│   └── routes/
│       ├── auth_routes.py           # Authentication API endpoints
│       └── file_routes.py           # File management API endpoints
└── tests/
    ├── test_auth.py                 # Authentication tests
    ├── test_encryption.py           # Encryption tests
    ├── test_access_control.py       # Access control tests
    ├── test_threat_detection.py     # Threat detection tests
    └── test_file_operations.py      # File operations tests
```

## Setup & Installation

### 1. Install Dependencies

```bash
cd project
pip install -r requirements.txt
```

### 2. Run the Server

```bash
# From workspace root (d:\OperatingProject)
python main.py

# OR from project folder
cd project
python main.py
```

The server starts at `http://127.0.0.1:5000`.

### Optional Groq AI Setup

If you want real AI-generated file insights, set these environment variables before starting the server:

```bash
set GROQ_API_KEY=your_key_here
set GROQ_MODEL=llama-3.3-70b-versatile
set GROQ_REQUIRE_SUCCESS=true
```

When `GROQ_REQUIRE_SUCCESS=true`, insights are Groq-only and local heuristic fallback is disabled.
If set to `false`, the app can fall back to local analysis when Groq is unavailable.

You can also place the same values in `project/.env` or workspace root `.env` and the app will load them automatically.

### 2.1 NPM-powered development

If you want simple NPM commands for frontend and backend, create a root `package.json` and install the helper packages from the workspace root:

```bash
cd d:\OperatingProject
npm install
```

Then use:

```bash
npm run server   # starts the Python backend
npm run dev      # starts a simple frontend dev server at http://127.0.0.1:3000
npm start        # runs both frontend and backend together
```

The frontend server hosts the `project/` static files and the existing frontend JavaScript is already configured to call the backend at `http://127.0.0.1:5000` when served from a dev host.
> Note: We replaced `live-server` with `http-server` so the frontend dev dependency is now more secure and should not introduce the legacy chokidar/micromatch vulnerability chain.
### 3. Run Tests

```bash
python -m pytest tests/ -v
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login with username/password |
| POST | `/api/auth/verify-2fa` | Verify second-step 6-digit PIN |
| POST | `/api/auth/setup-2fa` | Enable account PIN lock |
| POST | `/api/auth/confirm-2fa` | Backward-compatible PIN enable endpoint |
| POST | `/api/auth/disable-2fa` | Disable 2FA |
| GET  | `/api/auth/me` | Get current user profile |
| GET  | `/api/auth/audit-log` | View audit logs |

### File Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/files/upload` | Upload a file (multipart or JSON/base64) |
| GET  | `/api/files/` | List user's owned and shared files |
| GET  | `/api/files/<id>` | Read/download a file |
| PUT  | `/api/files/<id>` | Update file content |
| DELETE | `/api/files/<id>` | Delete a file |
| GET  | `/api/files/<id>/metadata` | View file metadata & permissions |
| GET  | `/api/files/<id>/insights` | Generate AI-style file insights |
| POST | `/api/files/<id>/share` | Share file with another user |
| POST | `/api/files/<id>/revoke` | Revoke user's file access |

## Usage Examples

### Register a User
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "Str0ng!Pass"}'
```

### Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "Str0ng!Pass"}'
```

### Upload a File
```bash
curl -X POST http://127.0.0.1:5000/api/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf"
```

### Share a File
```bash
curl -X POST http://127.0.0.1:5000/api/files/1/share \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "permission": "read"}'
```

### View File Metadata
```bash
curl http://127.0.0.1:5000/api/files/1/metadata \
  -H "Authorization: Bearer <token>"
```

## Security Architecture

```
┌─────────────────────────────────────────────────┐
│                   Client Request                 │
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Threat Detector │  ← Input validation, injection checks
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  Authentication  │  ← Password + account PIN verification
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  Access Control  │  ← RBAC + file-level permissions
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   Encryption     │  ← AES encrypt/decrypt at rest
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  File Storage    │  ← Encrypted files on disk
              └─────────────────┘
```

## Requirement Coverage Matrix

This maps your project requirement directly to implemented modules.

| Requirement | Implemented In | Coverage |
|-------------|----------------|----------|
| Password-based authentication | `app/auth/authentication.py`, `app/routes/auth_routes.py` | Username/password login with bcrypt hash verification and policy checks |
| Two-factor mechanism | `app/auth/two_factor.py`, `app/routes/auth_routes.py`, `templates/login.html`, `templates/dashboard.html` | Account-wise 6-digit PIN lock (second-step after password when enabled) |
| Access control | `app/protection/access_control.py`, `app/files/file_operations.py` | RBAC (admin/user/viewer) + file-level read/write/share checks + deny audit logs |
| Encryption | `app/protection/encryption.py`, `app/files/file_operations.py` | Fernet authenticated encryption at rest, secure key loading, encrypted storage files |
| Buffer overflow protection | `app/detection/threat_detector.py` | Input length checks against configured maximum |
| Malware detection | `app/detection/threat_detector.py` | Signature scanning (EICAR) + PE executable header detection |
| Common injection detection | `app/detection/threat_detector.py` | SQL/XSS/path traversal/null-byte pattern detection |
| Read operation | `app/files/file_operations.py`, `app/routes/file_routes.py` | Access-controlled read + decrypt + audit |
| Write operation | `app/files/file_operations.py`, `app/routes/file_routes.py` | Access-controlled write + threat scan + re-encrypt + audit |
| Share operation | `app/protection/access_control.py`, `app/files/file_operations.py`, `app/routes/file_routes.py` | Permission-checked share/revoke + share history + audit |
| Metadata view | `app/files/file_operations.py`, `app/routes/file_routes.py` | Access-controlled metadata with permissions visibility for owner/admin |

## Test Coverage (Security-Critical)

- Authentication and second-step PIN flow: `tests/test_auth.py`
- RBAC and permission boundaries: `tests/test_access_control.py`
- Encryption/decryption: `tests/test_encryption.py`
- Threat detection (overflow/malware/injection/extensions): `tests/test_threat_detection.py`
- Secure file operations (upload/read/write/share/metadata/history): `tests/test_file_operations.py`
