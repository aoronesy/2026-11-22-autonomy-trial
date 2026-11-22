# DECISIONS.md

このリポで決めたことと、試験のための例外を記録する。新しい決定は下に足す。

## 2026-11-22 承認なしで行う操作（試験のための例外）

- 決定: このリポでは、ブランチの push・PR 作成・必須チェック（`test`・`risky-paths`・`cross-review`）が緑の PR の main へのマージを承認なしで行う。
- 理由: AOS-441 の推奨構成の試験。
- 承認: オーナーが「全て推奨で進めて」で承認（2026-11-22）。
- 範囲: このリポだけ。`risky-paths` が失敗した PR は自動でマージせず、司令塔がオーナーに聞く。

## 2026-11-22 土台のコミットは risky-paths の例外とする

- 決定: 土台のコミット（AOS-442）は `.github/`・`scripts/`・`AGENTS.md` に触れるが、初期設定なので例外とする。
- 理由: CI の定義とリポの規約を置かないと、試験の仕組み自体が動かないため。
- 範囲: 土台のコミットだけ。以後の変更で `.github/`・`scripts/`・`AGENTS.md` に触れるものは、通常どおり `risky-paths` で止める。

## 2026-11-22 scripts/ を risky-paths の対象に足す

- 決定: `scripts/` に触れる差分も `risky-paths` で失敗させる。危ないパスは、リポ直下の `migrations/`・`.env` で始まるもの・`secrets/`・`scripts/`・`.github/`・`AGENTS.md`・`.claude/`。
- 理由: CI は PR 側の `scripts/check_risky_paths.sh` を実行するため、PR が検査スクリプトを書き換えると、その PR 自身の検査を変えられる。触れたら自動でマージせず、オーナーに聞く。
- 範囲: `tests/`（`tests/test_readme.py` を含む）は対象にしない。

## 2026-11-22 risky-paths を base 側で動かし、owner-approved ラベルで通す（AOS-446）

- 決定: `risky-paths` を `.github/workflows/risky-paths.yml`（`pull_request_target`、main 宛て、opened・synchronize・reopened・labeled・unlabeled）に移す。base 側（main）をチェックアウトして base 側の `scripts/check_risky_paths.sh` を使い、PR の head は `refs/pull/<番号>/head` を fetch して差分を見るだけにする。権限は `contents: read`・`pull-requests: read`、secrets は使わない。`ci.yml` は `test` だけにする。
- 決定: PR に `owner-approved` ラベルがあれば、触れた危ないパスを出したうえで成功にする。承認の通り道は、オーナーの OK → 司令塔が `owner-approved` ラベルを付ける → `risky-paths` が再実行されて通る。
- 理由: これまでは PR 側のワークフローとスクリプトを実行していたため、PR が自分の検査を書き換えればすり抜けられた（「scripts/ を risky-paths の対象に足す」の理由に書いた問題）。base 側で動かせば、PR の変更は検査に効かない。PR のコードは実行しないので、`pull_request_target` でも PR から権限を使われない。オーナーの OK を、チェックを落としたままの手動マージではなく、必須チェックの緑で表せる。
- 置き換え: 「scripts/ を risky-paths の対象に足す」の理由のうち「CI は PR 側の `scripts/check_risky_paths.sh` を実行する」は、この決定で当てはまらなくなる。`scripts/`・`.github/` は引き続き危ないパスとして扱う（検査の仕組みの変更はオーナーが確かめる）。
- 限界: ラベルはコミットに結び付かず、承認後の push でも残る。新しい push があったら司令塔がラベルを外して聞き直す。worker とオーナーは同じ GitHub アカウントなので、ラベルを付けるのが司令塔だけというのは運用上の決まりで、GitHub の権限では強制できない。
