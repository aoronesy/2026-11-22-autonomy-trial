from pathlib import Path

HELP = "migrations/001_create_notes.sql の SQL を出力する"

SQL_PATH = Path(__file__).resolve().parent.parent.parent / "migrations" / "001_create_notes.sql"


def run(args):
    print(SQL_PATH.read_text(encoding="utf-8"), end="")
    return 0
