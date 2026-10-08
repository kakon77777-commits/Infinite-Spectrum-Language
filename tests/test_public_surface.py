"""Behavioral guard tests; no real credentials or personal information."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_public_surface import scan


class PublicSurfaceTests(unittest.TestCase):
    def test_current_tree(self):
        root = Path(__file__).resolve().parent.parent
        self.assertEqual(scan(root), [])

    def test_email_rejected_without_echoing_value(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "note.md"
            p.write_text("contact " + "sample" + "@" + "example.test" + "\n", encoding="utf-8")
            self.assertEqual([(x.path, x.category) for x in scan(Path(td))],
                             [("note.md", "personal-email")])

    def test_credential_rejected(self):
        with TemporaryDirectory() as td:
            (Path(td) / "notes.txt").write_text("ghp_" + "a" * 24, encoding="utf-8")
            self.assertIn("credential-token", [x.category for x in scan(Path(td))])

    def test_sensitive_filename_rejected(self):
        with TemporaryDirectory() as td:
            p = Path(td) / ".env"
            p.write_text("not-secret-demo", encoding="utf-8")
            self.assertIn("private-file-name", [x.category for x in scan(Path(td))])

    def test_user_path_rejected(self):
        with TemporaryDirectory() as td:
            (Path(td) / "log.md").write_text("C:" + "\\\\Users\\\\" + "Sample\\\\data", encoding="utf-8")
            self.assertIn("local-user-path", [x.category for x in scan(Path(td))])

    def test_non_utf8_source_rejected(self):
        with TemporaryDirectory() as td:
            (Path(td) / "bad.md").write_bytes(b"\xff")
            self.assertIn("invalid-utf8-text", [x.category for x in scan(Path(td))])


if __name__ == "__main__":
    unittest.main()
