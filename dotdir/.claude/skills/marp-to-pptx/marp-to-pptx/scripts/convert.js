#!/usr/bin/env node
/**
 * Marp Rector Slides -> Editable PPTX Converter
 *
 * Usage: node convert.js <input.md> [output.pptx]
 * Dependencies: npm install pptxgenjs cheerio
 */

const fs = require("fs");
const path = require("path");

let PptxGenJS, cheerio;
try {
  PptxGenJS = require("pptxgenjs");
  cheerio = require("cheerio");
} catch {
  console.error("Missing dependencies. Run:\n  npm install pptxgenjs cheerio");
  process.exit(1);
}

// ── Rector Color Palette (no # prefix) ──
const C = {
  navy: "1B4565",
  teal: "3E9BA4",
  bgSec: "F5F5F5",
  textPri: "1A1A1A",
  textSec: "4A4A4A",
  textMut: "6B6B6B",
  white: "FFFFFF",
};

// ── Font sizes (pt) ──
const F = { "3xl": 48, "2xl": 32, xl: 24, lg: 20, base: 16, sm: 14 };

// ── Slide dimensions (16:9 inches) ──
const W = 10;
const H = 5.625;
const M = 0.5;

// ── Helper: fresh shadow object (PptxGenJS mutates options) ──
const cardShadow = () => ({
  type: "outer",
  color: "000000",
  blur: 4,
  offset: 2,
  angle: 135,
  opacity: 0.1,
});

// ── Helper: extract trimmed text from cheerio element ──
function txt($el) {
  return $el.text().replace(/\s+/g, " ").trim();
}

// ═══════════════════════════════════════
//  Parse Marp Markdown
// ═══════════════════════════════════════

function parseMarpFile(filePath) {
  const content = fs.readFileSync(filePath, "utf-8");

  // Strip YAML frontmatter (first --- block)
  const body = content.replace(/^---\n[\s\S]*?\n---\n/, "");

  return body
    .split(/\n---\n/)
    .map((raw) => {
      let html = raw.replace(/<script[\s\S]*?<\/script>/g, "").trim();
      if (!html) return null;

      let comment = "";
      const m = html.match(/<!--\s*([\s\S]*?)\s*-->/);
      if (m) {
        comment = m[1].trim();
        html = html.replace(/<!--[\s\S]*?-->/g, "").trim();
      }
      if (!html) return null;

      return { html, comment };
    })
    .filter(Boolean);
}

// ═══════════════════════════════════════
//  Layout Detection
// ═══════════════════════════════════════

function detectLayout({ html, comment }) {
  const cl = comment.toLowerCase();
  const h = html.toLowerCase();

  if (cl.includes("section") || h.includes("border-l-4")) return "section-break";
  if (cl.includes("chapter") || (h.includes("justify-end") && h.includes("pb-")))
    return "chapter-title";
  if (h.includes("blockquote") || cl.includes("quote")) return "quote";
  if (
    cl.includes("number") ||
    cl.includes("statistic") ||
    cl.includes("stat") ||
    (h.includes("text-em-3xl") && h.includes("font-bold") && !h.includes("grid"))
  )
    return "big-number";
  if (h.includes("\u25cf") || cl.includes("bullet")) return "bullet-list";
  if (h.includes("grid-cols-3")) {
    return h.includes("rounded-lg") ? "feature-cards" : "three-column";
  }
  if (h.includes("grid-cols-2")) {
    if (h.includes("grid-rows-2")) return "grid-2x2";
    if (h.includes("bg-navy") && cl.includes("title")) return "split-title";
    return "two-column";
  }
  if (cl.includes("title") || cl.includes("_class: title")) {
    return h.includes("opacity-") ? "title-bg" : "hero-title";
  }
  if (cl.includes("thank") || cl.includes("closing") || html.includes("Thank You"))
    return "closing";
  if (
    h.includes("items-center") &&
    h.includes("justify-center") &&
    h.includes("text-em-3xl")
  )
    return "hero-title";

  return "text-only";
}

// ═══════════════════════════════════════
//  Content Extraction
// ═══════════════════════════════════════

