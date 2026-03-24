#!/bin/bash
# patch-ecc-hooks.sh
# everything-claude-code プラグインの hooks.json を拡張パッチする
# - docs/ ディレクトリ配下の .md ファイル作成を許可
# - marketplace 版と cache 版の両方をパッチ
# - プラグイン更新後に再実行が必要
#
# Usage: ~/.claude/scripts/patch-ecc-hooks.sh

set -euo pipefail

# Node で全 hooks.json を検出 → 冪等チェック → パッチ適用
node << 'NODESCRIPT'
const fs = require("fs");
const path = require("path");
const glob = require("child_process")
  .execSync('find "$HOME/.claude/plugins" -name "hooks.json" -path "*everything-claude-code*" 2>/dev/null', { encoding: "utf8" })
  .trim()
  .split("\n")
  .filter(Boolean);

if (glob.length === 0) {
  console.error("[patch-ecc] No hooks.json found. Is everything-claude-code installed?");
  process.exit(1);
}

const TARGET = 'CONTRIBUTING)\\.md$/.test(p)){';
const REPLACEMENT = 'CONTRIBUTING)\\.md$/.test(p)&&!/\\/docs\\//.test(p)){';
const MARKER = "\\/docs\\/";

let totalPatched = 0;
let totalSkipped = 0;

for (const filePath of glob) {
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  const preToolUse = data.hooks?.PreToolUse;
  if (!preToolUse) continue;

  let patched = false;
  let alreadyPatched = false;

  for (const entry of preToolUse) {
    if (entry.matcher === "Write") {
      for (const hook of entry.hooks) {
        const cmd = hook.command;
        if (cmd.includes(MARKER)) {
          alreadyPatched = true;
          break;
        }
        if (cmd.includes(TARGET)) {
          hook.command = cmd.replace(TARGET, REPLACEMENT);
          patched = true;
        }
      }
    }
  }

  if (alreadyPatched) {
    console.log("[patch-ecc] Already patched: " + filePath);
    totalSkipped++;
    continue;
  }

  if (patched) {
    fs.copyFileSync(filePath, filePath + ".bak");
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n", "utf8");
    console.log("[patch-ecc] Patched: " + filePath);
    totalPatched++;
  }
}

if (totalPatched > 0) {
  console.log("[patch-ecc] Done: " + totalPatched + " file(s) patched, " + totalSkipped + " already patched");
} else if (totalSkipped > 0) {
  console.log("[patch-ecc] All files already patched. Skipping.");
} else {
  console.error("[patch-ecc] Target pattern not found (hook structure may have changed)");
  process.exit(1);
}
NODESCRIPT
