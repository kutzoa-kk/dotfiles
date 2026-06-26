# 報告ガイドライン知識ベース（レイヤーA）

> **役割**: 医療 AI・臨床予測モデル研究の論文執筆時に適用すべき報告ガイドライン（GL）の概要と選択基準を提供する。  
> 各 GL の項目名完全一覧は収録していない。チェックリスト全文・説明文書（E&E paper）は必ず一次情報を参照すること（末尾「未確認事項の扱い」参照）。

---

## GL 選択早見表

| 研究タイプ | 第一選択 GL | 補完 GL |
|---|---|---|
| 予測モデル開発・検証（AI/ML） | **TRIPOD+AI** (2024) | — |
| 医用画像 AI（予測モデル） | **TRIPOD+AI** (2024) | + **CLAIM** (2020) |
| 診断精度研究（AI） | **STARD-AI** (2025) | — |
| AI 介入 RCT（結果報告） | **CONSORT-AI** (2020) | CONSORT 2025 を基盤に参照 |
| AI 介入試験プロトコル | **SPIRIT-AI** (2020) | SPIRIT 2025 を基盤に参照 |
| AI 意思決定支援の早期臨床評価 | **DECIDE-AI** (2022) | — |
| 観察研究（コホート・症例対照・横断） | **STROBE** | — |
| RCT mainline（非 AI 特化基盤確認） | **CONSORT 2025** | — |

> **注**: 研究が複数の研究タイプにまたがる場合は、AI 特化 GL を優先し mainline GL を補完的に確認する。

---

## 1. TRIPOD+AI (2024)

**正式名称**: Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis + Artificial Intelligence  
**版年**: 2024  
**原著**: Collins GS, Moons KGM, et al. *BMJ* 2024;385:e078378  
**公式サイト**: https://www.tripod-statement.org/tripod-ai/  
**原著 DOI**: https://doi.org/10.1136/bmj-2023-078378  
**EQUATOR**: https://resources.equator-network.org/reporting-guidelines/tripod-ai/

### 概要

- 本体 27 項目＋抄録 13 項目
- 対象: AI・機械学習を用いた臨床予測モデルの開発・検証・更新を報告する研究
- fairness（公平性）のサブグループ分析と、コード・モデルの寄託（open science）を重視する
- **旧 TRIPOD (2015) は使用非推奨**。本 TRIPOD+AI への移行が求められる

### 利用時の注意

- 項目名完全一覧・各項目の詳細説明: 上記一次情報参照

---

## 2. CONSORT 2025 / SPIRIT 2025

