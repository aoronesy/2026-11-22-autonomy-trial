# 2026-11-22-autonomy-trial

承認を減らす自律運用（AOS-441）を試すための使い捨てリポ。計画は [docs/trial-plan.md](docs/trial-plan.md)。

中身は依存なしの小さな Python CLI `tcli`。

## 使い方

Python 3.12 以上。外部の依存はない。

```sh
python -m tcli <command> [args...]
python -m tcli --help   # コマンドの一覧を出す
python -m unittest      # テストを実行する
```

## コマンド一覧

- `hello`: "hello" を出力する
- `reverse`: text を逆順にして出力する

コマンドを足したら、この一覧にも 1 行足す（`tests/test_readme.py` が `tcli/commands/` の全コマンドが載っているかを確かめる）。

## コマンドの足し方

1. `tcli/commands/<name>.py` を作り、`HELP`（1 行の説明）と `run(args) -> int` を書く。ファイル名がそのままコマンド名になる。
2. 上の「コマンド一覧」に `` - `<name>`: 説明 `` の形で 1 行足す。
3. `tests/` にテストを足し、`python -m unittest` を通す。

## チェック

PR では次の 3 つが必須。詳しくは [AGENTS.md](AGENTS.md)。

- `test`: `python -m unittest`
- `risky-paths`: base 側の `scripts/check_risky_paths.sh`（危ないパスに触れたら失敗。`owner-approved` ラベルを付けたときの実行は成功）
- `cross-review`: 別モデルのレビューが合格のとき success になる commit status
