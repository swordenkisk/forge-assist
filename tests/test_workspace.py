import tempfile
import unittest
from pathlib import Path

from forge\_assist.workspace import (
    apply\_changes,
    collect\_context,
    validate\_target,
)


class WorkspaceTests(unittest.TestCase):
    def test\_rejects\_parent\_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                validate\_target(root, "../outside.txt")

    def test\_rejects\_private\_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                validate\_target(root, ".env")

    def test\_applies\_new\_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            written = apply\_changes(
                root,
                [{"path": "src/hello.txt", "content": "Hello\n"}],
            )
            self.assertEqual(written, ["src/hello.txt"])
            self.assertEqual((root / "src" / "hello.txt").read\_text(), "Hello\n")

    def test\_context\_skips\_env\_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write\_text("print('hello')", encoding="utf-8")
            (root / ".env").write\_text("API\_KEY=secret", encoding="utf-8")

            context = collect\_context(root)

            self.assertIn("main.py", context)
            self.assertNotIn("API\_KEY", context)
            self.assertNotIn("secret", context)


if __name__ == "\_\_main\_\_":
    unittest.main()
