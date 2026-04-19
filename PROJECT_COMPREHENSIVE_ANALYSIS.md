# Secure File Management System - Comprehensive Project Analysis

## Executive Summary

This is a **Secure File Management System** built with Python (Flask) and JavaScript. It provides enterprise-grade file handling with encryption, role-based access control, threat detection, audit logging, and AI-powered file insights. The system emphasizes security through multiple defensive layers while maintaining usability for both technical and non-technical users.

**Core Purpose:** Enable users to securely upload, store, encrypt, and share files while maintaining detailed audit trails and preventing security threats through pattern detection and rate limiting.

---

## Part 1: Project Architecture & Design Patterns

### 1.1 Overall Architecture

The system follows a **three-tier architecture**:

1. **Frontend Tier** (Static HTML/CSS/JavaScript)
   - Client-side UI in browser
   - JavaScript modules for API communication, file operations, theme management
   - Real-time user feedback and error handling
   - Responsive dashboard with dark/light theme support

2. **Backend API Tier** (Flask Python Application)
   - RESTful API endpoints for authentication and file operations
   - Business logic layer handling validation, encryption, access control
   - Service-oriented architecture with specialized service classes
   - JWT-based stateless authentication
   - Rate limiting per user (30 requests/minute for AI operations)

3. **Data Persistence Tier** (SQLite Database)
   - Structured data storage for users, files, permissions, audit logs
   - Encrypted file storage in filesystem
   - Foreign key constraints for data integrity
   - PRAGMA foreign_keys enabled for referential integrity

### 1.2 Key Design Patterns

**Service-Oriented Architecture:**
- Specialized service classes handle specific domains (Authentication, File Operations, Encryption, Threat Detection, AI Intelligence)
- Each service is stateless and reusable across routes
- Separation of concerns makes code maintainable and testable

**Layered Security:**
- Input validation at API entry point
- Threat detection before processing
- Encryption at storage
- Access control checks before data exposure
- Audit logging of all sensitive actions

**Model-Repository Pattern:**
- Database models (User, FileRecord, FilePermission, AuditLog) encapsulate data structure
- Static methods on models act as repositories for CRUD operations
- Each model knows how to serialize itself (to_dict methods)

**Middleware Pattern:**
- JWT verification middleware via Flask-JWT-Extended
- Security headers applied via after_request hook
- CORS origin validation for development environments
- Pending 2FA claim checking on protected routes

---

## Part 2: Technology Stack & Dependencies

### 2.1 Backend Dependencies

```
Framework & Core:
- Flask (3.0.0): Lightweight web framework for routing and request handling
- Flask-JWT-Extended (4.6.0): JWT token generation and verification
- Werkzeug (3.0.1): WSGI utility library for secure operations

Security & Cryptography:
- bcrypt (4.1.2): Password hashing with 12-round salt
- cryptography (41.0.7): Fernet symmetric encryption for file storage
- pyotp (2.9.0): OTP library (infrastructure for 2FA)
- qrcode (7.4.2): QR code generation for 2FA setup

Document Processing:
- python-docx (1.1.2): Microsoft Word document parsing
- openpyxl (3.1.5): Excel spreadsheet parsing and extraction
- python-pptx (0.6.23): PowerPoint presentation parsing
- pypdf (4.3.1): PDF text extraction
- Pillow (10.4.0): Image processing and analysis

AI Integration:
- groq (0.11.0): Groq API SDK for LLM inference

System:
- pywin32 (306): Windows-specific system utilities
```

### 2.2 Frontend Technologies

```
Core:
- HTML5: Semantic structure with accessibility considerations
- CSS3: CSS custom properties (variables) for theming, flexbox/grid layout
- JavaScript (ES6+): Modular code with closures for private state

Dependencies:
- None (vanilla JavaScript - zero external dependencies for client-side)

Theme Support:
- CSS variable switching via data-theme attribute
- Light/dark mode with explicit overrides for visibility
```

### 2.3 Development & Runtime

```
Runtime:
- Python 3.8+
- SQLite3 (built-in)

Development:
- pytest: Unit and integration testing
- Node.js/npm: Optional development server coordination
```

---

## Part 3: File Structure & Module Breakdown

### 3.1 Root Configuration Files

**main.py** (Entry Point)
- Creates Flask application using factory pattern
- Sets up JWT authentication with custom callbacks
- Registers authentication and file operation blueprints
- Applies security headers to all responses
- Configures CORS for development environments
- Initializes database on app creation
- Key Feature: Validates dev-origin CORS requests (localhost:* only)

**config.py** (Configuration Management)
- Loads secrets from environment variables or persistent files
- Secrets stored in `.data/.secret_key` and `.data/.jwt_secret_key` (read on first boot)
- Reads `.env` files from project root or workspace root
- Defines all system configuration constants:
  - JWT expiration: 3600 seconds (1 hour)
  - Groq API settings with fallback model strategy
  - File upload limit: 50 MB
  - AI rate limit: 30 requests/minute per user
  - Rate limit window: 60 seconds
  - Max input length for threat detection: 10000 characters
  - Allowed file extensions (comprehensive whitelist)
  - Blocked extensions (.exe, .bat, .com, etc.)
- Key Pattern: Centralized configuration prevents hardcoding across modules

### 3.2 Authentication Module (`app/auth/`)

**authentication.py** - User Registration & Login
- **Username validation**: 3-30 alphanumeric + underscore characters
- **Password policy**:
  - Minimum 8 characters, maximum 128 characters
  - Requires uppercase, lowercase, digit, and special character (!@#$%^&*(),.?":{}\|<>)
- **Password hashing**: bcrypt with 12-round salt (computationally expensive to prevent brute force)
- **Registration workflow**:
  1. Validate username format
  2. Check password complexity
  3. Verify username doesn't exist (case-insensitive)
  4. Hash password with bcrypt
  5. Create user record in database
  6. Log registration in audit trail
- **Login workflow**:
  1. Retrieve user by username (case-insensitive)
  2. Verify password hash matches
  3. Check if 2FA is enabled (PIN verification required)
  4. Issue JWT token with user ID as identity
  5. Log login attempt in audit trail
- **Key Security**: All authentication attempts (successful and failed) logged with IP address

**two_factor.py** - Account PIN Lock (Simple 2FA)
- **PIN Format**: Exactly 6 numeric digits (000000-999999)
- **PIN Storage**: Hashed with bcrypt 12-round salt (never stored in plain text)
- **Setup workflow**:
  1. User provides 6-digit PIN
  2. PIN validated against pattern
  3. PIN hashed and stored in users.totp_secret field
  4. two_factor_enabled flag set to 1
  5. Audit logged
- **Verification workflow**:
  1. User provides PIN during login second step
  2. Compare user input against bcrypt hash
  3. Return pass/fail result
  4. Log all verification attempts (pass and fail)
- **Purpose**: Simple second-step verification to prevent account takeover even if password compromised
- **Note**: Named "totp_secret" for extensibility but currently implements PIN-based (not time-based OTP)

### 3.3 Protection Module (`app/protection/`)

**encryption.py** - File Encryption & Decryption
- **Encryption Cipher**: Fernet (symmetric AES encryption from cryptography library)
- **Key Management**:
  - Master key stored in `.data/master.key` with 0o600 permissions
  - Key generated on first boot using cryptography.Fernet.generate_key()
  - Key validation on load (fails fast if corrupted)
  - Refuses to generate new key if encrypted files exist (prevents lockout)
- **Encryption Process**:
  1. Load master key (single for all files)
  2. Create Fernet cipher instance
  3. Encrypt file bytes with cipher
  4. Return encrypted bytes (suitable for storage)
- **Decryption Process**:
  1. Load master key
  2. Create Fernet cipher instance
  3. Decrypt file bytes with cipher
  4. Return plaintext bytes
- **Security Properties**:
  - AES encryption with authentication tags (prevents tampering)
  - Same master key encrypts all files (trade-off: if master key compromised, all files at risk; but simpler operational overhead)
- **Future Improvement**: Per-file key derivation or key wrapping could enhance security

**access_control.py** - Role-Based Access Control (RBAC)
- **Role Hierarchy**:
  - Admin (level 3): Full capabilities
  - User (level 2): Standard user capabilities
  - Viewer (level 1): Read-only access
- **Role-Based Capabilities**:
  - Admin: {upload, read, write, delete, share}
  - User: {upload, read, write, delete, share}
  - Viewer: {read}
- **Access Control Workflow**:
  1. Check role-based capability (can this role do this action?)
  2. Check file-level ACL (does this user have permission to this file?)
  3. Owner checks (owner always has full access to owned files)
  4. Admin bypass (admins can access all files)
- **File Permission Model**:
  - File ownership (owner can read, write, delete)
  - Shared permissions via file_permissions table
  - Permissions: "read" (download/view) or "write" (modify content)
- **Key Methods**:
  - `can_perform_action()`: Role capability check
  - `can_read_file()`: Read permission check
  - `can_write_file()`: Write permission check
  - `can_delete_file()`: Delete permission (owner or admin only)
  - `can_share_file()`: Share permission (owner or admin)

### 3.4 Detection Module (`app/detection/`)

**threat_detector.py** - Security Scanning & Validation
- **Buffer Overflow Prevention**:
  - All input strings checked against MAX_INPUT_LENGTH (10000 characters)
  - Returns error if input exceeds limit
  - Prevents stack overflow or denial of service via huge inputs

- **File Extension Validation**:
  - Blocked extensions: .exe, .bat, .com, .scr, .pif, .dll, .sys, .vbs, .js, .jse, .vb, .vbe, etc.
  - Allowed extensions: Comprehensive whitelist (documents, spreadsheets, presentations, images, audio, video, archives, etc.)
  - Two-level check: 1) Block dangerous 2) Allow only known types
  - Prevents users from uploading executable or installer files

