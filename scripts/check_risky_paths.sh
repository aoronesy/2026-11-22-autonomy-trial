#!/usr/bin/env bash
# 差分が危ないパスに触れていないかを確かめる。
#   使い方: scripts/check_risky_paths.sh [base] [head]   （base の既定は origin/main、head の既定は HEAD）
#   比べる範囲: <base>...<head>（base と head の分岐点から head までの変更）
#   CI（.github/workflows/risky-paths.yml）は base 側をチェックアウトし、PR の head を fetch して head に渡す。
#   PR のコードはチェックアウトも実行もしない。
#   終了コード: 0 = 触れていない / 1 = 触れた（パスを出す） / 2 = 差分を取れない
set -euo pipefail

base="${1:-origin/main}"
head="${2:-HEAD}"

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
tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT
if ! git diff --name-only -z --no-renames "${base}...${head}" >"${tmp}"; then
  echo "error: '${base}...${head}' の差分を取れない" >&2
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
  echo "危ないパスに触れている（${base}...${head}）:"
  printf '%s' "${hits}"
  exit 1
fi

echo "危ないパスには触れていない（${base}...${head}）"
exit 0
