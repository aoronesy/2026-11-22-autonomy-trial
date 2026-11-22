import io
import unittest
from contextlib import redirect_stdout

from tcli.commands import a


class ATest(unittest.TestCase):
    def run_a(self, args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = a.run(args)
        return code, buf.getvalue()

    def test_upper(self):
        self.assertEqual(self.run_a(["hello"]), (0, "HELLO\n"))

    def test_multiple_words_are_joined(self):
        self.assertEqual(self.run_a(["hello", "world"]), (0, "HELLO WORLD\n"))


if __name__ == "__main__":
    unittest.main()
