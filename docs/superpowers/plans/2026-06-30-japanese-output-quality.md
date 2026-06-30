# 日本語出力の品質安定化システム 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Claude Code の日本語出力を、記録駆動の予防と明示レビューで安定させる仕組みを `~/.claude/` 配下に構築する。

**Architecture:** 3要素の責務分離 ―― ① CLAUDE.md 常駐ルール（予防・検知の号令）／② 記録ファイル `japanese-style-guide.md`（@参照で常駐するデータ本体）／③ スキル `japanese-output-review`（明示起動でレビュー→可視化→記録追記）。`dotdir/.claude/` 配下に置き `make link` で `~/.claude/` へ展開する。

**Tech Stack:** Markdown ドキュメント、Claude Code skill（SKILL.md frontmatter: name + description）、dotfiles symlink（`make link` / `.bin/link.sh`）、bash（grep による構造検証）。

## Global Constraints

- 言語：日本語（技術用語は英語のみ許可）。です/ます体で統一。結論ファースト。
- 配置：成果物は `dotdir/.claude/` 配下に作る。`make link` で `~/.claude/` にリンクされる（link.sh: 直下ファイルは無条件リンク=226行、`skills/` ディレクトリはリンク対象=203行）。
- スキル frontmatter は `name` + `description` の2フィールド（既存 `chatgpt-bridge` スキルに倣う）。description にトリガー語と Do NOT trigger を明記。
- `docs/` と一部成果物は `.gitignore`（`/*` ホワイトリスト方式）対象 → コミットは `git add -f` を使う。`.gitignore` 自体は変更しない。
- 記録ファイルのエントリ形式は厳密に `- ❌ 旧 → ✅ 新（理由 / YYYY-MM-DD）`。
- 既存の hook（GateGuard の Fact-Forcing Gate）に留意：Write/Bash 前に facts 提示が必要な場合がある。

---

## File Structure

| ファイル | 種別 | 責務 |
|---------|------|------|
| `dotdir/.claude/japanese-style-guide.md` | 新規 | 記録データ本体（一般ルール＋禁止→推奨 対応表）。@参照で常駐 |
| `dotdir/.claude/CLAUDE.md` | 修正 | 予防・検知の号令を追記し、`@japanese-style-guide.md` を常駐させる |
| `dotdir/.claude/skills/japanese-output-review/SKILL.md` | 新規 | レビュー&記録スキル本体 |

HTML 詳細レポートは既存の `html-report-generator` スキルへ委譲するため、references/ やテンプレートは作らない（YAGNI）。

---

## Task 1: 記録ファイル `japanese-style-guide.md` を作成

**Files:**
- Create: `dotdir/.claude/japanese-style-guide.md`

**Interfaces:**
- Produces: `~/.claude/japanese-style-guide.md`（リンク後）。CLAUDE.md（Task 2）が `@japanese-style-guide.md` で参照し、スキル（Task 3）が読み書きする。必須セクション見出し：`## 一般ルール`、`## 禁止→推奨 対応表（フィードバックで育つ）`。

- [ ] **Step 1: ファイルを作成**

`dotdir/.claude/japanese-style-guide.md` に以下を書く（全文）：

```markdown
# 日本語スタイルガイド（記録・育成ファイル）

Claude Code の日本語出力品質を律する常駐ルール。CLAUDE.md から `@japanese-style-guide.md` で参照され、常にコンテキストに載る。ユーザーが表現へ不満・言い換え要望を示したら、応答の前に「## 禁止→推奨 対応表」へ1行追記する。

## 一般ルール

- **文体**：です/ます体で統一。結論ファースト、前置き・段階報告は不要。
- **英語混入の線引き**：
  - ✅ 許可：コード識別子（変数/関数/ファイルパス）、確立した技術用語（API, git, commit, hook, MCP, PR 等）、製品名・固有名詞
  - ❌ 禁止：日常語の英語化（"Let me...", "First,", "Note that", "OK", "Done" 等を地の文に）、理由なきカタカナ英語、英文の地の文
- **崩壊出力の禁止**：ツール呼び出しマークアップ（`invoke` / `parameter` タグ等）を地の文に書かない。ツール呼び出しは正規チャネルで行う。
- **冗長さの回避**：直訳調・二重表現・冗長な敬語を避け、簡潔に書く。

## 禁止→推奨 対応表（フィードバックで育つ）

<!-- 形式: - ❌ 旧 → ✅ 新（理由 / YYYY-MM-DD） -->
（初期は空。指摘を受けるたびに1行追記する）
```

- [ ] **Step 2: 構造を検証**

Run:
```bash
grep -q '^## 一般ルール' dotdir/.claude/japanese-style-guide.md && \
grep -q '^## 禁止→推奨 対応表' dotdir/.claude/japanese-style-guide.md && \
grep -q '崩壊出力の禁止' dotdir/.claude/japanese-style-guide.md && echo "OK: 必須セクションあり"
```
Expected: `OK: 必須セクションあり`