- **Injection Attack Detection**:
  - Pattern-based scanning for:
    - XSS: `<script>`, `javascript:`, `on*=` event handlers
    - SQL injection: Union/select/insert/update/delete with from/into/table/where
    - Path traversal: `../`, `..\\`, etc.
    - Null byte/CRLF injection: `\x00`, `\x0a`, `\x0d`
  - Checks both filename and file content
  - Returns detailed error message if threat detected
  - Logged to audit trail

- **Malware Signature Scanning**:
  - Currently includes EICAR test signature (standard test file)
  - PE executable header detection (checks for MZ signature + PE header)
  - Extensible framework for adding real malware signatures
  - Reports all detected threats to user and audit log

- **Comprehensive File Upload Scanning**:
  - Combines all threat checks: extension, injection, malware
  - Called before file storage
  - Returns all detected issues (may have multiple threats)
  - Audit logged with user ID, action, and details

### 3.5 File Operations Module (`app/files/`)

**file_operations.py** - Core File CRUD Operations
- **Storage Directory Setup**:
  - Ensures `project/storage/` exists with 0o700 permissions
  - All files stored encrypted with `.enc` extension
  - Internal filename: UUID hex + .enc (hides original filename)

- **Upload Workflow**:
  1. Check user role can upload (via AccessControlService)
  2. Scan file for threats (ThreatDetector)
  3. Generate unique internal filename (UUID)
  4. Encrypt file data with EncryptionService
  5. Write securely to storage (atomic write with fsync)
  6. Create database record (filename, original_name, owner_id, file_size, file_type)
  7. Audit log the upload
  8. Return success with file metadata

- **Read/Download Workflow**:
  1. Retrieve file record from database
  2. Check user has read permission (via AccessControlService)
  3. Load encrypted file from storage
  4. Decrypt with EncryptionService
  5. Return file content to user
  6. Audit log the download

- **Update Workflow**:
  1. Check user has write permission
  2. Validate new content
  3. Encrypt new content
  4. Replace encrypted file in storage
  5. Update database record
  6. Audit log the update

- **Delete Workflow**:
  1. Check user has delete permission (owner or admin)
  2. Remove encrypted file from storage
  3. Remove database record (cascades to permissions)
  4. Audit log the deletion

- **Share Workflow**:
  1. Check user has share permission
  2. Validate target user exists
  3. Check permission level (read or write)
  4. Create file_permissions record
  5. Record in share_history
  6. Audit log the share event

- **List Files**:
  - User's owned files: Query by owner_id, sorted by created_at DESC
  - User's shared files: Query via file_permissions join, with owner info
  - Includes permission info and share history

- **Atomic Write Pattern**:
  - Write to temporary file first
  - Flush and fsync to ensure disk write
  - Atomic rename to final location
  - Clean up temp file on error
  - Prevents partial file corruption on failure

**bot_service.py** - AI Chatbot & File Insights Requests
- **Purpose**: Process user chat messages and provide intelligent responses using Groq LLM

- **Rate Limiting**:
  - Global rate limit: 30 requests per minute per user
  - 60-second sliding window
  - Tracks request timestamps in memory per user_id
  - Returns 429 status with retry_after seconds if exceeded
  - Applied to both bot chat and file insights

- **Model Fallback Strategy**:
  - Primary model: llama-3.3-70b-versatile (high quality)
  - Fallback model: llama-3.1-8b-instant (if primary fails)
  - Attempts primary first, falls back on 429 (quota exhausted) or network error
  - Returns error if both models fail
  - Reduces API quota burn from duplicate requests

- **Response Processing**:
  - User message limited to 500 characters
  - Combines user message with dashboard context (file counts, recent actions)
  - Builds system prompt emphasizing beginner-friendly guidance
  - Sends to Groq API via single HTTP request (no SDK duplication)
  - Parses response and extracts suggested actions

- **Intent-Based Local Responses**:
  - Small talk: "Hi", "Hello", "How are you?" → Local friendly reply without API call
  - Intent detection: "Show my files", "Preview file", "Audit log?" → Context-aware local response
  - File selection checking: If user asks "Preview file" but no file context, suggests file selection
  - Reduces API calls for common queries

- **Action Suggestions**:
  - Bot analyzes user query and suggests next steps
  - Examples: "Upload a file", "Share with someone", "Check audit log"
  - Max 3 deduplicated actions to prevent overwhelm
  - Action buttons clickable in frontend

- **Context Data**:
  - Current file info (if viewing specific file)
  - User role (determines capabilities)
  - Action type (what user is trying to do)
  - Current dashboard page (files, shared, security, etc.)
  - Project context: file counts, recent files, recent actions (if relevant to query)

**intelligence.py** - File Content Analysis & Insights
- **Text Extraction**:
  - Plain text files: Direct UTF-8 decoding
  - Office documents: python-docx, openpyxl, python-pptx for structured extraction
  - PDFs: pypdf for text extraction
  - Images: Pillow for dimensions, EXIF data, basic analysis
  - CSV/Excel: tabular data extraction with column names

- **Local Insights** (heuristics-based):
  - File classification by extension
  - Estimated sensitivity (high/medium/low) based on filename patterns
  - Keyword extraction via stop-word filtering
  - Word frequency analysis
  - Estimated read time
  - Basic content summary via first/last paragraphs

- **AI-Powered Insights** (Groq LLM):
  - Detailed summary (50-100 words)
  - Extracted keywords (5-10 terms)
  - Sensitivity tags (credentials, personal, financial, operations)
  - Suggested tags/categories
  - Uses same model fallback strategy as bot
  - Limited to 260 tokens output (reduced for cost efficiency)

- **Context Gating**:
  - Project context injected only when query mentions "project", "analysis", "overview", etc.
  - Reduces token consumption for simpler queries
  - Project context includes: file counts, recent files, recent actions

- **Error Handling**:
  - Accumulates errors from model attempts
  - Falls back to local insights if API fails
  - Returns graceful error if all fallbacks exhausted

### 3.6 Models Module (`app/models/`)

**database.py** - SQLite Setup & Connection Management
- **Connection Pool**: `get_connection()` returns fresh connection each call (SQLite handles locking)
- **Row Factory**: Enables dict-like access to rows via `sqlite3.Row`
- **Foreign Key Enforcement**: `PRAGMA foreign_keys = ON` enables referential integrity
- **Database Schema** (created on init_db()):