**正式名称**: Consolidated Standards of Reporting Trials 2025（CONSORT 2025）/ Standard Protocol Items: Recommendations for Interventional Trials 2025（SPIRIT 2025）  
**版年**: 2025（mainline 本体改訂版）  
**原著・一次情報 URL**: 未確認（[EQUATOR Network](https://www.equator-network.org/) または https://www.consort-statement.org / https://www.spirit-statement.org を参照）

> ⚠️ **重要: CONSORT 2025 / SPIRIT 2025 は 2020年の CONSORT-AI / SPIRIT-AI とは別物である。**  
> - CONSORT 2025 / SPIRIT 2025 = RCT・試験プロトコルの mainline 本体改訂版。AI 特化項目は含まない。  
> - CONSORT-AI (2020) / SPIRIT-AI (2020) = AI 介入試験に特化した拡張版（CONSORT 2010 / SPIRIT 2013 を基盤に AI 専用項目を追加）。  
> - AI 介入 RCT を報告する際は、CONSORT 2025 の基盤項目と CONSORT-AI の AI 拡張項目を**両方**参照すること。

### 概要

- CONSORT 2025: ランダム化比較試験全般の報告基準（mainline 本体）
- SPIRIT 2025: 臨床試験プロトコル全般の記述基準（mainline 本体）
- 項目名完全一覧: 一次情報参照

---

## 3. CONSORT-AI (2020)

**正式名称**: Consolidated Standards of Reporting Trials — Artificial Intelligence  
**版年**: 2020（CONSORT 2010 拡張版）  
**原著**: *Nat Med* 2020;26:1364–1374  
**一次情報 URL**: 未確認（[EQUATOR Network](https://www.equator-network.org/) で「CONSORT-AI」検索、または PubMed で *Nat Med* 2020;26:1364 を参照）

### 概要

- CONSORT 2010 の全項目に AI 特化項目 14 件を追加
- 対象: AI を介入として用いるランダム化比較試験の**結果報告**
- SPIRIT-AI と対をなす（SPIRIT-AI はプロトコル版）
- 項目名完全一覧: 一次情報参照

---

## 4. SPIRIT-AI (2020)

**正式名称**: Standard Protocol Items: Recommendations for Interventional Trials — Artificial Intelligence  
**版年**: 2020（SPIRIT 2013 拡張版）  
**原著**: *Nat Med* 2020;26:1351–1363  
**PMC**: https://pmc.ncbi.nlm.nih.gov/articles/PMC7788716/

### 概要

- SPIRIT 2013 の全項目に AI 特化項目 15 件を追加
- 対象: AI を介入として用いる臨床試験の**プロトコル記述**
- CONSORT-AI と対をなす（CONSORT-AI は結果報告版）
- 項目名完全一覧: 一次情報参照

---

## 5. STARD-AI (2025)

**正式名称**: Standards for Reporting of Diagnostic Accuracy Studies — Artificial Intelligence  
**版年**: 2025  
**原著**: Sounderajah V, et al. *Nat Med* 2025;31:3283–3289  
**原著 DOI**: https://doi.org/10.1038/s41591-025-03953-8

### 概要

- 対象: AI を用いた診断精度研究（画像診断・検査結果判定等）
- 基盤となる STARD（非 AI 版）の AI 特化拡張版
- 項目名完全一覧: 一次情報参照

---

## 6. DECIDE-AI (2022)

**正式名称**: Developmental and Exploratory Clinical Investigations of DEcision-support systems driven by Artificial Intelligence  
**版年**: 2022  
**原著**: Vasey B, et al. *BMJ* 2022;377:e070904  
**原著 DOI**: https://doi.org/10.1136/bmj-2022-070904

### 概要

- 対象: AI 意思決定支援システムの**早期臨床評価**（first-in-human・探索的臨床試験段階）
- 本格的な RCT より前の段階を扱う点で CONSORT-AI と役割が異なる
- 項目名完全一覧: 一次情報参照

---

## 7. CLAIM (2020)

**正式名称**: Checklist for Artificial Intelligence in Medical Imaging  
**版年**: 2020  
**原著**: Mongan J, et al. *Radiol Artif Intell* 2020;2(2):e200029  
**PMC**: https://pmc.ncbi.nlm.nih.gov/articles/PMC8017414/

### 概要

- 対象: 医用画像 AI 研究（放射線科・病理・眼科等）
- 42 項目のチェックリスト
- TRIPOD+AI と補完的に使用する（特に画像 AI 特有の技術的項目をカバー）
- 項目名完全一覧: 一次情報参照

---

## 8. STROBE

**正式名称**: Strengthening the Reporting of Observational Studies in Epidemiology  
**版年・一次情報 URL**: 未確認（[EQUATOR Network](https://www.equator-network.org/) で「STROBE」検索を参照）

### 概要

- 対象: 観察研究（コホート研究・症例対照研究・横断研究）
- AI 特化項目は含まない（観察デザインの基盤 GL として利用）
- 項目名完全一覧: 一次情報参照

---

## 未確認事項の扱い

> **本ファイルの方針**: 各 GL のチェックリスト全文・項目名完全一覧・E&E（Explanation and Elaboration）論文は収録していない。以下から一次情報を取得すること。

| GL | 確認先 |
|---|---|
| 全 GL 共通 | [EQUATOR Network](https://www.equator-network.org/) で GL 名を検索 |
| TRIPOD+AI | https://www.tripod-statement.org/tripod-ai/ または https://doi.org/10.1136/bmj-2023-078378 |
| CONSORT-AI | *Nat Med* 2020;26:1364–1374 — EQUATOR Network で「CONSORT-AI」検索 |
| SPIRIT-AI | https://pmc.ncbi.nlm.nih.gov/articles/PMC7788716/ |
| STARD-AI | https://doi.org/10.1038/s41591-025-03953-8 |
| DECIDE-AI | https://doi.org/10.1136/bmj-2022-070904 |
| CLAIM | https://pmc.ncbi.nlm.nih.gov/articles/PMC8017414/ |
| CONSORT 2025 | 未確認 — https://www.consort-statement.org または EQUATOR Network を参照 |
| SPIRIT 2025 | 未確認 — https://www.spirit-statement.org または EQUATOR Network を参照 |
| STROBE | 未確認 — EQUATOR Network で「STROBE」検索を参照 |

> **CONSORT-AI 原著 DOI**: 本ファイルでは未確認。PubMed または EQUATOR Network で "CONSORT-AI Nat Med 2020" を検索して確認すること。
