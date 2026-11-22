#!/usr/bin/env bash
# 差分が危ないパスに触れていないかを確かめる。
#   使い方: scripts/check_risky_paths.sh [base]   （base の既定は origin/main）
#   比べる範囲: <base>...HEAD（base と HEAD の分岐点から HEAD までの変更）
#   終了コード: 0 = 触れていない / 1 = 触れた（パスを出す） / 2 = 差分を取れない
set -euo pipefail

base="${1:-origin/main}"

if ! git rev-parse --verify --quiet "${base}^{commit}" >/dev/null; then
  echo "error: base '${base}' が見つからない" >&2
  exit 2
fi

# 差分のパスを NUL 区切りで一時ファイルに取る。
#   -z: 引用符・タブ・改行を含むパスも、引用符で囲まずそのまま出す（検査のすり抜けを防ぐ）。
#   --no-renames: 危ないパスからの移動・削除も元のパスとして出す。
# パイプで git の失敗を握りつぶさないよう、先に終了コードを確かめる。
tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT
if ! git diff --name-only -z --no-renames "${base}...HEAD" >"${tmp}"; then
  echo "error: '${base}...HEAD' の差分を取れない" >&2
  exit 2
fi

risky_pattern='^(migrations/|secrets/|scripts/|\.github/|\.claude/|AGENTS\.md$|\.env)'

hits=""
while IFS= read -r -d '' path; do
  if [[ "${path}" =~ ${risky_pattern} ]]; then
    hits+="${path}"$'\n'
  fi
done <"${tmp}"

if [ -n "${hits}" ]; then
  echo "危ないパスに触れている（${base}...HEAD）:"
  printf '%s' "${hits}"
  exit 1
fi

echo "危ないパスには触れていない（${base}...HEAD）"
exit 0
