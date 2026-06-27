# Layer B: 開発・規制の国際規格

医療AI・SaMD（Software as a Medical Device）の開発・薬事対応における  
国際規格の定義・分類・要件を提供するリファレンス。

---

## 対象スコープ

このドキュメントは **レイヤーB（国際規格）のみ** を扱う。

- ✅ IMDRF SaMD 定義・リスク分類（N10・N12）
- ✅ ISO/IEC 製品安全・QMS・AI 規格（13485・14971・62304・82304-1・42001）
- ❌ 報告ガイドライン（CONSORT-AI・TRIPOD-AI 等）→ `reporting-guidelines.md`
- ❌ 日本固有の薬機法・PMDA 規制 → 別ファイル（レイヤーC）
- ❌ FDA・EMA 規制詳細 → 別ファイル（海外規制）

---

## 1. IMDRF SaMD 定義

### 1.1 文書情報

| 項目 | 内容 |
|------|------|
| 文書番号 | IMDRF N10FINAL:2013 |
| 発行日 | 2013-12-18 |
| 発行機関 | International Medical Device Regulators Forum（IMDRF） |
| URL | https://www.imdrf.org/documents/software-medical-device-samd-key-definitions |

### 1.2 SaMD の定義

> **Software as a Medical Device (SaMD)**: software intended to be used for one or more medical purposes that perform these purposes without being part of a hardware medical device.

日本語訳（参考）: ハードウェア医療機器の一部ではなく、単体で医療目的を果たすことを意図したソフトウェア。

### 1.3 スコープの境界

| 分類 | SaMD か？ | 備考 |
|------|-----------|------|
| 単体医療目的ソフトウェア | ✅ はい | 例：診断アルゴリズム、臨床意思決定支援 |
| ハードウェア機器に組み込まれたソフトウェア | ❌ いいえ | ペースメーカー内蔵ソフト等は対象外 |
| 汎用ソフトウェア（一般目的） | ❌ いいえ | 医療目的でない場合は対象外 |
| インフラ・クラウドサービス | ❌ いいえ | ただし SaMD 動作環境としては関連あり |

---

## 2. IMDRF SaMD リスク分類

### 2.1 文書情報

| 項目 | 内容 |
|------|------|
| 文書番号 | IMDRF N12FINAL:2014 |
| 発行年 | 2014 |
| 発行機関 | IMDRF |
| URL | https://www.imdrf.org/documents/software-medical-device-possible-framework-risk-categorization-and-corresponding-considerations |

### 2.2 リスク分類の 2 軸

N12 は以下の 2 軸によってリスクカテゴリを決定する。

**軸 1：医療状況の重大性（State of Healthcare Situation）**

| 区分 | 概要（参考訳） |
|------|---------------|
| **Critical（重大）** | 生命を脅かす疾患・状態。迅速な介入が必要。 |
| **Serious（重篤）** | 生命を脅かす可能性があるが、迅速な介入を要しない疾患・状態。 |
| **Non-serious（非重篤）** | Critical・Serious に分類されないその他の状態。 |

> ⚠️ **未確認注記**: 上記の定義文言は N12 PDF の条文を直接抽出したものではなく、  
> 二次的な解説資料に基づく参考訳です。正確な条文は一次情報（N12FINAL:2014 PDF）  
> を参照して確認してください。

**軸 2：SaMD が提供する情報の重要性（Significance of Information Provided by SaMD）**

| 区分 | 概要（参考訳） |
|------|---------------|
| **Treat or diagnose（治療・診断）** | SaMD の情報が患者の治療または診断に直接使われる。 |
| **Drive clinical management（臨床管理を主導）** | SaMD の情報が臨床管理の決定を駆動・影響する。 |
| **Inform clinical management（臨床管理を補助）** | SaMD の情報が臨床管理の判断材料として用いられる。 |

> ⚠️ **未確認注記**: 上記の区分文言は N12 PDF の条文を直接抽出したものではありません。  
> 正確な条文は一次情報（N12FINAL:2014 PDF）を参照してください。

### 2.3 リスク分類マトリクス（Category I〜IV）

Category I が最低リスク、Category IV が最高リスク。

| 情報の重要性 ↓ / 医療状況の重大性 → | **Critical** | **Serious** | **Non-serious** |
|--------------------------------------|:------------:|:-----------:|:---------------:|
| **Treat or diagnose**                | **IV**       | **III**     | **II**          |
| **Drive clinical management**        | **III**      | **II**      | **I**           |
| **Inform clinical management**       | **II**        | **I**       | **I**           |