```sql
users:
  - id (PRIMARY KEY)
  - username (UNIQUE)
  - password_hash (bcrypt hash)
  - role (admin/user/viewer)
  - totp_secret (PIN hash, nullable)
  - two_factor_enabled (0/1)
  - created_at, updated_at (TIMESTAMP)

files:
  - id (PRIMARY KEY)
  - filename (internal UUID + .enc)
  - original_name (user-visible name)
  - owner_id (FOREIGN KEY → users)
  - file_size (bytes)
  - file_type (extension)
  - is_encrypted (always 1)
  - created_at, updated_at (TIMESTAMP)

file_permissions:
  - id (PRIMARY KEY)
  - file_id (FOREIGN KEY → files)
  - user_id (FOREIGN KEY → users)
  - permission (read/write)
  - granted_by (FOREIGN KEY → users)
  - UNIQUE(file_id, user_id) - prevents duplicate permissions

audit_log:
  - id (PRIMARY KEY)
  - user_id (FOREIGN KEY → users, nullable)
  - action (REGISTER, LOGIN, UPLOAD, DOWNLOAD, DELETE, etc.)
  - resource (file_id:123, user:456, etc.)
  - details (human-readable description)
  - ip_address (source IP)
  - timestamp (TIMESTAMP)

share_history:
  - id (PRIMARY KEY)
  - file_id (FOREIGN KEY → files)
  - sender_user_id (FOREIGN KEY → users)
  - target_user_id (FOREIGN KEY → users)
  - action (SHARED, REVOKED, PERMISSION_CHANGED)
  - permission (read/write)
  - previous_permission (if changed)
  - created_at (TIMESTAMP)
```

**user.py** - User Model
- **Fields**: id, username, password_hash, role, totp_secret, two_factor_enabled, created_at, updated_at
- **Key Methods**:
  - `create()`: Insert new user, return User instance
  - `get_by_id()`: Retrieve by primary key
  - `get_by_username()`: Case-insensitive lookup (normalized comparison)
  - `update_totp_secret()`: Enable 2FA (set PIN hash and flag)
  - `disable_2fa()`: Disable 2FA (clear PIN and flag)
  - `to_dict()`: Serialize to JSON (excludes password_hash)

**file_record.py** - File & Permission Models
- **FileRecord Fields**: id, filename, original_name, owner_id, file_size, file_type, is_encrypted, created_at, updated_at, plus shares/permission info
- **FileRecord Methods**:
  - `create()`: Insert file record
  - `get_by_id()`: Retrieve file
  - `get_by_owner()`: List files owned by user
  - `get_shared_with_user()`: List files shared to user (with owner info)
  - `delete()`: Remove file record
  - `to_dict()`: Serialize with share info
- **FilePermission Methods** (static methods for permission checks):
  - `grant_permission()`: Add permission record
  - `get_permission()`: Check what permission user has (read/write/None)
  - `revoke_permission()`: Remove permission
  - `update_permission()`: Change permission level

**audit_log.py** - Audit Logging Model
- **Purpose**: Immutable record of all security-relevant actions
- **Fields**: user_id, action, resource, details, ip_address, timestamp
- **Methods**:
  - `log()`: Insert audit entry (called after every action)
  - `get_logs()`: Retrieve logs filtered by user_id or unfiltered
  - `get_file_logs()`: Retrieve logs for specific file_id
- **Key Logged Actions**:
  - REGISTER, LOGIN, PIN_VERIFY, 2FA_SETUP, 2FA_DISABLE
  - UPLOAD, DOWNLOAD, DELETE, UPDATE, PREVIEW
  - SHARE, REVOKE_ACCESS, PERMISSION_CHANGED
  - THREAT_DETECTED, ACCESS_DENIED, RATE_LIMITED
  - PIN_VERIFY_FAILED, INJECTION_BLOCKED, MALWARE_DETECTED

**share_history.py** - Share History Model
- **Purpose**: Track all file sharing events with before/after state
- **Fields**: file_id, sender_user_id, target_user_id, action, permission, previous_permission, created_at
- **Methods**: `get_share_history()`, `log_share_event()`, `log_revoke_event()`
- **Enables**: Audit trail of permissions changes, revocation history

### 3.7 Routes Module (`app/routes/`)

**auth_routes.py** - Authentication API Endpoints
- **POST /api/auth/register**:
  - Input: {username, password}
  - Validates input length and injection
  - Calls AuthenticationService.register()
  - Returns: 201 with user object or 400 with error

- **POST /api/auth/login**:
  - Input: {username, password}
  - Calls AuthenticationService.login()
  - If 2FA enabled: Returns 200 with requires_2fa flag + temp_token (5-min expiry)
  - If successful: Returns 200 with access_token (1-hour expiry)
  - Returns: 401 on failure

- **POST /api/auth/verify-2fa**:
  - Input: {otp_code} (6-digit PIN)
  - Verifies PIN using TwoFactorAuth.verify_otp()
  - Returns: 200 with access_token or 400/401 on failure

- **POST /api/auth/setup-2fa** & **POST /api/auth/confirm-2fa**:
  - Input: {pin_code}
  - Enables account PIN lock
  - Returns: 200 with success or 400 on validation error

- **POST /api/auth/disable-2fa**:
  - Disables account PIN lock
  - Returns: 200 with success

- **GET /api/auth/me**:
  - Returns current user profile (requires valid JWT)
  - Returns: 200 with user object or 401 if unauthorized

- **GET /api/auth/audit-log**:
  - Returns audit log entries for current user
  - Returns: 200 with log entries (last 100)

**file_routes.py** - File Management & Bot API Endpoints
- **POST /api/files/upload**:
  - Accepts multipart file or JSON base64
  - Calls FileOperations.upload_file()
  - Returns: 201 with file object or 400 on error

