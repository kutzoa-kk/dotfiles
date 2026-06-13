#!/usr/bin/env bash
#
# gen_image.sh — Codex CLI の image_gen ツール (gpt-image-2) を呼び出す薄いラッパー。
#
# なぜラッパーが要るか:
#   生の `codex exec` 呼び出しは、正しいフラグ (--sandbox / --skip-git-repo-check)、
#   `$imagegen` トリガ、絶対パスでの保存指示、`< /dev/null` による非対話化、
#   そして「本当に PNG が出力されたか」の検証を毎回手で組み立てる必要がある。
#   1 つでも欠けると静かに失敗する（モデルが保存をスキップする / sandbox に弾かれる）。
#   ここに固めておけば、スキル利用側はプロンプトと出力先だけ考えればよい。
#
# 認証:
#   API キーは不要。`codex login`（ChatGPT サブスク）で取得したトークンを使う。
#   生成トークンは Codex の利用枠を消費する（低品質 1 枚で概ね 30k tokens）。
#
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  gen_image.sh --out <path> [options] <prompt...>

Required:
  --out <path>          生成画像の保存先。相対パスは絶対パスに解決される。
                        親ディレクトリは自動作成される。

Options:
  --ref <image>         参照画像（繰り返し可）。トーン/構図の下敷きや、既存画像の
                        編集・リスタイルに使う。codex の -i に渡される。
  --size <WxH>          希望解像度のヒント（例: 1536x1024 / 1024x1024 / 1024x1536）。
                        プロンプトに添えるだけ。未指定なら用途に任せる。
  --quality <level>     low | medium | high（既定: low）。コスト/品質のヒント。
                        まず low で構図を確認し、確定後に high で焼き直すのが安い。
  --timeout <sec>       codex 実行のタイムアウト秒（既定: 300）。gtimeout/timeout が
                        無ければ無視される。
  -h, --help            このヘルプ。

Examples:
  # レポート用カバー画像
  gen_image.sh --out assets/cover.png --size 1536x1024 \
    "落ち着いたコーポレートブルーの抽象幾何カバー。余白広め、テキストなし、印刷品質"

  # 参照画像と同じトーンで別アングル
  gen_image.sh --out assets/cup_side.png --ref refs/cup_front.png \
    "添付と同じトーン・ライティングで、真横アングルのコーヒーカップ"
EOF
}

# --- 引数パース ---------------------------------------------------------------
OUT=""
SIZE=""
QUALITY="low"
TIMEOUT="300"
REFS=()
PROMPT_PARTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out)     OUT="${2:-}"; shift 2 ;;
    --ref)     REFS+=("${2:-}"); shift 2 ;;
    --size)    SIZE="${2:-}"; shift 2 ;;
    --quality) QUALITY="${2:-}"; shift 2 ;;
    --timeout) TIMEOUT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --)        shift; PROMPT_PARTS+=("$@"); break ;;
    -*)        echo "[gen_image] 不明なオプション: $1" >&2; usage >&2; exit 2 ;;
    *)         PROMPT_PARTS+=("$1"); shift ;;
  esac
done

PROMPT="${PROMPT_PARTS[*]:-}"

# --- 入力検証（境界で fail-fast） ---------------------------------------------
if [[ -z "$OUT" ]]; then
  echo "[gen_image] --out は必須です" >&2; usage >&2; exit 2
fi
if [[ -z "$PROMPT" ]]; then
  echo "[gen_image] プロンプトが空です" >&2; usage >&2; exit 2
fi
if ! command -v codex >/dev/null 2>&1; then
  echo "[gen_image] codex が見つかりません。'brew install --cask codex' 後に 'codex login'" >&2
  exit 127
fi

# 参照画像の存在チェック（指定されたのに無ければ静かに無視せず止める）
for r in "${REFS[@]:-}"; do
  [[ -z "$r" ]] && continue
  if [[ ! -f "$r" ]]; then
    echo "[gen_image] 参照画像が見つかりません: $r" >&2; exit 2
  fi
done

# --- 出力先を絶対パス化し、親ディレクトリを用意 -------------------------------
# codex の workspace-write sandbox は cwd 配下を書き込み可能にするため、
# 出力先の親へ cd してから実行することで、任意の保存先を確実に書き込めるようにする。
mkdir -p "$(dirname "$OUT")"
OUT_DIR="$(cd "$(dirname "$OUT")" && pwd)"
OUT_ABS="$OUT_DIR/$(basename "$OUT")"

# --- プロンプト組み立て -------------------------------------------------------
# `$imagegen` は image_gen ツールを起動するトリガ。リテラルで渡す必要があるため
# single-quote 変数に格納し、二重展開を避ける。
TRIGGER='$imagegen'
HINTS=""
[[ -n "$SIZE" ]]    && HINTS+=" 解像度の目安は ${SIZE}。"
[[ -n "$QUALITY" ]] && HINTS+=" 品質は ${QUALITY}。"

FULL_PROMPT="${TRIGGER} ${PROMPT}.${HINTS} 生成した画像を ${OUT_ABS} に PNG 形式で保存してください。"

# --- codex exec 引数組み立て --------------------------------------------------
CODEX_ARGS=(exec --sandbox workspace-write --skip-git-repo-check)
for r in "${REFS[@]:-}"; do
  [[ -z "$r" ]] && continue
  CODEX_ARGS+=(-i "$(cd "$(dirname "$r")" && pwd)/$(basename "$r")")
done
CODEX_ARGS+=("$FULL_PROMPT")

# タイムアウトコマンドを検出（GNU coreutils: timeout / macOS+brew: gtimeout）
TIMEOUT_CMD=()
if command -v timeout >/dev/null 2>&1; then
  TIMEOUT_CMD=(timeout "$TIMEOUT")
elif command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_CMD=(gtimeout "$TIMEOUT")
fi

echo "[gen_image] 生成中... -> $OUT_ABS" >&2
echo "[gen_image] prompt: $FULL_PROMPT" >&2

# cwd を出力先の親に移して実行（sandbox 書き込み権限の確実化）
(
  cd "$OUT_DIR"
  "${TIMEOUT_CMD[@]}" codex "${CODEX_ARGS[@]}" < /dev/null
) || {
  echo "[gen_image] codex 実行が失敗しました。'codex login status' で認証を確認してください。" >&2
  exit 1
}

# --- 生成結果の検証（動作を証明できるまで成功としない） -----------------------
if [[ ! -f "$OUT_ABS" ]]; then
  echo "[gen_image] 失敗: 画像が保存されていません ($OUT_ABS)。" >&2
  echo "[gen_image] モデルが保存指示を実行しなかった可能性。プロンプトに保存先を明示して再試行してください。" >&2
  exit 1
fi

BYTES=$(wc -c < "$OUT_ABS" | tr -d ' ')
if [[ "$BYTES" -lt 1000 ]]; then
  echo "[gen_image] 警告: 生成ファイルが極端に小さい (${BYTES} bytes)。破損の可能性あり: $OUT_ABS" >&2
  exit 1
fi

echo "[gen_image] OK: $OUT_ABS (${BYTES} bytes)"
