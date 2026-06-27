# medical-ai-compliance スキル 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 医療AI／SaMD／臨床予測モデルの論文・開発・スライド・薬事対応で、該当ガイドラインの適用判定→チェックリスト→トレーサビリティ記録生成を支援する Claude Code スキルを作る。

**Architecture:** 薄いルーター `SKILL.md` ＋ 知識ベース `references/`（5ファイル）＋ 雛形 `assets/`（3ファイル）。SKILL.md は references/assets に相対リンクで誘導するだけに留め、800行制限を大きく下回らせる。

**Tech Stack:** Markdown（SKILL.md frontmatter は YAML）。実行コードなし。検証は grep / wc / ファイル実在チェック。

## Global Constraints

- 配置は必ず `dotdir/.claude/skills/medical-ai-compliance/`（リポジトリルートの `.claude/` ではない。`.bin/link.sh` がルート `.claude` を除外し `dotdir/.claude/skills` をディレクトリごと symlink するため）。
- frontmatter は `name`（= ディレクトリ名 `medical-ai-compliance` と一致する kebab-case）と `description` を必須記載。`auto-format-hook` の無 frontmatter 形式は踏襲しない。
- 全ガイドライン記述に「正式名称・版年・一次情報URL」を併記する。
- 「未確認」事項（TRIPOD+AI 27項目の項目名完全一覧、IMDRF N12のセル定義文言、IEC 62304クラス定義条文、IMDRF Category↔薬機法クラスの対応）は推測で埋めず、一次情報リンクへ誘導し「未確認」と明記する。
- 免責（規制適合性の最終判断・法的助言ではない）と「AI生成記録は人間レビュー必須」を SKILL.md と `traceability-record.md` に含める。
- 各 references / assets ファイルは単一責務・焦点を保ち、肥大化させない。
- コミットメッセージは Conventional Commits（`feat:` 等）。Attribution なし。

---

## File Structure

| ファイル | 責務 |
|---|---|
| `SKILL.md` | ルーター：適用判定表・4ステップフロー・references/assets 誘導・安全原則 |
| `references/reporting-guidelines.md` | レイヤーA（報告GL）知識 |
| `references/regulatory-standards.md` | レイヤーB（国際規格）知識 |
| `references/japan-regulatory.md` | レイヤーC（日本制度）知識 |
| `references/international-regulatory.md` | 海外規制（FDA/EU）軽量参照 |
| `references/traceability-crosswalk.md` | 10記録 × 各GL 対応表 |
| `assets/traceability-record.md` | トレーサビリティ記録テンプレ |
| `assets/tripod-ai-checklist.md` | TRIPOD+AI チェックリスト |
| `assets/samd-risk-worksheet.md` | SaMD リスク分類ワークシート |

**ビルド順序の理由**: SKILL.md は全 references/assets への相対リンクを持つ（リンク先が実在しないと検証で落ちる）。よって references/assets を先に作り、SKILL.md を最後に作って統合検証する。

---

### Task 1: スキルディレクトリ作成 ＋ `references/reporting-guidelines.md`（レイヤーA）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/references/reporting-guidelines.md`

**Interfaces:**
- Produces: ファイルパス `references/reporting-guidelines.md`（Task 9 の SKILL.md がリンク）。レイヤーA の GL 選択早見表を提供。

**含めるセクションと確定出典**（各項目に版年・URL を必ず併記）:
- **TRIPOD+AI**（2024）— Collins GS, Moons KGM, et al. *BMJ* 2024;385:e078378。本体27項目＋抄録13項目。fairness サブグループ分析・コード/モデル寄託（open science）を重視。旧 TRIPOD(2015) は使用非推奨。公式 https://www.tripod-statement.org/tripod-ai/ ／ 原著 https://doi.org/10.1136/bmj-2023-078378 ／ EQUATOR https://resources.equator-network.org/reporting-guidelines/tripod-ai/
- **CONSORT 2025 / SPIRIT 2025** — 本体（mainline）改訂版。**2020年の CONSORT-AI / SPIRIT-AI とは別物**である旨を明記。
- **STROBE** — 観察研究の報告。
- **CONSORT-AI**（2020）— *Nat Med* 2020;26:1364–1374。CONSORT 2010 に14項目追加。AI介入RCTの報告。
- **SPIRIT-AI**（2020）— *Nat Med* 2020;26:1351–1363。SPIRIT 2013 に15項目追加。AI介入試験プロトコル。https://pmc.ncbi.nlm.nih.gov/articles/PMC7788716/
- **STARD-AI** — Sounderajah V, et al. *Nat Med* 2025;31:3283–3289。診断精度研究。https://doi.org/10.1038/s41591-025-03953-8
- **DECIDE-AI** — Vasey B, et al. *BMJ* 2022;377:e070904。AI意思決定支援の早期臨床評価。https://doi.org/10.1136/bmj-2022-070904
- **CLAIM** — Mongan J, et al. *Radiol AI* 2020;2(2):e200029。医用画像AI、42項目。https://pmc.ncbi.nlm.nih.gov/articles/PMC8017414/
- **GL選択早見表**: 研究タイプ → 適用GL（予測モデル開発/検証→TRIPOD+AI、画像AI→＋CLAIM、診断精度→STARD-AI、AI介入RCT→CONSORT-AI、試験プロトコル→SPIRIT-AI、早期臨床評価→DECIDE-AI、観察研究→STROBE）。
- 末尾に「未確認」注記: 各GLの項目名完全一覧は一次情報参照（本ファイルでは早見表と要点のみ）。

