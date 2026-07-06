# settings.json 一本化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** git(dotdir) を恒久設定の正とし、`make link` が稼働 settings.json を壊さず、稼働→git の吸い上げ経路を持つ状態にする。

**Architecture:** 設定キーを3層（①orca 注入 hooks／②個人可変 model・通知／③恒久）に分け、③のみ git 追跡。link.sh は settings.json を seed-if-absent／preserve-if-present で扱い、`settings-pull` が③だけを稼働から吸い上げる。

**Tech Stack:** zsh（link.sh・settings-pull.sh）、python3（JSON 操作、jq 非依存）、Make。

## Global Constraints

- git 追跡する③: `enabledPlugins` / `extraKnownMarketplaces` / 非 orca hooks / `permissions` / `effortLevel`
- git 非追跡: orca hooks（`command` が `.orca/` を参照）/ `model` / `agentPushNotifEnabled` / `inputNeededNotifEnabled`
- `effortLevel` の git 既定 = `"xhigh"`（意図的設定。`settings-pull` の吸い上げからは除外＝セッション値の逆流防止）
- settings.json は決して symlink しない。seed は `cp`（実ファイル）
- link.sh は `#!/bin/zsh`・`set -e` なし。テストは temp HOME／コピーで行い実 `~/.claude/settings.json` に触れない
- dotdir settings.json は git 追跡下 → 吸い上げのバックアップは `.bak` を作らず `git checkout` で戻す
- 稼働 nam-tech-studio marketplace 構造: `{"source":{"source":"github","repo":"nam-tech-studio/toolcall-recover"}}`
- コミットは `<type>: <説明>` 形式、attribution なし。docs/ 配下は gitignore のため `git add -f`

---

### Task 1: Part 2 — git 種の整備（dotdir/.claude/settings.json）

**Files:**
- Modify: `dotdir/.claude/settings.json`

**Interfaces:**
- Produces: git 種に `effortLevel="xhigh"`・`toolcall-recover@nam-tech-studio: true`・`nam-tech-studio` marketplace が入った状態（Task 3 のテスト前提、Task 2 の seed が配る内容）

- [ ] **Step 1: 検証コマンドを書き、失敗を確認**

Run:
```bash
cd /Users/kkmclab/dotfiles
python3 -c "
import json,sys
d=json.load(open('dotdir/.claude/settings.json'))
ok=(d.get('effortLevel')=='xhigh'
    and d.get('enabledPlugins',{}).get('toolcall-recover@nam-tech-studio') is True
    and 'nam-tech-studio' in d.get('extraKnownMarketplaces',{}))
print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)"
```
Expected: `FAIL`（effortLevel=high、toolcall-recover 不在）

- [ ] **Step 2: 3点を編集（python で JSON 安全に）**

Run:
```bash
cd /Users/kkmclab/dotfiles
python3 -c "
import json
p='dotdir/.claude/settings.json'
d=json.load(open(p))
d['effortLevel']='xhigh'
d['enabledPlugins']['toolcall-recover@nam-tech-studio']=True
d['extraKnownMarketplaces']['nam-tech-studio']={'source':{'source':'github','repo':'nam-tech-studio/toolcall-recover'}}
with open(p,'w') as f:
    json.dump(d,f,indent=2,ensure_ascii=False); f.write('\n')
print('done')"
```

- [ ] **Step 3: 検証コマンド再実行 + JSON 妥当性**

Run:
```bash
cd /Users/kkmclab/dotfiles
python3 -c "import json; json.load(open('dotdir/.claude/settings.json')); print('JSON OK')"
python3 -c "
import json,sys
d=json.load(open('dotdir/.claude/settings.json'))
ok=(d.get('effortLevel')=='xhigh'
    and d.get('enabledPlugins',{}).get('toolcall-recover@nam-tech-studio') is True
    and 'nam-tech-studio' in d.get('extraKnownMarketplaces',{}))
print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)"
git --no-pager diff --stat -- dotdir/.claude/settings.json
```
Expected: `JSON OK` と `PASS`。diff は settings.json のみ

- [ ] **Step 4: コミット**

```bash
cd /Users/kkmclab/dotfiles
git add dotdir/.claude/settings.json
git commit -m "chore: settings.json 種に恒久設定を反映（effortLevel=xhigh・toolcall-recover）"
```

---

### Task 2: Part 1 — link.sh 安全化（seed-if-absent / preserve-if-present）

