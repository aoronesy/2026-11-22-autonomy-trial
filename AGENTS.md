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

1. `risky-paths` が落ちたら、司令塔は触れたパス（ジョブのログに出る）と PR の差分を添えてオーナーに聞く。
2. オーナーが OK したら、司令塔はその時点の head SHA と PR の差分（`gh pr diff <番号>` の内容。main との merge-base からの差分）を記録する。PR のコメントに head SHA と差分の SHA-256（`gh pr diff <番号> | shasum -a 256`）を書き、差分本体も手元に残す。
3. 司令塔はブランチを main に追いつかせ、`test` と `cross-review` を緑にする。
4. ラベルを付ける直前に、司令塔は PR の差分を取り直し、記録と同じことを確かめる。同じなら `owner-approved` ラベルを最後に付ける（`gh pr edit <番号> --add-label owner-approved`）。違えば付けずに、オーナーに聞き直す。worker はラベルを付けない。
5. ラベルを付けると `risky-paths` が再実行され、触れたパスを出したうえで成功になる。ほかの必須チェックも緑なら、通常どおりマージする。
6. 承認の後に新しい push（main の取り込みを含む）で head が変わると、`risky-paths` はまた落ちる（ラベルが残っていても通さない）。司令塔はラベルを外し、PR の差分が記録と同じときだけ付け直す。違えば聞き直す。パス名が同じというだけでは判断しない。

- `risky-paths` は base 側（main）のワークフローとスクリプトで動き、PR の head は fetch して差分を見るだけにする。PR が `.github/` や `scripts/` を書き換えても、その PR 自身の検査は変わらず、すり抜けられない。PR のコードは実行しない。
- ラベルはコミットに結び付かないため、承認として扱うのは `owner-approved` を付けたときの実行だけにしている。他のラベルの付け外しや reopen でも落ちるので、そのときは手順 6 と同じく差分を記録と照合してから付け直す。
- ワークフローは承認者や承認時の SHA を照合しない。承認と対象の照合は、司令塔が記録した差分との比較（手順 2・4・6）で行う。
- `scripts/check_risky_paths.sh` は、危ないパスを見つけたときだけ 1、内部のエラー（引数の誤り、`mktemp` や git の失敗など）はすべて 2 を返す。ラベルで成功に変わるのは 1 だけで、2 はラベルがあっても失敗する。
- 検査の仕組み自体（`risky-paths.yml`・`check_risky_paths.sh`）を変える PR は、base にまだ無い変更なので、マージされるまで新しい検査は動かない。

## コード

- Python 3.12 以上、標準ライブラリだけを使う（依存を足さない）。
- コマンドは `tcli/commands/<name>.py` に 1 ファイルずつ置く。ファイル名がコマンド名になり、`HELP` と `run(args) -> int` を持つ。中央の登録表は作らない。
- コマンドを足したら、README.md の「コマンド一覧」にも 1 行足す（`tests/test_readme.py` が確かめる）。
- テストは `tests/` に標準の unittest で書き、`python -m unittest` で通す。
