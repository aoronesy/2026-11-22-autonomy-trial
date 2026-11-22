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

1. `risky-paths` が落ちたら、司令塔はオーナーに聞く前に、提示する対象を記録する。今の head SHA を取り（`gh pr view <番号> --json headRefOid -q .headRefOid`）、その SHA の差分を作って SHA-256 を取る（`git fetch origin main pull/<番号>/head` の後、`git diff origin/main...<SHA> > approved.diff`、`shasum -a 256 approved.diff`）。差分は main との merge-base からの差分で、`gh pr diff` と同じ範囲。PR のコメントに SHA と SHA-256 を書き、差分本体は手元に残す。
2. 司令塔はオーナーへの質問に、その SHA・SHA-256・触れた危ないパス・差分（または差分へのリンク）を載せる。オーナーの OK は、この記録に対する承認として扱う。回答の後に差分を取り直して記録し直さない。
3. OK が来たら、司令塔はブランチを main に追いつかせ、`test` と `cross-review` を緑にする。
4. ラベルを付ける直前に、司令塔は今の head SHA を取り、手順 1 と同じ方法でその SHA の差分の SHA-256 を取り、記録と比べる。同じなら `owner-approved` ラベルを最後に付ける（`gh pr edit <番号> --add-label owner-approved`）。違えば付けず、新しい SHA と差分で手順 1 からやり直してオーナーに聞き直す。worker はラベルを付けない。
5. ラベルを付けると `risky-paths` が再実行され、触れたパスを出したうえで成功になる。司令塔は、成功した `risky-paths` が手順 4 で照合した SHA のチェックであること（`gh api repos/<owner>/<repo>/commits/<SHA>/check-runs` で `risky-paths` が success）を確かめ、その SHA を指定してマージする（`gh pr merge <番号> --squash --match-head-commit <SHA>`）。
6. 承認の後に新しい push（main の取り込みを含む）で head が変わると、`risky-paths` はまた落ちる（ラベルが残っていても通さない）。司令塔はラベルを外し、手順 4 からやり直す（差分が記録と同じときだけ付け直し、違えば聞き直す）。パス名が同じというだけでは判断しない。

- `risky-paths` は base 側（main）のワークフローとスクリプトで動き、PR の head は fetch して差分を見るだけにする。PR が `.github/` や `scripts/` を書き換えても、その PR 自身の検査は変わらず、すり抜けられない。PR のコードは実行しない。
- ラベルはコミットに結び付かないため、承認として扱うのは `owner-approved` を付けたときの実行だけにしている。他のラベルの付け外しや reopen でも落ちるので、そのときは手順 4 から（差分を記録と照合してから付け直す）。
- ワークフローは承認者や承認時の SHA を照合しない。承認と対象の照合は、オーナーに提示した時点の記録と今の差分の比較、検査した SHA の確認と SHA を指定したマージ（手順 1・4・5・6）で行う。
- `scripts/check_risky_paths.sh` は、危ないパスを見つけたときだけ 1、内部のエラー（引数の誤り、`mktemp` や git の失敗、差分ファイルを開けない・読み切れないなど）はすべて 2 を返す。ラベルで成功に変わるのは 1 だけで、2 はラベルがあっても失敗する。
- 検査の仕組み自体（`risky-paths.yml`・`check_risky_paths.sh`）を変える PR は、base にまだ無い変更なので、マージされるまで新しい検査は動かない。

## コード

- Python 3.12 以上、標準ライブラリだけを使う（依存を足さない）。
- コマンドは `tcli/commands/<name>.py` に 1 ファイルずつ置く。ファイル名がコマンド名になり、`HELP` と `run(args) -> int` を持つ。中央の登録表は作らない。
- コマンドを足したら、README.md の「コマンド一覧」にも 1 行足す（`tests/test_readme.py` が確かめる）。
- テストは `tests/` に標準の unittest で書き、`python -m unittest` で通す。