> ⚠️ **未確認注記**: 上記マトリクスの各セルの割り当て（Category I〜IV）は  
> 二次的な解説資料に基づいています。各セルの正確な値・境界条件・根拠条文は  
> N12FINAL:2014 の PDF 本文（特に Appendix を含む Table）を直接確認してください。

### 2.4 カテゴリ別の含意（概要）

| カテゴリ | リスクレベル | 規制対応の方向性（概要） |
|----------|--------------|--------------------------|
| **Category I** | 最低 | 多くの国で軽微な規制 |
| **Category II** | 低〜中 | 一般的な規制要件 |
| **Category III** | 中〜高 | 強化された規制要件 |
| **Category IV** | 最高 | 最も厳格な規制要件 |

> ⚠️ **未確認注記**: 具体的な規制要件の対応関係は国・地域の規制当局の判断に依存します。  
> N12FINAL:2014 および各国の実施文書を参照してください。

---

## 3. ISO 13485:2016 — 医療機器 QMS

### 3.1 文書情報

| 項目 | 内容 |
|------|------|
| 規格番号 | ISO 13485:2016 |
| 正式名称 | Medical devices — Quality management systems — Requirements for regulatory purposes |
| 版年 | 2016 |
| 発行機関 | ISO |
| URL | https://www.iso.org/standard/59752.html |

### 3.2 概要

医療機器の設計・開発・製造・保守・廃棄にわたる品質マネジメントシステム（QMS）の要件を規定する。規制目的に特化しており、ISO 9001 を基礎としつつ、医療機器固有の要件を追加している。

### 3.3 SaMD 開発との関係

- SaMD の設計管理・変更管理に直接適用
- リスクマネジメント（ISO 14971）との統合が求められる
- 多くの国の薬事規制で適合が求められる（日本 QMS 省令のベース）

---

## 4. ISO 14971:2019 — リスクマネジメント

### 4.1 文書情報

| 項目 | 内容 |
|------|------|
| 規格番号 | ISO 14971:2019 |
| 正式名称 | Medical devices — Application of risk management to medical devices |
| 版年 | 2019 |
| 発行機関 | ISO |
| URL | https://www.iso.org/standard/72704.html |

### 4.2 プロセス概要

ISO 14971 は以下のリスクマネジメントサイクルを規定する。

```
1. リスクマネジメント計画
2. ハザードの特定
3. リスク推定（確率 × 重大性）
4. リスク評価（許容可能か？）
5. リスクコントロール（低減策の実施）
6. 残余リスクの評価
7. リスクマネジメントレポート
8. 市販後監視（Post-market surveillance）
```

### 4.3 ベネフィット・リスク分析

ISO 14971:2019 は「ベネフィット・リスク判断」を明確に組み込んでいる。残余リスクがベネフィットを超える場合は市場投入不可。

### 4.4 SaMD・AI との関係

- AI モデルの誤予測・バイアスはハザードとして特定すること
- データドリフト・モデル劣化は市販後監視の対象
- IEC 62304 および IEC 82304-1 とのインターフェースが重要

---

## 5. IEC 62304:2006+AMD1:2015 — ソフトウェアライフサイクル

### 5.1 文書情報

| 項目 | 内容 |
|------|------|
| 規格番号 | IEC 62304:2006+AMD1:2015 |
| 正式名称 | Medical device software — Software life cycle processes |
| 版年 | 2006（本体）、AMD1:2015（改訂） |
| 発行機関 | IEC |
| URL | https://webstore.iec.ch/en/publication/22794 |

### 5.2 ソフトウェア安全クラス

IEC 62304 はソフトウェアを 3 つの安全クラスに分類する。

| クラス | 傷害の可能性（参考訳） | 要求水準 |
|--------|----------------------|----------|
| **Class A** | 傷害なし（Injury not possible） | 最低限 |
| **Class B** | 非重篤な傷害の可能性（Non-serious injury possible） | 中程度 |
| **Class C** | 死亡または重篤な傷害の可能性（Death or serious injury possible） | 最高 |

> ⚠️ **未確認注記**: 上記クラス定義の括弧内文言は二次情報に基づきます。  
> 標準の正確な条文は IEC 62304:2006+AMD1:2015 の本文（4.3 節相当）を  
> 参照してください。番号・版年は確認済みです。

### 5.3 Class C の追加要件（主要なもの）

Class C では以下が追加で要求される：

- **詳細設計（detailed design）** の文書化
- **単体テスト（unit testing）** の実施
- **双方向トレーサビリティ（bidirectional traceability）** の確保  
  （要件 ↔ アーキテクチャ設計 ↔ 詳細設計 ↔ 実装 ↔ テスト）

### 5.4 ソフトウェア開発プロセスへの適用

