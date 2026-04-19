from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from app.auth.authentication import AuthenticationService
from app.auth.two_factor import TwoFactorAuth
from app.models.user import User
from app.models.audit_log import AuditLog
from app.detection.threat_detector import ThreatDetector
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _get_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def _current_user_id():
    identity = get_jwt_identity()
    if not identity:
        return None
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def _reject_pending_second_step_token():
    claims = get_jwt()
    if claims.get("2fa_pending"):
        return jsonify({"error": "Second-step PIN verification is required."}), 403
    return None


@auth_bp.route('/register', methods=['POST'])
def register():
    data = _get_json_body()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = 'user'

    # Input validation against threats
    safe, msg = ThreatDetector.check_input_length(username, "username")
    if not safe:
        return jsonify({"error": msg}), 400

    safe, msg = ThreatDetector.check_injection(username)
    if not safe:
        return jsonify({"error": msg}), 400

    user, message = AuthenticationService.register(username, password, role)
    if not user:
        return jsonify({"error": message}), 400

    return jsonify({
        "message": message,
        "user": user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = _get_json_body()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')
    ip_address = request.remote_addr

    user, message = AuthenticationService.login(username, password, ip_address)

    if not user:
        return jsonify({"error": message}), 401

    if message in ("2FA_REQUIRED", "PIN_REQUIRED"):
        # Issue a temporary token for second-step PIN verification
        temp_token = create_access_token(
            identity=str(user.id),
            additional_claims={"2fa_pending": True},
            expires_delta=timedelta(minutes=5)
        )
        return jsonify({
            "message": "PIN verification required.",
            "requires_2fa": True,
            "requires_pin": True,
            "temp_token": temp_token,
        }), 200

    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    )
    return jsonify({
        "message": message,
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


@auth_bp.route('/verify-2fa', methods=['POST'])
@jwt_required()
def verify_2fa():
    data = _get_json_body()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    claims = get_jwt()
    if not claims.get("2fa_pending"):
        return jsonify({"error": "Invalid 2FA verification token."}), 403

    otp_code = str(data.get('pin_code', data.get('otp_code', '')))
    if not otp_code:
        return jsonify({"error": "PIN code is required."}), 400

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    success, message = TwoFactorAuth.verify_otp(user_id, otp_code)
    if not success:
        return jsonify({"error": message}), 401

    # Issue a full access token
    access_token = create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    )

    user = User.get_by_id(user_id)
    return jsonify({
        "message": "Login successful.",
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


@auth_bp.route('/setup-2fa', methods=['POST'])
@jwt_required()
def setup_2fa():
    blocked = _reject_pending_second_step_token()
    if blocked:
        return blocked

    data = _get_json_body()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    pin_code = str(data.get('pin_code', ''))
    if not pin_code:
        return jsonify({"error": "PIN code is required."}), 400

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    result, message = TwoFactorAuth.setup_2fa(user_id, pin_code)
    if not result:
        return jsonify({"error": message}), 400

    return jsonify({
        "message": message,
        "setup": result,
    }), 200


@auth_bp.route('/confirm-2fa', methods=['POST'])
@jwt_required()
def confirm_2fa():
    blocked = _reject_pending_second_step_token()
    if blocked:
        return blocked

    data = _get_json_body()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    pin_code = str(data.get('pin_code', data.get('otp_code', '')))
    if not pin_code:
        return jsonify({"error": "PIN code is required."}), 400

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    success, message = TwoFactorAuth.confirm_2fa(user_id, None, pin_code)
    if not success:
        return jsonify({"error": message}), 400

    return jsonify({"message": message}), 200


@auth_bp.route('/disable-2fa', methods=['POST'])
@jwt_required()
def disable_2fa():
    blocked = _reject_pending_second_step_token()
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    success, message = TwoFactorAuth.disable_2fa(user_id)
    if not success:
        return jsonify({"error": message}), 400

    return jsonify({"message": message}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    blocked = _reject_pending_second_step_token()
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route('/audit-log', methods=['GET'])
@jwt_required()
def get_audit_log():
    blocked = _reject_pending_second_step_token()
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    if user.role == "admin":
        logs = AuditLog.get_logs(limit=200)
    else:
        logs = AuditLog.get_logs(limit=100, user_id=user_id)

    return jsonify({"logs": logs}), 200
