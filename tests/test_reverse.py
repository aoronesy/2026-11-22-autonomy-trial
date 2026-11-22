import io
import unittest
from contextlib import redirect_stdout

from tcli.commands import reverse


class TestReverse(unittest.TestCase):
    def test_reverse(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = reverse.run(["abc"])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue(), "cba\n")
