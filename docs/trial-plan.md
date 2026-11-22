# 自律運用の試験計画（AOS-441 / AOS-442）

## 結論
使い捨てリポを GitHub に置き、main をブランチ保護で守ったうえで、機能 4 件を PM ボット → 司令塔（New bot）→ worker で回す。
必須チェックがすべて通った PR は、司令塔が承認なしで main へマージする。オーナーに聞くのは、危ない種類に当たった 1 件だけの見込み。

## 構成

```
オーナー ──要望──▶ PM ボット（新規）
                    │ 要件メモ・Linear 起票（AOS-442 の子）
                    ▼ handoff
               司令塔 = New bot（機能チャット = この会話）
                    │ 並列の判断・worker 起動・マージ
          ┌─────────┼─────────┐
          ▼         ▼         ▼
     実装 worker  実装 worker  レビュー worker（codex）
     (claude)    (claude)     └─ 合格なら commit status「cross-review」を success にする
          │ ブランチ push・PR 作成・CI 失敗の修正まで worker が持つ
          ▼
   GitHub: main 保護（必須チェック 3 つ・管理者にも適用・force push 禁止）
          │ 3 つとも緑 → 司令塔が gh pr merge --squash
          ▼
        main
```

## 試験リポ
- 場所: `~/dev/sandbox/2026-11-22-autonomy-trial`、GitHub `aoronesy/2026-11-22-autonomy-trial`（SSH で push。workflow 権限の追加は不要と確認済み）。
- 中身: 依存なしの小さな Python CLI（標準の unittest）。AGENTS.md と DECISIONS.md（試験のための例外を記録）を置く。
- 必須チェック（ブランチ保護で必須にする）:

| チェック | 中身 | 落ちたら |
|---|---|---|
| test | `python -m unittest` | worker が直して push し直す |
| risky-paths | 差分が `migrations/`・`.env*`・`secrets/`・`.github/`・`AGENTS.md`・`.claude/` に触れたら失敗 | 自動マージしない。司令塔がオーナーに聞く |
| cross-review | レビュー worker（codex）が合格のとき commit status を success にする | 実装 worker に差し戻す |

- PR の作成者もレビューの記録者も同じ GitHub アカウントなので、GitHub の「承認」は使えない。別モデルのレビューは commit status で表す。

## 機能と、わざと起こす失敗

| 機能 | 触る範囲 | 確かめること |
|---|---|---|
| F1 | `commands/a.py` | F2 と並列で進み、止まらずにマージされる |
| F2 | `commands/b.py` | F1 と並列。最初の push では README を更新しない指示で CI 失敗を起こし、worker が自分で直す |
| F3 | `commands/a.py`（F1 と重なる） | 司令塔が F1 のマージ後に着手させる（順番待ち） |
| F4 | `migrations/001.sql` を足す | risky-paths で止まり、オーナーに 1 回聞く（正当な承認として数える） |

- レビューの差し戻しは自然に起きるのを待つ。起きなければ F3 に既知の不具合を入れる指示で 1 回起こす。
- 管理者にも保護が効くことを、main への直接 push が拒否されることで 1 回確かめる。

## 測るもの

| 項目 | 測り方 | 基準（これまで） |
|---|---|---|
| オーナーの承認・回答の回数 | 項目の Needs you と、オーナーの返事の数 | 項目 5・6・7 で 2・1・8 回 |
| 止まった回数 | 誰かの返事待ちで進まなかった回数と時間 | — |
| 着手からマージまでの時間 | 機能ごと（Linear の In Progress → PR の merged） | — |
| 事故 | 誤ったマージ、壊れた main、消えた作業、保護のすり抜け | 0 であること |
| 消費 | worker の記録。機能チャットの分は Home Chat が測る | 項目 6: 機能チャット約 350 万、worker 約 147 万 |

## 止める条件
- main が壊れた、必須チェックが緑でないのにマージされた、試験リポの外を触った → 試験を止めてオーナーに報告する。

## 権限の扱い（戻せる判断として推奨で進める）
- 試験中のボットは Full access のまま。試験リポに書き込むのはオーナーとボットだけで、外部の人の Issue やコメントを読まないため。承認を求めるモードは、外部の入力を読むボットに使う。
- イベントで起きる流れ（CI 失敗・レビュー指摘で司令塔が起きる）は、GitHub 接続ができた場合だけ別に試す。基本の流れは、worker が自分の PR のチェックを見て直す形にし、接続に頼らない。

## 今回の範囲
- 達成条件 1（試験して結果をオーナーに見せる）まで。orca-ops.md などの書き換え（達成条件 2・3）は、結果をオーナーが OK した後に行う。
