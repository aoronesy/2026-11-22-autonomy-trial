import contextlib
import io
import sqlite3
import unittest

from tcli.commands import schema


class SchemaTest(unittest.TestCase):
    def run_schema(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = schema.run([])
        return code, buf.getvalue()

    def test_outputs_create_table_notes(self):
        code, out = self.run_schema()
        self.assertEqual(code, 0)
        self.assertIn("CREATE TABLE notes", out)

    def test_sql_defines_expected_columns(self):
        _, out = self.run_schema()
        conn = sqlite3.connect(":memory:")
        conn.executescript(out)
        cols = {r[1]: (r[2], r[3], r[5]) for r in conn.execute("PRAGMA table_info(notes)")}
        self.assertEqual(cols["id"], ("INTEGER", 0, 1))
        self.assertEqual(cols["body"], ("TEXT", 1, 0))
        self.assertEqual(cols["created_at"], ("TEXT", 1, 0))


if __name__ == "__main__":
    unittest.main()
