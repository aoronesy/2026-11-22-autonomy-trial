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
- 決定: PR に `owner-approved` ラベルを付けたときの実行（`labeled` で、付けたラベルが `owner-approved`）は、触れた危ないパスを出したうえで成功にする。ラベルが残っていても、後の push（`synchronize`）や他のラベルの付け外し・reopen の実行では通さない。承認の通り道は、オーナーの OK → 司令塔が `owner-approved` ラベルを付ける → `risky-paths` が再実行されて通る。
- 理由: これまでは PR 側のワークフローとスクリプトを実行していたため、PR が自分の検査を書き換えればすり抜けられた（「scripts/ を risky-paths の対象に足す」の理由に書いた問題）。base 側で動かせば、PR の変更は検査に効かない。PR のコードは実行しないので、`pull_request_target` でも PR から権限を使われない。オーナーの OK を、チェックを落としたままの手動マージではなく、必須チェックの緑で表せる。
- 置き換え: 「scripts/ を risky-paths の対象に足す」の理由のうち「CI は PR 側の `scripts/check_risky_paths.sh` を実行する」は、この決定で当てはまらなくなる。`scripts/`・`.github/` は引き続き危ないパスとして扱う（検査の仕組みの変更はオーナーが確かめる）。
- 理由（ラベルを付けた実行だけ通す）: ラベルはコミットに結び付かず、承認後の push でも残る。権限を読み取りに絞ったままラベルを自動で外せないため、承認をラベルを付けた時点の head に限る。新しい push があったら、司令塔がラベルを外す。main は `strict`（最新に追いつく必要がある）なので、ラベルは追いついた後、マージの直前に付ける。
- 限界: worker とオーナーは同じ GitHub アカウントなので、ラベルを付けるのが司令塔だけというのは運用上の決まりで、GitHub の権限では強制できない。また、PR が `pull_request` のワークフローに同じ名前のジョブ `risky-paths` を足すと、同じアプリ（GitHub Actions）から同名のチェックが出て、必須チェックを見かけ上満たせるおそれがある。そうした PR は `.github/` に触れるので本物の `risky-paths` は落ちるが、塞ぐにはブランチ保護か ruleset の変更（ワークフローを指定して必須にするなど）が要る。

## 2026-11-22 オーナーの承認を差分に結び付け、検査エラーはラベルで通さない（AOS-446 のレビュー対応）

- 決定: オーナーが OK した時点の head SHA と PR の差分（`gh pr diff` の内容。main との merge-base からの差分）を司令塔が記録する（PR のコメントに head SHA と差分の SHA-256、差分本体は手元）。ラベルを付ける直前と、main の取り込みなどで head が変わった後は、PR の差分を取り直して記録と比べ、同じときだけラベルを付ける（付け直す）。違えばオーナーに聞き直す。危ないパスの名前が同じというだけでは判断しない。
- 決定: ワークフローに承認者や SHA を照合する仕組みは足さない。照合は司令塔の手順で行う。
- 決定: `scripts/check_risky_paths.sh` は、危ないパスを見つけたときだけ 1 を返し、内部のエラー（引数の誤り、`mktemp` や git の失敗、`set -u` の失敗など）はすべて 2 にする。ワークフローは 1 のときだけ `owner-approved` で成功に変え、2 などそれ以外は常に失敗にする。
- 理由: オーナーの OK からラベルまでに head が変わると、承認していない内容が承認済みとして通る。パス名だけでは差分の中身が同じか分からない。また、`mktemp` の失敗などで検査せずに 1 を返すと、ラベルで成功に変わり、検査をすり抜ける（cross-review の R1・R2）。
- 置き換え: 前の項の「main を取り込んだだけの更新で危ないパスが承認時と同じなら、聞き直さずに付け直してよい」は、この項の差分の照合に置き換える。
- 限界: 差分の照合は司令塔の手順で、ワークフローでは強制しない。main 側で同じファイルが変わると、PR の内容が同じでも差分の文脈行や index 行が変わり、聞き直しになることがある（安全側に倒れる）。
