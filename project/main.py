import os
import sys
from urllib.parse import urlparse
from flask import Flask, render_template, redirect, jsonify, request
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.models.database import init_db
from app.routes.auth_routes import auth_bp
from app.routes.file_routes import file_bp


def create_app(testing=False):
    """Application factory."""
    def _is_allowed_dev_origin(origin):
        if not origin:
            return False
        try:
            parsed = urlparse(origin)
        except Exception:
            return False

        if parsed.scheme not in ('http', 'https'):
            return False

        host = parsed.hostname
        port = parsed.port
        if host not in ('127.0.0.1', 'localhost'):
            return False
        return isinstance(port, int) and 1 <= port <= 65535

    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Configuration
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(
        seconds=Config.JWT_ACCESS_TOKEN_EXPIRES
    )
    app.config['MAX_CONTENT_LENGTH'] = Config.UPLOAD_MAX_SIZE

    if testing:
        app.config['TESTING'] = True

    # Initialize extensions
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauthorized_callback(_reason):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Missing or invalid authorization token."}), 401
        return redirect('/login')

    @jwt.invalid_token_loader
    def invalid_token_callback(_reason):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Invalid authentication token."}), 401
        return redirect('/login')

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Authentication token has expired."}), 401
        return redirect('/login')

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Authentication token has been revoked."}), 401
        return redirect('/login')

    @app.after_request
    def apply_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        if request.path.startswith('/api/'):
            origin = request.headers.get('Origin')
            if _is_allowed_dev_origin(origin):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Vary'] = 'Origin'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(file_bp)

    # ── Frontend routes ──
    @app.route('/')
    def index():
        return redirect('/login')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        return {"status": "ok", "service": "Secure File Management System"}, 200

    # Initialize database
    with app.app_context():
        init_db()

    return app


if __name__ == '__main__':
    app = create_app()
    print("\n=== Secure File Management System ===")
    print("Server running at http://127.0.0.1:5000")
    print("\nFrontend:")
    print("  http://127.0.0.1:5000/login       - Login page")
    print("  http://127.0.0.1:5000/register     - Registration page")
    print("  http://127.0.0.1:5000/dashboard    - Dashboard")
    print("\nAPI Endpoints:")
    print("  POST   /api/auth/register     - Register a new user")
    print("  POST   /api/auth/login        - Login")
    print("  POST   /api/auth/verify-2fa   - Verify 2FA OTP")
    print("  POST   /api/auth/setup-2fa    - Set up 2FA")
    print("  POST   /api/auth/confirm-2fa  - Confirm 2FA setup")
    print("  POST   /api/auth/disable-2fa  - Disable 2FA")
    print("  GET    /api/auth/me           - Current user info")
    print("  GET    /api/auth/audit-log    - View audit logs")
    print("  POST   /api/files/upload      - Upload a file")
    print("  GET    /api/files/            - List user files")
    print("  GET    /api/files/<id>        - Read/download a file")
    print("  PUT    /api/files/<id>        - Update a file")
    print("  DELETE /api/files/<id>        - Delete a file")
    print("  GET    /api/files/<id>/metadata - View file metadata")
    print("  POST   /api/files/<id>/share  - Share a file")
    print("  POST   /api/files/<id>/revoke - Revoke file access")
    print("=" * 40)
    app.run(debug=False, host='127.0.0.1', port=5000)
