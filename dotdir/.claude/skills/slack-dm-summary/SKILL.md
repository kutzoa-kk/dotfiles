---
name: slack-dm-summary
description: Slack の DM・グループ DM を、人に頼まれたときだけ読んで要約する手順（~/ai-agent-ops の intake を使う）。「この DM を要約して」「藤原さんとの DM を確認して」「膝OA の DM を見て」など、DM やグループ DM の中身を知りたいと頼まれたら使う。原文を残さず、投稿もしない。Do NOT use for: 許可リストのチャンネルの収集（uv run intake slack collect）、Slack への投稿、DM を定期に読む仕組みを足すこと。
---

# Slack の DM を頼まれたときだけ要約する

DM とグループ DM は、送り手が限られた相手に向けて書いたもので、自動で読み集めて編纂されることを想定していない。だから、人が「この DM を要約して」と頼んだときだけ読み、その依頼を読むことへの承認とみなす（設計書 `~/ai-agent-ops/docs/superpowers/specs/2026-10-12-business-layer-design.md` §6.2）。

## 手順

1. `~/ai-agent-ops/src/intake/dm.py` があるかを確かめる。無ければこの PC では使えないので、そう伝えて止まる。
2. 頼まれた DM の ID（`D…` または `C…`）かリンクを確かめる。分からなければ人に聞く。推測で ID を探しに行かない。
3. 次を実行する。期間の既定は直近7日。

   ```bash
   cd ~/ai-agent-ops && uv run intake dm summarize <ID> [--since YYYY-MM-DD]
   ```

   hermes が読み取り専用の Slack MCP で読み、利用者が参加者でない会話や、DM でない会話は読まずに失敗する。要約は画面に出るだけで、ファイルには残らない。1回に1分ほどかかる。
4. 出てきた要約を、日本語で人に伝える。vault に残すかは人が決める。残すときは brain の CLI で、頼まれた範囲だけを書く。

## してはいけないこと

- Slack への投稿、返信、リアクション
- DM の原文を、リポジトリ・vault・下書きのどこかに保存すること
- DM を定期に読むこと。定期の例外は DM-003 の1件だけで、`intake/sources.yaml` とコードが持つ（`uv run intake dm periodic`）。例外を足すのは人の判断で、このスキルからは足さない
- 頼まれた範囲を超えて要約を残すこと

## 注意

- グループ DM にも、チャンネルと同じ `C` で始まる ID が付く。ID の形でチャンネルと判断しない（`intake` は読み取りの結果の種別で確かめる）。
- 許可リストのチャンネルの ID を渡すと拒む。チャンネルは `uv run intake slack collect` で読む。
- hermes は自分の会話の記録（`~/.hermes/sessions/`、`state.db`）に読んだ内容を残す。これは利用者の判断（2026-10-13）で「保存」に数えない。