**Files:**
- Modify: `.bin/link.sh:203`（`PRESERVE_FILES` 定義追加）と `.bin/link.sh:224-227`（ファイル分岐）
- Test: `/tmp/test-link-settings.sh`（temp HOME 統合テスト）

**Interfaces:**
- Consumes: Task 1 の dotdir settings.json（seed が配る内容）
- Produces: `make link` 全実行が `~/.claude/settings.json` を保全（実ファイルなら触らず、無ければ cp で種蒔き）

- [ ] **Step 1: 統合テストを書く（temp HOME で本物の link.sh を駆動）**

Create `/tmp/test-link-settings.sh`:
```bash
#!/bin/zsh
set -u
LINK=/Users/kkmclab/dotfiles/.bin/link.sh
DOT=/Users/kkmclab/dotfiles/dotdir/.claude/settings.json
TMP=$(mktemp -d)
fail=0

# preserve ケース: 既存の実ファイルは保全されること
mkdir -p "$TMP/.claude"
print -r -- '{"sentinel":"KEEP-ME"}' > "$TMP/.claude/settings.json"
HOME="$TMP" zsh "$LINK" >/dev/null 2>&1
if grep -q 'KEEP-ME' "$TMP/.claude/settings.json"; then echo "PRESERVE: PASS"; else echo "PRESERVE: FAIL"; fail=1; fi
if [[ -L "$TMP/.claude/settings.json" ]]; then echo "PRESERVE-TYPE: FAIL(symlink になった)"; fail=1; else echo "PRESERVE-TYPE: PASS(実ファイルのまま)"; fi

# seed ケース: 無ければ dotdir から実ファイルで種蒔き
rm -f "$TMP/.claude/settings.json"
HOME="$TMP" zsh "$LINK" >/dev/null 2>&1
if [[ -L "$TMP/.claude/settings.json" ]]; then echo "SEED-TYPE: FAIL(symlink)"; fail=1; else echo "SEED-TYPE: PASS(実ファイル)"; fi
if diff -q "$TMP/.claude/settings.json" "$DOT" >/dev/null 2>&1; then echo "SEED-CONTENT: PASS"; else echo "SEED-CONTENT: FAIL"; fail=1; fi

rm -rf "$TMP"
exit $fail
```

- [ ] **Step 2: テスト実行して失敗を確認**

Run: `zsh /tmp/test-link-settings.sh`
Expected: `PRESERVE: FAIL`（現状は `ln -fnsv` が sentinel を symlink で上書き）と `SEED-TYPE: FAIL(symlink)`。exit 1

- [ ] **Step 3: link.sh に PRESERVE_FILES 定義を追加**

`.bin/link.sh` の 203行目付近、`LINK_DIRECTORIES=(...)` の直後に1行追加。

古い:
```zsh
    LINK_DIRECTORIES=("agents" "workflows" "scripts" "assets" "skills" "rules")
```
新しい:
```zsh
    LINK_DIRECTORIES=("agents" "workflows" "scripts" "assets" "skills" "rules")
    PRESERVE_FILES=("settings.json")   # 外部ツール(orca/Claude Code)が書き換える → リンクせず保全（seed-if-absent）
```

- [ ] **Step 4: link.sh のファイル分岐を書き換え**

`.bin/link.sh:224-227` のファイル分岐を置換。

古い:
```zsh
        else
            # Link files
            ln -fnsv "$claudefile" "$HOME/.claude/$filename"
        fi
```
新しい:
```zsh
        else
            # Link files（外部ツールが書き換えるファイルは保全）
            is_preserve=false
            for pf in "${PRESERVE_FILES[@]}"; do
                [[ "$filename" == "$pf" ]] && is_preserve=true && break
            done
            if [[ "$is_preserve" == true ]]; then
                if [[ ! -e "$HOME/.claude/$filename" ]]; then
                    cp "$claudefile" "$HOME/.claude/$filename"      # 種を蒔く（新マシン）
                    echo "seeded (copy): $filename"
                else
                    echo "preserved (exists): $filename"            # 既存を保全
                fi
            else
                ln -fnsv "$claudefile" "$HOME/.claude/$filename"
            fi
        fi
```

- [ ] **Step 5: テスト再実行して成功を確認**

Run: `zsh /tmp/test-link-settings.sh`
Expected: `PRESERVE: PASS` / `PRESERVE-TYPE: PASS` / `SEED-TYPE: PASS` / `SEED-CONTENT: PASS`。exit 0

- [ ] **Step 6: コミット**

