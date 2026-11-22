# AGENTS.md — 2026-11-22-autonomy-trial

自律運用の試験（AOS-441 / AOS-442）のための使い捨てリポ。計画は `docs/trial-plan.md`、試験のための例外は `DECISIONS.md` にある。

## 作業の流れ

- 作業はブランチで行う（1 機能 = 1 ブランチ）。main へ直接 push しない（ブランチ保護で拒否される）。
- 変更の出口は main 宛ての PR だけにする。
- PR は次の必須チェックがすべて緑になってからマージする（squash）。

| チェック | 中身 | 落ちたとき |
|---|---|---|
| `test` | `python -m unittest` | 実装した worker が直して push し直す |
| `risky-paths` | `scripts/check_risky_paths.sh`。差分がリポ直下の `migrations/`・`.env` で始まるもの・`secrets/`・`scripts/`・`.github/`・`AGENTS.md`・`.claude/` に触れたら失敗 | 自動でマージしない。司令塔がオーナーに聞く |
| `cross-review` | レビュー worker（別モデル）が合格のとき、commit status `cross-review` を success にする | 実装した worker に差し戻す |

- 承認なしで行ってよい操作の範囲は `DECISIONS.md` に従う。

## コード

- Python 3.12 以上、標準ライブラリだけを使う（依存を足さない）。
- コマンドは `tcli/commands/<name>.py` に 1 ファイルずつ置く。ファイル名がコマンド名になり、`HELP` と `run(args) -> int` を持つ。中央の登録表は作らない。
- コマンドを足したら、README.md の「コマンド一覧」にも 1 行足す（`tests/test_readme.py` が確かめる）。
- テストは `tests/` に標準の unittest で書き、`python -m unittest` で通す。
