#!/usr/bin/env python3
"""Scaffold a starter HTML report from the base.html template.

This is a convenience for repetitive structured cases (weekly status, audit
findings drops, recurring data analyses). For one-off reports, copy
`assets/base.html` directly and edit by hand.

Usage:
    python scaffold.py --type data-analysis --title "Q2 churn investigation" --out report.html
    python scaffold.py --spec spec.yaml --out report.html

Spec file (YAML or JSON) shape:

    type: data-analysis           # data-analysis | system-development | status-progress | audit-review
    title: "Q2 churn investigation"
    subtitle: "April 2026 review"
    eyebrow: "Data analysis · 2026-05-16"
    lang: ja
    author: "Alice"
    period: "2026-04-01 – 2026-04-30"
    status:                       # optional
      label: "Final"
      pip: success                # success | warning | danger | info
    sections:                     # ordered list — drives TOC + section stubs
      - id: summary
        toc: "サマリー"
        heading: "サマリー"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPORT_TYPE_DEFAULTS: dict[str, list[dict[str, str]]] = {
    "data-analysis": [
        {"id": "tldr",            "toc": "TL;DR",            "heading": "TL;DR"},
        {"id": "kpi",             "toc": "主要指標",         "heading": "主要指標"},
        {"id": "methodology",     "toc": "計測方法",         "heading": "計測方法"},
        {"id": "findings",        "toc": "発見",             "heading": "発見"},
        {"id": "segments",        "toc": "セグメント別",     "heading": "セグメント別"},
        {"id": "caveats",         "toc": "留意点",           "heading": "留意点"},
        {"id": "recommendations", "toc": "提言",             "heading": "提言"},
    ],
    "system-development": [
        {"id": "summary",         "toc": "サマリー",         "heading": "サマリー"},
        {"id": "context",         "toc": "背景",             "heading": "背景"},
        {"id": "goals",           "toc": "ゴールと非ゴール", "heading": "ゴールと非ゴール"},
        {"id": "current",         "toc": "現状",             "heading": "現状アーキテクチャ"},
        {"id": "proposed",        "toc": "提案",             "heading": "提案アーキテクチャ"},
        {"id": "alternatives",    "toc": "代替案",           "heading": "代替案"},
        {"id": "design",          "toc": "詳細設計",         "heading": "詳細設計"},
        {"id": "operations",      "toc": "運用",             "heading": "運用面の検討"},
        {"id": "risks",           "toc": "リスク",           "heading": "リスクと未解決事項"},
        {"id": "decision",        "toc": "決定事項",         "heading": "決定と次のステップ"},
    ],
    "status-progress": [
        {"id": "headline",        "toc": "ヘッドライン",     "heading": "ヘッドライン"},
        {"id": "kpi",             "toc": "主要指標",         "heading": "主要指標"},
        {"id": "trends",          "toc": "トレンド",         "heading": "トレンド"},
        {"id": "highlights",      "toc": "ハイライト",       "heading": "ハイライト / ローライト"},
        {"id": "by-segment",      "toc": "セグメント別",     "heading": "セグメント別"},
        {"id": "risks",           "toc": "リスク・ブロッカー", "heading": "リスク・ブロッカー"},
        {"id": "decisions",       "toc": "判断事項",         "heading": "判断が必要な事項"},
        {"id": "timeline",        "toc": "マイルストーン",   "heading": "マイルストーン"},
    ],
    "audit-review": [
        {"id": "summary",         "toc": "サマリー",         "heading": "サマリー"},
        {"id": "findings-summary","toc": "発見サマリー",     "heading": "発見サマリー"},
        {"id": "findings",        "toc": "発見詳細",         "heading": "発見詳細"},
        {"id": "methodology",     "toc": "調査方法・範囲",   "heading": "調査方法・範囲"},
        {"id": "plan",            "toc": "対応計画",         "heading": "対応計画"},
        {"id": "out-of-scope",    "toc": "範囲外の観察",     "heading": "範囲外の観察"},
        {"id": "appendix",        "toc": "付録",             "heading": "付録"},
    ],
}

PIP_HTML = {
    "success": '<span class="pip pip--success"></span>',
    "warning": '<span class="pip pip--warning"></span>',
    "danger":  '<span class="pip pip--danger"></span>',
    "info":    '<span class="pip pip--info"></span>',
}

# Markers in base.html used to splice in the new sections.
# Update these if assets/base.html headers change.
SECTIONS_START_MARKER = "<!-- =================== SUMMARY ==================="
FOOTER_MARKER = '<footer class="report-footer">'


def load_spec(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError:
            sys.exit("PyYAML is required to load YAML specs. `pip install pyyaml`.")
        return yaml.safe_load(text)
    return json.loads(text)


def build_meta_html(spec: dict[str, Any]) -> str:
    items: list[str] = []
    if spec.get("author"):
        items.append(f'<span><dt>作成者</dt><dd>{spec["author"]}</dd></span>')
    if spec.get("period"):
        items.append(f'<span><dt>期間</dt><dd>{spec["period"]}</dd></span>')
    status = spec.get("status")
    if isinstance(status, dict):
        pip = PIP_HTML.get(status.get("pip", "info"), "")
        items.append(
            f'<span><dt>ステータス</dt><dd>{pip} {status.get("label", "")}</dd></span>'
        )
    return "\n          ".join(items)


def build_section_html(section: dict[str, str], idx: int) -> str:
    sid = section["id"]
    toc = section["toc"]
    heading = section["heading"]
    h2_style = ' style="margin-top:0;padding-top:0;border-top:0;"' if idx == 0 else ""
    return (
        f'\n      <section id="{sid}" data-toc="{toc}">\n'
        f'        <h2{h2_style}>{heading}</h2>\n'
        f'        <p>セクション本文を書く。</p>\n'
        f'      </section>\n'
    )


def render(spec: dict[str, Any], template: str) -> str:
    rtype = spec.get("type", "data-analysis")
    sections = spec.get("sections") or REPORT_TYPE_DEFAULTS.get(rtype, [])
    if not sections:
        sys.exit(f"Unknown report type '{rtype}' and no sections provided in spec.")

    lang = spec.get("lang", "ja")
    title = spec.get("title", "Report")
    subtitle = spec.get("subtitle", "")
    eyebrow = spec.get("eyebrow", rtype.replace("-", " ").title())
    description = spec.get("description") or subtitle or title

    html = template
    html = html.replace('lang="ja"', f'lang="{lang}"')
    html = html.replace(
        "<title>Report Title — Subtitle</title>",
        f"<title>{title}</title>",
    )
    html = html.replace(
        '<meta name="description" content="One-sentence summary of what this report is about.">',
        f'<meta name="description" content="{description}">',
    )
    html = html.replace(
        '<p class="eyebrow">Report Type · 2026-05-16</p>',
        f'<p class="eyebrow">{eyebrow}</p>',
    )
    html = html.replace("<h1>レポートタイトル</h1>", f"<h1>{title}</h1>")

    lead_template = (
        '<p class="lead" style="margin-top:0.75rem;">'
        "サブタイトル、または一文の要約。読み手が30秒で全体像を把握できる粒度で書く。</p>"
    )
    lead_replacement = (
        f'<p class="lead" style="margin-top:0.75rem;">{subtitle}</p>' if subtitle else ""
    )
    html = html.replace(lead_template, lead_replacement)

    meta_inner = build_meta_html(spec)
    if meta_inner:
        meta_default = (
            '<span><dt>作成者</dt><dd>Author Name</dd></span>\n'
            '          <span><dt>期間</dt><dd>2026-04-01 – 2026-05-15</dd></span>\n'
            '          <span><dt>ステータス</dt><dd><span class="pip pip--success"></span> Final</dd></span>'
        )
        html = html.replace(meta_default, meta_inner)

    sections_html = "".join(build_section_html(s, i) for i, s in enumerate(sections))
    sections_start = html.find(SECTIONS_START_MARKER)
    footer_start = html.find(FOOTER_MARKER)
    if sections_start == -1 or footer_start == -1:
        sys.exit("Template structure has changed; scaffold.py needs an update.")
    html = html[:sections_start] + sections_html + "\n      " + html[footer_start:]
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold an HTML report from base.html.")
    parser.add_argument("--spec", type=Path, help="YAML or JSON spec file.")
    parser.add_argument(
        "--type",
        choices=sorted(REPORT_TYPE_DEFAULTS),
        help="Report type (if no spec).",
    )
    parser.add_argument("--title", help="Report title (if no spec).")
    parser.add_argument(
        "--out", type=Path, default=Path("report.html"), help="Output HTML path."
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Path to base.html (defaults to ../assets/base.html relative to this script).",
    )
    args = parser.parse_args()

    if args.spec:
        spec = load_spec(args.spec)
    else:
        if not args.type:
            sys.exit("Provide either --spec or --type.")
        spec = {"type": args.type, "title": args.title or "Report"}

    template_path = (
        args.template
        or (Path(__file__).resolve().parent.parent / "assets" / "base.html")
    )
    if not template_path.exists():
        sys.exit(f"Template not found: {template_path}")
    template = template_path.read_text(encoding="utf-8")

    html = render(spec, template)
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out} ({args.out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
