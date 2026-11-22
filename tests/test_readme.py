import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTION_HEADING = "## コマンド一覧"


def command_files():
    return {p.stem for p in (ROOT / "tcli" / "commands").glob("*.py") if not p.stem.startswith("_")}


def readme_commands():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        start = lines.index(SECTION_HEADING)
    except ValueError:
        raise AssertionError(f"README.md に「{SECTION_HEADING}」の見出しがない")
    names = set()
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        # 一覧の行は「- `name`: 説明」の形
        match = re.match(r"^\s*[-*]\s+`([^`]+)`", line)
        if match:
            names.add(match.group(1))
    return names


class ReadmeTest(unittest.TestCase):
    def test_every_command_is_listed_in_readme(self):
        missing = sorted(command_files() - readme_commands())
        self.assertEqual(missing, [], f"README.md のコマンド一覧に載っていないコマンド: {missing}")


if __name__ == "__main__":
    unittest.main()