- [ ] **Step 3: コミット**

```bash
git -C /Users/kkmclab/dotfiles add -f dotdir/.claude/japanese-style-guide.md
git -C /Users/kkmclab/dotfiles commit -m "feat: 日本語スタイルガイド記録ファイルを追加"
```

---

## Task 2: CLAUDE.md に予防・検知の号令と @参照を追記

**Files:**
- Modify: `dotdir/.claude/CLAUDE.md`（`## 基本情報` の言語行、およびファイル末尾の `@RTK.md` 隣）

**Interfaces:**
- Consumes: Task 1 が作った `japanese-style-guide.md`（@参照対象）。
- Produces: CLAUDE.md 末尾に `@japanese-style-guide.md` 行（常駐トリガー）。

現状の `## 基本情報` は以下：
```
## 基本情報

- 言語：日本語 (技術用語は英語)
- 結論ファースト。挨拶・前置き・段階報告は不要
- 敬語（です/ます体）で統一
```

現状の末尾は `@RTK.md`（単独行）。

- [ ] **Step 1: 言語行に予防の号令を追記し、検知の号令を1行加える**

`## 基本情報` を以下に置換：
```
## 基本情報

- 言語：日本語 (技術用語は英語)。`@japanese-style-guide.md` の禁止表現を避け、推奨表現を使う
- 結論ファースト。挨拶・前置き・段階報告は不要
- 敬語（です/ます体）で統一
- ユーザーが表現へ不満・言い換え要望を示したら、応答前に `japanese-style-guide.md` の対応表へ1行追記する（再発防止）
```

- [ ] **Step 2: 末尾の @参照を追加**

末尾 `@RTK.md` を以下に置換：
```
@RTK.md
@japanese-style-guide.md
```

- [ ] **Step 3: 追記を検証**

Run:
```bash
grep -q '@japanese-style-guide.md' dotdir/.claude/CLAUDE.md && \
grep -q '対応表へ1行追記' dotdir/.claude/CLAUDE.md && echo "OK: 号令と@参照あり"
```
Expected: `OK: 号令と@参照あり`

- [ ] **Step 4: コミット**

```bash
git -C /Users/kkmclab/dotfiles add dotdir/.claude/CLAUDE.md
git -C /Users/kkmclab/dotfiles commit -m "feat: CLAUDE.md に日本語出力の予防・検知号令と@参照を追加"
```
（注：`dotdir/.claude/CLAUDE.md` は追跡済みのため `-f` 不要。`git status` で確認してから add する）

---

## Task 3: スキル `japanese-output-review` を作成

**Files:**
- Create: `dotdir/.claude/skills/japanese-output-review/SKILL.md`

**Interfaces:**
- Consumes: `~/.claude/japanese-style-guide.md`（Task 1、レビュー基準の出典・追記先）。`html-report-generator` スキル（詳細レポート生成）。
- Produces: トリガー語でユーザーが起動できるレビュースキル。

- [ ] **Step 1: スキルファイルを作成**

`dotdir/.claude/skills/japanese-output-review/SKILL.md` に以下を書く（全文）：

````markdown
---
name: japanese-output-review
description: Claude Code 自身の日本語出力品質をレビューし、問題を記録ファイルに蓄積するスキル。直前/最近の応答（または指定テキスト）を5観点（不要な英語混入・文体の乱れ・記録済み禁止表現・わかりにくい表現・崩壊出力）で点検し、軽量なら Markdown、詳細なら HTML レポートで可視化、発見した問題と確定した言い換えを japanese-style-guide.md へ追記する。トリガー：「日本語チェックして」「今の出力レビューして」「日本語の品質見て」「文体チェック」「日本語レビュー」「review my Japanese output」。Do NOT trigger for: 英文の校正・翻訳、コードレビュー、Markdown/HTML の体裁のみの整形、他言語の出力。
---

# Japanese Output Review

Claude Code 自身の日本語出力を点検し、問題を `japanese-style-guide.md`（記録ファイル）へ蓄積してフィードバックループを回すスキル。

## 前提

- 基準の出典：`~/.claude/japanese-style-guide.md`（CLAUDE.md から @参照され常駐）。
- 役割分担：日常の予防と即記録は CLAUDE.md 常駐ルールが担う。本スキルは「明示的に呼ばれたときの点検と一括記録」を担う。

## フロー

### Step 1: レビュー対象の確定
- 既定：直前/最近の Claude 応答。
- 指定があればそのテキスト/ファイル。
- 対象が曖昧ならユーザーに確認する。