function extractContent(slide) {
  const $ = cheerio.load(slide.html, null, false);
  const layout = detectLayout(slide);
  const result = { layout };

  switch (layout) {
    case "hero-title":
    case "closing": {
      result.title = txt($("h1, h2").first());
      const allP = $("p");
      result.subtitle = txt(allP.first());
      const extras = [];
      allP.slice(1).each((_, el) => extras.push(txt($(el))));
      if (extras.length) result.extras = extras;
      break;
    }
    case "title-bg": {
      result.title = txt($("h1").first());
      result.subtitle = txt($("p").first());
      break;
    }
    case "split-title": {
      const cells = $(".grid > div, [class*='grid'] > div");
      result.title = txt(cells.eq(0).find("h1, h2"));
      result.subtitle = txt(cells.eq(1).find("p"));
      break;
    }
    case "section-break": {
      result.label = txt($("p").first());
      result.title = txt($("h2").first());
      break;
    }
    case "chapter-title": {
      result.number = txt($("span").first());
      result.title = txt($("h2").first());
      break;
    }
    case "text-only": {
      result.title = txt($("h2, h1").first());
      const allP = $("p");
      result.body = allP
        .map((_, el) => txt($(el)))
        .get()
        .join("\n");
      break;
    }
    case "bullet-list": {
      result.title = txt($("h2").first());
      result.items = [];
      $(".flex.items-start, [class*='flex'][class*='items-start']").each((_, el) => {
        const spans = $(el).find("span");
        const text = txt(spans.length > 1 ? spans.last() : $(el));
        if (text && text !== "\u25cf") result.items.push(text);
      });
      if (!result.items.length) {
        $("li").each((_, el) => result.items.push(txt($(el))));
      }
      break;
    }
    case "quote": {
      result.quote = txt($("blockquote p, p").first());
      result.author = txt($("cite").first()) || txt($(".text-text-muted, .text-muted").last());
      break;
    }
    case "big-number": {
      result.number = txt($("span, .text-em-3xl").first());
      const ps = $("p");
      result.label = txt(ps.eq(0));
      result.sublabel = txt(ps.eq(1));
      break;
    }
    case "two-column": {
      const cells = $(".grid > div, [class*='grid'] > div");
      result.left = {
        title: txt(cells.eq(0).find("h2, h3")),
        body: txt(cells.eq(0).find("p")),
      };
      result.right = {
        title: txt(cells.eq(1).find("h2, h3")),
        body: txt(cells.eq(1).find("p")),
      };
      const img = cells.find("img");
      if (img.length) result.image = img.attr("src");
      break;
    }
    case "three-column":
    case "feature-cards": {
      result.title = txt($("h2").first());
      result.columns = [];
      $(".grid > div, [class*='grid'] > div").each((_, el) => {
        const $el = $(el);
        result.columns.push({
          icon: txt($el.find("span").first()),
          title: txt($el.find("h3")),
          body: txt($el.find("p")),
        });
      });
      break;
    }
    case "grid-2x2": {
      result.title = txt($("h2").first());
      result.cells = [];
      $(".grid > div, [class*='grid'] > div").each((_, el) => {
        result.cells.push({
          title: txt($(el).find("h3, strong")),
          body: txt($(el).find("p")),
        });
      });
      break;
    }
  }

  return result;
}

// ═══════════════════════════════════════
//  PPTX Slide Generators
// ═══════════════════════════════════════

