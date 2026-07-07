# Opus 4.8 Fable 級化基盤 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Opus 4.8 で Fable 級の実行品質（深い推論・意図汲み取り）を得るためのコスト階段型四層基盤（L0 蒸留知識 / L1 外注検証 / L2 専門 Agent / L3 並列 Workflow）を dotfiles に構築する。

**Architecture:** 設計書 `docs/superpowers/specs/2026-07-07-opus-fable-parity-design.md` のとおり。検証の本体を Codex CLI・agy CLI（外部クォータ）へ外注して Claude 週次トークンを温存し、Claude は裁定・統合のみ担う。L0（常時）→ L1（自動）→ L2（重要タスクで準自動）→ L3（明示のみ）のコスト階段。

**Tech Stack:** bash（llm-worker）、Claude Code Agent 定義（Markdown + frontmatter）、Claude Code Workflow（JavaScript）、Claude Code スキル（SKILL.md）、codex CLI 0.142.5、agy CLI 1.0.10、GNU timeout（/opt/homebrew/bin/timeout）。

## Global Constraints

- dotdir/ 配下の編集は `$HOME` に即影響する（merge リンク）。`agents`/`workflows`/`skills`/`scripts`/`assets`/`rules` はディレクトリごとリンク済み＝中に新規ファイルを置くだけで反映。ルート直下の新規ファイルは `make link` 再実行が必要
- 秘密情報は絶対にコミットしない
- コミットは日本語 conventional commits（`feat:` / `docs:` / `chore:`）
- このリポジトリの .gitignore はホワイトリスト方式（`/*` で全無視）。追跡外の新規パスは `git add -f` が必要
- decision-patterns.md は 100 行上限
- agy のモデル指定は `"Gemini 3.1 Pro (High)"`（軽量確認は `"Gemini 3.5 Flash (Low)"`）
- Claude トークンを消費する検証（Workflow 実行等）は最小構成で1回のみ

---

### Task 1: decision-patterns.md の作成（Fable 蒸留・L0）

**Files:**
- Create: `dotdir/.claude/decision-patterns.md`

**Interfaces:**
- Produces: `$HOME/.claude/decision-patterns.md`（リンク経由）。Task 2 の CLAUDE.md が `@decision-patterns.md` で import する

- [ ] **Step 1: ファイルを作成する**

以下の内容で `dotdir/.claude/decision-patterns.md` を作成する（Fable 5 蒸留済みの完成品。変更せずそのまま使う）:

```markdown
# Decision Patterns（判断パターン集）

Fable 5 が過去セッションから蒸留した「依頼の型 → 正しい解釈・動き方」。曖昧な依頼の解釈時に参照する。
ユーザーの修正・指摘があったら該当行を追記・更新する（育成型、100行上限。超過時は自明になった行を削る）。

## 依頼の型と解釈

| 依頼の型 | 正しい解釈・動き方 |
|---------|------------------|
| 「確認して」「見て」「チェックして」 | 読み取り専用の点検と報告。修正はユーザーが求めるまでしない |
| 「〜したい」（構想・願望形） | 要件のブレインストーミングから開始。いきなり実装しない |
| 「進めて」「順番に進めて」 | 直前に合意した計画の次ステップを実行。新しい解釈を持ち込まない |
| 「修正しました」「直しました」 | ユーザーが手動対応済み。同じ修正を繰り返さず次へ。必要なら結果だけ検証 |
| 「残りは？」「次は？」 | タスク一覧と根拠を提示。勝手に着手しない |
| 「OK」 | 直前の提案への承認。それ以前の保留事項すべてへの許可ではない |
| 質問形（「〜はどう？」「なぜ？」） | 求められているのは分析・説明。ファイル変更はしない |
| 表現への不満・言い換え要望 | 応答前に japanese-style-guide.md の対応表へ1行追記（再発防止） |

## このユーザーの固有文脈

- 医学研究者（老年医学・フレイル研究）＋開発者。論文執筆と環境整備（dotfiles/ハーネス）が2大領域
- トークン効率への意識が高い：週次制限あり。Claude 並列（サブエージェント・Workflow）は高価値タスク限定、検証・調査は Codex/agy への外注を優先
- 監査可能性を重視：環境変更にはレポート（docs/reports/）やログを残す。env-audit が月次自動実行される
- シンプル第一・YAGNI：ラッパーや抽象層の追加は「本当に要るか」を先に問う
- dotdir/ 配下の編集は $HOME に即影響（merge リンク）。影響範囲を宣言してから編集する
- settings.json は symlink 禁止（git=種／稼働=ライブ）。恒久変更は make settings-pull
- 秘密情報（.ssh 鍵・トークン）は絶対にコミットしない
- 3ステップ以上のタスクは Plan モードで開始。5分未満の作業は委譲しない
- 重要な設計判断では Codex・agy のセカンドオピニオンを取ると信頼される

## 危険な誤解釈（Opus がやりがちなミスの先回り）

- 分析依頼に対して修正まで実行してしまう → 依頼の動詞と対象を見る。調査対象なら報告止まり
- 曖昧なまま大規模作業を開始する → 解釈が2つ以上あり結果が大きく変わるなら AskUserQuestion で確認
- スコープの勝手な拡大 → ついでの改善・リファクタリングは提案に留め、承認を得てから実行
- 確認質問のしすぎで作業が止まる → 可逆で小さい判断は自分で決めて宣言。不可逆・高コストのみ確認
- 完了の早計宣言 → 「動くはず」ではなく動作証拠（実行ログ・テスト結果）を示してから完了とする
- 週次トークンを考慮せず Claude 並列を乱発 → L2/L3 起動前にコストを一言明示する
```