- [ ] **Step 1: ファイルを作成し、上記8GL ＋ 早見表 ＋ 未確認注記を記述**（各GLに版年・原著・URL併記）
- [ ] **Step 2: 出典の機械検証**

Run: `grep -c 'https\?://' dotdir/.claude/skills/medical-ai-compliance/references/reporting-guidelines.md`
Expected: 6 以上（主要GLの一次情報URLが入っている）

- [ ] **Step 3: CONSORT-AI と CONSORT 2025 の区別が明記されているか確認**

Run: `grep -n '別物\|mainline\|本体' dotdir/.claude/skills/medical-ai-compliance/references/reporting-guidelines.md`
Expected: 1行以上ヒット

---

### Task 2: `references/regulatory-standards.md`（レイヤーB：国際規格）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/references/regulatory-standards.md`

**Interfaces:**
- Produces: `references/regulatory-standards.md`。IMDRF SaMD 定義/分類と ISO/IEC 規格の対応を提供。`samd-risk-worksheet.md`（Task 8）と内容整合させる。

**含めるセクションと確定出典**:
- **IMDRF SaMD 定義** — N10FINAL:2013（2013-12-18）。「ハードウェア医療機器の一部でなく単体で医療目的を果たすソフトウェア」。組込みソフトは対象外。https://www.imdrf.org/documents/software-medical-device-samd-key-definitions
- **IMDRF SaMD リスク分類** — N12FINAL:2014。2軸（医療状況の重大性 Critical/Serious/Non-serious × 情報の重要性 Treat or diagnose / Drive clinical management / Inform clinical management）→ Category I〜IV。マトリクスを掲載。https://www.imdrf.org/documents/software-medical-device-possible-framework-risk-categorization-and-corresponding-considerations
  - 未確認注記: Critical/Serious/Non-serious 等の定義文言・セル文言は N12 PDF 直接抽出未了。枠組みのみ提示。
- **ISO 13485:2016** — QMS。https://www.iso.org/standard/59752.html
- **ISO 14971:2019** — リスクマネジメント（ハザード特定→評価→コントロール→監視、ベネフィット・リスク、市販後）。https://www.iso.org/standard/72704.html
- **IEC 62304:2006+AMD1:2015** — ソフトウェアライフサイクル。安全クラスA/B/C（A=傷害なし／B=非重篤傷害可能性／C=死亡・重篤傷害可能性）。Class C は詳細設計・単体テスト・双方向トレーサビリティ必須。https://webstore.iec.ch/en/publication/22794
  - 未確認注記: クラス定義の標準条文は二次情報。番号・版年は確認済み。
- **IEC 82304-1:2016** — ヘルスソフト製品の安全要求。https://webstore.iec.ch/en/publication/26120
- **ISO/IEC 42001:2023** — AIマネジメントシステム（AIMS）。AIリスクアセスメント・学習データガバナンス・説明可能性・性能計測。https://www.iso.org/standard/42001

- [ ] **Step 1: 6規格＋IMDRF定義/分類マトリクスを記述**（版年・URL併記、未確認注記を含む）
- [ ] **Step 2: 版年の機械検証**

Run: `grep -oE '(ISO|IEC)[^0-9]*[0-9]{4,5}(:[0-9]{4})?' dotdir/.claude/skills/medical-ai-compliance/references/regulatory-standards.md`
Expected: ISO 13485:2016 / ISO 14971:2019 / IEC 62304 / IEC 82304-1:2016 / ISO/IEC 42001:2023 が現れる

