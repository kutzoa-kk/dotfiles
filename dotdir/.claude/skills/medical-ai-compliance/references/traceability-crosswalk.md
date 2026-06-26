# 残すべき10記録 × ガイドライン対応表（トレーサビリティ・クロスウォーク）

> **役割**: 医療 AI 研究において保存すべき10カテゴリの記録と、それぞれを要求する報告 GL・国際規格・日本制度の対応マトリクス。  
> `assets/traceability-record.md` の各記入欄はこの表を「記録↔GL」対応の根拠として参照する。

---

## 対応マトリクス（10記録 × 主な要求 GL）

| 記録番号 | 記録カテゴリ | 記録の主な内容 | 報告 GL | 国際規格 | 日本制度 |
|---|---|---|---|---|---|
| ①データ来歴 | データセット来歴・前処理 | 収集元・期間・対象集団・適格/除外基準・前処理手順・アノテーション方法 | TRIPOD+AI, CLAIM, STARD-AI | ISO 14971, ISO/IEC 42001 | 3省2GL（データ管理） |
| ②バリデーション | 検証設計・実施記録 | 内部検証・外部検証の設計根拠・実施結果・検証者の独立性 | TRIPOD+AI, STARD-AI | IEC 62304, ISO 14971 | PMDA 臨床評価 |
| ③リスク管理ファイル | ハザード・リスク評価 | ハザード識別・リスク評価・コントロール措置・残留リスク根拠・SaMD 分類根拠 | — | ISO 14971, IEC 62304, IMDRF N12 | PMDA, 3省2GL |
| ④変更管理 | 再学習・変更計画 | 再学習方針・変更計画書・影響評価・版管理ログ | TRIPOD+AI | IEC 62304, ISO 13485 | IDATEN/PCCP |
| ⑤トレーサビリティ | 要件〜テスト双方向記録 | 要求→設計→実装→テストの双方向マトリクス・再現用コード/環境寄託 | TRIPOD+AI | IEC 62304, ISO 13485 | PMDA（変更管理記録） |
| ⑥公平性・バイアス | サブグループ別性能 | サブグループ別性能指標・データ偏り評価・事前指定分析計画 | TRIPOD+AI, STARD-AI, DECIDE-AI | ISO/IEC 42001 | 3省2GL（バイアス評価） |
| ⑦QMS/AIガバナンス | 品質体制・AIMS 運用 | 品質管理体制・AI マネジメントシステム（AIMS）運用記録・役割責任マトリクス | — | ISO 13485, ISO/IEC 42001 | 3省2GL（QMS） |
| ⑧セキュリティ/個人情報 | アクセス制御・監査ログ | アクセス制御ポリシー・監査ログ・委託先管理・匿名化記録 | — | ISO/IEC 42001 | 3省2GL（個人情報保護） |
| ⑨意図する使用/性能仕様 | Intended use・受入基準 | intended use 文書・対象患者定義・性能目標・受入基準 | TRIPOD+AI, STARD-AI, CONSORT-AI, DECIDE-AI | IMDRF N12, IEC 82304-1, ISO 14971 | PMDA, 薬機法（承認申請） |
| ⑩市販後監視 | 実使用性能モニタリング | 実使用性能モニタリング計画・インシデント報告記録・是正措置（CAPA） | DECIDE-AI | ISO 14971, IEC 82304-1 | PMDA/IDATEN（市販後変更） |

---

## GL 凡例

### 報告ガイドライン（論文化レイヤー）

| 略称 | 正式名称 | 対象研究 |
|---|---|---|
| TRIPOD+AI | Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis + Artificial Intelligence (2024) | 予測モデル開発・検証（AI/ML） |
| STARD-AI | Standards for Reporting Diagnostic Accuracy Studies – Artificial Intelligence (2025) | 診断精度研究（AI） |
| CONSORT-AI | Consolidated Standards of Reporting Trials – Artificial Intelligence (2020) | AI 介入 RCT（結果報告） |
| SPIRIT-AI | Standard Protocol Items: Recommendations for Interventional Trials – Artificial Intelligence (2020) | AI 介入試験プロトコル |
| DECIDE-AI | Developmental and Exploratory Clinical Investigation of DEcision support systems driven by Artificial Intelligence (2022) | AI 意思決定支援の早期臨床評価 |
| CLAIM | Checklist for Artificial Intelligence in Medical Imaging (2020) | 医用画像 AI（予測モデル） |

### 国際規格（規制レイヤー）

