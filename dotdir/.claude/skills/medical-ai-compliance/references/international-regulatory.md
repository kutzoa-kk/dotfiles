# 海外規制リファレンス（FDA / EU）— 軽量参照

> **本ファイルは軽量参照です。** 要点と一次情報 URL のみを提供します。  
> 各制度の詳細・最新情報は必ず各一次情報（fda.gov / eur-lex.europa.eu 等）で確認してください。

---

## 対象スコープ

| カバー範囲 | 参照先 |
|------------|--------|
| ✅ FDA GMLP（Good Machine Learning Practice、10 原則） | 本ファイル § 1 |
| ✅ FDA PCCP（Predetermined Change Control Plan） | 本ファイル § 2 |
| ✅ EU AI Act（Regulation (EU) 2024/1689） | 本ファイル § 3 |
| ✅ EU MDR（Regulation (EU) 2017/745） | 本ファイル § 4 |
| ❌ 日本固有の制度（薬機法・IDATEN 等） | `japan-regulatory.md` |
| ❌ IMDRF・ISO 国際規格 | `regulatory-standards.md` |
| ❌ 報告ガイドライン（CONSORT-AI・TRIPOD-AI 等） | `reporting-guidelines.md` |

---

## 1. FDA GMLP（Good Machine Learning Practice）

### 1.1 文書情報

| 項目 | 内容 |
|------|------|
| 正式名称 | Good Machine Learning Practice for Medical Device Development: Guiding Principles |
| 発行年月 | 2021年10月 |
| 発行機関 | FDA / Health Canada / 英国 MHRA（三機関共同） |
| 原則数 | 10 原則 |
| 一次情報 URL | https://www.fda.gov/medical-devices/software-medical-device-samd/good-machine-learning-practice-medical-device-development-guiding-principles |

### 1.2 概要

GMLP は FDA・Health Canada・MHRA が共同策定した、AI/ML 医療機器の開発・評価における優良実践の10指導原則。製品ライフサイクル全体（Total Product Life Cycle, TPLC）を通じた安全・有効・高品質な AI/ML 医療機器の実現を目的とする。

**10 原則の主要テーマ（WebSearch 結果より要約）**:

| # | テーマ |
|---|--------|
| 1 | 多職種チームが TPLC 全体を通じて関与する |
| 2 | 良好なソフトウェアエンジニアリングおよびセキュリティ実践を採用する |
| 3 | 臨床試験参加者・データセットは対象患者集団を代表する |
| 4 | 訓練データセットとテストデータセットは独立している |
| 5 | 参照データセットは利用可能な最良の方法に基づく |
| 6 | モデル設計は利用可能なデータと使用目的（Intended Use）に適合している |
| 7 | 人間と AI チームのパフォーマンスに焦点を当てる（ヒューマンファクター考慮） |
| 8 | 臨床的に妥当な条件でのデバイス性能をテストで実証する |
| 9 | ユーザーに明確かつ必要不可欠な情報を提供する（透明性） |
| 10 | 市販後の性能モニタリングと再学習リスクを管理する |

> **位置づけ**: GMLP は法的義務ではなく Guiding Principles（指導原則）。ただし FDA 審査において実質的な参照基準として機能する。

---

## 2. FDA PCCP（Predetermined Change Control Plan）

### 2.1 文書情報

| 項目 | 内容 |
|------|------|
| 正式名称（最終ガイダンス） | Marketing Submission Recommendations for a Predetermined Change Control Plan for Artificial Intelligence-Enabled Device Software Functions |
| 最終ガイダンス発行 | 2024年12月4日 |
| 発行機関 | FDA（CDRH） |
| 関連 Guiding Principles | Predetermined Change Control Plans for Machine Learning-Enabled Medical Devices: Guiding Principles（FDA/Health Canada/MHRA 共同、2023年10月） |
| 一次情報 URL（最終ガイダンス） | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence |
| 一次情報 URL（Guiding Principles） | https://www.fda.gov/medical-devices/software-medical-device-samd/predetermined-change-control-plans-machine-learning-enabled-medical-devices-guiding-principles |

### 2.2 日本 IDATEN との対応

**FDA PCCP は、日本の IDATEN（変更計画確認手続制度）に相当する位置づけ**の制度。

| 比較軸 | FDA PCCP | 日本 IDATEN |
|--------|----------|-------------|
| 対象 | AI-Enabled Device Software Functions（AI-DSF） | 承認済医療機器（プログラム医療機器含む） |
| 仕組み | 変更計画を承認申請時に添付 → 計画内変更は追加申請不要 | 変更計画を PMDA が事前確認 → 計画内変更は軽微変更届出のみ |
| 主管 | FDA（CDRH） | PMDA |

> **注意**: PCCP は AI/ML 医療機器（SaMD 含む）の用語。医薬品分野の PACMP（Post-Approval Change Management Protocol）とは**別制度**であり、混同しないこと。