- [ ] **Step 3: IMDRFマトリクス（Category I〜IV）が表で入っているか確認**

Run: `grep -n 'Category\|IV\|Critical' dotdir/.claude/skills/medical-ai-compliance/references/regulatory-standards.md`
Expected: 複数行ヒット

---

### Task 3: `references/japan-regulatory.md`（レイヤーC：日本制度）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/references/japan-regulatory.md`

**Interfaces:**
- Produces: `references/japan-regulatory.md`。薬機法クラス分類・PMDA経路・3省2GL・IDATEN を提供。

**含めるセクションと確定出典**:
- **3省2ガイドライン**:
  - 厚労省「医療情報システムの安全管理に関するガイドライン」第6.0版（令和5年=2023年5月）。対象=医療機関等。https://www.mhlw.go.jp/stf/shingi/0000516275_00006.html
  - 経産省・総務省「医療情報を取り扱う情報システム・サービスの提供事業者における安全管理ガイドライン」第2.0版（令和2年制定、令和7年=2025年3月28日改定）。対象=IT/クラウド事業者。https://www.meti.go.jp/policy/mono_info_service/healthcare/teikyoujigyousyagl.html
  - 役割分担（医療機関側 vs 事業者側）を明記。未確認注記: 厚労省第6.1版は草案の存在のみ。
- **薬機法・プログラム医療機器（SaMD）**: 2014年施行改正で単体プログラムが医療機器規制対象。クラスI〜IV（I=届出、II/III=認証基準あれば登録認証機関認証・なければ大臣承認、IV=大臣承認必須）。PMDAが審査・QMS適合性調査。https://www.pmda.go.jp/review-services/drug-reviews/about-reviews/devices/0048.html
- **DASH for SaMD**（2020年11月、厚労省）: SaMD総合相談窓口、審査体制強化。https://www.pmda.go.jp/review-services/f2f-pre/strategies/0011.html
- **IDATEN（変更計画確認手続制度）**: 市販後の継続的変更（追加学習・RWD改善等）の変更計画を事前承認、計画内変更は軽微変更届出。PACMP 相当。https://www.pmda.go.jp/review-services/drug-reviews/about-reviews/devices/0039.html
  - 未確認注記: IDATEN 英語頭字語の公式定義は未確認（韋駄天由来は確認）。

- [ ] **Step 1: 3省2GL・薬機法クラス・PMDA経路・DASH・IDATEN を記述**（版年・URL併記）
- [ ] **Step 2: 一次情報URL（mhlw/meti/pmda）の存在検証**

Run: `grep -cE 'mhlw\.go\.jp|meti\.go\.jp|pmda\.go\.jp' dotdir/.claude/skills/medical-ai-compliance/references/japan-regulatory.md`
Expected: 4 以上

- [ ] **Step 3: 薬機法クラスI〜IVの記述確認**

Run: `grep -n 'クラスI\|クラスIV\|届出\|承認' dotdir/.claude/skills/medical-ai-compliance/references/japan-regulatory.md`
Expected: 複数行ヒット

---

### Task 4: `references/international-regulatory.md`（海外規制：軽量参照）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/references/international-regulatory.md`

**Interfaces:**
- Produces: `references/international-regulatory.md`。FDA/EU の要点と一次情報リンクのみ（深いチェックリストは作らない）。

**実装前に必須の追加調査**（self-review で特定した未調査領域）: FDA GMLP / PCCP、EU AI Act、EU MDR の一次情報を取得してから記述する。一次情報が確認できない項目は「未確認・要一次情報確認」と明記し、推測で書かない。

**含めるセクション（一次情報確認後に確定）**:
- **FDA GMLP**（Good Machine Learning Practice、FDA/Health Canada/MHRA 共同10原則）— 一次情報URLを取得して併記。
- **FDA PCCP**（Predetermined Change Control Plan、市販後のモデル変更計画。日本の IDATEN に相当する位置づけ）— 一次情報URL併記。`japan-regulatory.md` の IDATEN とクロスリンク。
- **EU AI Act**（高リスクAIシステム規制）— 一次情報URL併記。
- **EU MDR**（Medical Device Regulation 2017/745）— 一次情報URL併記。
- 冒頭に「本ファイルは軽量参照。詳細・最新は各一次情報を確認」と明記。