| 略称 | 規格番号 | 内容 |
|---|---|---|
| ISO 13485 | ISO 13485:2016 | 医療機器 QMS |
| ISO 14971 | ISO 14971:2019 | 医療機器リスクマネジメント |
| IEC 62304 | IEC 62304:2006+AMD1:2015 | 医療機器ソフトウェアライフサイクル |
| IEC 82304-1 | IEC 82304-1:2016 | ヘルスソフトウェア製品安全要求事項 |
| ISO/IEC 42001 | ISO/IEC 42001:2023 | AI マネジメントシステム |
| IMDRF N12 | IMDRF N12FINAL:2014 | SaMD リスク分類フレームワーク |

### 日本制度（レイヤーC）

| 略称 | 正式名称 / 内容 |
|---|---|
| 3省2GL | 厚労省・経産省・総務省が策定した AI 利活用・医療機器 AI に関する 2 本のガイドライン群 |
| 薬機法 | 医薬品、医療機器等の品質、有効性及び安全性の確保等に関する法律 |
| PMDA | 独立行政法人 医薬品医療機器総合機構（審査・相談窓口） |
| IDATEN/PCCP | 変更計画確認手続制度（IDATEN）。FDA の PCCP（Predetermined Change Control Plan）に対応する日本制度 |

---

## 論文化レイヤーと規制レイヤーの交差点

医療 AI 研究においては「論文発表」と「薬事承認」が独立したプロセスに見えるが、実際にはいくつかの記録が**両レイヤーで同時に問われる**。この交差点を意識した記録設計が効率的なエビデンス構築につながる。

### ④変更管理：TRIPOD+AI × IDATEN/PCCP

```
論文化レイヤー（TRIPOD+AI）
  └── 項目 8b: 再学習・アップデートの方針を報告すること
       ↕ 同一記録を兼用
規制レイヤー（IDATEN/PCCP）
  └── 変更計画確認手続：再学習・改良の計画を事前に PMDA へ確認
```

**実践的含意**: 再学習方針文書（変更計画書）を TRIPOD+AI の報告要件に合わせて記述しておくと、IDATEN 申請の基礎資料として転用できる。論文著者と薬事担当が同一ドキュメントを参照することで、主張の一貫性も担保される。

### ⑥公平性・バイアス：TRIPOD+AI × ISO/IEC 42001

```
論文化レイヤー（TRIPOD+AI + STARD-AI + DECIDE-AI）
  └── サブグループ別性能・データ偏り・事前指定分析の報告
       ↕ 同一記録を兼用
規制レイヤー（ISO/IEC 42001）
  └── AI マネジメントシステム: 公平性・偏り対策の文書化と継続的モニタリング
```

**実践的含意**: サブグループ別性能解析の結果と事前指定分析計画を統合した「バイアス評価記録」を1つ作成すれば、論文付録（報告 GL 要件）と ISO/IEC 42001 の AIMS 記録（規制要件）の両方を満たす資料として機能する。

### ⑨意図する使用：報告 GL 各種 × IMDRF N12 + 薬機法

```
論文化レイヤー（TRIPOD+AI・STARD-AI・CONSORT-AI・DECIDE-AI）
  └── 対象集団・clinical use case の明確な記述
       ↕ 共通の「intended use 文書」を起点
規制レイヤー（IMDRF N12・IEC 82304-1・薬機法承認申請）
  └── SaMD 分類根拠・承認申請における使用目的の記載
```

**実践的含意**: 論文の Methods 冒頭に記述する「対象患者・想定臨床場面・使用目的」をそのまま IMDRF N12 の intended use 記述フォーマットに合わせて書くと、薬事申請時の使用目的記載と整合した記録を最初から確保できる。

---

## 記録設計の優先度マトリクス

| 優先度 | 記録 | 理由 |
|---|---|---|
| 必須（研究開始前に設計） | ①データ来歴・②バリデーション・⑨意図する使用 | 遡及的確認が困難。研究設計段階で固定が必要 |
| 必須（開発プロセス中に維持） | ③リスク管理ファイル・⑤トレーサビリティ・⑦QMS | 工程に紐付くため随時更新が前提 |
| 計画ベースで先行作成 | ④変更管理・⑥公平性・バイアス | 事前指定（pre-specification）が報告 GL・規制双方で評価される |
| 市販後フェーズで継続 | ⑧セキュリティ・⑩市販後監視 | 承認後も継続的に更新・報告が求められる |

---

## 関連ファイル

| ファイル | 内容 |
|---|---|
| `references/reporting-guidelines.md` | 報告 GL（TRIPOD+AI・STARD-AI 等）の詳細 |
| `references/regulatory-standards.md` | 国際規格（ISO 14971・IEC 62304 等）の詳細 |
| `references/japan-regulatory.md` | 日本制度（3省2GL・PMDA・IDATEN）の詳細 |
| `references/international-regulatory.md` | FDA・EMA 等の海外規制詳細 |
| `assets/traceability-record.md` | 本クロスウォークを根拠とする記録テンプレート（各欄に GL 根拠を記載） |