function addHeroTitle(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addText(d.title || "", {
    x: M, y: H * 0.3, w: W - M * 2, h: 1.2,
    fontSize: F["3xl"], fontFace: "Arial", color: C.navy,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  if (d.subtitle) {
    slide.addText(d.subtitle, {
      x: M, y: H * 0.3 + 1.4, w: W - M * 2, h: 0.8,
      fontSize: F.xl, fontFace: "Arial", color: C.textSec,
      align: "center", valign: "top", margin: 0,
    });
  }
}

function addTitleBg(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.navy };
  slide.addText(d.title || "", {
    x: M, y: H * 0.3, w: W - M * 2, h: 1.2,
    fontSize: F["3xl"], fontFace: "Arial", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  if (d.subtitle) {
    slide.addText(d.subtitle, {
      x: M, y: H * 0.3 + 1.4, w: W - M * 2, h: 0.8,
      fontSize: F.lg, fontFace: "Arial", color: C.white,
      align: "center", valign: "top", margin: 0,
    });
  }
}

function addSplitTitle(pres, d) {
  const slide = pres.addSlide();
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W / 2, h: H, fill: { color: C.navy },
  });
  slide.addText(d.title || "", {
    x: 0.8, y: H * 0.3, w: W / 2 - 1.6, h: H * 0.4,
    fontSize: F["2xl"], fontFace: "Arial", color: C.white,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  if (d.subtitle) {
    slide.addText(d.subtitle, {
      x: W / 2 + 0.8, y: H * 0.3, w: W / 2 - 1.6, h: H * 0.4,
      fontSize: F.lg, fontFace: "Arial", color: C.textSec,
      align: "left", valign: "middle", margin: 0,
    });
  }
}

function addSectionBreak(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addShape(pres.shapes.RECTANGLE, {
    x: M, y: H * 0.3, w: 0.06, h: 1.5, fill: { color: C.teal },
  });
  if (d.label) {
    slide.addText(d.label, {
      x: M + 0.4, y: H * 0.3, w: 6, h: 0.5,
      fontSize: F.base, fontFace: "Arial", color: C.textMut,
      align: "left", valign: "bottom", margin: 0,
    });
  }
  slide.addText(d.title || "", {
    x: M + 0.4, y: H * 0.3 + 0.6, w: 6, h: 0.8,
    fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
    bold: true, align: "left", valign: "top", margin: 0,
  });
}

function addChapterTitle(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addText(d.number || "", {
    x: M, y: H - 2.5, w: 4, h: 1.2,
    fontSize: F["3xl"], fontFace: "Arial", color: C.teal,
    bold: true, align: "left", valign: "bottom", margin: 0,
  });
  slide.addText(d.title || "", {
    x: M, y: H - 1.2, w: 8, h: 0.8,
    fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
    bold: true, align: "left", valign: "top", margin: 0,
  });
}

function addTextOnly(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addText(d.title || "", {
    x: 1.5, y: M, w: 7, h: 0.8,
    fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
    bold: true, align: "left", valign: "bottom", margin: 0,
  });
  if (d.body) {
    slide.addText(d.body, {
      x: 1.5, y: M + 1.0, w: 7, h: 3.5,
      fontSize: F.lg, fontFace: "Arial", color: C.textSec,
      align: "left", valign: "top", margin: 0,
    });
  }
}

function addBulletList(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addText(d.title || "", {
    x: M, y: M, w: W - M * 2, h: 0.8,
    fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
    bold: true, align: "left", margin: 0,
  });
  if (d.items && d.items.length) {
    const items = d.items.map((item, i) => ({
      text: item,
      options: {
        bullet: { color: C.teal },
        breakLine: i < d.items.length - 1,
        fontSize: F.lg,
        color: C.textPri,
        paraSpaceAfter: 8,
      },
    }));
    slide.addText(items, {
      x: M + 0.3, y: M + 1.2, w: W - M * 2 - 0.6, h: H - M - 1.8,
      fontFace: "Arial", valign: "top", margin: 0,
    });
  }
}

function addQuote(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addText(d.quote || "", {
    x: 1.5, y: H * 0.25, w: 7, h: 2.5,
    fontSize: F.xl, fontFace: "Arial", color: C.navy,
    italic: true, align: "center", valign: "middle", margin: 0,
  });
  if (d.author) {
    slide.addText(d.author, {
      x: 1.5, y: H * 0.25 + 2.8, w: 7, h: 0.5,
      fontSize: F.base, fontFace: "Arial", color: C.textMut,
      align: "center", valign: "top", margin: 0,
    });
  }
}

function addBigNumber(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addText(d.number || "", {
    x: M, y: H * 0.2, w: W - M * 2, h: 1.5,
    fontSize: F["3xl"], fontFace: "Arial", color: C.teal,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  if (d.label) {
    slide.addText(d.label, {
      x: M, y: H * 0.2 + 1.7, w: W - M * 2, h: 0.8,
      fontSize: F.xl, fontFace: "Arial", color: C.navy,
      align: "center", valign: "top", margin: 0,
    });
  }
  if (d.sublabel) {
    slide.addText(d.sublabel, {
      x: M, y: H * 0.2 + 2.6, w: W - M * 2, h: 0.5,
      fontSize: F.base, fontFace: "Arial", color: C.textMut,
      align: "center", valign: "top", margin: 0,
    });
  }
}

function addTwoColumn(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  const colW = (W - M * 2 - 0.5) / 2;

  if (d.left) {
    if (d.left.title) {
      slide.addText(d.left.title, {
        x: M, y: M, w: colW, h: 0.8,
        fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
        bold: true, align: "left", margin: 0,
      });
    }
    if (d.left.body) {
      slide.addText(d.left.body, {
        x: M, y: M + 1.0, w: colW, h: H - M * 2 - 1.2,
        fontSize: F.lg, fontFace: "Arial", color: C.textSec,
        align: "left", valign: "top", margin: 0,
      });
    }
  }

  const rx = M + colW + 0.5;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: M, w: colW, h: H - M * 2,
    fill: { color: C.bgSec }, rectRadius: 0.1,
  });

  if (d.image && fs.existsSync(path.resolve(d.image))) {
    slide.addImage({
      path: path.resolve(d.image),
      x: rx + 0.3, y: M + 0.3, w: colW - 0.6, h: H - M * 2 - 0.6,
      sizing: { type: "contain", w: colW - 0.6, h: H - M * 2 - 0.6 },
    });
  } else if (d.right) {
    if (d.right.title) {
      slide.addText(d.right.title, {
        x: rx + 0.3, y: M + 0.3, w: colW - 0.6, h: 0.8,
        fontSize: F.lg, fontFace: "Arial", color: C.navy,
        bold: true, align: "left", margin: 0,
      });
    }
    if (d.right.body) {
      slide.addText(d.right.body, {
        x: rx + 0.3, y: M + 1.2, w: colW - 0.6, h: H - M * 2 - 1.5,
        fontSize: F.lg, fontFace: "Arial", color: C.textSec,
        align: "left", valign: "top", margin: 0,
      });
    }
  }
}

function addFeatureCards(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  if (d.title) {
    slide.addText(d.title, {
      x: M, y: M, w: W - M * 2, h: 0.8,
      fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
      bold: true, align: "center", margin: 0,
    });
  }

  const cols = d.columns || [];
  const gap = 0.4;
  const cardW = (W - M * 2 - gap * (cols.length - 1)) / cols.length;
  const cardY = M + 1.2;
  const cardH = H - cardY - M;

  cols.forEach((col, i) => {
    const cx = M + i * (cardW + gap);
    slide.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cardY, w: cardW, h: cardH,
      fill: { color: C.bgSec }, rectRadius: 0.1, shadow: cardShadow(),
    });
    if (col.icon) {
      slide.addText(col.icon, {
        x: cx, y: cardY + 0.3, w: cardW, h: 0.8,
        fontSize: F["2xl"], fontFace: "Arial", color: C.teal,
        align: "center", margin: 0,
      });
    }
    if (col.title) {
      slide.addText(col.title, {
        x: cx + 0.3, y: cardY + 1.2, w: cardW - 0.6, h: 0.6,
        fontSize: F.lg, fontFace: "Arial", color: C.navy,
        bold: true, align: "center", margin: 0,
      });
    }
    if (col.body) {
      slide.addText(col.body, {
        x: cx + 0.3, y: cardY + 1.9, w: cardW - 0.6, h: cardH - 2.3,
        fontSize: F.base, fontFace: "Arial", color: C.textSec,
        align: "center", valign: "top", margin: 0,
      });
    }
  });
}

function addThreeColumn(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  if (d.title) {
    slide.addText(d.title, {
      x: M, y: M, w: W - M * 2, h: 0.8,
      fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
      bold: true, align: "center", margin: 0,
    });
  }
  const cols = d.columns || [];
  const gap = 0.4;
  const colW = (W - M * 2 - gap * (cols.length - 1)) / cols.length;
  const colY = M + 1.2;

  cols.forEach((col, i) => {
    const cx = M + i * (colW + gap);
    if (col.title) {
      slide.addText(col.title, {
        x: cx, y: colY, w: colW, h: 0.6,
        fontSize: F.lg, fontFace: "Arial", color: C.navy,
        bold: true, align: "center", margin: 0,
      });
    }
    if (col.body) {
      slide.addText(col.body, {
        x: cx, y: colY + 0.8, w: colW, h: H - colY - 0.8 - M,
        fontSize: F.base, fontFace: "Arial", color: C.textSec,
        align: "center", valign: "top", margin: 0,
      });
    }
  });
}

function addGrid2x2(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  if (d.title) {
    slide.addText(d.title, {
      x: M, y: M, w: W - M * 2, h: 0.6,
      fontSize: F["2xl"], fontFace: "Arial", color: C.navy,
      bold: true, align: "left", margin: 0,
    });
  }
  const cells = d.cells || [];
  const gap = 0.4;
  const cellW = (W - M * 2 - gap) / 2;
  const startY = M + 1.0;
  const cellH = (H - startY - M - gap) / 2;

  cells.slice(0, 4).forEach((cell, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const cx = M + col * (cellW + gap);
    const cy = startY + row * (cellH + gap);

    slide.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cy, w: cellW, h: cellH,
      fill: { color: C.bgSec }, rectRadius: 0.1,
    });
    if (cell.title) {
      slide.addText(cell.title, {
        x: cx + 0.2, y: cy + 0.2, w: cellW - 0.4, h: 0.5,
        fontSize: F.lg, fontFace: "Arial", color: C.navy,
        bold: true, align: "left", margin: 0,
      });
    }
    if (cell.body) {
      slide.addText(cell.body, {
        x: cx + 0.2, y: cy + 0.8, w: cellW - 0.4, h: cellH - 1.0,
        fontSize: F.base, fontFace: "Arial", color: C.textSec,
        align: "left", valign: "top", margin: 0,
      });
    }
  });
}