- [ ] **Step 1: FDA GMLP/PCCP・EU AI Act・EU MDR の一次情報を WebSearch/WebFetch で確認**（確認できた URL のみ採用）
- [ ] **Step 2: 4制度の要点＋一次情報URL＋軽量参照の断り書きを記述**（未確認項目は明記）
- [ ] **Step 3: 一次情報URLの存在検証**

Run: `grep -cE 'fda\.gov|europa\.eu' dotdir/.claude/skills/medical-ai-compliance/references/international-regulatory.md`
Expected: 2 以上（確認できた一次情報URLが入っている。確認不可なら未確認注記でフォールバック）

---

### Task 5: `references/traceability-crosswalk.md`（横断：10記録 × 各GL対応表）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/references/traceability-crosswalk.md`

**Interfaces:**
- Consumes: Task 1〜4 の GL名称（表記を一致させる）。
- Produces: `references/traceability-crosswalk.md`。`traceability-record.md`（Task 6）の各記入欄が参照する「記録↔GL」対応の根拠表。

**含める対応表**（10記録 × 主要GL。調査で確定済み）:
| 記録 | 内容 | 主な要求GL |
|---|---|---|
| ①データ来歴 | 収集元・期間・集団・適格/除外・前処理・アノテーション | TRIPOD+AI, CLAIM, STARD-AI, ISO 14971, ISO/IEC 42001 |
| ②バリデーション | 内部/外部検証の設計・結果・独立性 | TRIPOD+AI, STARD-AI, IEC 62304, PMDA臨床評価 |
| ③リスク管理ファイル | ハザード・リスク評価・コントロール・残留リスク・分類根拠 | ISO 14971, IEC 62304, IMDRF N12 |
| ④変更管理 | 再学習方針・変更計画・影響評価・版管理 | IDATEN/PCCP, IEC 62304, ISO 13485, TRIPOD+AI |
| ⑤トレーサビリティ | 要求→設計→実装→テストの双方向・再現用コード/環境寄託 | IEC 62304, ISO 13485, TRIPOD+AI |
| ⑥公平性・バイアス | サブグループ別性能・データ偏り・事前指定分析 | TRIPOD+AI, STARD-AI, DECIDE-AI, ISO/IEC 42001 |
| ⑦QMS/AIガバナンス | 品質体制・AIMS運用・役割責任 | ISO 13485, ISO/IEC 42001 |
| ⑧セキュリティ/個人情報 | アクセス制御・監査ログ・委託先管理 | 3省2GL, ISO/IEC 42001 |
| ⑨意図する使用/性能仕様 | intended use・対象患者・性能目標・受入基準 | IMDRF SaMD, IEC 82304-1, ISO 14971, 報告GL各種 |
| ⑩市販後監視 | 実使用性能モニタリング・インシデント・是正 | ISO 14971, IEC 82304-1, PMDA/IDATEN |

- 「論文化と規制の交差点」（④変更管理・⑥公平性が TRIPOD+AI と IDATEN/ISO42001 双方で問われる）を強調する解説を添える。

- [ ] **Step 1: 上記10記録×GL対応表＋交差点解説を記述**
- [ ] **Step 2: 10記録すべてが揃っているか検証**

Run: `grep -cE '^\| ?[①-⑩]' dotdir/.claude/skills/medical-ai-compliance/references/traceability-crosswalk.md`
Expected: 10

- [ ] **Step 3: GL表記が Task 1〜3 と一致しているか目視確認**（TRIPOD+AI / ISO 14971 / IEC 62304 等の表記ゆれがないこと）

---

### Task 6: `assets/traceability-record.md`（トレーサビリティ記録テンプレ）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/assets/traceability-record.md`

**Interfaces:**
- Consumes: `traceability-crosswalk.md`（Task 5）の10記録区分。
- Produces: ユーザーが作業ディレクトリにコピーして埋めるテンプレ。論文「方法」と技術文書を兼ねる。

**含める構造**:
- 冒頭ヘッダ: プロジェクト名／対象（intended use）／SaMD該当性／適用GL一覧／記入者／**人間レビュー欄（レビュー者・日付・承認）**。
- 10記録区分それぞれに「記入欄＋満たすGL＋記入のヒント」。各欄は空欄テンプレ（プレースホルダではなく記入指示）。
- 末尾に免責: 「本記録は AI 支援で生成され得る。薬事・監査の証跡として用いる前に有資格者の人間レビューが必須」。

- [ ] **Step 1: 10区分の記入テンプレ＋人間レビュー欄＋免責を記述**
- [ ] **Step 2: 10区分と人間レビュー欄・免責の存在検証**

Run: `grep -cE '①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩' dotdir/.claude/skills/medical-ai-compliance/assets/traceability-record.md; grep -n '人間レビュー\|免責' dotdir/.claude/skills/medical-ai-compliance/assets/traceability-record.md`
Expected: 10区分ヒット ＋ 人間レビュー・免責が各1行以上

---

### Task 7: `assets/tripod-ai-checklist.md`（TRIPOD+AI チェックリスト）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/assets/tripod-ai-checklist.md`

**Interfaces:**
- Consumes: `reporting-guidelines.md`（Task 1）の TRIPOD+AI 出典。
- Produces: チェックボックス形式の準拠確認雛形。

**含める構造**:
- TRIPOD+AI の構成（Title / Abstract / Introduction / Methods / Results / Discussion / Other information）を見出しに、各セクションに `- [ ]` チェック欄。
- 本体27項目＋抄録13項目という**総数**を明記。ただし**項目名の正確な完全一覧は未確認**のため、一次情報（https://www.tripod-statement.org/tripod-ai/ ／ BMJ 2024;385:e078378）へのリンクを冒頭に置き「正式項目は原著チェックリストPDFで確認」と指示。
- TRIPOD+AI 特有の強調点（fairness サブグループ分析・コード/モデル/データ可用性）を専用チェック欄として明示（これは確認済み事実）。

- [ ] **Step 1: セクション別チェック欄＋総数＋一次情報リンク＋fairness/open science欄を記述**
- [ ] **Step 2: 未確認の扱いとチェックボックスの検証**

Run: `grep -c '\- \[ \]' dotdir/.claude/skills/medical-ai-compliance/assets/tripod-ai-checklist.md; grep -n 'tripod-statement.org\|e078378\|未確認\|原著' dotdir/.claude/skills/medical-ai-compliance/assets/tripod-ai-checklist.md`
Expected: チェックボックス複数 ＋ 一次情報リンク/未確認注記がヒット

---

### Task 8: `assets/samd-risk-worksheet.md`（SaMD リスク分類ワークシート）

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/assets/samd-risk-worksheet.md`

**Interfaces:**
- Consumes: `regulatory-standards.md`（Task 2）の IMDRF N12 マトリクス。
- Produces: 2軸判定ワークシート。

**含める構造**（IMDRF N12、確定済み枠組み）:
- ステップ1: 医療状況の重大性を選択（Critical / Serious / Non-serious）。
- ステップ2: 情報の重要性を選択（Treat or diagnose / Drive clinical management / Inform clinical management）。
- ステップ3: マトリクスで Category I〜IV を判定:
  | 情報の重要性 ↓ ／ 医療状況 → | Critical | Serious | Non-serious |
  |---|---|---|---|
  | Treat or diagnose | IV | III | II |
  | Drive clinical management | III | II | I |
  | Inform clinical management | II | I | I |
- **薬機法クラス（I〜IV）との対応は単純な1対1ではない**旨を明記し、対応表は作らず「薬機法上の分類は PMDA 相談・該当性確認で確定する」と誘導（未確認領域を推測で埋めない）。
- 判定結果に応じた次アクション（ISO 14971リスク管理・IEC 62304安全クラス検討等）への参照。

- [ ] **Step 1: 2軸選択＋マトリクス＋薬機法非1対1注記＋次アクションを記述**
- [ ] **Step 2: マトリクスと注記の検証**

Run: `grep -n 'Critical\|Category\|薬機法\|1対1\|PMDA' dotdir/.claude/skills/medical-ai-compliance/assets/samd-risk-worksheet.md`
Expected: マトリクス語＋薬機法非1対1注記がヒット

---

### Task 9: `SKILL.md`（ルーター）＋ 統合検証 ＋ コミット

**Files:**
- Create: `dotdir/.claude/skills/medical-ai-compliance/SKILL.md`

**Interfaces:**
- Consumes: Task 1〜8 の全ファイルパス（相対リンクで参照）。
- Produces: スキル本体。frontmatter（name=`medical-ai-compliance`）＋ description（トリガー付き）。

**SKILL.md の構成**:
- frontmatter:
  ```yaml
  ---
  name: medical-ai-compliance
  description: 医療AI／SaMD／臨床予測モデルの論文執筆・AI開発・スライド/資料作成・薬事(PMDA)対応で、該当ガイドライン（TRIPOD+AI / IMDRF SaMD / ISO 14971 / IEC 62304 / ISO/IEC 42001 / 3省2ガイドライン / PMDA・IDATEN 等）の適用判定・準拠チェックリスト・トレーサビリティ記録生成を支援する。トリガー：「医療AI 論文」「SaMD」「TRIPOD」「PMDA」「薬機法」「医療機器ソフト」「3省ガイドライン」「ISO 14971」「臨床予測モデル」「medical AI compliance」「SaMD risk classification」。Do NOT trigger for 純粋な非医療領域のML・医療目的を持たないデータ分析。
  ---
  ```
- `# Medical AI Compliance` タイトル。
- `## 適用判定`: 作業種別（論文/開発/スライド・資料/規制相談）× 型（予測モデル/診断精度/RCT/画像AI/SaMD該当性）の判定表。
- `## 4ステップフロー`: ①コンテキスト判定 ②該当GL特定 ③チェックリスト提示 ④記録生成。各ステップから references/assets への相対リンク。
- `## 安全原則`: 出典必須・未確認は推測しない・免責・人間レビュー必須。
- `## References`: 全 references/assets への相対リンク一覧。

- [ ] **Step 1: SKILL.md を記述**（frontmatter ＋ 判定表 ＋ 4フロー ＋ 安全原則 ＋ References リンク）
- [ ] **Step 2: frontmatter の name がディレクトリ名と一致するか検証**

Run: `grep -A1 '^name:' dotdir/.claude/skills/medical-ai-compliance/SKILL.md | head -1`
Expected: `name: medical-ai-compliance`

- [ ] **Step 3: SKILL.md の相対リンク先がすべて実在するか検証**

Run:
```bash
cd dotdir/.claude/skills/medical-ai-compliance && \
for f in $(grep -oE '\(\.?/?(references|assets)/[a-z0-9-]+\.md\)' SKILL.md | tr -d '()'); do \
  [ -f "$f" ] && echo "OK $f" || echo "MISSING $f"; done
```
Expected: 全行 `OK`、`MISSING` なし

- [ ] **Step 4: 全ファイルの行数が 800 未満であることを検証**

Run: `find dotdir/.claude/skills/medical-ai-compliance -name '*.md' -exec wc -l {} + | awk '$1>=800{print "OVER:",$2}'`
Expected: 出力なし（OVER なし）

- [ ] **Step 5: 免責・人間レビュー注記が SKILL.md に存在するか検証**

Run: `grep -n '免責\|人間レビュー\|法的助言' dotdir/.claude/skills/medical-ai-compliance/SKILL.md`
Expected: 1行以上

- [ ] **Step 6: コミット**（スキル一式＋設計doc＋本計画をまとめて1コミット）

```bash
git add dotdir/.claude/skills/medical-ai-compliance docs/superpowers/specs/2026-06-26-medical-ai-compliance-design.md docs/superpowers/plans/2026-06-26-medical-ai-compliance.md
git commit -m "feat: add medical-ai-compliance skill (SaMD/TRIPOD+AI/ISO/PMDA guideline compliance)"
```

---

## Self-Review（計画作成後の自己点検）

**1. Spec coverage**（design doc の各セクション → 実装タスク）:
- スコープ レイヤーA/B/C → Task 1/2/3 ✓／海外軽量参照 → Task 4 ✓／クロスウォーク → Task 5 ✓
- 実チェックリスト（TRIPOD+AI, SaMDリスク）→ Task 7, 8 ✓／記録テンプレ → Task 6 ✓
- 動作フロー4ステップ → Task 9 SKILL.md ✓
- 正確性・安全性原則（出典・未確認・免責・人間レビュー）→ Global Constraints ＋ 各検証Step ＋ Task 6/9 ✓
- トリガー設計 → Task 9 frontmatter ✓
- 受け入れ基準 → 各 Task の検証Step ＋ Task 9 Step 2〜5 ✓

**2. Placeholder scan**: 各タスクに確定出典（URL・版年・原著）を記載。Task 4 のみ「実装前に追加調査」を明示（未調査領域のため。空欄放置ではなく調査指示＋未確認フォールバック）。コード的 TODO なし。

**3. Type consistency**（スキルでは「ファイルパス・GL表記」の一致）: 全 references/assets パスは File Structure 表と一致。GL表記（TRIPOD+AI / ISO 14971:2019 / IEC 62304 / IMDRF N12）はタスク間で統一。Task 5 Step 3 と Task 9 Step 3 で表記一致・リンク実在を機械検証。

ギャップなし。実装に進める。