```bash
cd /Users/kkmclab/dotfiles
git add .bin/link.sh
git commit -m "fix: link.sh が settings.json を保全（seed-if-absent/preserve-if-present）"
```

---

### Task 3: Part 3 — settings-pull.sh + Makefile ターゲット

**Files:**
- Create: `.bin/settings-pull.sh`
- Modify: `Makefile`（`settings-pull` ターゲット追加）
- Test: `/tmp/test-settings-pull.sh`（fixture で挙動検証）

**Interfaces:**
- Produces: `make settings-pull` / `.bin/settings-pull.sh [--dry-run|--yes]`。env `SP_RUNTIME`・`SP_GIT` で入出力を差し替え可能（テスト用）

- [ ] **Step 1: fixture テストを書く**

Create `/tmp/test-settings-pull.sh`:
```bash
#!/bin/zsh
set -u
SP=/Users/kkmclab/dotfiles/.bin/settings-pull.sh
TMP=$(mktemp -d)
cat > "$TMP/runtime.json" <<'JSON'
{
  "effortLevel": "xhigh",
  "model": "claude-fable-5[1m]",
  "agentPushNotifEnabled": true,
  "inputNeededNotifEnabled": true,
  "enabledPlugins": {"foo@bar": true, "toolcall-recover@nam-tech-studio": true},
  "extraKnownMarketplaces": {"nam-tech-studio": {"source":{"source":"github","repo":"nam-tech-studio/toolcall-recover"}}},
  "hooks": {
    "PreToolUse": [
      {"matcher":"*","hooks":[{"type":"command","command":"/Users/x/.orca/agent-hooks/claude-hook.sh"}]},
      {"matcher":"Bash","hooks":[{"type":"command","command":"real-hook.sh"}]}
    ],
    "StopFailure": [
      {"hooks":[{"type":"command","command":"/Users/x/.orca/agent-hooks/claude-hook.sh"}]}
    ]
  }
}
JSON
cat > "$TMP/git.json" <<'JSON'
{
  "effortLevel": "high",
  "enabledPlugins": {"foo@bar": true},
  "extraKnownMarketplaces": {},
  "hooks": {"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"real-hook.sh"}]}]}
}
JSON
SP_RUNTIME="$TMP/runtime.json" SP_GIT="$TMP/git.json" zsh "$SP" --yes >/dev/null 2>&1
python3 -c "
import json,sys
r=json.load(open('$TMP/git.json')); s=json.dumps(r)
checks={
 'effortLevel は git 値保持': r.get('effortLevel')=='high',
 'model 除外': 'model' not in r,
 '通知フラグ除外': 'agentPushNotifEnabled' not in r and 'inputNeededNotifEnabled' not in r,
 'toolcall-recover 吸い上げ': r['enabledPlugins'].get('toolcall-recover@nam-tech-studio') is True,
 'marketplace 吸い上げ': 'nam-tech-studio' in r['extraKnownMarketplaces'],
 'orca hooks 除去': '.orca/' not in s,
 'orca 専用イベント削除': 'StopFailure' not in r.get('hooks',{}),
 '非 orca hook 保持': any('real-hook' in json.dumps(b) for b in r['hooks']['PreToolUse']),
}
bad=[k for k,v in checks.items() if not v]
print('ALL PASS' if not bad else 'FAIL: '+', '.join(bad)); sys.exit(1 if bad else 0)"
rc=$?
rm -rf "$TMP"; exit $rc
```

- [ ] **Step 2: テスト実行して失敗を確認**

Run: `zsh /tmp/test-settings-pull.sh`
Expected: 失敗（`.bin/settings-pull.sh` 未作成でエラー）

- [ ] **Step 3: settings-pull.sh を作成**

