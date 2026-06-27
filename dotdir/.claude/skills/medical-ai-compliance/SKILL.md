---
name: medical-ai-compliance
description: 医療AI／SaMD／臨床予測モデルの論文執筆・AI開発・スライド/資料作成・薬事(PMDA)対応で、該当ガイドライン（TRIPOD+AI / IMDRF SaMD / ISO 14971 / IEC 62304 / ISO/IEC 42001 / 3省2ガイドライン / PMDA・IDATEN 等）の適用判定・準拠チェックリスト・トレーサビリティ記録生成を支援する。トリガー：「医療AI 論文」「SaMD」「TRIPOD」「PMDA」「薬機法」「医療機器ソフト」「3省ガイドライン」「ISO 14971」「臨床予測モデル」「medical AI compliance」「SaMD risk classification」。Do NOT trigger for 純粋な非医療領域のML・医療目的を持たないデータ分析。
---

# Medical AI Compliance

医療AI・SaMD・臨床予測モデルに関する論文執筆・開発・資料作成・規制対応を **4ステップ** で支援するルータースキル。適用ガイドラインの特定からトレーサビリティ記録の生成まで、references/ および assets/ への誘導を担います。

---

## 適用判定

ユーザーの作業種別と対象モデル/研究の型を照合し、必要なガイドライン層を決定します。

| 作業種別 / 型 | 臨床予測モデル | 診断精度検証 (DTA) | RCT・介入研究 | 画像AI (放射線・病理) | SaMD該当性評価 |
|---|---|---|---|---|---|
| **論文執筆** | TRIPOD+AI ✓ | TRIPOD+AI / QUADAS-2 | CONSORT-AI ✓ | TRIPOD+AI ✓ | 必要なし |
| **AI開発** | ISO/IEC 42001 / IEC 62304 | IEC 62304 | — | ISO 14971 / IEC 62304 | IMDRF SaMD N12 ✓ |
| **スライド・資料作成** | 該当GL要旨を参照 | 診断精度指標の正確な表現 | CONSORT-AI 図表基準 | 画像AI性能評価の可視化 | SaMD分類・リスク図 |
| **規制相談 (PMDA・薬事)** | 3省2GL / PMDA相談 | — | — | — | IMDRF N12 / 薬機法 / IDATEN |

凡例:
- `✓` = 最優先で参照すべきGL
- `—` = 通常は適用外（個別判断が必要な場合は Step 2 で確認）

---

## 4ステップフロー

### Step 1: コンテキスト判定

以下を確認してから進みます。

1. **作業種別** — 論文執筆 / AI開発 / スライド資料 / 規制相談
2. **モデル・研究の型** — 予測モデル / 診断精度 / RCT / 画像AI / SaMD
3. **対象地域** — 日本（PMDA主管） / 海外（FDA・EU MDR） / グローバル
4. **フェーズ** — 開発中 / 論文投稿前 / 規制申請準備 / 市販後

→ 判定結果を踏まえて Step 2 へ進みます。

---

### Step 2: 該当GL特定

対象に応じて以下の参照ファイルを開き、適用するガイドラインを特定します。

#### レイヤーA：報告・透明性ガイドライン

> 論文執筆・スライド資料の場合に最初に参照してください。

- [references/reporting-guidelines.md](references/reporting-guidelines.md) — TRIPOD+AI / CONSORT-AI / DECIDE-AI / SPIRIT-AI / STARD

#### レイヤーB：国際規格・IMDRF

> AI開発・SaMD設計・品質マネジメントに適用します。

- [references/regulatory-standards.md](references/regulatory-standards.md) — IMDRF N12 (SaMD定義・リスク分類) / ISO 14971 / IEC 62304 / ISO/IEC 42001

#### レイヤーC：日本規制（薬機法・PMDA・3省2GL・IDATEN）

> 国内の薬事対応・PMDA相談・SaMD申請に必須。

- [references/japan-regulatory.md](references/japan-regulatory.md) — 薬機法 / 3省2GL / PMDA AI GL / IDATEN（国際整合：FDA PCCP を参照）

#### 海外規制（軽量参照）

> FDA / EU MDR の概要確認、国際比較に使用します。

- [references/international-regulatory.md](references/international-regulatory.md) — FDA SaMD / FDA PCCP / EU MDR / MDR IVDR

#### GL横断トレーサビリティ

> 複数GLにまたがる記録項目の対応関係を確認します。

- [references/traceability-crosswalk.md](references/traceability-crosswalk.md) — 10記録 × GLクロスウォーク表

---

### Step 3: チェックリスト提示

特定したGLに対応するチェックリスト / ワークシートを提示します。

#### TRIPOD+AI 準拠チェックリスト

論文・報告書の透明性要件を項目別に確認します。

- [assets/tripod-ai-checklist.md](assets/tripod-ai-checklist.md) — TRIPOD+AI 全項目チェックリスト（予測モデル・診断精度共通）

#### SaMD リスク分類ワークシート

IMDRF N12 に基づくSaMD該当性・リスク層の判定を行います。

- [assets/samd-risk-worksheet.md](assets/samd-risk-worksheet.md) — SaMDリスク分類ワークシート（対象疾患状態 × 医療介入レベル）

---

### Step 4: 記録生成

チェックリスト結果をもとにトレーサビリティ記録を生成します。

- [assets/traceability-record.md](assets/traceability-record.md) — トレーサビリティ記録テンプレート（10記録項目）
- [references/traceability-crosswalk.md](references/traceability-crosswalk.md) — 記録×GL対応表（記録漏れ確認に使用）

生成手順:
1. `assets/traceability-record.md` のテンプレートを開く
2. `references/traceability-crosswalk.md` で各記録が必要なGL層を確認
3. 各フィールドに Step 3 チェックリストの結果を転記
4. 未記入フィールドを洗い出し、補完情報をユーザーに確認

> **AI生成記録は人間レビュー必須です。** 生成された記録を最終化する前に、担当者（研究責任者・薬事担当者等）が内容を確認・署名してください。

---

## 安全原則

このスキルを使用する際は以下の原則を厳守します。

### 出典の明示

- 参照するガイドライン・規格・通知は **版年・番号** を明示する（例：ISO 14971:2019、IMDRF N12 最終版 2021年）
- 未確認の情報を事実として述べない。情報が不確かな場合は「要確認」と明示する

### 推測の禁止

- ガイドラインの要件について不確かな場合は、当該 references/ ファイルを確認するよう案内する
- 規制の解釈・申請戦略については憶測を述べず、一次情報（PMDA通知・官報等）の参照を促す

### 免責

**本スキルはガイドライン準拠の支援ツールであり、規制適合性の最終判断・法的助言を提供するものではありません。** 規制申請・承認判断・法律解釈については、薬事専門家・法務担当者・規制当局への相談を必ず行ってください。

### 人間レビューの義務

- AI が生成したチェックリスト記録・トレーサビリティドキュメントは、必ず担当者による人間レビューを経てから正式文書として使用してください
- 特に SaMD リスク分類結果・PMDA相談資料・治験申請書類は、専門家の確認なしに提出しないでください

---

## References

このスキルが参照するファイルの一覧です。

### references/（ガイドライン参照資料）

| ファイル | 内容 |
|---|---|
| [references/reporting-guidelines.md](references/reporting-guidelines.md) | レイヤーA：TRIPOD+AI / CONSORT-AI / DECIDE-AI / SPIRIT-AI / STARD |
| [references/regulatory-standards.md](references/regulatory-standards.md) | レイヤーB：IMDRF N12 / ISO 14971 / IEC 62304 / ISO/IEC 42001 |
| [references/japan-regulatory.md](references/japan-regulatory.md) | レイヤーC：薬機法 / 3省2GL / PMDA AI GL / IDATEN（FDA PCCP参照） |
| [references/international-regulatory.md](references/international-regulatory.md) | 海外規制：FDA SaMD / FDA PCCP / EU MDR・IVDR（軽量参照） |
| [references/traceability-crosswalk.md](references/traceability-crosswalk.md) | 10記録 × GL対応クロスウォーク表 |

### assets/（実用テンプレート・チェックリスト）

| ファイル | 内容 |
|---|---|
| [assets/traceability-record.md](assets/traceability-record.md) | トレーサビリティ記録テンプレート（記録生成用） |
| [assets/tripod-ai-checklist.md](assets/tripod-ai-checklist.md) | TRIPOD+AI 全項目チェックリスト |
| [assets/samd-risk-worksheet.md](assets/samd-risk-worksheet.md) | SaMD リスク分類ワークシート（IMDRF N12準拠） |
