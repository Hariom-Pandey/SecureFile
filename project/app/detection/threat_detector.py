import os
import re
from config import Config
from app.models.audit_log import AuditLog


class ThreatDetector:
    # Known malware signatures (explicit and low false-positive patterns)
    MALWARE_SIGNATURES = {
        "EICAR_TEST": b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR",
    }

    # Patterns that may indicate injection attempts
    INJECTION_PATTERNS = [
        r'<script[^>]*>',           # XSS script tags
        r'javascript:',             # JavaScript protocol
        r'on\w+\s*=',              # Event handlers
        r'(\b(union|select|insert|update|delete|drop|alter)\b.*\b(from|into|table|where)\b)',  # SQL
        r'(\.\./|\.\.\\)',          # Path traversal
        r'(\x00|\x0a|\x0d)',       # Null byte / CRLF injection
    ]

    @staticmethod
    def check_input_length(data, field_name="input"):
        """Detect potential buffer overflow via oversized input."""
        if isinstance(data, str):
            length = len(data)
        elif isinstance(data, bytes):
            length = len(data)
        else:
            return True, ""

        if length > Config.MAX_INPUT_LENGTH:
            return False, (
                f"Input '{field_name}' exceeds maximum allowed length "
                f"({length} > {Config.MAX_INPUT_LENGTH}). "
                "Possible buffer overflow attempt detected."
            )
        return True, ""

    @staticmethod
    def check_file_extension(filename):
        """Check if a file extension is allowed.
        
        Blocks dangerous executable/installer files and unknown extensions.
        """
        if not filename:
            return False, "Filename is required."

        # Get the extension
        _, ext = os.path.splitext(filename.lower())

        # Block genuinely dangerous executables & system files.
        if ext in Config.BLOCKED_EXTENSIONS:
            return False, (
                f"File extension '{ext}' is blocked. "
                "Executable and installer files are not allowed for security reasons."
            )

        # Require allow-listed extensions to reduce unsafe or unknown uploads.
        if ext not in Config.ALLOWED_EXTENSIONS:
            return False, (
                f"File extension '{ext}' is not allowed. "
                "Only approved document and media types are accepted."
            )

        return True, ""

    @staticmethod
    def scan_for_malware(data):
        """Scan file content for known malware signatures."""
        if isinstance(data, str):
            data = data.encode('utf-8')

        threats_found = []
        for name, signature in ThreatDetector.MALWARE_SIGNATURES.items():
            if signature in data:
                threats_found.append(name)

        if ThreatDetector._has_pe_executable_header(data):
            threats_found.append("PE_HEADER")

        if threats_found:
            return False, (
                f"Malware signatures detected: {', '.join(threats_found)}. "
                "File upload blocked."
            )
        return True, ""

    @staticmethod
    def _has_pe_executable_header(data):
        """Detect Windows PE binaries via DOS + PE headers to reduce false positives."""
        if not isinstance(data, (bytes, bytearray)):
            return False

        if len(data) < 64:
            return False

        if data[0:2] != b"MZ":
            return False

        pe_offset = int.from_bytes(data[0x3C:0x40], byteorder="little", signed=False)
        if pe_offset <= 0 or pe_offset + 4 > len(data):
            return False

        return data[pe_offset:pe_offset + 4] == b"PE\x00\x00"

    @staticmethod
    def check_injection(text):
        """Check text input for injection attack patterns."""
        if not isinstance(text, str):
            return True, ""

        for pattern in ThreatDetector.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, (
                    "Potential injection attack detected in input. "
                    "Request blocked for security."
                )
        return True, ""

    @staticmethod
    def check_file_size(file_size):
        """Validate file size is within limits."""
        if file_size > Config.UPLOAD_MAX_SIZE:
            return False, (
                f"File size ({file_size} bytes) exceeds maximum allowed "
                f"({Config.UPLOAD_MAX_SIZE} bytes)."
            )
        return True, ""

    @staticmethod
    def scan_file_upload(filename, file_data, user_id=None):
        """Comprehensive scan of an uploaded file."""
        results = []

        # Check filename for injection
        safe, msg = ThreatDetector.check_injection(filename)
        if not safe:
            results.append(("INJECTION", msg))

        # Check file extension
        safe, msg = ThreatDetector.check_file_extension(filename)
        if not safe:
            results.append(("BLOCKED_EXTENSION", msg))

        # Check file size
        safe, msg = ThreatDetector.check_file_size(len(file_data))
        if not safe:
            results.append(("SIZE_LIMIT", msg))

        # Scan for malware
        safe, msg = ThreatDetector.scan_for_malware(file_data)
        if not safe:
            results.append(("MALWARE", msg))

        if results:
            # Log security events
            for threat_type, detail in results:
                AuditLog.log(
                    user_id, "THREAT_DETECTED",
                    f"file:{filename}",
                    f"[{threat_type}] {detail}"
                )
            messages = [msg for _, msg in results]
            return False, messages

        return True, ["File passed all security checks."]
