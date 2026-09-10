#!/usr/bin/env sh
# 出力したPPTXを全ページ画像化し、フォント代替の有無を報告する描画確認スクリプト。
# 使い方: sh render-check.sh <input.pptx> [出力ディレクトリ]
set -eu

SRC=${1:?入力PPTXを指定してください}
OUT=${2:-./render}

[ -f "$SRC" ] || { echo "見つかりません: $SRC" >&2; exit 1; }

SOFFICE=$(command -v soffice 2>/dev/null || echo /Applications/LibreOffice.app/Contents/MacOS/soffice)
[ -x "$SOFFICE" ] || { echo "LibreOffice が見つかりません（brew install --cask libreoffice）" >&2; exit 1; }

mkdir -p "$OUT"

# 前回の出力を掃除する。残しておくと、ページ数の少ない資料を確認したときに
# 古いページ画像が混ざる。pdftoppm は page-01.png、sips は page-1.png と
# 命名が異なるため、経路が変わった場合も取り残しが出る。
find "$OUT" -maxdepth 1 -name 'page-*.png' -delete

# -env:UserInstallation は指定しない。一時プロファイルではHiragino Sansが解決されず、
# 日本語が全て豆腐（□）になる。既定プロファイルのまま実行すること。
"$SOFFICE" --headless --norestore --convert-to pdf --outdir "$OUT" "$SRC" >/dev/null 2>&1

BASE=$(basename "$SRC")
PDF="$OUT/${BASE%.*}.pdf"
[ -f "$PDF" ] || { echo "PDFへの変換に失敗しました: $SRC" >&2; exit 1; }

if command -v pdftoppm >/dev/null 2>&1; then
    pdftoppm -png -r 110 "$PDF" "$OUT/page"
    echo "全ページを画像化しました:"
    ls "$OUT"/page-*.png
else
    sips -s format png "$PDF" --out "$OUT/page-1.png" >/dev/null
    echo "pdftoppm が未導入のため1ページ目のみ画像化しました: $OUT/page-1.png" >&2
    echo "全ページを確認するには brew install poppler が必要です。" >&2
fi

python3 - "$PDF" <<'PY'
import re
import sys

data = open(sys.argv[1], 'rb').read()
fonts = sorted({f.decode().split('+')[-1]
                for f in re.findall(rb'/BaseFont\s*/([A-Za-z0-9+\-,#]+)', data)})
print("埋込フォント:", ", ".join(fonts) or "(なし)")

JP = ('Hiragino', 'Noto', 'Gothic', 'Mincho', 'YuGo', 'Meiryo')
if not any(any(j in f for j in JP) for f in fonts):
    print("警告: 日本語フォントが埋め込まれていません。文字が豆腐（□）になっている可能性があります。")
if not any('Roboto' in f for f in fonts):
    print("注意: Robotoが未導入のため、英数字が代替フォントで描画されています。")
PY
