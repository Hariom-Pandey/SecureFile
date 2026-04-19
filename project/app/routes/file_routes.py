import base64
import binascii
from html import escape
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from io import BytesIO
from config import Config
from app.files.file_operations import FileOperations
from app.files.preview_converter import PreviewConverter
from app.files.bot_service import BotService
from app.detection.threat_detector import ThreatDetector
from app.models.audit_log import AuditLog

file_bp = Blueprint('files', __name__, url_prefix='/api/files')


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


def _reject_pending_second_step_claims(claims):
    if claims.get("2fa_pending"):
        return jsonify({"error": "Second-step PIN verification is required."}), 403
    return None


def _status_from_message(message, denied_default=403):
    text = (message or "").lower()
    if "not found" in text:
        return 404
    if "denied" in text or "permission" in text:
        return denied_default
    return denied_default


def _build_bot_project_context(user_id):
    """Collect compact, non-sensitive dashboard context for AI bot answers."""
    files = FileOperations.list_user_files(user_id)
    owned = files.get('owned', [])
    shared = files.get('shared', [])

    recent_owned = [f.get('filename') for f in owned[:5] if f.get('filename')]
    share_history, _ = FileOperations.get_share_history(user_id, limit=5)
    recent_share_targets = [r.get('target_username') for r in share_history[:5] if r.get('target_username')]

    recent_logs = AuditLog.get_logs(limit=10, user_id=user_id)
    recent_actions = []
    for row in recent_logs:
        action = row.get('action')
        if action and action not in recent_actions:
            recent_actions.append(action)

    return {
        'counts': {
            'owned_files': len(owned),
            'shared_with_me': len(shared),
            'encrypted_files': len([f for f in (owned + shared) if f.get('is_encrypted')]),
        },
        'recent_owned_files': recent_owned,
        'recent_share_targets': recent_share_targets,
        'recent_actions': recent_actions[:6],
    }


@file_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    if 'file' in request.files:
        # Multipart file upload
        uploaded = request.files['file']
        if not uploaded.filename:
            return jsonify({"error": "No file selected."}), 400

        filename = uploaded.filename
        file_data = uploaded.read()
    else:
        # JSON-based upload (base64 encoded)
        data = _get_json_body()
        if not data:
            return jsonify({"error": "File data is required."}), 400

        filename = data.get('filename', '')
        file_content = data.get('content', '')

        if not filename or not file_content:
            return jsonify({"error": "Filename and content are required."}), 400

        # Input validation
        safe, msg = ThreatDetector.check_input_length(filename, "filename")
        if not safe:
            return jsonify({"error": msg}), 400

        try:
            file_data = base64.b64decode(file_content, validate=True)
        except (binascii.Error, ValueError, TypeError):
            # Treat as plain text
            file_data = file_content.encode('utf-8')

    record, messages = FileOperations.upload_file(filename, file_data, user_id)
    if not record:
        return jsonify({"errors": messages}), 400

    return jsonify({
        "message": messages[0],
        "file": record.to_dict()
    }), 201


