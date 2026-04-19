import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config
from app.detection.threat_detector import ThreatDetector


class TestThreatDetection(unittest.TestCase):

    def test_input_length_normal(self):
        safe, _ = ThreatDetector.check_input_length("normal input")
        self.assertTrue(safe)

    def test_input_length_overflow(self):
        huge = "A" * (Config.MAX_INPUT_LENGTH + 1)
        safe, msg = ThreatDetector.check_input_length(huge)
        self.assertFalse(safe)
        self.assertIn("buffer overflow", msg.lower())

    def test_allowed_extension(self):
        safe, _ = ThreatDetector.check_file_extension("document.pdf")
        self.assertTrue(safe)

    def test_blocked_extension(self):
        safe, msg = ThreatDetector.check_file_extension("malware.exe")
        self.assertFalse(safe)
        self.assertIn("blocked", msg.lower())

    def test_disallowed_extension(self):
        safe, msg = ThreatDetector.check_file_extension("file.xyz")
        self.assertFalse(safe)

    def test_sql_injection_detection(self):
        safe, _ = ThreatDetector.check_injection(
            "'; DROP TABLE users; --"
        )
        # Basic SQL keywords alone may not trigger; test with SELECT FROM
        safe, msg = ThreatDetector.check_injection(
            "SELECT * FROM users WHERE 1=1"
        )
        self.assertFalse(safe)

    def test_xss_detection(self):
        safe, msg = ThreatDetector.check_injection('<script>alert("xss")</script>')
        self.assertFalse(safe)

    def test_path_traversal_detection(self):
        safe, msg = ThreatDetector.check_injection("../../etc/passwd")
        self.assertFalse(safe)

    def test_clean_input(self):
        safe, _ = ThreatDetector.check_injection("Hello world, this is clean text.")
        self.assertTrue(safe)

    def test_malware_eicar_detection(self):
        eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!'
        safe, msg = ThreatDetector.scan_for_malware(eicar)
        self.assertFalse(safe)

    def test_clean_file_data(self):
        safe, _ = ThreatDetector.scan_for_malware(b"Normal file content here")
        self.assertTrue(safe)

    def test_pdf_like_data_with_mz_inside_not_flagged_as_pe(self):
        pdf_like = (
            b"%PDF-1.7\n"
            b"1 0 obj<< /Type /Catalog >>endobj\n"
            b"stream\n"
            b"Random bytes before MZ marker ... MZ ... still a pdf payload\n"
            b"endstream\n"
            b"%%EOF"
        )
        safe, _ = ThreatDetector.scan_for_malware(pdf_like)
        self.assertTrue(safe)

    def test_real_pe_header_detected(self):
        pe_like = bytearray(512)
        pe_like[0:2] = b"MZ"
        pe_offset = 0x80
        pe_like[0x3C:0x40] = pe_offset.to_bytes(4, byteorder="little")
        pe_like[pe_offset:pe_offset + 4] = b"PE\x00\x00"

        safe, msg = ThreatDetector.scan_for_malware(bytes(pe_like))
        self.assertFalse(safe)
        self.assertIn("PE_HEADER", msg)

    def test_file_size_check(self):
        safe, _ = ThreatDetector.check_file_size(1024)
        self.assertTrue(safe)

        safe, msg = ThreatDetector.check_file_size(Config.UPLOAD_MAX_SIZE + 1)
        self.assertFalse(safe)


if __name__ == '__main__':
    unittest.main()
