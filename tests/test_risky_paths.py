"""scripts/check_risky_paths.sh の自己テスト。一時的な git リポを作って実行する。"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_risky_paths.sh"

# 一時リポでの commit に要る設定。利用者や CI の git 設定に左右されないようにする。
GIT_ENV = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "git と bash が要る")
class TestCheckRiskyPaths(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.env = {**os.environ, **GIT_ENV}
        self.git("init", "-q", "-b", "main")
        self.write("README.md", "base\n")
        self.write("scripts/old.sh", "echo old\n")
        self.commit("base")
        self.git("checkout", "-q", "-b", "feature")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, env=self.env, check=True,
            capture_output=True, text=True,
        ).stdout

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def check(self, *args, env=None):
        return subprocess.run(
            [shutil.which("bash"), str(SCRIPT), *args], cwd=self.repo, env=env or self.env,
            capture_output=True, text=True,
        )

    def env_with_shim(self, name, script):
        """PATH の先頭に偽のコマンドを置いた環境を返す（内部エラーを起こすため）。"""
        shim_dir = Path(self._tmp.name + "-shim")
        shim_dir.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, shim_dir, True)
        shim = shim_dir / name
        shim.write_text("#!/bin/sh\n" + script)
        shim.chmod(0o755)
        return {**self.env, "PATH": f"{shim_dir}{os.pathsep}{self.env['PATH']}"}

    def commit_risky(self):
        self.write("migrations/001.sql", "x\n")
        self.commit("risky")

    def test_safe_change_passes(self):
        self.write("tcli/commands/x.py", "pass\n")
        self.write("tests/test_x.py", "pass\n")
        self.commit("safe")
        result = self.check("main")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("触れていない", result.stdout)

    def test_each_risky_path_fails(self):
        for rel in [
            "migrations/001.sql", ".env", ".env.local", "secrets/key",
            "scripts/new.sh", ".github/workflows/x.yml", "AGENTS.md", ".claude/settings.json",
        ]:
            with self.subTest(rel=rel):
                self.git("checkout", "-q", "-B", "feature", "main")
                self.write(rel, "x\n")
                self.commit(rel)
                result = self.check("main")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(rel, result.stdout)

    def test_nested_paths_are_not_risky(self):
        # 危ないのはリポ直下だけ。下の階層の同名ディレクトリは対象外。
        self.write("docs/scripts/note.md", "x\n")
        self.write("tests/AGENTS.md", "x\n")
        self.commit("nested")
        self.assertEqual(self.check("main").returncode, 0)

    def test_rename_out_of_risky_path_fails(self):
        (self.repo / "tools").mkdir()
        self.git("mv", "scripts/old.sh", "tools/old.sh")
        self.commit("move")
        result = self.check("main")
        self.assertEqual(result.returncode, 1)
        self.assertIn("scripts/old.sh", result.stdout)

    def test_head_argument_without_checkout(self):
        # CI と同じく、base 側をチェックアウトしたまま head を引数で渡す。
        self.write("scripts/evil.sh", "x\n")
        self.commit("risky on feature")
        self.git("checkout", "-q", "main")
        self.assertEqual(self.check("main").returncode, 0)  # HEAD=main では差分が無い
        result = self.check("main", "feature")
        self.assertEqual(result.returncode, 1)
        self.assertIn("scripts/evil.sh", result.stdout)

    def test_missing_ref_exits_2(self):
        self.assertEqual(self.check("no-such-base").returncode, 2)
        self.assertEqual(self.check("main", "no-such-head").returncode, 2)

    # 内部エラーは、危ないパスに触れた差分があっても 1 ではなく 2 になる（ラベルで通らない）。

    def test_too_many_args_exits_2(self):
        self.commit_risky()
        self.assertEqual(self.check("main", "HEAD", "extra").returncode, 2)

    def test_mktemp_failure_exits_2(self):
        self.commit_risky()
        env = self.env_with_shim("mktemp", "exit 1\n")
        result = self.check("main", env=env)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("migrations/001.sql", result.stdout)

    def test_git_diff_failure_exits_2(self):
        self.commit_risky()
        real_git = shutil.which("git")
        env = self.env_with_shim(
            "git", f'if [ "$1" = diff ]; then exit 1; fi\nexec "{real_git}" "$@"\n'
        )
        result = self.check("main", env=env)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_not_a_git_repo_exits_2(self):
        with tempfile.TemporaryDirectory() as empty:
            result = subprocess.run(
                [shutil.which("bash"), str(SCRIPT), "main"], cwd=empty, env=self.env,
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