- [ ] **Step 2: 行数が 100 行以内であることを確認する**

Run: `wc -l dotdir/.claude/decision-patterns.md`
Expected: 50 行前後（100 未満）

- [ ] **Step 3: make link で $HOME へ反映する**

Run: `cd /Users/kkmclab/dotfiles && make link 2>&1 | grep -i "decision"`
Expected: `decision-patterns.md` のリンク作成行が出力される

- [ ] **Step 4: リンクを検証する**

Run: `ls -la ~/.claude/decision-patterns.md`
Expected: `-> /Users/kkmclab/dotfiles/dotdir/.claude/decision-patterns.md` のシンボリックリンク

- [ ] **Step 5: コミット**

```bash
git add -f dotdir/.claude/decision-patterns.md
git commit -m "feat: decision-patterns.md を追加（L0 判断パターン蒸留・Fable 5 執筆）"
```

---

### Task 2: CLAUDE.md へ intent-gate ルール追記（L0）

**Files:**
- Modify: `dotdir/.claude/CLAUDE.md`（「### 検証」セクションの直前に挿入 + 末尾 import 追加）

**Interfaces:**
- Consumes: Task 1 の `decision-patterns.md`
- Produces: 全セッション常駐の intent-gate ルール

- [ ] **Step 1: 「### 検証」の直前に intent-gate セクションを挿入する**

`dotdir/.claude/CLAUDE.md` の `### 検証` の直前に以下を挿入:

```markdown
### Intent Gate（曖昧な依頼の解釈宣言）

- 依頼が曖昧（複数解釈可・成功基準不明・影響範囲不明）なら、着手前に解釈・前提・成功基準を1〜3行で宣言する
- 解釈の分岐が結果を大きく変えるときは AskUserQuestion で確認（推測で大きな作業を進めない）
- 依頼の解釈は decision-patterns.md の判断パターンに従う

```

- [ ] **Step 2: 末尾の import 群に decision-patterns.md を追加する**

`dotdir/.claude/CLAUDE.md` 末尾の

```markdown
@RTK.md
@japanese-style-guide.md
```

を次に変更:

```markdown
@RTK.md
@japanese-style-guide.md
@decision-patterns.md
```

- [ ] **Step 3: 変更内容を確認する**

Run: `grep -n "Intent Gate\|decision-patterns" dotdir/.claude/CLAUDE.md`
Expected: intent-gate セクション見出し・参照行・末尾 import の3箇所以上が表示される

- [ ] **Step 4: コミット**

```bash
git add dotdir/.claude/CLAUDE.md
git commit -m "feat: CLAUDE.md へ Intent Gate（解釈宣言）ルールを追加（L0）"
```

---

### Task 3: llm-worker.sh の作成とスモークテスト（L1 土台）

**Files:**
- Create: `.bin/llm-worker.sh`

**Interfaces:**
- Produces: `echo PROMPT | ~/dotfiles/.bin/llm-worker.sh <codex|agy|both> [--role reviewer|researcher] [--timeout SEC] [--cd DIR]`。Task 5 の second-opinion スキルが呼ぶ。終了コード: 0=少なくとも1つ成功 / 1=全 worker 失敗 / 2=引数エラー