@file_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def read_file(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    result, message = FileOperations.read_file(file_id, user_id)
    if not result:
        return jsonify({"error": message}), _status_from_message(message)

    # Return file content as base64
    return jsonify({
        "message": message,
        "file": {
            "filename": result["filename"],
            "content": base64.b64encode(result["data"]).decode('utf-8'),
            "file_type": result["file_type"],
            "size": result["size"],
        }
    }), 200


@file_bp.route('/<int:file_id>/preview', methods=['GET'])
def preview_file(file_id):
    # Allow token from Authorization header or query parameter
    token = None
    user_id = None
    
    # Try to get token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    # If no header token, try query parameter
    if not token:
        token = request.args.get('token', '')
    
    if not token:
        return jsonify({"error": "Authentication required."}), 401
    
    # Verify the token manually
    from flask_jwt_extended import decode_token
    try:
        decoded = decode_token(token)
        blocked = _reject_pending_second_step_claims(decoded)
        if blocked:
            return blocked
        user_id = int(decoded.get('sub', 0))
    except Exception as e:
        return jsonify({"error": "Invalid token."}), 401
    
    if not user_id:
        return jsonify({"error": "Invalid authentication token."}), 401

    result, message = FileOperations.read_file(file_id, user_id)
    if not result:
        return jsonify({"error": message}), _status_from_message(message)

    file_type = result.get("file_type", "").lower()
    filename = result.get("filename", "file")
    file_data = result.get("data", b"")
    raw_mode = request.args.get('mode', '').lower() == 'raw'

    mime_mapping = {
        # Documents
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'log': 'text/plain',
        'rst': 'text/plain',
        'rtf': 'application/rtf',
        'md': 'text/markdown',
        'json': 'application/json',
        'xml': 'application/xml',
        'csv': 'text/csv',
        'tsv': 'text/tab-separated-values',
        'yaml': 'application/yaml',
        'yml': 'application/yaml',
        'toml': 'application/toml',
        'ini': 'text/plain',
        'cfg': 'text/plain',
        'conf': 'text/plain',
        'odt': 'application/vnd.oasis.opendocument.text',
        'ods': 'application/vnd.oasis.opendocument.spreadsheet',
        'odp': 'application/vnd.oasis.opendocument.presentation',
        # Office
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        # Images
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'tif': 'image/tiff',
        'tiff': 'image/tiff',
        'svg': 'image/svg+xml',
        'ico': 'image/x-icon',
        # Audio
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'flac': 'audio/flac',
        'aac': 'audio/aac',
        'm4a': 'audio/mp4',
        'ogg': 'audio/ogg',
        # Video
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'mkv': 'video/x-matroska',
        'flv': 'video/x-flv',
        'wmv': 'video/x-ms-wmv',
        'm4v': 'video/x-m4v',
        # Archives
        'zip': 'application/zip',
        '7z': 'application/x-7z-compressed',
        'rar': 'application/x-rar-compressed',
        'tar': 'application/x-tar',
        'gz': 'application/gzip',
        'bz2': 'application/x-bzip2',
        'xz': 'application/x-xz',
    }

    # Native/raw preview mode bypasses converters and returns the original file stream.
    if raw_mode:
        mime_type = mime_mapping.get(file_type, 'application/octet-stream')
        return send_file(
            BytesIO(file_data),
            mimetype=mime_type,
            as_attachment=False,
            download_name=filename
        )

    # For PPT/PPTX on Windows, prefer MS PowerPoint-driven PDF page preview when available.
    if file_type in {'ppt', 'pptx'}:
        ms_pdf = PreviewConverter.convert_presentation_to_pdf_with_ms_office(file_data, filename, file_type)
        if ms_pdf:
            pdf_name = f"{filename.rsplit('.', 1)[0]}.pdf" if '.' in filename else f"{filename}.pdf"
            return send_file(
                BytesIO(ms_pdf),
                mimetype='application/pdf',
                as_attachment=False,
                download_name=pdf_name
            )

    # Provide robust inline preview for text/code/data files.
    text_preview_types = {
        'txt', 'md', 'log', 'rst', 'json', 'xml', 'csv', 'tsv',
        'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
        'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'cs',
        'go', 'rs', 'rb', 'php', 'sh', 'bash', 'sql', 'html', 'css', 'vue', 'dat', 'hex'
    }
    
    # Try to convert file to preview HTML (for documents)
    try:
        preview_result = PreviewConverter.convert_file(file_data, filename, file_type)
        
        if preview_result and not preview_result.get('error'):
            # Return JSON with HTML preview
            return jsonify({
                "type": "html",
                "preview": preview_result,
                "filename": filename
            }), 200
    except Exception as e:
        import traceback
        print(f"Preview conversion error: {str(e)}")
        traceback.print_exc()

    if file_type in text_preview_types:
        text = file_data.decode('utf-8', errors='ignore')
        if len(text) > 50000:
            text = text[:50000] + '\n\n... [File truncated for preview] ...'

        return jsonify({
            "type": "html",
            "preview": {
                "type": "text",
                "html": (
                    '<pre style="white-space:pre-wrap;max-height:70vh;overflow:auto;'
                    'background:#0f1320;padding:14px;border-radius:8px;font-size:.85rem;'
                    f'line-height:1.5;font-family:monospace;">{escape(text)}</pre>'
                )
            },
            "filename": filename
        }), 200
    
    # Fallback: return raw file with proper MIME type (for images, PDFs, audio, video)
    mime_type = mime_mapping.get(file_type, 'application/octet-stream')
    
    # Send file with proper MIME type for inline preview
    return send_file(
        BytesIO(file_data),
        mimetype=mime_type,
        as_attachment=False,
        download_name=filename
    )


@file_bp.route('/<int:file_id>', methods=['PUT'])
@jwt_required()
def write_file(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    data = _get_json_body()

    if not data or 'content' not in data:
        return jsonify({"error": "Content is required."}), 400

    content = data['content']
    try:
        file_data = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError, TypeError):
        file_data = content.encode('utf-8')

    success, message = FileOperations.write_file(file_id, file_data, user_id)
    if not success:
        if isinstance(message, list):
            return jsonify({"errors": message}), 400
        return jsonify({"error": message}), _status_from_message(message)

    return jsonify({"message": message}), 200


@file_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    success, message = FileOperations.delete_file(file_id, user_id)
    if not success:
        return jsonify({"error": message}), _status_from_message(message)

    return jsonify({"message": message}), 200


@file_bp.route('/<int:file_id>/metadata', methods=['GET'])
@jwt_required()
def get_metadata(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    metadata, message = FileOperations.get_metadata(file_id, user_id)
    if not metadata:
        return jsonify({"error": message}), _status_from_message(message)

    return jsonify({
        "message": message,
        "metadata": metadata
    }), 200


@file_bp.route('/<int:file_id>/insights', methods=['GET'])
@jwt_required()
def get_file_insights(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    allowed, retry_after = BotService.check_user_ai_rate_limit(user_id)
    if not allowed:
        return jsonify({
            "error": f"Rate limited at {Config.AI_RATE_LIMIT_PER_MINUTE}/min. Please wait {retry_after} seconds.",
            "retry_after": retry_after,
        }), 429

    insights, message = FileOperations.get_ai_insights(file_id, user_id)
    if not insights:
        return jsonify({"error": message}), _status_from_message(message)

    return jsonify({
        "message": message,
        "insights": insights
    }), 200


@file_bp.route('/<int:file_id>/history', methods=['GET'])
@jwt_required()
def get_file_history(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    history, message = FileOperations.get_file_history(file_id, user_id)
    if history is None:
        return jsonify({"error": message}), _status_from_message(message)

    return jsonify({
        "message": message,
        "history": history
    }), 200


@file_bp.route('/share-history', methods=['GET'])
@jwt_required()
def get_share_history():
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    records, message = FileOperations.get_share_history(user_id)
    return jsonify({
        "message": message,
        "records": records
    }), 200


@file_bp.route('/', methods=['GET'])
@jwt_required()
def list_files():
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    files = FileOperations.list_user_files(user_id)
    return jsonify({"files": files}), 200


@file_bp.route('/<int:file_id>/share', methods=['POST'])
@jwt_required()
def share_file(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    data = _get_json_body()

    if not data:
        return jsonify({"error": "Request body is required."}), 400

    target_username = data.get('username', '').strip()
    permission = data.get('permission', 'read').strip()

    if not target_username:
        return jsonify({"error": "Target username is required."}), 400

    # Validate input
    safe, msg = ThreatDetector.check_injection(target_username)
    if not safe:
        return jsonify({"error": msg}), 400

    success, message = FileOperations.share_file(
        file_id, target_username, permission, user_id
    )
    if not success:
        return jsonify({"error": message}), _status_from_message(message)

    return jsonify({"message": message}), 200


@file_bp.route('/<int:file_id>/revoke', methods=['POST'])
@jwt_required()
def revoke_access(file_id):
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    data = _get_json_body()

    if not data:
        return jsonify({"error": "Request body is required."}), 400

    from app.models.user import User
    target_username = data.get('username', '').strip()
    if not target_username:
        return jsonify({"error": "Target username is required."}), 400

    target = User.get_by_username(target_username)
    if not target:
        return jsonify({"error": "User not found."}), 404

    from app.protection.access_control import AccessControlService
    success, message = AccessControlService.revoke_access(
        file_id, target.id, user_id
    )
    if not success:
        return jsonify({"error": message}), _status_from_message(message)

    return jsonify({"message": message}), 200


@file_bp.route('/bot/message', methods=['POST'])
@jwt_required()
def bot_message():
    """Process user message through AI bot with rate limiting."""
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    data = _get_json_body()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    message = data.get('message', '').strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400

    context_data = data.get('context', {})
    if not isinstance(context_data, dict):
        context_data = {}

    if BotService._needs_project_context(message):
        context_data['project_context'] = _build_bot_project_context(user_id)

    # Process message with user_id for rate limiting
    response = BotService.process_message(message, context_data, user_id)

    return jsonify(response), 200 if response.get('success') else 429 if response.get('type') == 'rate_limit' else 400


@file_bp.route('/bot/tips', methods=['GET'])
@jwt_required()
def bot_tips():
    """Get quick security and productivity tips."""
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    tips = BotService.get_quick_tips()
    return jsonify({"tips": tips}), 200


@file_bp.route('/bot/topics', methods=['GET'])
@jwt_required()
def bot_help_topics():
    """Get available help topics."""
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    topics = BotService.get_help_topics()
    return jsonify({"topics": topics}), 200


@file_bp.route('/bot/context', methods=['GET'])
@jwt_required()
def bot_context():
    """Get lightweight project-wide context for bot UI and prompts."""
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    context = _build_bot_project_context(user_id)
    return jsonify({"context": context}), 200


@file_bp.route('/bot/capabilities', methods=['GET'])
@jwt_required()
def bot_capabilities():
    """Expose bot capabilities to render quick-action chips in UI."""
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    return jsonify({
        "capabilities": [
            "File sharing guidance",
            "Security best practices",
            "Permission troubleshooting",
            "Dashboard navigation help",
            "Audit and activity explanation",
            "AI insights usage guidance",
        ],
        "quick_prompts": []
    }), 200


@file_bp.route('/bot/user-files', methods=['GET'])
@jwt_required()
def bot_get_user_files():
    """Get user's files for bot file selection prompts."""
    blocked = _reject_pending_second_step_claims(get_jwt())
    if blocked:
        return blocked

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid authentication token."}), 401

    files = FileOperations.list_user_files(user_id)
    owned = files.get('owned', [])
    
    # Return compact file list for bot UI
    file_list = [
        {
            'id': f['id'],
            'filename': f['filename'],
            'file_type': f.get('file_type', ''),
            'size': f.get('file_size', f.get('size', 0)),
            'is_encrypted': f.get('is_encrypted', False),
            'upload_date': f.get('created_at', f.get('upload_date', '')),
        }
        for f in owned[:20]  # Limit to 20 most recent
    ]

    return jsonify({
        'success': True,
        'files': file_list,
        'total': len(owned),
    }), 200
