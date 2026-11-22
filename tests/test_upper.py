import io
import unittest
from contextlib import redirect_stdout

from tcli.commands import upper


class UpperTest(unittest.TestCase):
    def run_upper(self, args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = upper.run(args)
        return code, buf.getvalue()

    def test_upper(self):
        self.assertEqual(self.run_upper(["hello"]), (0, "HELLO\n"))

    def test_multiple_words_are_joined(self):
        self.assertEqual(self.run_upper(["hello", "world"]), (0, "HELLO WORLD\n"))

    def test_first_only_capitalizes_first_char(self):
        self.assertEqual(self.run_upper(["--first", "hello world"]), (0, "Hello world\n"))

    def test_first_option_position_is_free(self):
        self.assertEqual(self.run_upper(["hello", "--first"]), (0, "Hello\n"))


if __name__ == "__main__":
    unittest.main()