- [ ] **Step 1: スクリプトを作成する**

以下の内容で `.bin/llm-worker.sh` を作成:

```bash
#!/usr/bin/env bash
# llm-worker.sh — Codex/agy 統一ヘッドレスラッパー（Opus Fable 級化基盤 L1）
# 使い方: echo "プロンプト" | llm-worker.sh <codex|agy|both> [--role reviewer|researcher] [--timeout SEC] [--cd DIR]
# 出力: worker ごとに「===== <worker> (Ns) =====」ヘッダー + 本文。障害時は FAILED ヘッダー。
# 終了コード: 0=少なくとも1つ成功 / 1=全 worker 失敗 / 2=引数エラー
set -u

usage() {
  echo "usage: echo PROMPT | llm-worker.sh <codex|agy|both> [--role reviewer|researcher] [--timeout SEC] [--cd DIR]" >&2
  exit 2
}

WORKER="${1:-}"
[ $# -gt 0 ] && shift
case "$WORKER" in codex|agy|both) ;; *) usage ;; esac

ROLE=""
TIMEOUT=300
WORKDIR="$PWD"
while [ $# -gt 0 ]; do
  case "$1" in
    --role)    ROLE="${2:?--role に値がありません}"; shift 2 ;;
    --timeout) TIMEOUT="${2:?--timeout に値がありません}"; shift 2 ;;
    --cd)      WORKDIR="${2:?--cd に値がありません}"; shift 2 ;;
    *) usage ;;
  esac
done

PROMPT="$(cat)"
[ -n "$PROMPT" ] || { echo "error: stdin からプロンプトを渡してください" >&2; exit 2; }

case "$ROLE" in
  reviewer) PROMPT="あなたは敵対的レビュアーです。対象を反証する視点で検証し、問題点を重大度順に根拠付きで指摘してください。反証できなければ「反証失敗」と明記してください。

$PROMPT" ;;
  researcher) PROMPT="あなたは調査担当です。事実と推測を明確に分け、事実には根拠を示し、不確かな点は不確かと明記してください。

$PROMPT" ;;
  "") ;;
  *) usage ;;
esac

LOG_DIR="$HOME/.claude/logs/llm-worker"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)-$$"

run_one() {
  local name="$1" out rc start end
  start=$(date +%s)
  case "$name" in
    codex) out=$(cd "$WORKDIR" && timeout "$TIMEOUT" codex exec --sandbox read-only "$PROMPT" 2>"$LOG_DIR/$STAMP-codex.err") ;;
    agy)   out=$(cd "$WORKDIR" && timeout "$TIMEOUT" agy --print "$PROMPT" --model "Gemini 3.1 Pro (High)" 2>"$LOG_DIR/$STAMP-agy.err") ;;
  esac
  rc=$?
  end=$(date +%s)
  printf '%s' "$out" > "$LOG_DIR/$STAMP-$name.out"
  if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
    printf '===== %s (%ss) =====\n%s\n' "$name" "$((end - start))" "$out"
    return 0
  fi
  printf '===== %s FAILED (rc=%s, %ss) — stderr: %s =====\n' "$name" "$rc" "$((end - start))" "$LOG_DIR/$STAMP-$name.err"
  return 1
}

case "$WORKER" in
  codex) run_one codex; exit $? ;;
  agy)   run_one agy; exit $? ;;
  both)
    TMP_C="$(mktemp)" TMP_A="$(mktemp)"
    run_one codex >"$TMP_C" 2>&1 & PID_C=$!
    run_one agy   >"$TMP_A" 2>&1 & PID_A=$!
    RC_C=0; RC_A=0
    wait "$PID_C" || RC_C=1
    wait "$PID_A" || RC_A=1
    cat "$TMP_C" "$TMP_A"
    rm -f "$TMP_C" "$TMP_A"
    if [ "$RC_C" -ne 0 ] && [ "$RC_A" -ne 0 ]; then exit 1; fi
    exit 0
    ;;
esac
```

- [ ] **Step 2: 実行権限を付与する**

Run: `chmod +x /Users/kkmclab/dotfiles/.bin/llm-worker.sh`

- [ ] **Step 3: 引数エラーを検証する（失敗ケース先行）**

