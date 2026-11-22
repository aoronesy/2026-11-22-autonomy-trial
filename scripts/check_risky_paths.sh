#!/usr/bin/env bash
# 差分が危ないパスに触れていないかを確かめる。
#   使い方: scripts/check_risky_paths.sh [base] [head]   （base の既定は origin/main、head の既定は HEAD）
#   比べる範囲: <base>...<head>（base と head の分岐点から head までの変更）
#   CI（.github/workflows/risky-paths.yml）は base 側をチェックアウトし、PR の head を fetch して head に渡す。
#   PR のコードはチェックアウトも実行もしない。
#   終了コード: 0 = 触れていない / 1 = 触れた（パスを出す） / 2 = 検査できなかった
#   1 は危ないパスを見つけたときだけ返す。引数の誤り・mktemp や git の失敗など、内部のエラーはすべて 2 にする
#   （CI は 1 だけを owner-approved ラベルで成功に変えるため、検査していないのに 1 を返すと承認ですり抜ける）。
set -euo pipefail

# main の終了コードの約束: 0 = 触れていない / 10 = 触れた。それ以外（ERR トラップの 2、set -u の 1、シグナルなど）はすべて内部エラー。
readonly FOUND=10

main() {
  set -eEuo pipefail
  trap 'exit 2' ERR

  if [ "$#" -gt 2 ]; then
    echo "error: 引数が多すぎる（使い方: $0 [base] [head]）" >&2
    exit 2
  fi
  local base="${1:-origin/main}"
  local head="${2:-HEAD}"

  local ref
  for ref in "${base}" "${head}"; do
    if ! git rev-parse --verify --quiet "${ref}^{commit}" >/dev/null; then
      echo "error: '${ref}' が見つからない" >&2
      exit 2
    fi
  done

  # 差分のパスを NUL 区切りで一時ファイルに取る。
  #   -z: 引用符・タブ・改行を含むパスも、引用符で囲まずそのまま出す（検査のすり抜けを防ぐ）。
  #   --no-renames: 危ないパスからの移動・削除も元のパスとして出す。
  # パイプで git の失敗を握りつぶさないよう、先に終了コードを確かめる。
  local tmp
  if ! tmp="$(mktemp)"; then
    echo "error: 一時ファイルを作れない" >&2
    exit 2
  fi
  trap 'rm -f "${tmp}"' EXIT
  if ! git diff --name-only -z --no-renames "${base}...${head}" >"${tmp}"; then
    echo "error: '${base}...${head}' の差分を取れない" >&2
    exit 2
  fi

  local risky_pattern='^(migrations/|secrets/|scripts/|\.github/|\.claude/|AGENTS\.md$|\.env)'

  local hits="" path
  while IFS= read -r -d '' path; do
    if [[ "${path}" =~ ${risky_pattern} ]]; then
      hits+="${path}"$'\n'
    fi
  done <"${tmp}"

  if [ -n "${hits}" ]; then
    echo "危ないパスに触れている（${base}...${head}）:"
    printf '%s' "${hits}"
    exit "${FOUND}"
  fi

  echo "危ないパスには触れていない（${base}...${head}）"
  exit 0
}

# サブシェルで動かし、終了コードを 0 / 1 / 2 に読み替える。
rc=0
( main "$@" ) || rc=$?
case "${rc}" in
  0) exit 0 ;;
  "${FOUND}") exit 1 ;;
  *) exit 2 ;;
esac
