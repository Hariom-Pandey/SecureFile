import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Directory for persistent data
_DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(_DATA_DIR, exist_ok=True)


def _load_or_create_key(filepath):
    """Load a secret key from file, or generate and save one if it doesn't exist."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(filepath, "w") as f:
        f.write(key)
    return key


_SECRET_KEY_FILE = os.path.join(_DATA_DIR, ".secret_key")
_JWT_SECRET_KEY_FILE = os.path.join(_DATA_DIR, ".jwt_secret_key")


def _load_env_file():
    """Load simple KEY=VALUE pairs from local .env files if present."""
    candidates = [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(os.path.dirname(BASE_DIR), ".env"),
    ]

    for path in candidates:
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except OSError:
            pass


_load_env_file()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or _load_or_create_key(_SECRET_KEY_FILE)
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or _load_or_create_key(_JWT_SECRET_KEY_FILE)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour in seconds

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL = os.environ.get("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")
    GROQ_API_URL = os.environ.get(
        "GROQ_API_URL",
        "https://api.groq.com/openai/v1/chat/completions",
    )
    GROQ_MAX_INPUT_CHARS = int(os.environ.get("GROQ_MAX_INPUT_CHARS", "2500"))
    GROQ_REQUIRE_SUCCESS = os.environ.get("GROQ_REQUIRE_SUCCESS", "true").lower() in {
        "1", "true", "yes", "on"
    }
    AI_RATE_LIMIT_PER_MINUTE = 30
    BOT_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("BOT_RATE_LIMIT_WINDOW_SECONDS", "60"))

    DATABASE_PATH = os.path.join(BASE_DIR, "data", "secure_files.db")
    STORAGE_PATH = os.path.join(BASE_DIR, "storage")
    UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 50 MB

    # Encryption
    ENCRYPTION_KEY_FILE = os.path.join(BASE_DIR, "data", "master.key")

    # Threat detection
    MAX_INPUT_LENGTH = 10000
    
    # Allowed for upload (comprehensive list)
    ALLOWED_EXTENSIONS = {
        # Documents
        ".txt", ".md", ".rst", ".rtf", ".pdf", ".doc", ".docx", ".odt",
        # Spreadsheets
        ".xls", ".xlsx", ".csv", ".ods", ".tsv",
        # Presentations
        ".ppt", ".pptx", ".odp",
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".ico",
        # Audio/Video
        ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg",
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v",
        # Archives
        ".zip", ".7z", ".tar", ".gz", ".rar", ".bz2", ".xz",
        # Data formats
        ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
        # Code/Scripts (safe - code editors don't execute them)
        ".py", ".js", ".java", ".cpp", ".c", ".cs", ".go", ".rs", ".rb", ".php", ".sh", ".bash",
        ".sql", ".html", ".css", ".ts", ".jsx", ".tsx", ".vue",
        # Other
        ".sql", ".db", ".sqlite", ".log", ".dat", ".bin", ".hex",
    }
    
    # Strictly blocked (dangerous executables & system-critical files only)
    BLOCKED_EXTENSIONS = {
        # Windows executables & installers
        ".exe", ".msi", ".scr", ".com", ".bat", ".cmd", ".pif",
        # Dangerous scripts that can auto-execute
        ".vbs", ".vbe", ".ws", ".wsf", ".msi",
        # System/DLL files
        ".dll", ".sys", ".drv", ".lot",
        # macOS executable
        ".app", ".deb", ".rpm",
    }