function addClosing(pres, d) {
  const slide = pres.addSlide();
  slide.background = { color: C.white };
  slide.addText(d.title || "Thank You", {
    x: M, y: H * 0.2, w: W - M * 2, h: 1.2,
    fontSize: F["3xl"], fontFace: "Arial", color: C.navy,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  if (d.subtitle) {
    slide.addText(d.subtitle, {
      x: M, y: H * 0.2 + 1.4, w: W - M * 2, h: 0.6,
      fontSize: F.lg, fontFace: "Arial", color: C.textSec,
      align: "center", margin: 0,
    });
  }
  if (d.extras && d.extras.length) {
    const lines = d.extras.map((line, i) => ({
      text: line,
      options: {
        breakLine: i < d.extras.length - 1,
        fontSize: F.base,
        color: C.textMut,
      },
    }));
    slide.addText(lines, {
      x: M, y: H * 0.2 + 2.2, w: W - M * 2, h: 1.5,
      fontFace: "Arial", align: "center", valign: "top", margin: 0,
    });
  }
}

// ── Layout -> Generator map ──
const GENERATORS = {
  "hero-title": addHeroTitle,
  "title-bg": addTitleBg,
  "split-title": addSplitTitle,
  "section-break": addSectionBreak,
  "chapter-title": addChapterTitle,
  "text-only": addTextOnly,
  "bullet-list": addBulletList,
  "quote": addQuote,
  "big-number": addBigNumber,
  "two-column": addTwoColumn,
  "three-column": addThreeColumn,
  "feature-cards": addFeatureCards,
  "grid-2x2": addGrid2x2,
  "closing": addClosing,
};

// ═══════════════════════════════════════
//  Main
// ═══════════════════════════════════════

async function main() {
  const args = process.argv.slice(2);
  if (!args.length) {
    console.log("Usage: node convert.js <input.md> [output.pptx]");
    process.exit(1);
  }

  const inputPath = path.resolve(args[0]);
  const outputPath = args[1]
    ? path.resolve(args[1])
    : inputPath.replace(/\.md$/, ".pptx");

  if (!fs.existsSync(inputPath)) {
    console.error(`File not found: ${inputPath}`);
    process.exit(1);
  }

  console.log(`Parsing: ${inputPath}`);
  const slides = parseMarpFile(inputPath);
  console.log(`  Found ${slides.length} slides`);

  const pres = new PptxGenJS();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Marp-to-PPTX Converter";

  for (let i = 0; i < slides.length; i++) {
    const content = extractContent(slides[i]);
    const gen = GENERATORS[content.layout] || addTextOnly;
    console.log(`  Slide ${i + 1}: ${content.layout}`);
    gen(pres, content);
  }

  await pres.writeFile({ fileName: outputPath });
  console.log(`Saved: ${outputPath}`);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
