# API Documentation

## Base URL
```
http://127.0.0.1:5000/api
```

## Authentication Endpoints

### Register User
```
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!"
}

Response (201):
{
  "message": "Registration successful.",
  "user": {
    "id": 1,
    "username": "john_doe",
    "role": "user",
    "created_at": "2026-04-19T10:00:00"
  }
}
```

### Login
```
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!"
}

Response (200):
{
  "access_token": "eyJhbGc...",
  "user": {
    "id": 1,
    "username": "john_doe"
  }
}
```

### Verify 2FA PIN
```
POST /auth/verify-2fa
Authorization: Bearer <temp_token>
Content-Type: application/json

{
  "otp_code": "123456"
}

Response (200):
{
  "access_token": "eyJhbGc...",
  "message": "PIN verified."
}
```

### Get User Profile
```
GET /auth/me
Authorization: Bearer <token>

Response (200):
{
  "id": 1,
  "username": "john_doe",
  "role": "user",
  "two_factor_enabled": false,
  "created_at": "2026-04-19T10:00:00"
}
```

### Get Audit Log
```
GET /auth/audit-log
Authorization: Bearer <token>

Response (200):
[
  {
    "action": "LOGIN",
    "resource": "user:1",
    "timestamp": "2026-04-19T10:00:00",
    "ip_address": "192.168.1.1"
  },
  ...
]
```

## File Management Endpoints

### Upload File
```
POST /files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>

Response (201):
{
  "message": "File uploaded successfully",
  "file": {
    "id": 42,
    "filename": "document.pdf",
    "file_size": 1024000,
    "created_at": "2026-04-19T10:00:00"
  }
}
```

### List Files
```
GET /files/
Authorization: Bearer <token>

Response (200):
{
  "owned": [
    {
      "id": 1,
      "filename": "document.pdf",
      "file_size": 1024000,
      "owner_username": "john_doe"
    }
  ],
  "shared": [
    {
      "id": 2,
      "filename": "report.xlsx",
      "shared_permission": "read",
      "owner_username": "jane_doe"
    }
  ]
}
```

### Download File
```
GET /files/<id>
Authorization: Bearer <token>

Response (200):
{
  "message": "File retrieved",
  "file": {
    "filename": "document.pdf",
    "content": "base64_encoded_data"
  }
}
```

### Delete File
```
DELETE /files/<id>
Authorization: Bearer <token>

Response (200):
{
  "message": "File deleted successfully"
}
```

### Get File Metadata
```
GET /files/<id>/metadata
Authorization: Bearer <token>

Response (200):
{
  "id": 1,
  "filename": "document.pdf",
  "owner_username": "john_doe",
  "file_size": 1024000,
  "is_encrypted": true,
  "shared_with": [
    {
      "username": "jane_doe",
      "permission": "read"
    }
  ]
}
```

### Generate AI Insights
```
GET /files/<id>/insights
Authorization: Bearer <token>

Response (200):
{
  "summary": "This document discusses...",
  "keywords": ["keyword1", "keyword2", ...],
  "sensitivity": "HIGH",
  "tags": ["confidential", "financial"]
}
```

## Sharing Endpoints

### Share File
```
POST /files/<id>/share
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "jane_doe",
  "permission": "read"
}

Response (200):
{
  "message": "File shared successfully"
}
```

### Revoke Access
```
POST /files/<id>/revoke
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "jane_doe"
}

Response (200):
{
  "message": "Access revoked successfully"
}
```

## Bot & AI Endpoints

### Send Bot Message
```
POST /bot/message
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "How do I share a file?",
  "context_data": {
    "current_page": "files"
  }
}

Response (200):
{
  "message": "To share a file...",
  "type": "help",
  "agent_actions": ["Share file", "View metadata"]
}
```

### Get Bot Capabilities
```
GET /bot/capabilities
Authorization: Bearer <token>

Response (200):
{
  "quick_prompts": [],
  "capabilities": ["file_sharing", "file_preview", "ai_insights"]
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Missing or invalid authorization token."
}
```

### 403 Forbidden
```json
{
  "error": "Permission denied. You do not have access to this file."
}
```

### 404 Not Found
```json
{
  "error": "File not found."
}
```

### 429 Rate Limited
```json
{
  "error": "Rate limited at 30/min. Please wait 45 seconds."
}
```

### 500 Server Error
```json
{
  "error": "An unexpected error occurred. Please try again."
}
```

## Example cURL Commands

### Register
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "SecurePass123!"}'
```

### Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "SecurePass123!"}'
```

### Upload File
```bash
curl -X POST http://127.0.0.1:5000/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

### Share File
```bash
curl -X POST http://127.0.0.1:5000/api/files/1/share \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "jane", "permission": "read"}'
```

---

For more information, see [README.md](README.md) and [INSTALLATION.md](INSTALLATION.md)
