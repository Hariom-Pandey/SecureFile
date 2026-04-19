# Installation Guide

## System Requirements

### Minimum Hardware
- **Processor**: Intel/AMD 2GHz dual-core
- **RAM**: 2 GB
- **Storage**: 5 GB (20 GB recommended)
- **Network**: 100 Mbps connection

### Operating System
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)

## Quick Start

### Step 1: Clone Repository
```bash
git clone https://github.com/Hariom-Pandey/SecureFile.git
cd SecureFile
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r project/requirements.txt
```

### Step 4: Configure Environment (Optional)

Create `.env` file in project root:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
AI_RATE_LIMIT_PER_MINUTE=30
UPLOAD_MAX_SIZE=52428800
```

**Note**: If `.env` not provided, system auto-generates secrets on first run.

### Step 5: Run Application

```bash
cd project
python main.py
```

Application starts at: `http://127.0.0.1:5000`

### Step 6: Access Dashboard
1. Open browser to `http://127.0.0.1:5000/login`
2. Register new account
3. Login and start using SecureFile

## Alternative Launch Methods

### Using npm (requires Node.js)
```bash
npm run server    # Backend only
npm run dev       # Frontend dev server
npm start         # Both together
```

### Using http-server (frontend)
```bash
cd project
npx http-server -p 3000
```

## Enable AI Features (Optional)

Get free Groq API key: https://console.groq.com

Set environment variable:
```bash
export GROQ_API_KEY=your_api_key_here
```

Restart application to activate AI insights and bot assistant.

## Troubleshooting

### Port Already in Use
```bash
# Find process on port 5000
netstat -ano | findstr :5000
# Kill it
taskkill /PID <PID> /F
```

### File Upload Fails
- Check file size (max 50 MB)
- Verify file extension allowed
- Ensure `project/storage/` directory exists

### Encryption Key Missing
- Auto-generated on first run
- Stored in `.data/master.key`
- Always backup `.data/` directory

### Database Locked
- Wait a few seconds and retry
- For production: migrate to PostgreSQL
- Restart app if persistent

## Run Tests

```bash
# All tests
pytest project/tests/ -v

# Specific test file
pytest project/tests/test_auth.py -v

# Specific test
pytest project/tests/test_auth.py::test_register -v
```

## Performance Tips

- **Large Files**: Use SSD for faster encryption
- **Many Users**: Consider PostgreSQL instead of SQLite
- **Production**: Use nginx as reverse proxy

## Next Steps

- Check [README.md](README.md) for project overview
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API details
- Review [LICENSE.md](LICENSE.md) for licensing info