Create `.bin/settings-pull.sh`:
```zsh
#!/bin/zsh
# settings-pull.sh — 稼働 settings.json から恒久設定(③)だけを git(dotdir) へ吸い上げる。
# 除外: orca hooks(command が .orca/ を参照) / model / 通知2フラグ / effortLevel(セッション値の逆流防止)。
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOTDIR_ROOT="$(cd "${SCRIPT_DIR}/../dotdir" && pwd)"
RUNTIME="${SP_RUNTIME:-$HOME/.claude/settings.json}"
GIT_SETTINGS="${SP_GIT:-${DOTDIR_ROOT}/.claude/settings.json}"
MODE="interactive"
[[ "${1:-}" == "--dry-run" ]] && MODE="dry"
[[ "${1:-}" == "--yes" ]] && MODE="yes"

python3 - "$RUNTIME" "$GIT_SETTINGS" "$MODE" <<'PY'
import json, sys, copy, difflib
runtime_p, git_p, mode = sys.argv[1], sys.argv[2], sys.argv[3]
EXCLUDE = {'model','agentPushNotifEnabled','inputNeededNotifEnabled','effortLevel'}
runtime = json.load(open(runtime_p))
git = json.load(open(git_p))

# クリーン版 = runtime から除外キーを外し、hooks の orca 参照要素を除去
clean = copy.deepcopy(runtime)
for k in EXCLUDE:
    clean.pop(k, None)
new_hooks = {}
for event, blocks in clean.get('hooks', {}).items():
    kept = []
    for block in blocks:
        hb = [h for h in block.get('hooks', []) if '.orca/' not in json.dumps(h)]
        if hb:
            nb = dict(block); nb['hooks'] = hb; kept.append(nb)
    if kept:
        new_hooks[event] = kept
clean['hooks'] = new_hooks

# merge: git を土台に clean の③キーで更新。effortLevel は git 値を保持。②キーは念のため落とす
result = dict(git)
for k, v in clean.items():
    result[k] = v
result['effortLevel'] = git.get('effortLevel', result.get('effortLevel'))
for k in ('model','agentPushNotifEnabled','inputNeededNotifEnabled'):
    result.pop(k, None)

def dump(o): return json.dumps(o, indent=2, ensure_ascii=False).splitlines()
diff = list(difflib.unified_diff(dump(git), dump(result), 'git(before)', 'git(after)', lineterm=''))
if not diff:
    print('差分なし。吸い上げる恒久変更はありません。'); sys.exit(0)
print('\n'.join(diff))
if mode == 'dry':
    print('\n[dry-run] 書き込みませんでした。'); sys.exit(0)
if mode == 'interactive':
    sys.stderr.write('\nこの差分を dotdir へ書き込みますか? [y/N]: '); sys.stderr.flush()
    if sys.stdin.readline().strip().lower() not in ('y','yes'):
        print('中止しました。'); sys.exit(0)
with open(git_p, 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False); f.write('\n')
print(f'\n書き込みました: {git_p}')
print('git status/diff を確認し、意図どおりならコミットしてください（誤りは git checkout で戻せます）。')
PY
```
Then: `chmod +x .bin/settings-pull.sh`

- [ ] **Step 4: テスト再実行して成功を確認**

Run: `chmod +x .bin/settings-pull.sh && zsh /tmp/test-settings-pull.sh`
Expected: `ALL PASS`。exit 0

- [ ] **Step 5: Makefile に settings-pull ターゲットを追加**

`Makefile` の `link:` ターゲット（17-19行）の直後に追加：
```makefile
settings-pull:
	@echo "\033[0;34mRun settings-pull.sh\033[0m"
	@.bin/settings-pull.sh
```
検証 Run: `cd /Users/kkmclab/dotfiles && make -n settings-pull`
Expected: `.bin/settings-pull.sh` を呼ぶ行が表示される

- [ ] **Step 6: コミット**

```bash
cd /Users/kkmclab/dotfiles
git add .bin/settings-pull.sh Makefile
git commit -m "feat: settings-pull で稼働→git の恒久設定を吸い上げ（orca hooks/一時値を除外）"
```

---

### Task 4: Part 4 — 運用メモと参照

**Files:**
- Create: `docs/settings-ownership.md`
- Modify: `CLAUDE.md`（リポジトリ直下。Change Guidelines に参照追加）

- [ ] **Step 1: 運用メモを作成**

