import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_tcli(*args):
    return subprocess.run(
        [sys.executable, "-m", "tcli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class HelloTest(unittest.TestCase):
    def test_hello_prints_hello(self):
        result = run_tcli("hello")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "hello\n")

    def test_unknown_command_fails(self):
        result = run_tcli("no-such-command")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown command", result.stderr)

    def test_help_lists_hello(self):
        result = run_tcli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hello", result.stdout)


if __name__ == "__main__":
    unittest.main()
