---
name: slack-dm-summary
description: ai-agent-ops で Slack の DM / group DM を証拠として確認・要約・監視登録するときの、§4 ポリシー準拠オンデマンド手順。「DMを確認して」「このDMを要約して」「膝OA DM を要約」「group DM を監視対象に」「このDMを台帳に」など、DM/group DM の読み取り・要約・監視化を求められたら必ず使う。read-only 読取・§4 正規化要約・raw 非保存・dm_ledger 登録・自動巡回/cron 非対象を強制し、必要なら共有 Drive 資料を gog で read-only 取得して実数値を拡充する。通常の public/private チャンネル巡回（slack-daily-digest-orchestrator / monitored_channels.yaml の channels:）や、角谷さんが YAML を投入する dm_intake とは別経路。Do NOT use for: 通常チャンネルの日次 digest、Slack への投稿、DM の自動巡回・cron 化、public/private チャンネルの要約。
---

# Slack DM / group DM を証拠として確認・要約する

ai-agent-ops で Slack の DM / group DM を人間トリガで read-only 確認し、§4（`docs/evidence_sprawl_and_slack_dm_policy.md`）に準拠した正規化要約を作って台帳に載せるための手順。対象リポジトリは `~/work/ai-agent-ops`（相対パスはこのリポジトリ基準）。

## なぜ特別扱いなのか（最初に理解すべき前提）

Slack の DM / group DM は「exception-only の機微証拠」で、public/private チャンネルとは扱いが根本的に違う。§0 amendment で private channel は通常の evidence layer に格上げされたが、**DM / group DM は §4 のまま**。したがって:

- **自動巡回できない。** `slack-daily-digest-orchestrator` は `dm_ledger` を完全にスキップする。DM を `channels:`（巡回リスト）に入れてはならない。cron にも載せない。
- **raw を保存しない。** 会話本文・添付ファイル・Drive URL をリポジトリに保存しない。残すのは正規化要約だけ（`raw_content_stored: false`）。
- **人間トリガのみ。** 角谷さんが「このDMを確認/要約して」と依頼したとき、その依頼自体が §4 の「明示承認」になる。cron や思いつきで DM を読みに行かない。

この skill は、その例外を安全に運用するための決まった流れを提供する。ID プレフィックスに注意：Slack は group DM(mpim) にも `C...` 形式 ID を割り当てるので、`C` だからチャンネルとは限らない。`slack_read_channel` のヘッダ種別で必ず確認する。

## 承認ゲート（着手前に必ず確認）

`config/monitored_channels.yaml` の `dm_ledger` を見て、対象 DM のエントリを探す。

- エントリがあり `ondemand_summary_approved: true` → 承認済み。読んで要約してよい。
- エントリが無い / `ondemand_summary_approved` が無い → **これが承認の瞬間**。角谷さんの依頼を承認とみなし、要約後にエントリを新設 or 更新する（下記「台帳登録」）。既定の `intake: human_yaml_only`（agent 非読取）のままのエントリを、角谷さんの明示依頼なく勝手に読まない。

`can_agent_read: false` は「自動巡回では読まない」の意味。人間トリガのオンデマンド要約はこの skill の管轄で、`ondemand_summary_approved` が根拠になる。

## 手順

### 1. 種別確認と本読取（read-only）
- `slack_read_channel` で対象 ID の直近メッセージを読み、ヘッダで種別（public / private channel / group DM / 1:1 DM）を確認。`slack_list_channel_members` で参加者。必要なら `slack_read_thread` でスレッド。
- **送信系は一切使わない**（reply / reaction / canvas / draft 禁止）。

### 2. 同一性照合（sprawl 回避）
- `dm_ledger` / `evidence_registry.csv` に、channel_id 未束縛のプレースホルダ（例: 「コアチーム group DM」）が無いか確認。参加者・話題が一致するなら**新規 ID を作らず既存を確定・束縛**する（重複を作らない）。判断が付かないときは新規を作りつつ両者に相互参照 note を付け、統合は人間に委ねる。

### 3. §4 正規化要約の生成
`docs/evidence_sprawl_and_slack_dm_policy.md` §4 の YAML 形式で、`normalized.*` を日本語で埋める:
`confirmed_facts` / `decisions` / `requirement_candidates` / `blockers` / `dependencies` / `open_questions` / `human_confirmation_needed`。
ヘッダ（`source` / `classification` / `storage_policy`）も付す。`storage_policy.raw_content_stored: false` 固定。

**redact ルール**（なぜ重要か＝機微証拠だから）:
- 参加者は原則ロール表記（PL / 解析担当 / 方針・レビュー担当 等）。台帳の owner 欄に実名を書くのは既存慣行どおり可。
- ハードシークレット（password / key / token / .env）は redact & 非 commit。
- 特定顧客企業リンクや医療（患者）データを含むなら `sensitivity: high`（SLK-H008 の前例に整合）。取扱可否の最終判断は角谷さん。
- 生スライド逐語・raw テーブルは貼らない。要点と必要な数値だけを構造化する。

