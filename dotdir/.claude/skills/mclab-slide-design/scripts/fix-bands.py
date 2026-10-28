#!/usr/bin/env python3
"""結論帯を、文字があるときだけ出て、上下中央にそろう作りに直す。

レイアウト：固定の背景図形「結論帯の背景」を消し、その色を結論ラベル（idx 80）に移す。
ラベルと本文（idx 81）は帯と同じ高さにし、上下中央揃えにする。
スライド：idx 80/81 の bodyPr の上書き（anchor="t"、lIns="0" など）を外し、レイアウトに従わせる。
"""
import glob
import os
import re
import sys

ROOT = sys.argv[1]  # 展開済みディレクトリ
NS_A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def shape(s, name):
    m = re.search(r'<p:sp><p:nvSpPr><p:cNvPr id="\d+" name="%s">.*?</p:sp>' % name, s, re.S)
    return m.group(0) if m else None


def xfrm(sp):
    return tuple(int(v) for v in re.search(r'<a:off x="(\d+)" y="(\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', sp).groups())


def set_xfrm(sp, x, y, cx, cy):
    return re.sub(r'<a:off x="\d+" y="\d+"/><a:ext cx="\d+" cy="\d+"/>',
                  f'<a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/>', sp, count=1)


def center(sp, lins=0):
    return re.sub(r'(<a:bodyPr [^>]*?)lIns="\d+"([^>]*?)anchor="t"',
                  rf'\1lIns="{lins}"\2anchor="ctr"', sp, count=1)


def fix_layout(p):
    L = read(p)
    bg = shape(L, "結論帯の背景")
    if bg is None:
        return False
    bx, by, bcx, bcy = xfrm(bg)
    fill = re.search(r"<a:solidFill[^>]*>.*?</a:solidFill>", bg, re.S).group(0)
    label, body = shape(L, "結論ラベル"), shape(L, "結論本文")
    lx = xfrm(label)[0]
    # ラベルは帯全体を覆い、帯の色を持つ。文字は元の位置から始まるよう左の余白で調整する
    label2 = set_xfrm(label, bx, by, bcx, bcy)
    # PowerPoint で保存し直すと名前空間の属性が消えるため、両方の書き方に合わせる
    label2, n = re.subn(r"<a:noFill(?: [^>]*)?/>(?=<a:ln)", lambda _: fill, label2, count=1)
    assert n == 1, p
    label2 = center(label2, lx - bx)
    tx, _, tcx, _ = xfrm(body)
    body2 = center(set_xfrm(body, tx, by, tcx, bcy))
    L = L.replace(bg, "").replace(label, label2).replace(body, body2)
    write(p, L)
    return True


def fix_slide(p):
    s = read(p)
    band = [sp for sp in re.findall(r"<p:sp>.*?</p:sp>", s, re.S) if re.search(r'<p:ph type="body" idx="8[01]"/>', sp)]
    # 空の枠でも帯の色は描かれるため、文字のない帯は枠ごと外す
    if band and not "".join(re.findall(r"<a:t>([^<]*)</a:t>", "".join(band))).strip():
        for sp in band:
            s = s.replace(sp, "")
        write(p, s)
        return "removed"
    n = 0
    for sp in band:
        sp2 = re.sub(r"<a:bodyPr [^>]*?(/>|>.*?</a:bodyPr>)", f"<a:bodyPr {NS_A}/>", sp, count=1, flags=re.S)
        if sp2 != sp:
            s = s.replace(sp, sp2)
            n += 1
    write(p, s)
    return n


layouts = [os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "ppt/slideLayouts/slideLayout*.xml")) if fix_layout(p)]
slides = {os.path.basename(p): fix_slide(p) for p in glob.glob(os.path.join(ROOT, "ppt/slides/slide*.xml"))}
print("layouts:", len(layouts), sorted(layouts))
print("slides:", {k: v for k, v in slides.items() if v})