- SaMD は SOUP（Software of Unknown Provenance）を含む場合が多い（オープンソースライブラリ等）
- SOUP のリスク管理手順を文書化すること
- AMD1:2015 でアジャイル開発への適用が明確化された

---

## 6. IEC 82304-1:2016 — ヘルスソフトウェアの安全要求

### 6.1 文書情報

| 項目 | 内容 |
|------|------|
| 規格番号 | IEC 82304-1:2016 |
| 正式名称 | Health software — Part 1: General requirements for product safety |
| 版年 | 2016 |
| 発行機関 | IEC |
| URL | https://webstore.iec.ch/en/publication/26120 |

### 6.2 概要と位置づけ

IEC 62304 がソフトウェアライフサイクルプロセスを扱うのに対し、IEC 82304-1 は**ヘルスソフトウェア製品（health software product）**の安全要件を規定する。

| 観点 | IEC 62304 | IEC 82304-1 |
|------|-----------|-------------|
| 焦点 | 開発プロセス | 製品の安全要件 |
| 適用範囲 | 医療機器ソフトウェア | ヘルスソフトウェア全般（医療機器以外を含む） |
| 関係性 | 補完的（両方参照推奨） | 補完的（両方参照推奨） |

### 6.3 主要要件

- ヘルスソフトウェアの計画・設計・検証・リリース・廃棄まで
- セキュリティ・プライバシー要件との統合
- リスクマネジメント（ISO 14971 参照）との連携

---

## 7. ISO/IEC 42001:2023 — AI マネジメントシステム（AIMS）

### 7.1 文書情報

| 項目 | 内容 |
|------|------|
| 規格番号 | ISO/IEC 42001:2023 |
| 正式名称 | Information technology — Artificial intelligence — Management system |
| 版年 | 2023 |
| 発行機関 | ISO / IEC |
| URL | https://www.iso.org/standard/42001 |

> ⚠️ **URL 注記**: 上記 URL は ISO の標準ページ指定パターンです。  
> 正確なカタログページは https://www.iso.org/standard/81230.html を  
> 参照してください（ISO/IEC 42001:2023 の ISN は 81230）。

### 7.2 概要

ISO/IEC 42001:2023 は組織が AI システムを責任ある方法で開発・提供・利用するための  
**AI マネジメントシステム（AIMS）**の要件と指針を規定する初の国際規格。

### 7.3 主要要素

| 要素 | 内容 |
|------|------|
| **AI リスクアセスメント** | AI 固有のリスク（バイアス・誤予測・悪用等）の特定と評価 |
| **学習データガバナンス** | データ品質・代表性・偏り・来歴の管理 |
| **説明可能性（Explainability）** | AI の判断根拠を適切なステークホルダーに説明可能にする |
| **性能計測・監視** | モデル性能の継続的な評価・ドリフト検知 |
| **透明性** | AI システムの能力・限界・目的の開示 |

### 7.4 医療 AI との関係

- ISO 14971 のリスクマネジメントと統合することで医療 AI の包括的なリスク管理が可能
- EU AI Act・FDA AI/ML 規制対応との整合が求められる場合に参照
- 医療 AI の倫理原則（公平性・説明可能性・患者安全）への対応基盤

---

## 規格間の関係マップ

```
医療 AI / SaMD 開発

  IMDRF N10 (定義) ──→ SaMD の範囲確定
  IMDRF N12 (分類) ──→ リスクカテゴリ (I〜IV) 決定
                            │
                            ▼
  ISO 13485:2016 ─────→ QMS（開発・製造・改善の枠組み）
                            │
                            ├──→ ISO 14971:2019（リスクマネジメント）
                            │           │
                            │           ├──→ IEC 62304:2006+AMD1:2015（ライフサイクル）
                            │           └──→ IEC 82304-1:2016（製品安全）
                            │
                            └──→ ISO/IEC 42001:2023（AI マネジメント）
```

---

## 参照ガイドライン

このファイルは Layer B（国際規格）を担当する。関連する他レイヤーは以下：

- **Layer A（報告ガイドライン）**: `reporting-guidelines.md`
- **Layer C（日本制度）**: 別ファイル（薬機法・PMDA ガイドライン・QMS 省令等）
- **海外規制詳細**: 別ファイル（FDA・EMA・CE Mark 等）
- **リスクワークシート**: `../assets/samd-risk-worksheet.md`（IMDRF N12 分類の実践）

---

## 改訂履歴

| 日付 | 内容 |
|------|------|
| 2026-06 | 初版作成（IMDRF N10/N12、ISO 13485/14971、IEC 62304/82304-1、ISO/IEC 42001） |
