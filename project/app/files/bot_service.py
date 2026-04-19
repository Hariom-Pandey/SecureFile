import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from config import Config

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class BotService:
    """Handles AI bot responses using Groq API for system-wide support."""

    # Rate limiting state per user
    _request_history = {}  # {user_id: [timestamp, timestamp, ...]}
    
    CONTEXT_SYSTEM_PROMPT = (
        'You are a helpful, beginner-friendly AI assistant for a Secure File Manager application. '
        'You provide clear, simple guidance for file operations, sharing, security, and troubleshooting. '
        'ALWAYS assume users may be first-time users - explain concepts simply without jargon. '
        'For file operations (share, preview, archive, encrypt), ALWAYS ask which file the user wants to work with. '
        'Use provided context fields only when relevant to the user question. '
        'Do not repeat dashboard stats for casual greetings or chit-chat. '
        'Be warm, encouraging, and concise, usually 30-100 words. Use simple language. '
        'If user asks for steps, return numbered steps with clear explanations. '
        'If user asks security-sensitive questions, explain in simple terms with practical advice. '
        'Never provide credentials, secrets, keys, or bypass recommendations.'
    )

    @staticmethod
    def _model_candidates():
        models = [Config.GROQ_MODEL, getattr(Config, 'GROQ_FALLBACK_MODEL', '')]
        return [m for i, m in enumerate(models) if m and m not in models[:i]]

    @staticmethod
    def _check_rate_limit(user_id, user_limit):
        """Check if user has exceeded rate limit. Returns (allowed, retry_after_seconds)."""
        current_time = time.time()
        request_window = getattr(Config, 'BOT_RATE_LIMIT_WINDOW_SECONDS', 60)
        
        if user_id not in BotService._request_history:
            BotService._request_history[user_id] = []

        # Clean old requests outside the window
        requests = BotService._request_history[user_id]
        requests[:] = [ts for ts in requests if current_time - ts < request_window]

        if len(requests) >= user_limit:
            oldest_request = min(requests)
            retry_after = request_window - (current_time - oldest_request)
            return False, int(retry_after) + 1

        requests.append(current_time)
        return True, 0

    @staticmethod
    def check_user_ai_rate_limit(user_id):
        """Developer-defined per-user AI rate limit used across bot and insights."""
        user_limit = getattr(Config, 'AI_RATE_LIMIT_PER_MINUTE', 30)
        return BotService._check_rate_limit(user_id, user_limit)

    @staticmethod
    def process_message(user_message, context_data=None, user_id=None):
        """
        Process user message and return AI bot response.
        
        Args:
            user_message (str): User query
            context_data (dict): Optional context (file info, user role, etc)
            user_id (int): User ID for rate limiting
        
        Returns:
            dict: Response with 'success', 'message', 'type' (help/info/action)
        """
        # Check developer-defined rate limit (shared AI budget per user)
        if user_id:
            user_limit = getattr(Config, 'AI_RATE_LIMIT_PER_MINUTE', 30)
            allowed, retry_after = BotService.check_user_ai_rate_limit(user_id)
            if not allowed:
                return {
                    'success': False,
                    'message': f'Rate limited at {user_limit}/min. Please wait {retry_after} seconds.',
                    'type': 'rate_limit',
                    'retry_after': retry_after,
                }
        
        if not Config.GROQ_API_KEY:
            return {
                'success': False,
                'message': 'AI assistant is temporarily unavailable. Please check back later.',
                'type': 'error',
            }

        if not user_message or not isinstance(user_message, str):
            return {
                'success': False,
                'message': 'Please provide a valid question or command.',
                'type': 'error',
            }

        user_message = user_message.strip()
        if len(user_message) > 500:
            user_message = user_message[:500]

        # Handle simple conversational messages with short, friendly replies.
        small_talk = BotService._small_talk_reply(user_message)
        if small_talk:
            return {
                'success': True,
                'message': small_talk,
                'type': 'chat',
                'source': 'small_talk',
                'agent_actions': BotService._build_action_suggestions(user_message, context_data or {}),
                'needs_file_selection': False,
            }

        intent_reply = BotService._intent_reply(user_message, context_data or {})
        if intent_reply:
            return {
                'success': True,
                'message': intent_reply,
                'type': 'help',
                'source': 'intent_local',
                'agent_actions': BotService._build_action_suggestions(user_message, context_data or {}),
                'needs_file_selection': BotService._needs_file_selection(user_message, context_data or {}),
            }

        # Build context-aware prompt
        context_str = ''
        include_project_context = BotService._needs_project_context(user_message)
        if context_data:
            if context_data.get('current_file'):
                context_str += f"\nCurrent file context: {context_data.get('current_file')}"
            if context_data.get('user_role'):
                context_str += f"\nUser role: {context_data.get('user_role')}"
            if context_data.get('action_type'):
                context_str += f"\nTrying to: {context_data.get('action_type')}"
            if context_data.get('current_page'):
                context_str += f"\nCurrent dashboard page: {context_data.get('current_page')}"
            if include_project_context and context_data.get('project_context'):
                context_str += f"\nProject context: {json.dumps(context_data.get('project_context'), ensure_ascii=True)}"

        user_content = f"{user_message}{context_str}"

        messages = [
            {
                'role': 'system',
                'content': BotService.CONTEXT_SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': user_content,
            },
        ]

        # Single request-path with model fallback to reduce quota burn
        model_errors = []
        for model_name in BotService._model_candidates():
            http_response, http_error, is_rate_limited = BotService._request_via_http(messages, model_name)
            if http_response:
                return {
                    'success': True,
                    'message': http_response,
                    'type': BotService._classify_response(user_message, http_response),
                    'source': 'groq_http',
                    'engine': f'groq:{model_name}',
                    'agent_actions': BotService._build_action_suggestions(user_message, context_data or {}),
                    'needs_file_selection': BotService._needs_file_selection(user_message, context_data or {}),
                }

            if http_error:
                model_errors.append(http_error)

            # If current model is rate-limited, try next fallback model.
            if is_rate_limited:
                continue

            # For non-rate limit failures, avoid excessive retries.
            break

        error_msg = ' | '.join(model_errors).lower()
        if 'rate_limit' in error_msg or '429' in error_msg:
            return {
                'success': False,
                'message': 'Model quota is temporarily exhausted. Please retry shortly.',
                'type': 'rate_limit',
            }
        if 'auth' in error_msg or 'invalid' in error_msg or '401' in error_msg:
            return {
                'success': False,
                'message': 'AI assistant authentication issue. Please try again later.',
                'type': 'auth_error',
            }

        return {
            'success': True,
            'message': BotService._get_fallback_response(user_message),
            'type': 'fallback',
            'source': 'local_fallback',
            'agent_actions': BotService._build_action_suggestions(user_message, context_data or {}),
            'needs_file_selection': BotService._needs_file_selection(user_message, context_data or {}),
        }

    @staticmethod
    def _small_talk_reply(query):
        text = (query or '').strip().lower()
        if text in {'hi', 'hello', 'hey', 'hii'}:
            return 'Hi! I can help with open, share, preview, security checks, and audit reports. What would you like to do?'
        if 'how are you' in text:
            return 'Doing great and ready to help. What would you like to do right now?'
        if text in {'thanks', 'thank you', 'thx'}:
            return 'You are welcome. Want me to help with sharing, upload, or security next?'
        return None

    @staticmethod
    def _needs_file_selection(query, context_data=None):
        """Check if user query requires file selection (share, preview, delete, etc)."""
        query_lower = (query or '').lower()
        context_data = context_data or {}
        if context_data.get('current_file'):
            return False
        file_operation_keywords = [
            'share', 'shared', 'preview', 'open', 'view', 'delete', 'archive', 'encrypt',
            'permissions', 'access', 'insight', 'analyze', 'analysis', 'download', 'move'
        ]
        return any(word in query_lower for word in file_operation_keywords)

    @staticmethod
    def _intent_reply(query, context_data):
        text = (query or '').strip().lower()
        selected_file = (context_data or {}).get('current_file', '')

        if any(word in text for word in ['open file', 'preview file', 'open document', 'preview']):
            if selected_file:
                return f'Great choice. I can open "{selected_file}" now. Click Preview below to continue.'
            return 'Sure. Please choose a file below, then click Preview.'

        if any(word in text for word in ['threat', 'threat detection', 'scan', 'security scan']):
            return 'I can show threat results quickly. Click View Threats to open Security and run checks.'

        if any(word in text for word in ['security audit report', 'audit report', 'generate report']):
            return 'I can generate a security audit report from activity logs. Click Security Report below.'

        return None

    @staticmethod
    def _needs_project_context(query):
        query_lower = (query or '').lower()
        context_keywords = {
            'status', 'dashboard', 'overview', 'count', 'how many', 'recent',
            'shared', 'encrypted', 'activity', 'audit', 'report', 'summary'
        }
        return any(word in query_lower for word in context_keywords)

    @staticmethod
    def _build_action_suggestions(user_query, context_data):
        """Return lightweight in-app actions the UI can execute. NO API CALLS - local only."""
        query = (user_query or '').lower()
        actions = []

        def add_action(action_id, label, payload=None):
            actions.append({
                'id': action_id,
                'label': label,
                'payload': payload or {},
            })

        def unique_actions(items):
            seen = set()
            result = []
            for action in items:
                key = (action.get('id'), json.dumps(action.get('payload', {}), sort_keys=True))
                if key in seen:
                    continue
                seen.add(key)
                result.append(action)
            return result

        # FILE UPLOAD ACTIONS
        if any(word in query for word in ['upload', 'upoad', 'add file', 'new file', 'import']):
            add_action('open_upload_modal', '📤 Upload File')

        # THREAT DETECTION & SECURITY ACTIONS
        if any(word in query for word in ['threat', 'detection', 'scan', 'malware', 'suspicious', 'virus']):
            add_action('run_threat_detection', '🔍 View Threats')

        # SHARING & PERMISSION ACTIONS
        if any(word in query for word in ['share', 'send', 'permission', 'access', 'collaborate', 'grant']):
            add_action('open_share_for_selected', '👥 Share File')
            add_action('switch_page', '📤 My Shares', {'page': 'shared-by-me'})
            add_action('filter_shared_files', 'View Shared Files')

        # SECURITY & AUDIT ACTIONS
        if any(word in query for word in ['security', '2fa', 'password', 'audit', 'log', 'activity', 'history']):
            add_action('switch_page', '🔐 Security', {'page': 'security'})
            add_action('switch_page', '📋 Activity Log', {'page': 'audit'})
            add_action('view_access_timeline', 'View Access Timeline')

        # ENCRYPTION & DATA PROTECTION ACTIONS
        if any(word in query for word in ['encrypt', 'encrypted', 'protection', 'private', 'secure', 'locked']):
            add_action('list_encrypted_files', '🔒 Encrypted Files')
            add_action('switch_page', '🔐 Security', {'page': 'security'})
            add_action('filter_encrypted', 'Filter by Encryption')

        # FILE PREVIEW & VIEW ACTIONS
        if any(word in query for word in ['preview', 'open', 'view', 'display', 'read', 'watch']):
            add_action('open_preview_for_selected', '👁️ Preview')
            add_action('list_open_files', 'Open Recent Files')

        # AI INSIGHTS & ANALYSIS ACTIONS
        if any(word in query for word in ['insight', 'summary', 'analyze', 'analysis', 'keywords', 'tags', 'smart']):
            add_action('run_ai_insights_selected', '✨ AI Insights')
            add_action('bulk_analyze_files', 'Analyze All Files')

        # FILE MANAGEMENT & ORGANIZATION ACTIONS
        if any(word in query for word in ['archive', 'bulk', 'delete', 'remove', 'manage', 'organize', 'sort']):
            add_action('bulk_archive_action', '📦 Archive Old')
            add_action('filter_by_type', 'Filter by Type')
            add_action('refresh_files', '🔄 Refresh')

        # REPORT & STATISTICS ACTIONS
        if any(word in query for word in ['report', 'summary', 'dashboard', 'status', 'overview', 'stats', 'count']):
            add_action('generate_security_report', '📊 Security Report')
            add_action('show_file_stats', 'File Statistics')
            add_action('refresh_files', '🔄 Refresh')

        # ACCESS CONTROL ACTIONS
        if any(word in query for word in ['access control', 'permissions', 'roles', 'admin', 'delegate']):
            add_action('switch_page', '🔐 Security', {'page': 'security'})
            add_action('list_shared_files', '📤 My Shares')
            add_action('manage_access', 'Manage Access')

        # SEARCH & FILTER ACTIONS
        if any(word in query for word in ['search', 'find', 'filter', 'find file', 'look for']):
            add_action('open_search', '🔍 Search Files')
            add_action('filter_by_date', 'Filter by Date')
            add_action('filter_by_type', 'Filter by Type')

        # BACKUP & EXPORT ACTIONS
        if any(word in query for word in ['backup', 'export', 'download', 'save', 'batch']):
            add_action('bulk_download', '📥 Batch Download')
            add_action('export_metadata', 'Export Metadata')

        # HELP & NAVIGATION ACTIONS
        if any(word in query for word in ['help', 'guide', 'tutorial', 'how to', 'what is']):
            add_action('show_bot_tips', '💡 Quick Tips')
            add_action('show_faq', '❓ FAQ')

        # REFRESH/STATUS ACTIONS
        if any(word in query for word in ['refresh', 'reload', 'status', 'update', 'sync']):
            add_action('refresh_files', '🔄 Refresh')

        # DEFAULT ACTION: TIPS
        if not actions:
            add_action('show_bot_tips', '💡 Quick Tips')

        actions = unique_actions(actions)
        return actions[:3]  # Keep focused and easy to use

    @staticmethod
    def _request_via_http(messages, model_name):
        """Fallback Groq request using direct HTTP to avoid SDK compatibility issues."""
        request_body = {
            'model': model_name,
            'temperature': 0.35,
            'max_tokens': 120,
            'messages': messages,
        }

        request = Request(
            Config.GROQ_API_URL,
            data=json.dumps(request_body).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {Config.GROQ_API_KEY}',
                'Content-Type': 'application/json',
                'User-Agent': 'SecureFileManagerBot/1.0',
            },
            method='POST',
        )

        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            try:
                detail = exc.read().decode('utf-8', errors='ignore')
            except Exception:
                detail = ''
            is_rate_limited = exc.code == 429 or 'rate limit' in detail.lower()
            return None, f'HTTP {exc.code}: {detail[:600]}', is_rate_limited
        except (URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
            return None, str(exc), False

        try:
            content = payload['choices'][0]['message']['content']
            if content and str(content).strip():
                return str(content).strip(), None, False
            return None, 'Empty content returned by Groq API.', False
        except (KeyError, IndexError, TypeError):
            return None, 'Groq API response did not contain chat content.', False

    @staticmethod
    def _get_fallback_response(query):
        """Provide fallback response when Groq API unavailable."""
        query_lower = query.lower()
        
        fallback_responses = {
            'password': 'Strong passwords should be at least 12 characters with uppercase, lowercase, numbers, and special characters. Enable 2FA for additional security.',
            'share': 'Use the Share button to grant file access. Choose read-only for viewing or read & write for collaboration. You can revoke access anytime.',
            'encrypt': 'Files are encrypted at rest using AES encryption. Your encryption key is stored securely. Never share your master key with anyone.',
            'security': 'Security best practices: use strong passwords, enable 2FA, review file permissions regularly, and check audit logs for access activity.',
            'delete': 'Deleted files are permanently removed. Use the delete button carefully. Consider archiving instead of deleting important files.',
            'audit': 'The Audit Log tracks all file access, sharing, and permission changes. Check it regularly for security monitoring.',
            'threat': 'The system includes threat detection to identify suspicious file patterns. Review threat alerts in the Security settings.',
            'permission': 'File permissions control who can view and edit files. Read-only allows viewing. Read & Write allows editing. Revoke access as needed.',
            'preview': 'If preview fails, open file metadata to verify type, then use Preview again. For PPT/PPTX, the app renders via PDF conversion when available.',
            'dashboard': 'Use left navigation to switch sections: My Files, Shared With Me, Shared By Me, Security Settings, and Audit Log. The AI assistant can summarize your current state.',
            'insight': 'AI Insights analyzes a file for summary, keywords, tags, and sensitivity. Select a file and run AI Insights from the feature panel or metadata modal.',
            'upload': 'Click Upload, select your file, then confirm. The system scans and encrypts the file automatically before saving.',
        }
        
        for keyword, response_text in fallback_responses.items():
            if keyword in query_lower:
                return response_text
        
        # Default fallback
        return 'I am having a temporary AI connection issue, but I can still help with quick actions. Try asking for upload, sharing, preview, or security steps.'

    @staticmethod
    def _classify_response(user_query, response):
        """Classify response type based on query and answer."""
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ['how', 'why', 'what', 'explain', 'help']):
            return 'help'
        elif any(word in query_lower for word in ['share', 'permission', 'access', 'security', 'encrypt']):
            return 'security'
        elif any(word in query_lower for word in ['create', 'upload', 'delete', 'move']):
            return 'action'
        elif any(word in query_lower for word in ['error', 'problem', 'issue', 'fail']):
            return 'troubleshooting'
        else:
            return 'info'

    @staticmethod
    def get_quick_tips():
        """Return quick security and productivity tips."""
        tips = [
            'Use strong, unique passwords with 2FA enabled for maximum security.',
            'Always review file permissions before sharing sensitive documents.',
            'Encrypted files are protected at rest. Never share encryption keys.',
            'Set expiration dates on shared links to limit access window.',
            'Check audit logs regularly to monitor file access activity.',
            'Use read-only access when collaborators only need to view files.',
            'Organize files with consistent naming and folder structure.',
            'Back up important files regularly to prevent data loss.',
            'Mark sensitive documents with appropriate sensitivity tags.',
            'Review and revoke old file shares you no longer need.',
        ]
        return tips

    @staticmethod
    def get_help_topics():
        """Return common help topics."""
        return {
            'file_management': 'Upload, organize, and manage your files securely',
            'sharing': 'Share files with colleagues with granular permission control',
            'security': 'Encryption, access controls, and threat detection features',
            'authentication': '2FA setup, password management, and session security',
            'troubleshooting': 'Common issues and how to resolve them',
            'privacy': 'Data privacy, compliance, and secure file handling',
        }