- **GET /api/files/**:
  - Lists user's owned and shared files
  - Returns: 200 with {owned: [...], shared: [...]}

- **GET /api/files/<id>**:
  - Downloads/reads file (returns base64 encoded)
  - Checks read permission
  - Returns: 200 with file content or 403/404 on error

- **PUT /api/files/<id>**:
  - Updates file content
  - Checks write permission
  - Returns: 200 with updated metadata or error

- **DELETE /api/files/<id>**:
  - Deletes file
  - Checks delete permission (owner/admin)
  - Returns: 200 with success or error

- **GET /api/files/<id>/metadata**:
  - Returns file metadata and permissions
  - Lists who file is shared with
  - Returns: 200 with metadata or error

- **POST /api/files/<id>/share**:
  - Input: {username, permission}
  - Shares file with another user
  - Returns: 200 with share info or error

- **POST /api/files/<id>/revoke**:
  - Input: {username}
  - Revokes user's access
  - Returns: 200 with success or error

- **GET /api/files/<id>/insights**:
  - Generates AI file insights
  - Rate limited to 30/minute
  - Returns: 200 with {summary, keywords, tags, sensitivity} or error

- **POST /api/files/<id>/preview**:
  - Converts file to HTML preview
  - Returns: 200 with HTML preview or error

- **POST /api/bot/message**:
  - Input: {message, context_data}
  - Rate limited to 30/minute
  - Calls BotService.process_message()
  - Returns: 200 with bot response or 429 if rate limited

- **GET /api/bot/capabilities**:
  - Returns bot capabilities and available quick prompts
  - Returns: 200 with {quick_prompts: []}

### 3.8 Frontend Module (`project/static/`)

**js/api.js** - API Communication Module
- **Purpose**: Encapsulates all HTTP communication with backend
- **Key Methods**:
  - `API.request()`: Generic HTTP wrapper (handles tokens, errors, CORS)
  - `API.auth.register()`, `API.auth.login()`, `API.auth.verify2fa()`: Auth endpoints
  - `API.files.list()`, `API.files.upload()`, `API.files.read()`: File operations
  - `API.files.delete()`, `API.files.share()`, `API.files.revoke()`: File management
  - `API.bot.sendMessage()`, `API.bot.getCapabilities()`: Bot endpoints
  - `API.setToken()`, `API.getToken()`: JWT token management
- **Error Handling**: Parses error responses, triggers error handlers
- **CORS**: Automatically includes authorization header, handles preflight

**js/dashboard.js** - Main Dashboard Logic
- **Initialization**: Checks auth, loads theme, initializes all sections
- **Navigation**: Switch between pages (files, shared, audit, security)
- **File Operations**:
  - `loadFiles()`: Fetch and display owned + shared files
  - `uploadFile()`: Multipart form upload with progress tracking
  - `downloadFile()`: Fetch and trigger browser download
  - `deleteFile()`: Confirm and delete file
  - `shareFile()`: Open share dialog, send share request
  - `revokeAccess()`: Revoke user access
  - `viewFileMetadata()`: Show permissions and share history
  - `generateInsights()`: Trigger AI analysis and show results
  - `previewFile()`: Convert to HTML and display
- **Bot Widget**:
  - `initializeBotWidget()`: Set up bot UI
  - `openBotWidget()`: Expand bot chat panel
  - `sendBotMessage()`: Send user query, display response
  - `displayBotActions()`: Show action buttons
  - `_displayBotResponse()`: Render bot reply with formatting
- **Audit Log**:
  - `loadAuditLog()`: Fetch audit entries, display in table
  - Format timestamps and action descriptions
- **Profile & Security**:
  - `loadProfile()`: Get user info and 2FA status
  - `enableTwoFactor()`: Enable PIN lock
  - `disableTwoFactor()`: Disable PIN lock
  - Display security summary (login history, permissions)
- **Theme Management**:
  - `initializeTheme()`: Load theme from localStorage or detect system preference
  - `toggleTheme()`: Switch between light/dark
  - Apply theme by setting data-theme attribute on html element
- **Error Handling**: Show error alerts for failed operations, allow retry

**js/login.js** - Authentication UI
- **Register Flow**:
  - Collect username and password
  - Validate password complexity in frontend
  - Call API.auth.register()
  - Show success or error message
  - Redirect to login on success
- **Login Flow**:
  1. Collect username and password
  2. Call API.auth.login()
  3. If 2FA required: Show PIN entry screen with temp token
  4. If successful: Store JWT token, redirect to dashboard
  5. If failed: Show error message
- **2FA PIN Entry**:
  - Show 6-digit PIN input
  - Call API.auth.verify2fa() with PIN
  - Validate format before sending

**css/style.css** - Unified Styling
- **CSS Variables** (theme-aware):
  - Color scheme: background, cards, borders, text
  - Dark mode (default): `--bg: #0f1117`, `--primary: #6c63ff`
  - Light mode: `--bg: #f8f9fa`, `--primary: #6c63ff`
  - All colors use var() for dynamic theming
  - Transitions for smooth theme switching
- **Layout**:
  - Sidebar (fixed left, 250px): Navigation + user info
  - Main content (flex, scrollable): Page sections
  - Responsive: Hamburger menu on small screens
- **Components**:
  - Buttons (primary, danger, ghost): Consistent styling with hover states
  - Forms (input, select, textarea): Themed with borders, focus states
  - Tables (files, audit log): Striped rows, sortable headers
  - Cards (file preview, metadata): Consistent padding and shadow
  - Modals (dialogs): Centered, overlay background
  - Alerts (success, error, warning): Colored text + background
- **Dark Mode Specific**:
  - Soft shadows for subtlety
  - High contrast text on dark backgrounds
  - Warm color accents (purple primary)
- **Light Mode Specific**:
  - Sharper shadows for depth
  - Dark text on light backgrounds
  - Blue color accents
  - Explicit overrides for chip/button visibility

**html/dashboard.html** - Main Application UI
- **Layout Sections**:
  - Header: Logo, user profile, theme toggle, logout
  - Sidebar: Navigation (Files, Shared, Audit Log, Security), logo
  - Main Content: Tabbed pages for each section
- **Files Page**:
  - Search and filter
  - File table: name, size, type, owner, actions (download, delete, share, preview, insights)
  - Upload button (multipart form)
  - Share dialog modal
- **Shared Files Page**:
  - Similar table but for shared files
  - Shows owner and permission level
  - Revoke access option
- **Audit Log Page**:
  - Table of recent actions
  - Filters by action type
  - Shows user, action, resource, timestamp
- **Security Page**:
  - User profile info (username, role, creation date)
  - 2FA status and enable/disable buttons
  - Recent login history
  - File permission summary
- **Bot Widget**:
  - Collapsible panel (bottom right)
  - Chat history display
  - Message input field
  - Bot response with suggested actions
  - Quick prompts section (expandable)

**html/login.html** - Authentication UI
- **Register Form**:
  - Username input (with validation feedback)
  - Password input (with strength indicator)
  - Password rules checklist (uppercase, lowercase, digit, special char)
  - Submit button
  - Link to login page
- **Login Form**:
  - Username input
  - Password input
  - Submit button
  - Link to register page
  - 2FA PIN entry (shown after login if required)
- **Error Display**: Alert box for validation or server errors

---

## Part 4: Feature Descriptions & Workflows

### 4.1 User Authentication & Accounts

**Registration Workflow**:
1. User navigates to /register
2. Frontend validates password strength (8+ chars, uppercase, lowercase, digit, special char)
3. User submits {username, password}
4. Backend validates username format (3-30 alphanumeric + underscore)
5. Backend checks username doesn't exist (case-insensitive)
6. Backend hashes password with bcrypt (12 rounds, ~300ms computation)
7. Backend creates user record with role="user"
8. Backend audits registration
9. Frontend redirects to login
10. Success message displayed

**Login Workflow**:
1. User navigates to /login
2. User submits {username, password}
3. Backend retrieves user by username (case-insensitive)
4. Backend verifies password hash
5. **If 2FA enabled**:
   - Backend issues temporary token (5-min expiry, 2fa_pending=True claim)
   - Frontend shows PIN entry screen
   - User enters 6-digit PIN
   - Backend verifies PIN hash
   - Backend issues full access token (1-hour expiry)
6. **If 2FA not enabled**:
   - Backend issues full access token immediately
7. Frontend stores token in localStorage
8. Frontend redirects to dashboard
9. Backend audits login with IP address

**Profile Management**:
- User can view profile on /security page
- Shows username, role, account creation date
- Shows current 2FA status

### 4.2 Account Security (2FA)

**Two-Factor Authentication (PIN-Based)**:
1. User navigates to /security page
2. User clicks "Enable PIN Lock"
3. Frontend shows PIN entry dialog
4. User enters 6-digit PIN (000000-999999)
5. Frontend validates format
6. Backend receives PIN
7. Backend validates format
8. Backend hashes PIN with bcrypt (12 rounds)
9. Backend stores hash in users.totp_secret
10. Backend sets two_factor_enabled=1
11. Backend audits 2FA enabling
12. Dashboard shows "PIN Lock Enabled"

**PIN Verification During Login**:
1. User completes password verification
2. If two_factor_enabled=1:
   - Backend issues temporary token (2fa_pending claim)
   - Frontend displays PIN entry
3. User enters PIN
4. Backend retrieves user
5. Backend verifies PIN against bcrypt hash
6. **If valid**:
   - Backend issues full access token
   - Frontend redirects to dashboard
7. **If invalid**:
   - Backend audits failed attempt
   - Frontend shows error message
   - User can retry
8. After 3 failed attempts (optional): Account temporarily locked

**Disabling 2FA**:
1. User clicks "Disable PIN Lock" on /security page
2. Backend clears totp_secret and sets two_factor_enabled=0
3. Backend audits 2FA disabling
4. Dashboard updates to show "PIN Lock Disabled"
5. Next login only requires password

### 4.3 File Upload & Encryption

**File Upload Workflow**:
1. User clicks "Upload File" on /files page
2. User selects file from filesystem (or drag-drop)
3. Frontend verifies file extension (client-side)
4. User submits file via multipart form
5. Backend receives file
6. Backend verifies MIME type (optional)
7. **Threat Detection**:
   - Extension check: Is it in allowed list? If not, reject
   - Injection scanning: Filename contains SQL/XSS patterns? Reject
   - Malware scanning: File contains known signatures? Reject
   - Buffer overflow: Filename >10000 chars? Reject
   - All checks logged to audit trail
8. **File Storage**:
   - Generate UUID for internal filename (e.g., "a1b2c3d4e5f6g7h8.enc")
   - Read file bytes into memory
   - Encrypt bytes with Fernet using master key
   - Write encrypted bytes atomically to storage/a1b2c3d4e5f6g7h8.enc
   - Create database record (filename=internal, original_name=user_visible, owner_id=user_id)
9. Backend returns success with file metadata
10. Frontend updates file list
11. Success message displayed
12. User can immediately download, share, or analyze file

**Encryption Details**:
- **Algorithm**: Fernet (AES-128 in CBC mode with HMAC)
- **Key**: Single master key stored in .data/master.key
- **Output**: Encrypted bytes with built-in timestamp and authentication tag
- **Security**: Prevents tampering; if any byte modified, decryption fails

### 4.4 File Download & Decryption

**File Download Workflow**:
1. User clicks download icon next to file
2. Frontend sends GET /api/files/<id>
3. Backend receives request
4. Backend checks JWT token validity
5. Backend retrieves file record by ID
6. **Access Control**:
   - Is user the owner? Grant access
   - Is user admin? Grant access
   - Does user have read permission? Grant access
   - Otherwise: Return 403 Forbidden
7. **File Retrieval**:
   - Load encrypted file from storage/a1b2c3d4e5f6g7h8.enc
   - Decrypt bytes with Fernet using master key
   - Return plaintext bytes as base64 in JSON response
8. Frontend receives response
9. Frontend decodes base64
10. Frontend triggers browser download
11. File saved to user's Downloads folder
12. User can open with their application
13. Backend audits download

### 4.5 File Sharing & Permissions

**Share File Workflow**:
1. User clicks share icon on file
2. Frontend shows "Share File" dialog
3. User enters target username and selects permission (Read or Write)
4. Frontend sends POST /api/files/<id>/share with {username, permission}
5. Backend receives request
6. **Permission Checks**:
   - Is user the file owner? Grant permission to share
   - Is user admin? Grant permission to share
   - Otherwise: Return 403 Forbidden
7. Backend retrieves target user by username
8. **Duplicate Check**: Does file_permissions already exist for this file+user combo?
   - If yes: Update permission (read → write or vice versa)
   - If no: Create new file_permissions record
9. Backend logs share event to share_history table
10. Backend audits share action
11. Backend returns success
12. Frontend updates share list (shows who file is shared with)
13. Target user sees file in "Shared With Me" section

**Permission Model**:
- **Read**: User can download/preview file (read-only)
- **Write**: User can download, preview, AND modify file content
- **No Permission**: File doesn't appear for user

**Revoke Access Workflow**:
1. User clicks revoke icon next to shared user
2. Frontend confirms action
3. Frontend sends POST /api/files/<id>/revoke with {username}
4. Backend retrieves file_permissions record
5. Backend deletes record
6. Backend logs revoke event to share_history
7. Backend audits revocation
8. Frontend refreshes share list
9. Shared user can no longer see file

### 4.6 File Metadata & Management

**View Metadata**:
1. User clicks info icon on file
2. Frontend sends GET /api/files/<id>/metadata
3. Backend returns:
   - Original filename
   - File size (bytes)
   - File type (extension)
   - Owner username
   - Upload/creation timestamp
   - Last modified timestamp
   - Encryption status (always "Encrypted")
   - Permission level (read/write/owner)
   - List of users file is shared with + their permissions
   - Share history (who shared with whom when)
4. Frontend displays in modal/panel

**Delete File**:
1. User clicks delete icon
2. Frontend confirms "This cannot be undone"
3. Frontend sends DELETE /api/files/<id>
4. Backend checks permission (owner or admin only)
5. Backend deletes encrypted file from storage
6. Backend deletes file record from database
7. Database CASCADE deletes all file_permissions records
8. Backend audits deletion
9. Frontend removes file from list
10. Success message displayed

**Update File Content**:
1. User clicks edit or update button
2. User selects new file or enters new content
3. Frontend sends PUT /api/files/<id> with new content (base64)
4. Backend checks write permission
5. Backend encrypts new content
6. Backend replaces encrypted file in storage
7. Backend updates file record (updated_at timestamp)
8. Backend audits update
9. Frontend refreshes file metadata

### 4.7 File Preview & Conversion

**File Preview Workflow**:
1. User clicks preview icon on file
2. Frontend sends POST /api/files/<id>/preview
3. Backend loads encrypted file
4. Backend decrypts file
5. **Format-Specific Processing**:
   - **Text files** (.txt, .md, .json, .csv): Direct UTF-8 decode, display in <pre> or formatted
   - **Office docs** (.docx, .xlsx, .pptx): Extract text via python-docx/openpyxl/python-pptx
   - **PDFs**: Extract text via pypdf
   - **Images** (.jpg, .png): Display with Pillow-generated thumbnail
   - **Others**: Return error "Format not supported for preview"
6. Backend returns HTML with formatted content
7. Frontend displays in modal or dedicated section
8. Backend audits preview

**Preview Limitations**:
- Binary formats may not preview (executables, archives)
- Large files (>10MB) may time out
- Password-protected documents may fail
- Complex layouts may not render perfectly

### 4.8 AI File Insights

**Generate Insights Workflow**:
1. User clicks "AI Insights" or "Analyze" button on file
2. Frontend sends GET /api/files/<id>/insights
3. **Rate Limiting Check** (30/minute per user):
   - Backend checks user's request history
   - If limit exceeded: Return 429 with retry_after seconds
   - Frontend shows "Rate limited. Please wait X seconds"
4. Backend loads encrypted file
5. Backend decrypts file
6. **Text Extraction** (via intelligence.py):
   - Extract text from file (varies by format)
   - Normalize to UTF-8
7. **Local Heuristics** (always runs):
   - Keyword extraction (word frequency minus stop words)
   - Sensitivity detection (presence of keywords like "password", "credit card")
   - File classification (document, spreadsheet, media, etc.)
   - Estimated read time
   - Basic summary of first/last paragraphs
8. **If Groq API available & REQUIRE_SUCCESS=false**:
   - Build Groq prompt with text + local insights
   - Call Groq LLM (llama-3.3-70b-versatile)
   - If successful: Return LLM-generated summary, keywords, tags
   - If 429 (quota): Fall back to local insights
   - If other error: Log error, fall back to local
   - If all fall back: Return local insights only
9. Backend returns comprehensive insights object with:
   - summary (50-100 words)
   - keywords (5-10 terms)
   - sensitivity_score (0-100)
   - suggested_tags (["financial", "confidential", etc.])
   - file_classification (document/spreadsheet/media/etc.)
   - word_count
   - estimated_read_time
10. Frontend displays insights in formatted card
11. Backend audits insights generation

**Insights Content**:
- **Summary**: What is this file about? What are its key points?
- **Keywords**: Top 10 most important terms in the document
- **Sensitivity**: HIGH/MEDIUM/LOW based on detected keywords
- **Tags**: Suggested categories (financial, personal, operational, etc.)
- **Classification**: Type of document (report, proposal, data, etc.)

### 4.9 AI Bot Chat & Guidance

**Bot Message Workflow**:
1. User opens bot widget (bottom right corner)
2. Bot shows initial greeting and suggests helpful quick prompts
3. User types question or selects quick prompt
4. Frontend sends POST /api/bot/message with {message, context_data}
5. **Rate Limiting Check** (30/minute shared with insights):
   - Backend checks user's request history
   - If limit exceeded: Return 429 with retry_after
   - Frontend displays "Rate limited" message
6. **Intent Detection** (before API call):
   - Is message small talk? ("Hi", "Hello") → Local friendly reply
   - Is message intent-based? ("Show threats", "Preview file") → Local context-aware reply
   - Skip Groq if local reply sufficient (saves API quota)
7. **If Groq Call Needed**:
   - Build system prompt (beginner-friendly guidance style)
   - Combine with dashboard context (file counts, recent actions)
   - Call Groq API (llama-3.3-70b-versatile, max_tokens=120)
   - If 429: Try fallback model (llama-3.1-8b-instant)
   - If both fail: Return error message
8. Backend returns response with:
   - message (bot reply)
   - type (chat/help/info/action/error/rate_limit)
   - source (groq/small_talk/intent_local)
   - agent_actions (suggested next steps)
   - needs_file_selection (does user need to select a file first?)
9. Frontend displays bot response
10. Frontend shows action buttons for suggested next steps
11. User can click action to execute (e.g., "Upload File" button)
12. Backend audits bot interaction

**Bot Capabilities**:
- **File Guidance**: "How do I upload a file?", "How do I share a file?"
- **Security Advice**: "How do I enable PIN lock?", "What is 2FA?"
- **Troubleshooting**: "Why can't I download this file?", "File preview not working"
- **System Info**: "How many files do I have?", "Who can access my files?"
- **General Chat**: Bot-like conversation with domain-aware responses

**Action Suggestions**:
- "Upload a file" → Takes user to upload interface
- "Share a file" → Opens share dialog for current file
- "View permissions" → Shows file metadata
- "Enable PIN lock" → Takes to security settings
- "Check audit log" → Shows recent actions

### 4.10 Audit Logging & Security

**What Gets Logged**:
- **Authentication**: REGISTER, LOGIN, PIN_VERIFY_FAILED, PIN_VERIFIED, 2FA_SETUP, 2FA_DISABLE
- **File Operations**: UPLOAD, DOWNLOAD, DELETE, UPDATE, PREVIEW, ANALYZE
- **Sharing**: SHARE, REVOKE, PERMISSION_CHANGED
- **Threats**: INJECTION_BLOCKED, MALWARE_DETECTED, BUFFER_OVERFLOW, EXTENSION_BLOCKED, THREAT_DETECTED
- **Access Control**: ACCESS_DENIED, PERMISSION_DENIED, RATE_LIMITED
- **Bot**: BOT_MESSAGE, BOT_INSIGHTS

**Audit Log Contents**:
- **user_id**: Who performed the action
- **action**: What action (enum above)
- **resource**: What was affected (file_id:123, user:456)
- **details**: Human-readable description
- **ip_address**: Source IP address
- **timestamp**: When it happened (UTC)

**Audit Log Access**:
1. User navigates to /audit page
2. Frontend sends GET /api/auth/audit-log
3. Backend retrieves last 100 audit entries for user
4. Frontend displays in chronological order (newest first)
5. Shows action, resource, details, timestamp
6. User can filter/search (client-side)

**Audit Log Immutability**:
- Logs written to database only (never modified)
- INSERTs only (no UPDATEs or DELETEs to audit_log)
- Enables forensics & security incident investigation

### 4.11 Theme & Appearance

**Theme System**:
- **Dark Mode** (default): `data-theme="dark"` or unset
  - Background: #0f1117 (almost black)
  - Text: #e4e6f0 (light gray)
  - Primary: #6c63ff (purple)
  - Cards: #1a1d27 (dark gray)
  - Inputs: #252836 (darker gray)
- **Light Mode**: `data-theme="light"`
  - Background: #f8f9fa (off-white)
  - Text: #212529 (dark gray)
  - Primary: #6c63ff (purple)
  - Cards: #ffffff (white)
  - Inputs: #f0f2f5 (light gray)

**Theme Toggle**:
1. User clicks theme toggle button (sun/moon icon)
2. Frontend reads current data-theme attribute
3. Frontend toggles to opposite theme
4. Frontend applies new theme by setting data-theme attribute
5. Frontend saves preference to localStorage
6. All CSS automatically switches via CSS variables

**Theme Persistence**:
- Stored in localStorage key (not in database)
- On page load: Check localStorage → Apply saved theme
- If no saved theme: Check system preference (prefers-color-scheme)
- Fallback: Default to dark mode

---

## Part 5: Security Implementation Details

### 5.1 Password Security

**Password Storage**:
- Users never store plaintext passwords
- bcrypt hashing with 12-round salt (default)
- Each password hash unique (salt included)
- Computation time ~300ms per hash (delays brute force attacks)
- Hash stored as UTF-8 string in database

**Password Validation**:
- Minimum 8 characters (prevents short passwords)
- Maximum 128 characters (prevents buffer overflow)
- Requires uppercase, lowercase, digit, special character (complexity)
- Regex patterns prevent common weak passwords
- Pattern: `[A-Z]`, `[a-z]`, `[0-9]`, `[!@#$%^&*(),.?"{}\|<>]`

**Login Security**:
- Username lookup case-insensitive (prevents enumeration)
- Password comparison timing-safe (prevents timing attacks)
- Failed login logged with IP (enables brute force detection)
- Account lockout not yet implemented (future enhancement)

### 5.2 File Encryption

**Encryption Algorithm**: Fernet (AES-128-CBC + HMAC)
- **Cipher**: AES-128 in CBC mode (block-based encryption)
- **Authentication**: HMAC prevents tampering/forgery
- **Nonce**: Random IV generated per file (same plaintext encrypts differently each time)
- **Format**: timestamp | nonce | ciphertext | mac (base64 encoded)

**Key Management**:
- **Master Key**: Single key for all files (trade-off for simplicity)
- **Storage**: `.data/master.key` with 0o600 permissions (owner read/write only)
- **Generation**: Fernet.generate_key() on first boot
- **Validation**: Key tested immediately after load (fails fast on corruption)
- **Backup**: User responsible for backing up .data/ directory

**Encryption Process**:
1. Read file bytes into memory
2. Create Fernet cipher with master key
3. Call cipher.encrypt(file_bytes)
4. Returns encrypted bytes with embedded timestamp & auth tag
5. Write encrypted bytes to storage (atomic)

**Decryption Process**:
1. Load encrypted file bytes from storage
2. Create Fernet cipher with master key
3. Call cipher.decrypt(encrypted_bytes)
4. Returns plaintext bytes
5. If any tampering detected: decrypt() raises exception

### 5.3 Access Control

**Role-Based Access (RBAC)**:
- **Admin**: Can upload, read, write, delete, share files; view all audit logs
- **User**: Can upload, read, write, delete, share files; view own audit logs
- **Viewer**: Can read files only; cannot upload or modify

**File-Level Permissions**:
- **Owner**: Always has read + write permission for owned files
- **Shared (Read)**: Can read/download/preview but not modify
- **Shared (Write)**: Can read/download/preview AND modify content
- **Not Shared**: No access (403 Forbidden)

**Access Check Order**:
1. Check role-based capability (can this role do this action?)
2. Check file-level permission (does this user have permission on this file?)
3. Admin bypass (admins can access all files)
4. Owner bypass (owners can access owned files)

**Example - Read File**:
1. Is user authenticated? If not: 401
2. Does user's role have read capability? (role check)
3. Is user owner of file? If yes: grant
4. Is user admin? If yes: grant
5. Does user have read permission in file_permissions? If yes: grant
6. Otherwise: 403 Forbidden

### 5.4 Threat Detection

**Input Validation**:
- **Length checks**: All inputs <10000 characters (buffer overflow prevention)
- **Format validation**: Username 3-30 alphanumeric, password 8-128 chars
- **Injection patterns**: Scan for SQL, XSS, path traversal

**File Upload Scanning** (multi-layer):

1. **Extension Validation**:
   - First: Is extension in BLOCKED list (.exe, .bat, .dll, .sys)? → Reject
   - Second: Is extension in ALLOWED list? → Allow; Otherwise: Reject
   - Prevents executable/installer uploads

2. **Filename Injection Scanning**:
   - Scan for XSS patterns: `<script>`, `javascript:`, `on*=`
   - Scan for SQL patterns: `union select`, `insert into`, etc.
   - Scan for path traversal: `../`, `..\\`
   - Scan for null bytes: `\x00`

3. **File Content Scanning**:
   - **Malware signatures**: Check for EICAR test file signature, PE headers
   - **Binary detection**: Attempt UTF-8 decode; if fails, likely binary
   - **Injection in content**: Scan first 1KB of content for patterns

4. **Size Validation**:
   - Maximum upload size: 50 MB (configurable)
   - Prevents disk exhaustion attacks

**Threat Response**:
- Log all detected threats to audit_log
- Return detailed error message to user
- Block file upload
- No half-written files in storage

### 5.5 Rate Limiting

**AI Rate Limiting** (shared between bot and insights):
- **Limit**: 30 requests per minute per user
- **Window**: 60-second sliding window
- **Tracking**: In-memory dictionary per user_id with request timestamps
- **Enforcement**: Before Groq API call
- **Response**: 429 Too Many Requests with retry_after seconds

**Rate Limit Check**:
1. Get current timestamp
2. Clean old requests outside 60-second window
3. Count remaining requests in window
4. If count >= limit: Return 429 with retry_after
5. If under limit: Add current timestamp to history, proceed

**Quota Exhaustion Handling**:
- If Groq returns 429: Try fallback model
- If fallback also returns 429: Return error to user
- Prevents excessive API calls burning quota

### 5.6 CORS & Origin Validation

**Development Origin Whitelist**:
- `127.0.0.1:3000+` (localhost on any port)
- `localhost:3000+` (localhost alias)
- Prevents CORS attacks from unauthorized domains
- Validates scheme (http or https only)
- Validates port is valid (1-65535)

**CORS Response Headers** (applied only if origin valid):
- `Access-Control-Allow-Origin: <validated-origin>`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Authorization`
- `Vary: Origin` (tells caches origin matters)

**Production Note**: When deploying, CORS should be:
- Removed entirely (frontend served from same domain as API)
- Or configured to match production frontend domain

### 5.7 Security Headers

**Applied to All Responses**:
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `Referrer-Policy: no-referrer` - Doesn't leak referrer
- `Permissions-Policy: camera=(), microphone=()` - Disables dangerous APIs
- `Cache-Control: no-store` - Prevents sensitive data caching
- `Pragma: no-cache` - HTTP/1.0 cache prevention
- `Expires: 0` - Expired cache

### 5.8 JWT Token Security

**Token Generation**:
- **Identity**: user.id (integer, base10 string)
- **Expiration**: 1 hour for normal tokens, 5 minutes for 2FA temp tokens
- **Claims**: Includes 2fa_pending flag if awaiting PIN verification
- **Secret**: Loaded from `.data/.jwt_secret_key` (random 64-hex-char key)

**Token Validation**:
- Signature verified on each request (tampering detected)
- Expiration checked (expired token rejected)
- Custom claims checked (2fa_pending flag respected)

**Token Storage** (Frontend):
- Stored in localStorage (XSS risk mitigation: no sensitive data)
- Sent in Authorization header: `Bearer <token>`
- Cleared on logout

**Logout Security**:
- Frontend removes token from localStorage
- Backend doesn't maintain revocation list (stateless)
- Old tokens still valid until expiration (trade-off for simplicity)
- Future enhancement: Implement token blacklist for immediate logout

---

## Part 6: Data Flow & Request Processing

### 6.1 Typical Request Flow

**Example: Upload a File**

```
User Action: Click "Upload" → Select file → Click "Upload Now"
↓
Frontend (JavaScript):
  - Read file bytes from input[type=file]
  - Create FormData with file
  - Call API.files.upload(file)
↓
API Layer (api.js):
  - Add Authorization header with JWT token
  - Make POST request to /api/files/upload
↓
Backend (Flask):
  - Receive multipart request
  - JWT validation middleware → Extract user_id
  - _reject_pending_second_step_claims() → Check 2FA not pending
  - Call FileOperations.upload_file()
↓
FileOperations Service:
  - AccessControlService.can_upload_file() → Check role
  - ThreatDetector.scan_file_upload() → Multi-layer scanning
  - Ensure storage directory exists
  - Generate UUID filename
  - EncryptionService.encrypt_data() → Fernet encryption
  - _write_bytes_secure() → Atomic write
  - FileRecord.create() → Insert to database
  - AuditLog.log() → Record upload event
↓
Backend Response:
  - Return 201 with file metadata
↓
Frontend (JavaScript):
  - Parse response
  - Add file to local list
  - Show success message
  - Update UI
```

### 6.2 Database Query Flow

**Example: List User's Files**

```
User clicks "Files" tab
↓
Frontend: GET /api/files/
↓
Backend Route Handler:
  - Get user_id from JWT
  - Call FileOperations.list_user_files(user_id)
↓
FileOperations:
  - Query 1: SELECT * FROM files WHERE owner_id = ? (owned files)
  - Query 2: SELECT * FROM files JOIN file_permissions ... (shared files)
  - For each shared file: Get permission level (read/write)
  - Get owner username via join
  - Build result dict: {owned: [...], shared: [...]}
↓
Backend Response:
  - Return 200 with files
↓
Frontend:
  - Display files in table
  - Show owner, size, type, actions
```

### 6.3 Encryption/Decryption Flow

**Upload Path** (Plain → Encrypted):
```
File bytes (plaintext)
↓
EncryptionService.encrypt_data(bytes)
  - Load master key from .data/master.key
  - Create Fernet(key)
  - cipher.encrypt(bytes)
  - Returns encrypted bytes with auth tag
↓
FileOperations._write_bytes_secure(path, encrypted_bytes)
  - Write to .tmp file
  - fsync() to disk
  - Atomic rename to final path
↓
Storage: /storage/a1b2c3d4e5f6g7h8.enc (encrypted)
```

**Download Path** (Encrypted → Plain):
```
Request: GET /api/files/<id>
↓
Backend:
  - Check permission
  - Load /storage/a1b2c3d4e5f6g7h8.enc
  - EncryptionService.decrypt_data(encrypted_bytes)
    - Load master key
    - Create Fernet(key)
    - cipher.decrypt(encrypted_bytes)
    - Returns plaintext bytes
  - Base64 encode plaintext
  - Return in JSON
↓
Response: {content: "base64_encoded_plaintext"}
↓
Frontend:
  - Base64 decode
  - Trigger browser download
```

### 6.4 Authentication Flow

**Registration**:
```
User submits registration form
↓
Frontend:
  - Validate password locally
  - POST /api/auth/register {username, password}
↓
Backend:
  - Validate username format
  - Validate password complexity
  - Check username not taken
  - Hash password with bcrypt
  - User.create()
  - AuditLog.log("REGISTER", ...)
  - Return 201
↓
Frontend:
  - Show success message
  - Redirect to /login
```

**Login without 2FA**:
```
User submits login form
↓
Frontend:
  - POST /api/auth/login {username, password}
↓
Backend:
  - Retrieve user by username (case-insensitive)
  - Verify password hash
  - Check two_factor_enabled flag
  - If enabled: Return 200 with temp_token + requires_2fa flag
  - If disabled: create_access_token() → 1-hour expiry
  - Return 200 with access_token
  - AuditLog.log("LOGIN", ...)
↓
Frontend:
  - Store token in localStorage
  - Redirect to /dashboard
```

**Login with 2FA**:
```
[Same as above until two_factor_enabled check]
↓
Backend:
  - two_factor_enabled == 1
  - Issue temporary token (5-min expiry, 2fa_pending claim)
  - Return 200 with temp_token and requires_2fa flag
↓
Frontend:
  - Display PIN entry screen
  - Store temp_token
↓
User enters PIN
↓
Frontend:
  - POST /api/auth/verify-2fa {otp_code} with temp_token
↓
Backend:
  - Verify temp_token has 2fa_pending claim
  - Retrieve user
  - Verify PIN against bcrypt hash
  - If match: create_access_token() → 1-hour expiry
  - Return 200 with access_token
  - AuditLog.log("PIN_VERIFIED", ...)
↓
Frontend:
  - Store access_token
  - Redirect to /dashboard
```

### 6.5 File Sharing Flow

**Share File**:
```
User selects file → Click "Share" → Enter username & permission
↓
Frontend:
  - POST /api/files/<id>/share {username: "bob", permission: "read"}
↓
Backend:
  - Check user_id is file owner or admin
  - Retrieve target user by username
  - Check file_permissions doesn't already exist
  - FilePermission.grant_permission(file_id, user_id, permission)
    - INSERT INTO file_permissions (file_id, user_id, permission, granted_by)
  - ShareHistory.log_share_event()
    - INSERT INTO share_history (file_id, sender_user_id, target_user_id, action, permission)
  - AuditLog.log("SHARE", ...)
  - Return 200
↓
Frontend:
  - Update share list
  - Show success
↓
Target user:
  - Refreshes /shared page
  - File now appears in shared list
  - Can download/preview based on permission
```

**Revoke Access**:
```
User clicks "Revoke" on shared user
↓
Frontend:
  - POST /api/files/<id>/revoke {username: "bob"}
↓
Backend:
  - Check user_id is file owner or admin
  - FilePermission.revoke_permission(file_id, user_id)
    - DELETE FROM file_permissions WHERE file_id=? AND user_id=?
  - ShareHistory.log_revoke_event()
    - INSERT INTO share_history ... action='REVOKED'
  - AuditLog.log("REVOKE", ...)
  - Return 200
↓
Frontend:
  - Remove user from share list
  - Show success
↓
Bob:
  - File disappears from /shared page on next refresh
  - Cannot access file (403 Forbidden)
```

---

## Part 7: System Configuration & Tuning

### 7.1 Environment Variables

**Authentication & JWT**:
- `SECRET_KEY`: Flask session secret (auto-generated if missing)
- `JWT_SECRET_KEY`: JWT signing secret (auto-generated if missing)

**Groq API**:
- `GROQ_API_KEY`: API key for Groq LLM (required for AI features)
- `GROQ_MODEL`: Primary model (default: llama-3.3-70b-versatile)
- `GROQ_FALLBACK_MODEL`: Fallback model (default: llama-3.1-8b-instant)
- `GROQ_API_URL`: API endpoint (default: https://api.groq.com/openai/v1/chat/completions)
- `GROQ_MAX_INPUT_CHARS`: Max input characters before truncation (default: 2500)
- `GROQ_REQUIRE_SUCCESS`: Require successful Groq call or allow fallback (default: true)

**Rate Limiting**:
- `AI_RATE_LIMIT_PER_MINUTE`: Max AI requests per minute per user (default: 30)
- `BOT_RATE_LIMIT_WINDOW_SECONDS`: Sliding window for rate limit (default: 60)

**File Storage**:
- `UPLOAD_MAX_SIZE`: Max upload file size in bytes (default: 50 MB)
- `MAX_INPUT_LENGTH`: Max input length for threat detection (default: 10000)

### 7.2 Performance Considerations

**Encryption Performance**:
- Fernet encryption ~1-2ms per MB (depends on CPU)
- Large files (>50MB) may take several seconds
- Decryption slightly faster than encryption

**Database Performance**:
- SQLite suitable for single-server deployments
- Concurrent writes queue (not multi-writer)
- For 1000+ users: Consider PostgreSQL

**API Performance**:
- Groq API calls: ~1-3 seconds per request (LLM inference)
- File uploads: Limited by network + encryption (~10MB/s CPU)
- File downloads: Immediate (decryption done on demand)

**Frontend Performance**:
- Zero external dependencies (fast load)
- Vanilla JavaScript (no framework overhead)
- CSS variables for theme switching (no repaint on toggle)

### 7.3 Scalability Limitations

**Current Bottlenecks**:
1. **Single Master Key**: All files encrypted with same key
   - If key compromised: All files at risk
   - Solution: Implement per-user or per-file key derivation

2. **In-Memory Rate Limiting**: Lost on app restart
   - Solution: Move to Redis for distributed rate limiting

3. **SQLite**: Not suitable for >10K concurrent users
   - Solution: Migrate to PostgreSQL + connection pooling

4. **Synchronous Flask**: No request queuing
   - Solution: Use async framework (FastAPI) or add worker queue (Celery)

5. **Groq API Quotas**: Rate limited and quota-limited
   - Solution: Implement caching for duplicate queries, batch processing

---

## Part 8: Testing & Validation

### 8.1 Test Suite Structure

**Test Files**:
- `test_auth.py`: Authentication, password hashing, 2FA
- `test_encryption.py`: Encryption/decryption, key management
- `test_access_control.py`: RBAC, file permissions
- `test_threat_detection.py`: Input validation, malware scanning, injection detection
- `test_file_operations.py`: Upload, download, delete, share operations

**Test Execution**:
```bash
pytest project/tests/ -v  # Run all tests with verbose output
pytest project/tests/test_auth.py -v  # Run specific test file
pytest project/tests/test_auth.py::test_register -v  # Run specific test
```

### 8.2 Test Coverage

**Key Test Categories**:
- **Happy Path**: Successful operations (register, login, upload, share)
- **Edge Cases**: Empty inputs, special characters, boundary values
- **Error Cases**: Missing fields, invalid inputs, permission denied
- **Security Cases**: SQL injection, XSS, buffer overflow, malware signatures
- **Integration**: End-to-end workflows (register → login → upload → share)

---

## Part 9: Deployment & Operations

### 9.1 Production Deployment Checklist

**Before Deployment**:
- [ ] Set `GROQ_API_KEY` environment variable
- [ ] Set `SECRET_KEY` and `JWT_SECRET_KEY` (or let system generate)
- [ ] Backup `.data/` directory (contains encryption key + secrets)
- [ ] Test all features in staging environment
- [ ] Configure database backups
- [ ] Set up monitoring/alerting
- [ ] Review security headers (CORS should be disabled or configured)
- [ ] Implement HTTPS/TLS for all traffic
- [ ] Set up rate limiting at reverse proxy layer (nginx)
- [ ] Enable database foreign key constraints (verify in config.py)

**Post-Deployment**:
- [ ] Test user registration and login
- [ ] Test file upload and encryption
- [ ] Test file sharing and permissions
- [ ] Test 2FA PIN setup
- [ ] Monitor API response times
- [ ] Monitor error rates
- [ ] Check audit logs for anomalies
- [ ] Verify backups are running

### 9.2 Operational Procedures

**Regular Backups**:
- Backup `.data/` directory (encryption key + secrets) - CRITICAL
- Backup `project/data/secure_files.db` (SQLite database)
- Backup `project/storage/` (encrypted files)
- Schedule daily incremental backups
- Test restore procedures regularly

**Monitoring**:
- Monitor `/var/log/app.log` for errors
- Monitor CPU/memory usage (encryption is CPU-intensive)
- Monitor disk usage (file storage growth)
- Monitor API response times (Groq latency)
- Alert on audit log anomalies (many failed logins = brute force attempt)

**Maintenance**:
- Regularly review audit logs for suspicious activity
- Rotate secrets periodically (SECRET_KEY, JWT_SECRET_KEY)
- Update Python dependencies for security patches
- Review and update password complexity policy if needed
- Audit user roles and permissions

---

## Part 10: Future Enhancements & Roadmap

### 10.1 Security Enhancements

1. **Per-File Encryption Keys**: Derive unique key per file from master key
2. **HSM Integration**: Use Hardware Security Module for key storage
3. **Multi-Factor Authentication**: TOTP/WebAuthn instead of simple PIN
4. **Account Lockout**: Temporary lock after N failed login attempts
5. **Session Management**: Logout invalidates tokens immediately (token blacklist)
6. **Encryption Rotation**: Re-encrypt files with new master key
7. **Data Residency**: Compliance with GDPR/CCPA requirements

### 10.2 Performance Enhancements

1. **Async API**: Replace Flask with FastAPI for concurrent request handling
2. **Caching**: Redis for rate limit state and frequently accessed data
3. **Database**: Migrate to PostgreSQL for better concurrency
4. **CDN**: Serve static files and file downloads via CDN
5. **Batch Operations**: Bulk upload, bulk share, bulk delete
6. **Background Jobs**: Move Groq API calls to async queue (Celery)

### 10.3 Feature Enhancements

1. **Full-Text Search**: Search file contents (indexed)
2. **File Versioning**: Keep history of file modifications
3. **Collaboration**: Real-time collaborative editing (like Google Docs)
4. **File Comments**: Annotations and discussions
5. **Workflow Automation**: Rules for automatic sharing/archiving
6. **Advanced Analytics**: Usage statistics, compliance reports
7. **Mobile Apps**: Native iOS/Android applications

### 10.4 Enterprise Features

1. **SAML/OAuth2 Integration**: Enterprise SSO
2. **Active Directory Sync**: Automatic user provisioning
3. **Compliance Reporting**: HIPAA, SOC2, ISO 27001 reports
4. **Data Classification**: Automatic DLP (Data Loss Prevention)
5. **Audit Retention**: Long-term audit log storage (tape archive)
6. **High Availability**: Multi-region deployment, failover

---

## Summary

This Secure File Management System is a comprehensive, production-ready application combining:
- **Security**: Encryption at rest, access control, threat detection, audit logging
- **Usability**: Intuitive UI, AI-powered guidance, file preview
- **Reliability**: Atomic operations, transaction integrity, backup procedures
- **Scalability**: Modular architecture, API-first design, stateless authentication

The system follows security best practices while maintaining ease of use for both technical and non-technical users. The modular architecture enables future enhancements without major refactoring.

Key architectural decisions balance security with performance:
- Single master key (simple) vs. per-file keys (complex but better isolation)
- In-memory rate limiting (fast) vs. persistent rate limiting (reliable across restarts)
- Synchronous Flask (simple) vs. async API (scalable)
- SQLite (simple) vs. PostgreSQL (scalable)

Each decision made with documented trade-offs for future optimization.
