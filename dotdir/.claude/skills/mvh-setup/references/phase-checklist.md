# Phase Checklist

各フェーズの詳細チェックリストと受け入れ基準。

## Week 1 -- Foundation

### 1. CLAUDE.md Generation

**委譲先**: `/claude-md-generator`

**受け入れ基準**:
- [ ] CLAUDE.md がプロジェクトルートに存在する
- [ ] 50 行以下である
- [ ] Pointer-based である（prose description ではなく、ファイルパスやコマンドへのポインタ）
- [ ] 全てのポインタの参照先が実在する（broken pointer がない）
- [ ] ビルド・テスト・lint のコマンドが記載されている
- [ ] 不要な記述がない（`package.json` が既に宣言している情報の重複等）

**判定方法**:
```bash
test -f CLAUDE.md && [ "$(wc -l < CLAUDE.md)" -le 50 ]
```

**失敗時のアクション**: `/claude-md-generator` を slim mode で実行

---

### 2. PostToolUse Auto-Format

**委譲先**: `/auto-format-hook`

**受け入れ基準**:
- [ ] `.claude/settings.json` に `PostToolUse` エントリが存在する
- [ ] hook スクリプトが存在し、実行可能である
- [ ] プロジェクトの formatter/linter が正しく検出されている
- [ ] hook が exit 0 を返す（agent をブロックしない）
- [ ] 実際にファイルを編集した後、自動フォーマットが走ることを確認

**判定方法**:
```bash
# settings.json に PostToolUse があるか
grep -q "PostToolUse" .claude/settings.json 2>/dev/null

# hook スクリプトが実行可能か
test -x .claude/scripts/hooks/post-edit-autoformat.sh 2>/dev/null || \
test -x ~/.claude/scripts/hooks/post-edit-autoformat.sh 2>/dev/null
```

**失敗時のアクション**: `/auto-format-hook` を実行

---

### 3. Linter Config Protection

**委譲先**: `/lint-config-guard`

**受け入れ基準**:
- [ ] `.claude/settings.json` に `PreToolUse` エントリが存在する
- [ ] lint-config-guard スクリプトが存在し、実行可能である
- [ ] 保護対象のファイルリストがプロジェクトの設定ファイルと一致する
- [ ] 保護対象ファイルへの Edit を試みると exit 2 (BLOCK) が返る
- [ ] エラーメッセージが「修正方法」を含んでいる

**判定方法**:
```bash
# PreToolUse hook があるか
grep -q "PreToolUse" .claude/settings.json 2>/dev/null

# guard スクリプトが存在するか
test -x .claude/scripts/hooks/lint-config-guard.sh 2>/dev/null
```

**失敗時のアクション**: `/lint-config-guard` を実行

---

### 4. First ADR (ADR-0001)

**直接生成**

**受け入れ基準**:
- [ ] `docs/adr/` ディレクトリが存在する
- [ ] ADR-0001 ファイルが存在する
- [ ] Status, Date, Context, Decision, Consequences セクションが全てある
- [ ] harness engineering の採用理由が Context に記載されている
- [ ] 具体的な harness コンポーネント（CLAUDE.md, hooks, linter protection 等）が Decision にリストされている

**判定方法**:
```bash
# ADR ディレクトリと最初の ADR が存在するか
ls docs/adr/ADR-0001* docs/adr/adr-0001* docs/adr/0001-* 2>/dev/null | head -1
```

**失敗時のアクション**: MVH スキルが直接生成する

---

## Week 2-4 -- Reinforcement

### 5. Repo Hygiene Audit

**委譲先**: `/repo-hygiene-audit`

**受け入れ基準**:
- [ ] 監査が実行済みである（監査レポートまたはスコアカードに記録あり）
- [ ] broken links / stale docs が特定されている
- [ ] 修正アクションが実行されたか、Issue として記録されている

**判定方法**:
```bash
# スコアカードに hygiene audit の記録があるか
grep -q "hygiene" .claude/harness-scorecard.md 2>/dev/null
```

**失敗時のアクション**: `/repo-hygiene-audit` を実行

---

### 6. Stop Hook (Test Gate)

**直接生成**

**受け入れ基準**:
- [ ] `.claude/scripts/hooks/stop-test-gate.sh` が存在し、実行可能である
- [ ] `.claude/settings.json` に `Stop` hook エントリが存在する
- [ ] テストコマンドがプロジェクトに合わせて設定されている
- [ ] テストが失敗した場合、hook の出力にエラー内容が含まれる
- [ ] テストが成功した場合、hook は exit 0 を返す

**判定方法**:
```bash
# Stop hook があるか
grep -q '"Stop"' .claude/settings.json 2>/dev/null

# スクリプトが実行可能か
test -x .claude/scripts/hooks/stop-test-gate.sh 2>/dev/null
```

**失敗時のアクション**: MVH スキルが stop-hook-template.md を基に生成

---

### 7. Session Startup Routine

**直接生成**

**受け入れ基準**:
- [ ] CLAUDE.md に "Session Startup" セクションが存在する
- [ ] `git log` で最近の変更を確認するステップがある
- [ ] スコアカードを確認するステップがある
- [ ] ビルド/dev server の動作確認ステップがある

**判定方法**:
```bash
# CLAUDE.md にスタートアップセクションがあるか
grep -qi "session startup\|session start\|セッション開始" CLAUDE.md 2>/dev/null
```

**失敗時のアクション**: MVH スキルが CLAUDE.md にセクションを追加

---

### 8. Pre-commit Hooks

**直接生成**

**受け入れ基準**:
- [ ] `lefthook.yml` または `.husky/` が存在する
- [ ] pre-commit で lint/format が実行される設定になっている
- [ ] PostToolUse hook と同じ linter/formatter が使われている
- [ ] `lefthook install` (または `husky install`) が実行済み

**判定方法**:
```bash
# Lefthook or Husky が設定されているか
test -f lefthook.yml || test -d .husky
```

**失敗時のアクション**: MVH スキルが lefthook.yml を生成

---

## Month 2-3 -- Advanced

### 9. Custom Lint Rules

**ガイダンス提供のみ**

**受け入れ基準**:
- [ ] プロジェクト固有の lint ルールが 1 つ以上存在する
- [ ] ルールに instructive なエラーメッセージがある
- [ ] ルールが CI で強制されている

**ガイダンス**:
- TypeScript: ESLint custom rules (`eslint-plugin-local` パターン)
- Python: Ruff custom rules or flake8 plugins
- Go: `go vet` analyzers
- Rust: clippy custom lints

---

### 10. Garbage Collection Schedule

**ガイダンス提供のみ**

**受け入れ基準**:
- [ ] スコアカードに次回監査日が記録されている
- [ ] CLAUDE.md に定期監査のリマインダーがある
- [ ] 前回の監査から 30 日以上経過していない

**ガイダンス**:
- `.claude/harness-scorecard.md` に `Next audit: YYYY-MM-DD` を追記
- CLAUDE.md に `## Periodic Tasks` セクションを追加
- 月次で `/repo-hygiene-audit` を実行する運用フローを確立

---

### 11. PreToolUse Safety Gates

**ガイダンス提供のみ**

**受け入れ基準**:
- [ ] 破壊的コマンドをブロックする PreToolUse hook が存在する
- [ ] 保護対象ファイル/ディレクトリのリストがある
- [ ] ブロック時に代替手段を提示するメッセージがある

**ガイダンス**:
- ブロック対象コマンド例: `rm -rf`, `git reset --hard`, `git push --force`, `DROP TABLE`
- 保護対象ファイル例: `.env`, `credentials.json`, `*.pem`, `*.key`
- hook は `Bash` ツールの引数をパースし、危険なパターンにマッチしたら exit 2 を返す