→ 日本の IDATEN の詳細は [`japan-regulatory.md` セクション 4（IDATEN）](japan-regulatory.md#4-idaten変更計画確認手続制度)を参照。

### 2.3 PCCP の構成要素

PCCP は marketing submission（510(k) 等）の一部として提出する。FDA が PCCP を審査・承認することで、承認された計画内の変更は追加 submission なしに実施できる。

**PCCP に含める主要要素**:

1. **計画された変更の内容**（Planned AI-DSF Modifications）— 変更の説明・変更前後の比較
2. **変更の方法論**（Methodology）— 開発・検証・実装の手順
3. **インパクト評価**（Impact Assessment）— 安全性・有効性への影響の事前評価

---

## 3. EU AI Act

### 3.1 文書情報

| 項目 | 内容 |
|------|------|
| 正式名称 | Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence |
| 規則番号 | (EU) 2024/1689 |
| 官報掲載 | 2024年7月12日 |
| 発効日 | 2024年8月1日 |
| 適用開始 | 段階的（§ 3.3 参照） |
| 一次情報 URL | https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng |

### 3.2 概要

EU 域内の AI システムに適用される初の包括的横断規制。リスクベースアプローチを採用し、AI システムをリスクレベル別に分類する。

**リスク分類**:

| 分類 | 主な要件 |
|------|----------|
| 許容不可能なリスク | 禁止（社会スコアリング、特定の遠隔生体認証等） |
| 高リスク（High Risk） | Annex III 列挙。義務的要件（リスク管理・データガバナンス・透明性・人間監視等） |
| 限定リスク | 透明性義務のみ（チャットボット等） |
| 最小リスク | 規制なし |

**医療 AI への直接的影響**:

| 観点 | 内容 |
|------|------|
| 高リスク AI 該当 | Annex III に「医療機器・体外診断機器の安全コンポーネントとして機能する AI システム」が列挙 |
| EU MDR との関係 | EU MDR の適合性評価を経た AI 医療機器は AI Act の高リスク AI 要件との整合が必要 |
| 適用対象 | EU 域内で AI システムを提供または使用する事業者（域外事業者含む） |

### 3.3 段階的適用スケジュール

| 時期 | 適用内容 |
|------|----------|
| 2025年2月2日 | 禁止 AI（Chapter II）および一般定義（Chapter I）の適用開始 |
| 2025年8月2日 | 汎用 AI モデル（GPAI、Chapter V/VI/VII 関連規定）の適用開始 |
| 2026年8月2日 | 高リスク AI システム（Annex III、独立型）の要件適用 |
| 2027年8月2日 | 製品の安全コンポーネントとして組み込まれた AI（Annex I 規制製品、MDR 対象機器含む）の適用 |

> **軽量参照注記**: AI Act の高リスク AI 義務（Art.9〜15 等）の逐条詳細は本ファイルの対象外。詳細は一次情報を参照すること。

---

## 4. EU MDR（Medical Device Regulation）

### 4.1 文書情報

| 項目 | 内容 |
|------|------|
| 正式名称 | Regulation (EU) 2017/745 of the European Parliament and of the Council of 5 April 2017 on medical devices |
| 規則番号 | (EU) 2017/745 |
| 制定日 | 2017年4月5日 |
| 適用開始 | 2021年5月26日 |
| 一次情報 URL（原文） | https://eur-lex.europa.eu/eli/reg/2017/745/oj/eng |
| 一次情報 URL（最新統合版） | https://eur-lex.europa.eu/eli/reg/2017/745/2025-01-10/eng |

### 4.2 概要

EU 域内の医療機器規制の中核規則。ソフトウェアが医療機器として明示的に対象とされており、SaMD に直接適用される。

**クラス分類**:

| クラス | リスク | 適合性評価 |
|--------|--------|------------|
| Class I | 最低リスク | 製造業者自己宣言（一部 Notified Body 関与） |
| Class IIa | 低〜中リスク | Notified Body による適合性評価 |
| Class IIb | 中〜高リスク | Notified Body による適合性評価 |
| Class III | 最高リスク | Notified Body による最も厳格な評価 |

**ソフトウェア（SaMD）への適用**:

- 医療目的で製造業者が意図するソフトウェア（SaMD）は医療機器として規制対象
- 一般目的ソフトウェア・生活習慣/ウェルネス目的ソフトウェアは適用外
- AI/ML を用いた診断支援ソフトウェアは医療目的の場合、SaMD として MDR の適用を受ける

> **軽量参照注記**: MDR の技術文書要件（Annex II・III）、QMS 要件（Annex IX）、EU AI Act との二重適用の詳細は本ファイルの対象外。詳細は一次情報を参照すること。

---

## 5. 一次情報リンク一覧

| 制度 | 発行機関 | 版年 | 一次情報 URL |
|------|----------|------|--------------|
| FDA GMLP（10 原則） | FDA / Health Canada / MHRA | 2021年10月 | https://www.fda.gov/medical-devices/software-medical-device-samd/good-machine-learning-practice-medical-device-development-guiding-principles |
| FDA PCCP 最終ガイダンス（AI-DSF） | FDA（CDRH） | 2024年12月4日 | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence |
| FDA PCCP Guiding Principles | FDA / Health Canada / MHRA | 2023年10月 | https://www.fda.gov/medical-devices/software-medical-device-samd/predetermined-change-control-plans-machine-learning-enabled-medical-devices-guiding-principles |
| EU AI Act 原文 | 欧州議会・理事会 | 2024年6月13日 | https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng |
| EU MDR 原文 | 欧州議会・理事会 | 2017年4月5日 | https://eur-lex.europa.eu/eli/reg/2017/745/oj/eng |
| EU MDR 最新統合版（2025-01-10） | EUR-Lex | 2025年1月10日 | https://eur-lex.europa.eu/eli/reg/2017/745/2025-01-10/eng |

---

## 付記：未確認事項

以下の事項は、本ドキュメント作成時点で一次情報ページの直接取得（WebFetch）ができなかった項目。URL は検索結果より存在を確認済み。

| 事項 | 状況 | 確認先 |
|------|------|--------|
| GMLP 10 原則の個別詳細テキスト | 主要テーマは検索結果から要約確認済み。各原則の正確な英語表記は一次情報で要確認 | https://www.fda.gov/medical-devices/software-medical-device-samd/good-machine-learning-practice-medical-device-development-guiding-principles |
| EU AI Act の条文ごとの適用スケジュール | 大枠（2025年2月〜2027年8月）は EUR-Lex 取得コンテンツから確認済み。Article 別の詳細スケジュールは一次情報で要確認 | https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng |
