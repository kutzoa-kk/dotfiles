# 設計: `medical-ai-compliance` スキル

- **日付**: 2026-06-26
- **対象**: Claude Code ユーザースキル（`dotdir/.claude/skills/medical-ai-compliance/`）
- **ステータス**: 設計合意済み（実装計画待ち）

## 1. 目的

医療AI／SaMD（Software as a Medical Device）／臨床予測モデルに関わる作業——**論文執筆・AI開発・スライド/資料作成・薬事規制対応**——の際に、該当するガイドライン・規格への準拠を支援する。中核的価値は、**論文化レイヤー（報告ガイドライン）と規制レイヤー（薬事・安全規格）を橋渡し**し、「後々の論文化・薬事申請・監査で再利用できる記録」を作業の最初期から残させること。

### 背景（調査で確定した事実）

- ユーザー参照記事（佐藤俊太朗「医学研究の報告ガイドライン〜CONSORT2025とTRIPOD+AI」, note.com/suntarooo3/n/n691c47974156）は **論文の報告ガイドライン**（TRIPOD+AI / CONSORT 2025 / STROBE / SPIRIT 2025）を扱い、規制への言及はない。
- ユーザー提示キーワード（SaMD / ISO / 3省ガイドライン / PMDA）は **医療機器ソフトの開発・薬事規制**のレイヤー。
- 両レイヤーは目的が異なるが、「残すべき記録」（データ来歴・バリデーション・リスク管理・公平性評価・変更管理・トレーサビリティ）で大きく交差する。**この交差点がスキルの本質的価値**。
- 重要な区別: 記事の「CONSORT 2025 / SPIRIT 2025」は本体（mainline）の改訂版であり、2020年の AI 拡張版（CONSORT-AI / SPIRIT-AI）とは**別物**。混同しないこと。

## 2. スコープ

### 含む

- 3レイヤーのガイドライン知識ベース:
  - **A. 報告ガイドライン**: TRIPOD+AI（2024）, CONSORT 2025, SPIRIT 2025, STROBE, CONSORT-AI/SPIRIT-AI（2020）, STARD-AI, DECIDE-AI, CLAIM
  - **B. 開発・規制の国際規格**: IMDRF SaMD（N10定義 / N12リスク分類）, ISO 13485:2016, ISO 14971:2019, IEC 62304:2006+AMD1:2015, IEC 82304-1:2016, ISO/IEC 42001:2023
  - **C. 日本固有の制度**: 3省2ガイドライン（厚労省 第6.0版/2023, 経産省・総務省 第2.0版/2025改定）, 薬機法・PMDA, DASH for SaMD, IDATEN（PACMP）
- 海外規制の**軽量参照**（要点＋一次情報リンクのみ、深いチェックリストは作らない）: FDA GMLP / PCCP, EU AI Act, EU MDR
- 適用判定 → 該当GL特定 → 準拠チェックリスト提示 → トレーサビリティ記録テンプレート生成、の一連フロー
- 実装する実チェックリスト雛形: **TRIPOD+AI**, **SaMDリスク分類（IMDRF 2軸）**
- 横断的な「残すべき10記録 × 各GL対応表」（クロスウォーク）

### 含まない（YAGNI / スコープ境界）

- 純粋な非医療領域の機械学習（医療目的を持たないモデル）
- チェックリスト判定の自動化スクリプト（医療GLは人間判断を要し、誤った自動判定は危険）
- 全ガイドラインの逐条チェックリスト（保守不能。実装は2つ、他は参照ナビゲーション）
- 法的助言・規制適合性の最終判断（スキルは支援ナビゲーションに留まる）

## 3. アーキテクチャ

**採用案: ルーター + references + assets**（既存最頻パターン: custom-lint-rules, html-report-generator に準拠）。

```
dotdir/.claude/skills/medical-ai-compliance/
├── SKILL.md                       # 薄いルーター：適用判定 → 該当GL特定 → フロー誘導
├── references/
│   ├── reporting-guidelines.md    # レイヤーA
│   ├── regulatory-standards.md    # レイヤーB
│   ├── japan-regulatory.md        # レイヤーC
│   ├── international-regulatory.md # 海外規制の軽量参照（FDA/EU）
│   └── traceability-crosswalk.md  # 横断：10記録 × 各GL対応表
└── assets/
    ├── traceability-record.md     # トレーサビリティ記録テンプレ（論文「方法」兼 技術文書）
    ├── tripod-ai-checklist.md     # TRIPOD+AI 準拠チェックリスト
    └── samd-risk-worksheet.md     # SaMDリスク分類（IMDRF 2軸）判定ワークシート
```

理由: 医療規制知識は量が多く改訂もされるため、SKILL.md（手順）と references（知識）を分離しないと腐敗しやすい。記録テンプレートは「コピーして埋める」性質なので assets が適切。SKILL.md は 800 行制限を大きく下回る薄さを保つ。

## 4. 動作フロー（SKILL.md の核）

```
①コンテキスト判定 → ②該当GL特定 → ③チェックリスト提示 → ④記録テンプレ生成/更新
```

1. **コンテキスト判定**: 作業種別（論文／開発／スライド・資料／規制相談）× 研究・製品の型（予測モデル／診断精度／RCT／画像AI／SaMD該当性）を切り分ける。判定に必要な最小限の質問のみ行う。
2. **該当GL特定**: 判定結果から適用GLを提示。
   - 例: 予測モデルの論文 → TRIPOD+AI（画像なら CLAIM 追加）
   - 例: 診断支援を市販化 → IMDRF分類 + ISO 14971 + IEC 62304 + PMDA経路 +（再学習あれば）IDATEN/PCCP
3. **チェックリスト提示**: 該当GLの必須項目を提示。スライド/資料モードでも「性能指標・検証法・公平性・限界・intended use」が落ちないか確認。規制提出資料モードでは「リスク分類根拠・検証エビデンスの提示順」を支援。
4. **記録生成/更新**: `assets/traceability-record.md` を作業ディレクトリに生成。これが論文「方法」セクションと技術文書（リスク管理ファイル等）を**兼ねる**粒度で記録を蓄積する——「後々の参考に」というユーザー要望の核心。

## 5. 各ファイルの責務

| ファイル | 責務 | 主な内容 |
|---|---|---|
| `SKILL.md` | ルーティングと安全原則 | 適用判定表、4ステップフロー、references/assets への誘導、免責、人間レビュー必須注記 |
| `reporting-guidelines.md` | レイヤーA知識 | 各GLの正式名称・発行主体・原著・適用場面・主要要求・一次情報URL・版年。GL選択早見表 |
| `regulatory-standards.md` | レイヤーB知識 | IMDRF SaMD定義/分類マトリクス、ISO/IEC各規格の規定内容・版年・一次情報URL |
| `japan-regulatory.md` | レイヤーC知識 | 3省2GL、薬機法クラス分類、PMDA審査経路、DASH、IDATEN/PACMP |
| `international-regulatory.md` | 海外規制の軽量参照 | FDA GMLP/PCCP、EU AI Act、EU MDR の要点＋一次情報URL（チェックリストは作らない） |
| `traceability-crosswalk.md` | 横断対応表 | 残すべき10記録（①データ来歴〜⑩市販後監視）× 各GLの対応マトリクス |
| `traceability-record.md` | 記録テンプレ | 10記録項目の記入欄。論文方法＋技術文書を兼ねる。各欄に「どのGLを満たすか」を併記 |
| `tripod-ai-checklist.md` | 実チェックリスト | TRIPOD+AI 本体27項目＋抄録13項目の構造（項目名の正確一覧は一次情報リンクへ誘導、未確認は明記） |
| `samd-risk-worksheet.md` | 実ワークシート | IMDRF 2軸（医療状況の重大性 × 情報の重要性）→ Category I〜IV 判定。日本クラス分類との対応 |

## 6. 正確性・安全性の原則（医療規制ゆえ必須）

1. **出典と版年を全記述に併記**（例: ISO 14971:2019、厚労省GL 第6.0版/2023、TRIPOD+AI=BMJ 2024;385:e078378）。
2. **「未確認」は推測で埋めない**: TRIPOD+AI 27項目の完全一覧、IMDRF N12のセル文言、IEC 62304クラス定義条文などは一次情報リンクへ誘導し、推測補完しない。
3. **免責の明示**: 本スキルは準拠を支援するナビゲーションであり、最終的な規制適合性判断・法的助言ではない。
4. **AI生成記録には人間レビュー必須**の注記（薬事・監査の証跡になるため）。
5. **一次情報優先**: EQUATOR Network, IMDRF, ISO, IEC, PMDA, 厚労省/経産省/総務省の公式を出典とする。

## 7. トリガー設計（description）

- **起動条件**: 医療AI／SaMD／臨床予測モデル／医療機器ソフトの、論文執筆・開発・スライド/資料作成・薬事/PMDA相談の文脈。
- **形式**: 1文の機能説明 ＋ 日英キーワード併記の明示トリガー ＋ 否定トリガー。
- **トリガー語例**: 「医療AI 論文」「SaMD」「TRIPOD」「PMDA」「薬機法」「医療機器ソフト」「3省ガイドライン」「ISO 14971」「臨床予測モデル」「medical AI compliance」「SaMD risk classification」等。
- **否定トリガー**: 純粋な非医療領域のML、医療目的を持たないデータ分析は対象外。

## 8. 受け入れ基準

- [ ] `dotdir/.claude/skills/medical-ai-compliance/SKILL.md` が frontmatter（name=ディレクトリ名一致, description=トリガー付き）を持ち、800行制限を大きく下回る薄さである。
- [ ] references 5ファイル・assets 3ファイルが揃い、SKILL.md から相対リンクで参照される。
- [ ] 全GL記述に正式名称・版年・一次情報URLが併記されている。
- [ ] 「未確認」事項が推測で埋められておらず、一次情報リンクへ誘導されている。
- [ ] 免責・人間レビュー必須の注記が SKILL.md と記録テンプレに含まれる。
- [ ] 4ステップフローが「論文／開発／スライド／規制提出」の4モードで成立する。
- [ ] `make link` 済みの `~/.claude/skills` symlink により追加即反映される（新規ディレクトリのため初回 `make link` の要否を確認）。