### Step 2: 5観点で点検
`japanese-style-guide.md` の「一般ルール」と「禁止→推奨 対応表」を基準に：
1. **不要な英語混入** — 許可（コード識別子・確立技術用語・固有名詞）以外の英語。`git`/`API`/ファイルパス等は誤検知しない。
2. **文体の乱れ** — です/ます体の不統一、敬語崩れ。
3. **記録済み禁止表現** — 対応表のエントリと照合。
4. **わかりにくい表現** — 直訳調・冗長・曖昧。
5. **崩壊出力** — ツールマークアップ（invoke/parameter タグ）混入等。

### Step 3: 可視化（出力形式は内容量で自動判定）
- **数件程度 → Markdown**：違反箇所のチェックリスト＋推奨置換。
- **多数 or 共有したい → HTML**：`html-report-generator` スキルを使い、違反ハイライト＋カテゴリ別集計＋推奨置換表＋記録反映候補のレポートを生成。

### Step 4: 記録へ追記
- 確定した言い換え・新たな禁止表現を `~/.claude/japanese-style-guide.md` の「禁止→推奨 対応表」へ追記。
- 形式：`- ❌ 旧 → ✅ 新（理由 / YYYY-MM-DD）`
- 既存エントリと重複しないか確認する。カテゴリが増えたら整理する。

## 注意
- 技術用語の英語は許可。過剰検知しない（負例を尊重）。
- 記録追記は「確定した」ものだけ。推測の言い換えは提案に留める。
````

- [ ] **Step 2: frontmatter と必須要素を検証**

Run:
```bash
f=dotdir/.claude/skills/japanese-output-review/SKILL.md
head -3 "$f" | grep -q 'name: japanese-output-review' && \
grep -q 'Do NOT trigger' "$f" && \
grep -q '5観点で点検' "$f" && \
grep -q 'html-report-generator' "$f" && echo "OK: スキル構造あり"
```
Expected: `OK: スキル構造あり`

- [ ] **Step 3: コミット**

```bash
git -C /Users/kkmclab/dotfiles add -f dotdir/.claude/skills/japanese-output-review/SKILL.md
git -C /Users/kkmclab/dotfiles commit -m "feat: japanese-output-review スキルを追加"
```

---

## Task 4: make link と統合・機能検証

**Files:**
- 変更なし（リンクと動作確認のみ）

**Interfaces:**
- Consumes: Task 1-3 の全成果物。

- [ ] **Step 1: make link でリンク**

Run:
```bash
cd /Users/kkmclab/dotfiles && make link
```
Expected: エラーなく完了。

- [ ] **Step 2: リンクを検証**

Run:
```bash
ls -la ~/.claude/japanese-style-guide.md ~/.claude/skills/japanese-output-review/SKILL.md 2>&1
```
Expected: 両方が dotdir 実体へのシンボリックリンクとして存在。

- [ ] **Step 3: 機能テスト（正例）— 英語混入を検出するか**

レビュースキルに以下のサンプル悪文を渡して点検させる：
```
Let me check this. まず設定を確認します。OK、問題なさそうです。
```
Expected: 「Let me check this」「OK」を観点1（不要な英語混入）として検出し、推奨置換（例：「確認します」「問題なさそうです」）を提示する。

- [ ] **Step 4: 機能テスト（負例）— 技術用語を誤検知しないか**

以下のサンプルを渡して点検させる：
```
git commit で変更を確定し、API のレスポンスを hook で検証します。
```
Expected: `git`, `commit`, `API`, `hook` は許可済み技術用語として**検出しない**（違反0件）。

- [ ] **Step 5: 機能テスト（即記録）— 記録追記を確認**

Step 3 で検出した「Let me check this → 確認します」を記録に追記させ、確認：
```bash
grep -q 'Let me check' ~/.claude/japanese-style-guide.md && echo "OK: 対応表へ追記された"
```
Expected: `OK: 対応表へ追記された`（追記は実体ファイル dotdir 経由で反映）

- [ ] **Step 6: 記録追記分をコミット**

```bash
git -C /Users/kkmclab/dotfiles add -f dotdir/.claude/japanese-style-guide.md
git -C /Users/kkmclab/dotfiles commit -m "test: 機能検証で得た初回エントリを記録に追加"
```
（注：テストで追記が不適切なら、コミット前に手動で除去してよい）

- [ ] **Step 7（任意）: HTML 詳細レポート生成を確認**

「HTML でレポートして」と明示するか、違反を多く含むサンプルを渡してレビューを起動し、`html-report-generator` 経由で HTML レポートが生成されることを確認する。
Expected: HTML ファイルが生成され、ブラウザで違反ハイライト・カテゴリ別集計が表示される。

---

## 完了条件

- [ ] 3成果物が `dotdir/.claude/` に存在し、`make link` で `~/.claude/` にリンクされている
- [ ] 新セッションで `@japanese-style-guide.md` がコンテキストにロードされる（CLAUDE.md 経由）
- [ ] レビュースキルが正例を検出し、負例を誤検知しない
- [ ] 指摘 → 記録追記のフローが動作する