### 4. 保存（リポジトリには正規化物のみ）
- 正規化要約: `outputs/inbox/<YYYY-MM-DD>/dm_ondemand/dm_normalized_<evidence_id>_<YYYY-MM-DD>.md`
- inbox item（`templates/inbox_item.schema.json` 準拠、1〜数件）: `outputs/inbox/<YYYY-MM-DD>/dm_ondemand/inbox_items.jsonl`
  - `source_type: slack` / `sensitivity: dm_sensitive` / `requires_human_review: true` / `raw_content_stored: false` / `source_id: slack:<channel_id>:<ts>`。raw 本文は入れない。
- 台帳更新提案（監査）: `dispatch/ledger_updates/registry_update_proposal_<YYYY-MM-DD>.md`（無ければ `templates/registry_update_proposal_template.md` から）。
- Vault ノートは角谷さんが明示要求したときのみ。

### 5. 台帳登録（dm_ledger + evidence_registry）
canonical 台帳は本来「提案→人間適用」。角谷さんの直接指示時のみ、正確な差分を提示のうえ更新してよい。

`dm_ledger` エントリ（既定を壊さない additive 設計）:
```yaml
  - evidence_id: DM-00X
    label: <一言説明（参加者・主題）>
    channel_id: C...
    project: Scoremap
    workstream: <例: OA / KL / GRS>
    visibility: group_dm            # または dm
    can_agent_read: false           # 自動巡回/cron では読まない（既定維持）
    intake: agent_ondemand_summary  # human_yaml_only ではなく人間トリガのオンデマンド
    ondemand_summary_approved: true # §4 例外: 角谷さん明示承認 <日付>
    sensitive: true                 # 機微を含む場合
    note: "<承認日・raw 非保存・cron/自動巡回なし・redact 方針>"
```
`evidence_registry.csv`（15 列）は対応行を追加/更新し、`can_agent_read=ondemand_only` / `can_store_normalized_summary=TRUE`。DM を `channels:` に入れない。`state/slack_last_seen.json` を書かない。

詳細な逐次プロンプトが要るときは `prompts/dm_ondemand_summary_prompt_ja.md` を読む（この skill と対の実行手順書）。運用位置づけは `docs/slack_monitor_ondemand_runbook.md` §2.5。

## 事前指定 DM の定期確認（無人 cron 経路）

角谷さんが「このDMを定期的に確認」を望む場合、人間トリガの ondemand とは別に無人 cron 経路がある。

- 対象化: `dm_ledger` に `periodic_check: true` + `can_agent_read: periodic` + `periodic_approved_by:` を付ける。**角谷さん参加 DM に限る**（毎回 member 再検証、非参加は skip）。high 機微を載せる行為が ETHICS-01 の事前決裁。
- 実行: `scripts/run_slack_monitor.sh dm_periodic`（手順書 `prompts/dm_periodic_check_prompt_ja.md`）。watermark 差分のみ・raw 非保存・digest は `reports/dm_periodic_digest_<date>.md`。`periodic_check:true` の DM が無ければ agent dispatch は skip。
- cron 化は `config/hermes_jobs.yaml § dm_periodic_check` を有効化 + plist load（角谷さん決裁後）。既定 disabled。
- 詳細ポリシーは `docs/evidence_sprawl_and_slack_dm_policy.md` §0b。

## 任意: 共有 Drive 資料で実数値まで拡充

DM に Google Drive リンクや添付資料があり、角谷さんが「実数値まで」「資料も見て」と求めた場合のみ:

1. `gog --version` で稼働確認。認証失効（`invalid_grant`）なら角谷さんに `! gog auth add <email>` での再認証を促す（インタラクティブなので agent は実行しない）。
2. フォルダ列挙: `gog drive ls --parent <folderId> --readonly --plain`（種別確認は `tree`）。
3. 取得は**リポジトリ外の scratchpad にのみ**: `gog drive download <fileId> --out <scratchpad>/... --readonly`。リポジトリに raw ファイル（pptx/pdf/png）を置かない。
4. 解析: pptx は zip 展開で `ppt/slides/*.xml` の `<a:t>` テキストを抽出。PDF / PNG は Read で図を解釈。
5. 抽出した数値・要点だけを §4 正規化要約に反映（生ファイル・スライド逐語・Drive URL はリポジトリ非保存）。

## やってはいけないこと（境界）

- DM の自動巡回・cron 化・`channels:` への追加・`hermes_jobs.yaml`/`phase8_5_sources.yaml` への登録。
- raw 会話・添付・Drive URL のリポジトリ保存。`raw_content_stored` を true にすること。
- Slack への投稿・reply・reaction・canvas（read-only 厳守）。
- `sensitivity` を根拠なく格下げすること（機微は保守的に）。
- Linear 直接作成・Backlog 更新・product repo 編集。
- public/private チャンネルの要約（それは `slack-daily-digest-orchestrator` の管轄）。

## 完了時

人間向けに日本語で要約を提示し、生成物のパスと「raw 非保存・自動巡回/cron 非対象」を明示する。監査用に registry update proposal を残す。