Run: `echo "x" | /Users/kkmclab/dotfiles/.bin/llm-worker.sh wrong; echo "rc=$?"`
Expected: usage メッセージ + `rc=2`

Run: `printf '' | /Users/kkmclab/dotfiles/.bin/llm-worker.sh codex; echo "rc=$?"`
Expected: `error: stdin からプロンプトを渡してください` + `rc=2`

- [ ] **Step 4: agy 単発を検証する**

Run: `echo "1+1の答えだけを数字で返してください" | /Users/kkmclab/dotfiles/.bin/llm-worker.sh agy --timeout 120`
Expected: `===== agy (Ns) =====` ヘッダー + `2` を含む応答。rc=0

- [ ] **Step 5: codex 単発を検証する**

Run: `echo "1+1の答えだけを数字で返してください" | /Users/kkmclab/dotfiles/.bin/llm-worker.sh codex --timeout 120`
Expected: `===== codex (Ns) =====` ヘッダー + `2` を含む応答。rc=0
注意: codex exec の stdout にセッションヘッダー等の付帯情報が混ざる場合はこの Step で確認し、必要なら出力抑制フラグ（`codex exec --help` で確認）を追加する

- [ ] **Step 6: タイムアウト動作を検証する**

Run: `echo "円周率を1000桁計算して" | /Users/kkmclab/dotfiles/.bin/llm-worker.sh agy --timeout 1; echo "rc=$?"`
Expected: `===== agy FAILED (rc=124, 1s) — stderr: ...` + `rc=1`（timeout の終了コード 124 が FAILED ヘッダーに入る）

- [ ] **Step 7: both（並列 + 片方成功で続行）を検証する**

Run: `echo "「テスト成功」とだけ返してください" | /Users/kkmclab/dotfiles/.bin/llm-worker.sh both --timeout 120; echo "rc=$?"`
Expected: codex と agy の両ヘッダーが出力され rc=0

Run: `ls ~/.claude/logs/llm-worker/ | tail -4`
Expected: 直前実行の STAMP を持つログファイル（.out ×2、.err ×2）

- [ ] **Step 8: コミット**

```bash
git add -f .bin/llm-worker.sh
git commit -m "feat: llm-worker.sh を追加（Codex/agy 統一ヘッドレスラッパー・L1 土台）"
```

---

### Task 4: 停止時レビューゲートの有効化（L1・既存機能）

**Files:**
- なし（openai-codex プラグインの設定変更のみ。dotfiles への変更なし）

**Interfaces:**
- Consumes: openai-codex プラグイン 1.0.5 の stop-review-gate（実装済み Stop hook）
- Produces: コード変更ターンの完了時に Codex 自動レビュー（ALLOW/BLOCK）

- [ ] **Step 1: codex:setup スキルでゲートを有効化する**

Skill ツールで `codex:setup` を args `--enable-review-gate` 付きで起動し、スキルの手順に従う。
Expected: 有効化完了のメッセージ（Codex CLI のログイン状態確認を含む）

- [ ] **Step 2: 動作を検証する**

このタスクの後、任意のコード変更を含むターン（例: Task 5 のスキル作成）の完了時に、Stop hook が Codex レビューを起動することを観察する。
Expected: ターン終了時に stop-review-gate のレビューが走る（ALLOW なら静かに完了、指摘があれば BLOCK メッセージ）
注意: レビューゲートはターンごとに最大15分の待ちが発生しうる。作業の妨げになる場合は `codex:setup --disable-review-gate` で無効化し、その旨をユーザーへ報告して判断を仰ぐ

---

### Task 5: second-opinion スキルの作成（L1 完成）

**Files:**
- Create: `dotdir/.claude/skills/second-opinion/SKILL.md`

**Interfaces:**
- Consumes: Task 3 の `llm-worker.sh`
- Produces: `dotdir:second-opinion` スキル（明示起動 + Claude 自発起動）

- [ ] **Step 1: SKILL.md を作成する**

以下の内容で `dotdir/.claude/skills/second-opinion/SKILL.md` を作成:

