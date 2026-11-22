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
