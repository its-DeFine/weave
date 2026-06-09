from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK_PATH = ROOT / "scripts" / "check_no_secrets.py"

spec = importlib.util.spec_from_file_location("check_no_secrets", CHECK_PATH)
assert spec is not None
check_no_secrets = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = check_no_secrets
spec.loader.exec_module(check_no_secrets)


class CheckNoSecretsTests(unittest.TestCase):
    def test_python_lowercase_token_state_is_not_env_secret_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.py"
            path.write_text(
                "token_configured = env_file.exists() and 'TOKEN_NAME=' in text\n"
                "state.auth_token = token_file.read_text().strip()\n",
                encoding="utf-8",
            )
            self.assertEqual(check_no_secrets.scan_file(path), [])

    def test_uppercase_env_style_secret_assignment_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.env"
            key = "SERVICE_" + "TOKEN"
            path.write_text(f"{key}=supersecretvalue\n", encoding="utf-8")
            hits = check_no_secrets.scan_file(path)
            self.assertEqual(len(hits), 1)
            self.assertIn("secret-assignment", hits[0])

    def test_quoted_env_style_secret_assignment_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.env"
            key = "SERVICE_" + "TOKEN"
            path.write_text(f'{key}="supersecretvalue"\n', encoding="utf-8")
            hits = check_no_secrets.scan_file(path)
            self.assertEqual(len(hits), 1)
            self.assertIn("secret-assignment", hits[0])

    def test_quoted_placeholder_secret_assignment_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.env"
            key = "SERVICE_" + "TOKEN"
            path.write_text(f'{key}="<redacted>"\n', encoding="utf-8")
            self.assertEqual(check_no_secrets.scan_file(path), [])

    def test_python_secret_regex_constant_is_not_env_secret_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.py"
            path.write_text(
                'SECRET_EXPORT_CONTENT_RE = re.compile(r"TOKEN=[^\\s]{8,}")\n',
                encoding="utf-8",
            )
            self.assertEqual(check_no_secrets.scan_file(path), [])

    def test_rfc1918_172_private_lan_address_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.md"
            private_address = "172." + "16.0.5"
            path.write_text(f"runtime endpoint {private_address}\n", encoding="utf-8")
            hits = check_no_secrets.scan_file(path)
            self.assertEqual(len(hits), 1)
            self.assertIn("internal-host", hits[0])


if __name__ == "__main__":
    unittest.main()