```markdown
---
name: second-opinion
description: 設計判断の分岐点・自信の持てない技術判断・不可逆操作の前に、Codex と agy へ並列でセカンドオピニオンを求め、Claude が裁定する。検証の本体を外部クォータへ外注し、Claude 週次トークンは裁定分のみに抑える。トリガー：「セカンドオピニオン」「他のモデルの意見」「second opinion」「外部の意見」、設計の重大な分岐、不可逆操作の直前、確信の持てない技術判断。Do NOT trigger for: ドキュメント参照で足りる単純な事実確認、些末な判断、方針が既に確定している作業、ブラウザ ChatGPT への質問（それは chatgpt-bridge）。
---

# Second Opinion（外注セカンドオピニオン）

Codex（コード・実装視点）と agy/Gemini（調査・仕様視点）へ同じ問いを並列で投げ、回答を Claude が裁定する。

## 手順

1. **問いの整形** — 次の3要素を含むプロンプトを構築する:
   - 背景（1〜3行。前提となるコンテキスト・制約）
   - 問い（明確な1問。選択肢があるなら列挙）
   - 回答形式の指定（例:「推奨案と根拠を5行以内で」）
2. **並列外注** — Bash で実行:
   `echo "$PROMPT" | ~/dotfiles/.bin/llm-worker.sh both --timeout 300`
   - コードの検証・レビューなら `--role reviewer`、調査なら `--role researcher` を付ける
   - 対象リポジトリのコードを読ませたい場合は `--cd <リポジトリ絶対パス>` を付ける（codex がその作業ディレクトリで実行される）
3. **裁定** — 両回答を読み、次の形式で報告する:
   - **一致点**: 両者が同意している点
   - **相違点**: 判断が分かれた点と、それぞれの根拠
   - **採用判断**: Claude としての最終判断と理由（両者と異なる判断も可）
4. 裁定は3〜5行。両回答の全文は貼らず、要点のみ引用する

## 原則

- 外注は参考意見。最終判断は常に Claude が下す（盲従しない）
- 片方障害（FAILED ヘッダー）時は残った回答で裁定し、障害を明記する
- 両方障害時は「外注不可」を宣言し、自己判断で進めてよいかユーザーに確認する
- 外注プロンプトに秘密情報（鍵・トークン・非公開の個人情報）を含めない
```

- [ ] **Step 2: スキルがリンク経由で見えることを検証する**

Run: `ls ~/.claude/skills/second-opinion/SKILL.md`
Expected: パスが表示される（skills はディレクトリごとリンク済みのため make link 不要）

- [ ] **Step 3: スキルを実際に1回起動して裁定形式を検証する**

Skill ツールで `dotdir:second-opinion` を起動し、実在の判断問題を1つ流す。
例の問い:「bash スクリプトで並列プロセスの終了コードを収集する方法として `wait $PID || RC=1` 方式と `wait -n` ループ方式のどちらが堅牢か。推奨と根拠を5行以内で」
Expected: llm-worker 経由で両 worker の回答を取得し、一致点・相違点・採用判断の3部裁定が出力される

- [ ] **Step 4: コミット**

```bash
git add -f dotdir/.claude/skills/second-opinion/
git commit -m "feat: second-opinion スキルを追加（Codex/agy 並列外注 + Claude 裁定・L1 完成）"
```

---

### Task 6: adversarial-verifier Agent の作成（L2）

**Files:**
- Create: `dotdir/.claude/agents/adversarial-verifier.md`

**Interfaces:**
- Produces: Agent タイプ `adversarial-verifier`（Agent ツールと Workflow の `agentType` から利用可能）。出力規約: verdict（REFUTED|SURVIVED）+ issues。Task 7 の deep-reason.js が `agentType: 'adversarial-verifier'` で消費する

- [ ] **Step 1: Agent 定義を作成する**

以下の内容で `dotdir/.claude/agents/adversarial-verifier.md` を作成:

```markdown
---
name: adversarial-verifier
description: 成果物・結論・計画の敵対的検証専任。「反証せよ」を専務とし、前提の誤り・見落とし・検証証拠の欠如・都合の良い解釈を探す。重要タスク（不可逆・本番反映・論文の数値）の完了前検証、および deep-reason Workflow の検証ステージで使用。
tools: Read, Grep, Glob, Bash
---

あなたは敵対的検証の専任エージェントです。提示された結論・成果物・計画を「壊す」ことが任務です。正しさの確認ではなく、反証を探索してください。

## 検証観点

1. 前提の裏取り — 主張の前提は事実か。コード・ログ・ドキュメントで確認できるか
2. 分岐の見落とし — 考慮されていないエッジケース・失敗モード・代替解釈はないか
3. 証拠の有無 — 「動くはず」と「動いた」を区別しているか。検証証拠（実行ログ・テスト結果）はあるか
4. 都合の良い解釈 — 反対証拠の無視、過度な一般化、確証バイアスはないか

## 原則

1. 読み取り専用。ファイルの作成・変更・削除は一切しない（Bash は照会・再現確認に限る）
2. 各指摘に根拠（file:line・実行結果・引用）と確信度を付ける
3. 反証できなければ SURVIVED と明記する（それが合格の意味。無理に問題を作らない）
4. 些末な好みは指摘しない。結論を変えうる欠陥のみ報告する

## 出力形式

- verdict: REFUTED（結論を変えうる欠陥あり）| SURVIVED（反証失敗＝合格）
- issues: 指摘リスト（重大度順、根拠付き）。SURVIVED の場合は試みた反証と失敗理由を1〜3行
依頼側がスキーマを指定した場合はそれに従う。
```

