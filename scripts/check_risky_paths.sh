#!/usr/bin/env bash
# 差分が危ないパスに触れていないかを確かめる。
#   使い方: scripts/check_risky_paths.sh [base] [head]   （base の既定は origin/main、head の既定は HEAD）
#   比べる範囲: <base>...<head>（base と head の分岐点から head までの変更）
#   CI（.github/workflows/risky-paths.yml）は base 側をチェックアウトし、PR の head を fetch して head に渡す。
#   PR のコードはチェックアウトも実行もしない。
#   終了コード: 0 = 触れていない / 1 = 触れた（パスを出す） / 2 = 検査できなかった
#   1 は危ないパスを見つけたときだけ返す。引数の誤り・mktemp や git の失敗・差分ファイルを読めないなど、内部のエラーはすべて 2 にする
#   （CI は 1 だけを owner-approved ラベルで成功に変えるため、検査していないのに 1 を返すと承認ですり抜ける）。
set -uo pipefail

# 本体（main）の終了コードの約束: 0 = 触れていない / 10 = 触れた。
# それ以外（ERR トラップの 2、set -u の 1、シグナルなど）はすべて内部エラーとして 2 に読み替える。
readonly FOUND=10

# 注意: main は if / while / && / || / ! の条件の中で呼ばない。
# 条件の中では、サブシェルでも set -e と ERR トラップが効かなくなり、失敗しても先へ進んでしまう。
# main の中で失敗を条件で受ける箇所（if ! ...）は、どれも明示的に exit 2 する。
main() {
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
  if ! tmp="$(mktemp)"; then
    echo "error: 一時ファイルを作れない" >&2
    exit 2
  fi
  trap 'rm -f "${tmp}"' EXIT
  if ! git diff --name-only -z --no-renames "${base}...${head}" >"${tmp}"; then
    echo "error: '${base}...${head}' の差分を取れない" >&2
    exit 2
  fi

  # 差分ファイルを開けないとき、while の入力リダイレクトの失敗では先へ進んでしまう場合があるため、
  # 先にファイル記述子 3 で開き、失敗したら 2 にする。
  if ! exec 3<"${tmp}"; then
    echo "error: 差分ファイル '${tmp}' を開けない" >&2
    exit 2
  fi

  local risky_pattern='^(migrations/|secrets/|scripts/|\.github/|\.claude/|AGENTS\.md$|\.env)'

  # read は EOF でも読み込みエラーでも 1 を返して区別できないため、読んだ件数を NUL の数と突き合わせる。
  # [[ =~ ]] は正規表現の誤りで 2 を返し、if の中では「一致しない」と同じに扱われるため、2 以上は明示的に 2 にする。
  local hits="" path="" count=0
  while IFS= read -r -d '' -u 3 path; do
    count=$((count + 1))
    if [[ "${path}" =~ ${risky_pattern} ]]; then
      hits+="${path}"$'\n'
    elif [ "$?" -ne 1 ]; then
      echo "error: パターンを照合できない" >&2
      exit 2
    fi
    path=""
  done
  exec 3<&-
  if [ -n "${path}" ]; then
    echo "error: 差分ファイルの末尾が NUL で終わっていない" >&2
    exit 2
  fi
  local expected
  expected="$(tr -cd '\000' <"${tmp}" | wc -c | tr -d ' ')"
  # 数値比較（-ne）は値が数でないと 2 を返し、if の中では「等しい」と同じに扱われるため、文字列で比べる。
  if [ "${count}" != "${expected}" ]; then
    echo "error: 差分ファイルを最後まで読めない（${count} / ${expected} 件）" >&2
    exit 2
  fi

  if [ -n "${hits}" ]; then
    echo "危ないパスに触れている（${base}...${head}）:"
    printf '%s' "${hits}"
    exit "${FOUND}"
  fi

  echo "危ないパスには触れていない（${base}...${head}）"
  exit 0
}

# 本体はサブシェルで、条件の外で動かす（set -e と ERR トラップを効かせるため）。終了コードを 0 / 1 / 2 に読み替える。
set +e
(
  set -Eeuo pipefail
  trap 'exit 2' ERR
  main "$@"
)
rc=$?
case "${rc}" in
  0) exit 0 ;;
  "${FOUND}") exit 1 ;;
  *) exit 2 ;;
esac
