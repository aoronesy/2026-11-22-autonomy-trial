# AGENTS.md — 2026-11-22-autonomy-trial

自律運用の試験（AOS-441 / AOS-442）のための使い捨てリポ。計画は `docs/trial-plan.md`、試験のための例外は `DECISIONS.md` にある。

## 作業の流れ

- 作業はブランチで行う（1 機能 = 1 ブランチ）。main へ直接 push しない（ブランチ保護で拒否される）。
- 変更の出口は main 宛ての PR だけにする。
- PR は次の必須チェックがすべて緑になってからマージする（squash）。

| チェック | 中身 | 落ちたとき |
|---|---|---|
| `test` | `python -m unittest` | 実装した worker が直して push し直す |
| `risky-paths` | `.github/workflows/risky-paths.yml`（`pull_request_target`）が base 側の `scripts/check_risky_paths.sh` で PR の差分を見る。リポ直下の `migrations/`・`.env` で始まるもの・`secrets/`・`scripts/`・`.github/`・`AGENTS.md`・`.claude/` に触れたら失敗。PR に `owner-approved` ラベルを付けたときの実行は、触れたパスを出して成功 | 自動でマージしない。司令塔がオーナーに聞く（下の「危ない種類の変更の承認」） |
| `cross-review` | レビュー worker（別モデル）が合格のとき、commit status `cross-review` を success にする | 実装した worker に差し戻す |

- 承認なしで行ってよい操作の範囲は `DECISIONS.md` に従う。

### 危ない種類の変更の承認

1. `risky-paths` が落ちたら、司令塔は触れたパス（ジョブのログに出る）を添えてオーナーに聞く。
2. オーナーが OK したら、司令塔が PR に `owner-approved` ラベルを付ける（`gh pr edit <番号> --add-label owner-approved`）。worker はラベルを付けない。
3. ラベルを付けると `risky-paths` が再実行され、触れたパスを出したうえで成功になる。ほかの必須チェックも緑なら、通常どおりマージする。
4. 承認の後に新しい push があると `risky-paths` はまた落ちる（ラベルが残っていても通さない）。司令塔はラベルを外し、改めてオーナーに聞き、OK なら付け直す。

- `risky-paths` は base 側（main）のワークフローとスクリプトで動き、PR の head は fetch して差分を見るだけにする。PR が `.github/` や `scripts/` を書き換えても、その PR 自身の検査は変わらず、すり抜けられない。PR のコードは実行しない。
- ラベルはコミットに結び付かないため、承認として扱うのは `owner-approved` を付けたときの実行だけにしている。他のラベルの付け外しや reopen でも落ちるので、そのときはラベルを付け直す。
- 検査の仕組み自体（`risky-paths.yml`・`check_risky_paths.sh`）を変える PR は、base にまだ無い変更なので、マージされるまで新しい検査は動かない。

## コード

- Python 3.12 以上、標準ライブラリだけを使う（依存を足さない）。
- コマンドは `tcli/commands/<name>.py` に 1 ファイルずつ置く。ファイル名がコマンド名になり、`HELP` と `run(args) -> int` を持つ。中央の登録表は作らない。
- コマンドを足したら、README.md の「コマンド一覧」にも 1 行足す（`tests/test_readme.py` が確かめる）。
- テストは `tests/` に標準の unittest で書き、`python -m unittest` で通す。