- [ ] **Step 2: 欠陥入りサンプルで REFUTED が返るか検証する**

実装セッション自身の scratchpad ディレクトリに欠陥入りサンプルを作成する（下記パスは例。自セッションのシステムプロンプトに記載された scratchpad パスへ読み替える）:

```bash
cat > <自セッションの scratchpad>/flawed-sample.md << 'EOF'
# 結論: llm-worker.sh はすべての異常系で安全である

根拠:
1. タイムアウトは timeout コマンドで処理される
2. 両 worker 失敗時は exit 1 を返すのでエラーは伝播する
3. ログは必ず ~/.claude/logs/llm-worker/ に残るため、ディスク満杯でも安全である
4. プロンプトはシェル変数展開されるため、どんな特殊文字も安全に扱える
EOF
```

Agent ツールで `adversarial-verifier` を起動し、次の指示を渡す:
「<自セッションの scratchpad>/flawed-sample.md の結論を検証せよ。対象スクリプトは /Users/kkmclab/dotfiles/.bin/llm-worker.sh」
Expected: verdict = REFUTED。根拠 3（ディスク満杯でも安全＝書き込み失敗を考慮していない）と根拠 4（特殊文字が常に安全＝過度な一般化）の少なくとも一方を指摘する

- [ ] **Step 3: 健全なサンプルで SURVIVED が返るか検証する**

Agent ツールで `adversarial-verifier` を起動し、次の指示を渡す:
「次の結論を検証せよ:『/Users/kkmclab/dotfiles/.bin/llm-worker.sh は引数なしで実行すると usage を表示して終了コード 2 を返す』。実行して確認してよい」
Expected: verdict = SURVIVED（実際にスクリプトを実行して確認した上で）

- [ ] **Step 4: コミット**

```bash
git add dotdir/.claude/agents/adversarial-verifier.md
git commit -m "feat: adversarial-verifier Agent を追加（敵対的検証専任・L2）"
```

---

### Task 7: deep-reason Workflow の作成（L3）

**Files:**
- Create: `dotdir/.claude/workflows/deep-reason.js`

**Interfaces:**
- Consumes: Task 6 の Agent タイプ `adversarial-verifier`
- Produces: named Workflow `deep-reason`（args: `{ question, perspectives?, model? }`、返り値: `{ question, survivors, final }`）

- [ ] **Step 1: Workflow スクリプトを作成する**

以下の内容で `dotdir/.claude/workflows/deep-reason.js` を作成:

```javascript
export const meta = {
  name: 'deep-reason',
  description: '難問をN視点の独立推論で解き、敵対的検証と審査で統合する（args: { question, perspectives?, model? }）',
  phases: [
    { title: 'Solve', detail: '視点別の独立推論（並列）' },
    { title: 'Verify', detail: 'adversarial-verifier による反証試行' },
    { title: 'Judge', detail: '生存解の比較・統合' },
  ],
}

const SOLUTION = {
  type: 'object',
  required: ['answer', 'reasoning', 'confidence'],
  properties: {
    answer: { type: 'string' },
    reasoning: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
}
const VERDICT = {
  type: 'object',
  required: ['verdict', 'issues'],
  properties: {
    verdict: { type: 'string', enum: ['REFUTED', 'SURVIVED'] },
    issues: { type: 'array', items: { type: 'string' } },
  },
}

// Workflow ランタイムは args を JSON 文字列で渡す場合があるため両対応にする
const A = typeof args === 'string' ? JSON.parse(args) : (args ?? {})
const question = A.question
if (!question) throw new Error('args.question に問いを渡してください')

const DEFAULT_PERSPECTIVES = [
  { key: 'principles', stance: '原理原則から考える。前提を疑い、第一原理から組み立てる' },
  { key: 'risk', stance: 'リスクと失敗モードから考える。この判断が間違うとしたらどこか、最悪ケースは何かを起点にする' },
  { key: 'pragmatist', stance: '実利と最短経路から考える。制約の中で最も費用対効果が高い現実解を探す' },
]
const perspectives = A.perspectives?.length
  ? A.perspectives.map((p, i) => ({ key: `custom${i + 1}`, stance: p }))
  : DEFAULT_PERSPECTIVES

// 検証・低予算時は args.model = 'haiku' 等で軽量化できる。省略時はセッションモデル継承
const modelOpt = A.model ? { model: A.model } : {}

const solved = await pipeline(
  perspectives,
  p => agent(`問い: ${question}