Create `docs/settings-ownership.md`:
```markdown
# settings.json 所有モデル

Claude Code の `settings.json` は git・orca・Claude Code の3者が関わるため、扱いを固定する。

## 3層

| 層 | キー | 所有者 | git 追跡 |
|----|------|--------|:---:|
| ① orca 注入 | hooks の `.orca/` 参照（7イベント）+ StopFailure | orca が起動時に注入 | ✕ |
| ② 個人・可変 | `model`・`agentPushNotifEnabled`・`inputNeededNotifEnabled` | Claude Code がセッションで書く | ✕ |
| ③ 恒久・意図 | `enabledPlugins`・`extraKnownMarketplaces`・非 orca hooks・`permissions`・`effortLevel` | 人が意図して決める | ○ git が正 |

## 鉄則

- **settings.json は決して symlink しない**。Claude Code も orca もアトミック書き込み（temp+rename）を使い、`rename()` がリンクを実ファイルへ置換するため、リンクは持続せず乖離する。
- `~/.claude/settings.json` は**ライブの実ファイル**（git 実体 `dotdir/.claude/settings.json` は種）。
- `make link` は settings.json を **seed-if-absent / preserve-if-present** で扱う（`link.sh` の `PRESERVE_FILES`）。既存は絶対に上書きしない。

## 恒久変更を git に取り込む

`/config` やプラグイン有効化で③の恒久変更をしたら：

    make settings-pull        # 差分を見て確認して dotdir へ書き込み（対話）
    .bin/settings-pull.sh --dry-run   # 確認のみ

`settings-pull` は orca hooks と②（model・通知・effortLevel）を自動除外する。書き込み後は `git diff` を確認してコミット。誤りは `git checkout dotdir/.claude/settings.json` で戻せる。

## 既知の制限

- `settings-pull` は追加・変更を吸い上げるが、稼働側で**キーごと削除**した変更は git に伝播しない（merge であってミラーではない）。削除を反映したい時は dotdir を直接編集する。
```

- [ ] **Step 2: リポジトリ CLAUDE.md に参照を追加**

`CLAUDE.md`（リポジトリ直下）の `## Change Guidelines` 節の末尾に1行追加：

古い:
```markdown
- `.Brewfile` 変更時は `brew bundle --file=.Brewfile` で検証可能
```
新しい:
```markdown
- `.Brewfile` 変更時は `brew bundle --file=.Brewfile` で検証可能
- `settings.json` の扱い（git=種／稼働=ライブ／symlink 禁止／`make settings-pull`）は [docs/settings-ownership.md](docs/settings-ownership.md) を参照
```

- [ ] **Step 3: 存在と参照を検証**

Run:
```bash
cd /Users/kkmclab/dotfiles
test -f docs/settings-ownership.md && echo "doc OK"
grep -q 'settings-ownership.md' CLAUDE.md && echo "ref OK"
```
Expected: `doc OK` と `ref OK`

- [ ] **Step 4: コミット**

```bash
cd /Users/kkmclab/dotfiles
git add -f docs/settings-ownership.md
git add CLAUDE.md
git commit -m "docs: settings.json 所有モデルの運用メモを追加し CLAUDE.md から参照"
```

---

### Task 5: 実環境の最終統合検証（`make link` を実走）

**Files:** なし（検証のみ）

**Interfaces:**
- Consumes: Task 2 の link.sh 修正
- Produces: 実 `~/.claude/settings.json` が `make link` 全実行後も保全されることの確証

- [ ] **Step 1: 稼働 settings.json を退避（安全のため）**

Run:
```bash
cp /Users/kkmclab/.claude/settings.json /private/tmp/claude-501/-Users-kkmclab-dotfiles/3b05fe0c-6a5c-4509-9d3c-d68b775352e2/scratchpad/settings.pre-link.bak
md5 -q /Users/kkmclab/.claude/settings.json
```
（表示された md5 を控える）

- [ ] **Step 2: `make link` を実走**

Run: `cd /Users/kkmclab/dotfiles && make link 2>&1 | grep -i settings`
Expected: `preserved (exists): settings.json` が出る

- [ ] **Step 3: 保全を確認**

Run:
```bash
[ -L /Users/kkmclab/.claude/settings.json ] && echo "FAIL: symlink 化した" || echo "PASS: 実ファイルのまま"
md5 -q /Users/kkmclab/.claude/settings.json
grep -q 'orca' /Users/kkmclab/.claude/settings.json && echo "PASS: orca hooks 保持" || echo "FAIL: orca hooks 消失"
```
Expected: `PASS: 実ファイルのまま`、md5 が Step 1 と一致、`PASS: orca hooks 保持`

- [ ] **Step 4: 記録**

`docs/reports/` またはメモリに「settings.json 一本化 完了」を記録し、次セッションの棚卸し対象から外す。

---

## Self-Review（記入済み）

- **Spec coverage**: Part 1→Task 2、Part 2→Task 1、Part 3→Task 3、Part 4→Task 4、全体統合テスト→Task 5。全 Part に対応タスクあり。
- **Placeholder scan**: 各ステップに実コード・実コマンド・期待出力を記載。TBD/TODO なし。
- **Type consistency**: `PRESERVE_FILES`（Task 2）・env `SP_RUNTIME`/`SP_GIT`・`MODE`（Task 3）・除外キー集合（Task 3/spec）は一貫。effortLevel は「③追跡だが pull 除外」で Task 1（設定）と Task 3（保持）が整合。
