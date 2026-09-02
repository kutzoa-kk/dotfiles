# 英語 AI 臭パターン辞書（patterns-en）

Wikipedia「Signs of AI writing」（WikiProject AI Cleanup 管理）を主資料とした英語文向け辞書。日本語文は patterns-ja.md を使う。指摘・修正時はパターン ID（E01 等）で参照する。

- 学術文書では robust・significant・comprehensive 等が正当な専門用語として使われる。用語としての使用は指摘せず、装飾としての密度で判断する
- ⚠ 印は強シグナル（1件でも AI 生成の直接証拠に近い）

## A. 語彙（密度で判断）

| ID | 名前 | パターン | 推奨対応 |
|----|------|---------|---------|
| E01 | AI 頻出語彙 | delve, tapestry, testament, landscape, robust, pivotal, crucial, intricate, meticulous, boasts, vibrant, foster, garner, underscore, highlight, showcase, interplay, enduring, bolster, leverage, seamless | 平易な動詞・名詞に置き換える（例：delve into → examine） |
| E02 | 重要性の水増し | stands/serves as a testament to, plays a crucial/pivotal role, underscores its importance, marks a significant shift, evolving landscape | 具体的に何がどう重要かを書くか、削る |
| E03 | -ing 句のぶら下げ | 文末の highlighting..., underscoring..., reflecting...（根拠のない意見の注入） | 独立した文にして根拠を書くか、削る |
| E04 | 宣伝調 | nestled in the heart of, breathtaking, groundbreaking, renowned, rich cultural heritage, diverse array, gateway to | 事実の記述に置き換える |
| E05 | be 動詞の回避 | is → serves as / stands as / functions as / represents | 単純に is / was を使う |
| E06 | 出典なき権威付け | experts argue, industry reports suggest, observers have cited, some critics argue | 出典を明示するか、主張を自分のものとして書く |

## B. 構文・定型句

| ID | 名前 | パターン | 推奨対応 |
|----|------|---------|---------|
| E07 | 否定並列 | not just X, but Y ／ It's not X, it's Y ／ This isn't X. It's Y. | 主張を1文で直接書く |
| E08 | 喉クリアリング | It is important to note that..., Here's the thing:, In today's fast-paced world | 前置きを削り、本題から書く |
| E09 | 定型導入・定型結論 | In conclusion, Despite these challenges, ...remains to be seen, 「Challenges and Future Directions」型の締め | 内容に固有の結論を書く |
| E10 | 過剰ヘッジ | may potentially, it could be argued that, arguably の乱用 | 断定するか、不確実性の根拠を書く |
| E11 | 三点セット癖 | 常に3項目の並列で文を組むリズム（rule of three） | 項目数・文構造を内容で変える |

## C. リズム・書式

| ID | 名前 | パターン | 推奨対応 |
|----|------|---------|---------|
| E12 | em dash の乱用 | 1段落に複数の「—」 | 約300語に1本まで。カンマ・コロン・文分割に置き換える |
| E13 | 文長の均一 | 同じ長さ・同じ構造の文の連続（burstiness の欠如） | 150語ごとに6語以下の短文を1つ置く。連続3文の文長を揃えない |
| E14 | 太字・書式の乱用 | 過剰な bold、文中 Title Case、絵文字見出し、水平線 | 強調は1セクション1〜2箇所。装飾を削る |
| E15 ⚠ | AI 痕跡文字列 | oaicite, turn0search, contentReference, [cite:, grok_card, utm_source=chatgpt.com | 完全に削除する（AI 生成の直接証拠） |
| E16 ⚠ | 引用の破綻 | 無効な DOI/ISBN、ページ番号なしの書籍引用 | 実在の出典に差し替えるか削除（検出時は事実確認を促す） |

## 育成手順

patterns-ja.md の育成手順と同じ。新パターン確定→表へ1行追記→更新履歴に1行。

## 更新履歴

- 2026-09-01 初版 E01〜E16（Wikipedia「Signs of AI writing」2026年時点の内容を翻案）