あなたの思考様式: ${p.stance}。この様式に忠実に、独立して問いに答えよ。
必要なら Read/Grep/Bash で事実を調べてよい（ファイル変更は禁止）。
出力: answer（結論）/ reasoning（根拠の要約、5行以内）/ confidence（high|medium|low）。`,
    { label: `solve:${p.key}`, phase: 'Solve', schema: SOLUTION, ...modelOpt }),
  (sol, p) => sol && agent(`役割: 敵対的検証者。次の解答を反証せよ。
問い: ${question}
解答: ${sol.answer}
根拠: ${sol.reasoning}
手順: 前提の誤り・見落とした分岐・根拠の飛躍を探す。必要なら Read/Grep/Bash で事実を裏取りする。
出力: verdict（REFUTED=結論を変えうる欠陥あり / SURVIVED=反証失敗）と issues（発見した問題。なければ空配列）。`,
    { label: `verify:${p.key}`, phase: 'Verify', schema: VERDICT, agentType: 'adversarial-verifier', ...modelOpt })
    .then(v => ({ perspective: p.key, solution: sol, verdict: v })),
)

const candidates = solved.filter(Boolean).filter(c => c.verdict)
if (!candidates.length) throw new Error('全視点の推論が失敗しました')

const survived = candidates.filter(c => c.verdict.verdict === 'SURVIVED')
const pool = survived.length ? survived : candidates // 全滅時は反証内容ごと審査に回す

const final = await agent(`役割: 審査員。次の問いに対する複数の独立解を比較し、最終解を統合せよ。
問い: ${question}

候補:
${pool.map(c => `--- 視点 ${c.perspective}（検証: ${c.verdict.verdict}${c.verdict.issues.length ? '、指摘: ' + c.verdict.issues.join(' / ') : ''}）
結論: ${c.solution.answer}
根拠: ${c.solution.reasoning}`).join('\n')}

手順: 一致点は採用。相違点は根拠の強さで裁定する。検証の指摘は最終解へ反映する。
出力: 最終解（結論 → 根拠 → 残る不確実性、の順で簡潔に）。`,
  { label: 'judge', phase: 'Judge', ...modelOpt })

log(`視点 ${perspectives.length} 件中、反証を生き残った解 ${survived.length} 件から統合`)
return { question, survivors: survived.map(c => c.perspective), final }
```

- [ ] **Step 2: 構文を検証する**

Run: `node --check dotdir/.claude/workflows/deep-reason.js && echo "syntax OK"`
Expected: `syntax OK`（Workflow スクリプトはトップレベル return を使うため --input-type=module では検査できない）

- [ ] **Step 3: 最小構成で1回実行して検証する（トークン消費を抑えるため haiku 指定）**

Workflow ツールで起動:

```
Workflow({
  name: 'deep-reason',
  args: {
    question: 'bash で「set -e と明示的な rc チェック」のどちらが並列ジョブ管理スクリプトに適するか。1段落で',
    model: 'haiku'
  }
})
```

Expected: Solve 3体 → Verify 3体（adversarial-verifier 経由）→ Judge 1体が完走し、`{ question, survivors, final }` が返る。survivors が空でも final は返る

- [ ] **Step 4: コミット**

```bash
git add dotdir/.claude/workflows/deep-reason.js
git commit -m "feat: deep-reason Workflow を追加（ベストオブN + 敵対的検証 + 審査・L3）"
```

---

### Task 8: CLAUDE.md 運用原則追記・メモリ更新・全体検証

**Files:**
- Modify: `dotdir/.claude/CLAUDE.md`（「### Intent Gate」の直後に品質階段セクションを追加）
- Modify: `/Users/kkmclab/.claude/projects/-Users-kkmclab-dotfiles/memory/MEMORY.md`
- Create: `/Users/kkmclab/.claude/projects/-Users-kkmclab-dotfiles/memory/opus-fable-parity-foundation.md`

**Interfaces:**
- Consumes: Task 1〜7 のすべての部品

- [ ] **Step 1: CLAUDE.md へ品質階段の運用原則を追記する**

`dotdir/.claude/CLAUDE.md` の「### Intent Gate（曖昧な依頼の解釈宣言）」セクションの直後に以下を挿入:

```markdown
### 品質階段（Fable 級化基盤の使い分け）

- 設計判断の分岐・確信の持てない技術判断・不可逆操作の前 → second-opinion スキル（Codex・agy 外注。Claude トークン温存）
- 重要タスク（不可逆・本番反映・論文の数値）の完了前 → adversarial-verifier Agent で反証検証
- 最重要の難問のみ → deep-reason Workflow（agent 7体分のコスト。起動前にコストを一言明示）
- 実装・調査の単体作業も Codex/agy への委譲を優先し、Claude 並列は高価値タスク限定

```

- [ ] **Step 2: メモリファイルを作成する**

以下の内容で `/Users/kkmclab/.claude/projects/-Users-kkmclab-dotfiles/memory/opus-fable-parity-foundation.md` を作成:

```markdown
---
name: opus-fable-parity-foundation
description: Opus 4.8 を Fable 級にするコスト階段型四層基盤（L0 蒸留知識/L1 外注検証/L2 敵対検証 Agent/L3 deep-reason）の構成と使い方
metadata:
  type: project
---

Opus 4.8 Fable 級化基盤（2026-07-07 構築、設計: docs/superpowers/specs/2026-07-07-opus-fable-parity-design.md）。

- L0: decision-patterns.md（判断パターン蒸留・CLAUDE.md 常駐）+ Intent Gate ルール
- L1: .bin/llm-worker.sh（Codex/agy 統一ラッパー）+ second-opinion スキル + codex 停止時レビューゲート
- L2: adversarial-verifier Agent（verdict: REFUTED|SURVIVED）
- L3: deep-reason Workflow（args: { question, perspectives?, model? }）

**Why:** 週次トークン不足のため、検証の本体を外部クォータ（ChatGPT/Google）へ外注し Claude は裁定のみ。
**How to apply:** 使い分けは CLAUDE.md の「品質階段」節。decision-patterns.md は育成型（ユーザー指摘で追記、100行上限）。関連 [[claude-env-audit-2026-07]]
```

- [ ] **Step 3: MEMORY.md へポインタを追加する**

`/Users/kkmclab/.claude/projects/-Users-kkmclab-dotfiles/memory/MEMORY.md` の末尾に追加:

```markdown
- [Opus Fable 級化基盤](opus-fable-parity-foundation.md) — 四層基盤の構成と使い分け（L0 蒸留/L1 外注/L2 敵対検証/L3 deep-reason）
```

- [ ] **Step 4: 全体検証チェックリストを実行する**

Run: `ls -la ~/.claude/decision-patterns.md ~/.claude/skills/second-opinion/SKILL.md ~/.claude/agents/adversarial-verifier.md ~/.claude/workflows/deep-reason.js && ls ~/.claude/logs/llm-worker | head -2 && grep -c "Intent Gate\|品質階段" ~/.claude/CLAUDE.md`
Expected: 4パスすべて存在（リンク解決）、llm-worker ログあり、CLAUDE.md の grep カウントが 2 以上

- [ ] **Step 5: intent-gate の実地検証（ユーザーと実施）**

新しいセッションを開き、曖昧な依頼（例:「あのレポートどうなってる？」)を投げて、解釈・前提・成功基準の宣言（または AskUserQuestion）が出ることを確認する。
Expected: 着手前に解釈宣言が出る。出ない場合は decision-patterns.md / intent-gate の文言を調整して再検証

- [ ] **Step 6: 最終コミット**

```bash
git add dotdir/.claude/CLAUDE.md
git commit -m "feat: CLAUDE.md へ品質階段（四層基盤の使い分け）を追記し基盤を完成"
```
