# ECC 共存ガイド

ECC（everything-claude-code）プラグインが稼働する環境で mvh-setup を実行するときの、検出・充足判定・干渉対処のリファレンス。

## なぜ必要か

ECC はグローバル（プラグイン由来）の hooks・スキル群で、mvh-setup の複数項目と同じ役割を既に果たしている。知らずにプロジェクトへ同じ仕組みを導入すると**二重ガード**（同じ編集に2つの保護 hook が発火し、挙動の切り分けが困難になる）や無駄な複雑化を招く。一方、ECC hooks は個人環境にしか存在しないため、**チームで共有すべき保護はプロジェクト成果物として別途必要**になる。この2つの判断を区別するのが本ガイドの目的。

## ECC の検出

```bash
# 有効化の確認（"ecc@ecc": true なら稼働中）
grep -o '"ecc@ecc"[^,}]*' ~/.claude/settings.json 2>/dev/null

# プラグイン実体の確認（バージョンはディレクトリ名）
ls ~/.claude/plugins/cache/ecc/ecc/ 2>/dev/null
```

検出できなければ本ガイドは不要。全項目を通常どおり判定する。

## mvh 項目 × ECC 対応表

| mvh 項目 | ECC 側の対応物 | 判定 |
|----------|----------------|------|
| 2. PostToolUse auto-format | `stop:format-typecheck` hook（応答終端で format + typecheck）、`/quality-gate` | ✳️ グローバル充足。チーム共有が要件なら `/auto-format-hook` でプロジェクト版を導入 |
| 3. Linter config protection | `pre:config-protection` hook（linter/formatter 設定の改変をブロック） | ✳️ グローバル充足。**二重導入注意**（同上） |
| 6. Stop Hook (test gate) | `verification-loop` スキル（Build→Type→Lint→Test の手順型検証） | **部分**充足のみ。ECC 版は手順であり強制力がない。完了を機械的にブロックしたいならプロジェクト Stop hook を導入する価値あり |
| 7. Session startup routine | `session:start` hook（前回コンテキスト復元等） | 部分充足。プロジェクト固有の起動チェック（build 確認等）は別途必要 |
| 10. Periodic audit | `config-gc` スキル（`~/.claude` の定期掃除） | 対象が違う（ECC=個人環境、mvh=プロジェクト）。両方に意味がある |
| 11. Safety gates | `safety-guard` スキル、GateGuard、（環境によっては自作 deny-check 等） | ✳️ グローバル充足になりやすい。まず既存の PreToolUse hook / permissions.deny を確認 |
| 全体のスコアカード | `/ecc:harness-audit`（rubric 固定・42 チェックの決定論採点） | 役割分担：mvh=導入ウィザード、harness-audit=採点器 |

対応物がない項目（1 CLAUDE.md、4 ADR、5 hygiene audit、8 Lefthook、9 custom lint rules）は ECC の有無に関係なく通常判定。

## 判定方針

1. **個人プロジェクト**（自分しか触らない）：✳️ グローバル充足を「充足」として扱い、プロジェクトへの再導入はしない。シンプル第一
2. **チーム開発プロジェクト**：グローバル充足に頼らない。他のメンバーの環境には ECC がない前提で、共有が必要な保護（auto-format・lint 保護・テストゲート）はプロジェクトの `.claude/settings.json` + スクリプトとして導入する。この場合スコアカードは ✳️ でなく ⬜/✅ で判定する
3. 迷ったらユーザーに「このプロジェクトはチームで共有しますか」と確認する

## GateGuard（Fact-Forcing Gate）干渉への対処

ECC の GateGuard は、**ファイルごとの初回 Edit/Write と初回 Bash をブロックし、事実の提示を要求する**。mvh-setup はファイルを多数生成するため、素朴に実行すると各生成でブロックされる。

対処手順：ブロックされたら、次の4点を応答本文で提示してから**同じ操作をそのまま再試行**する（2回目は通る）:

1. このファイルを参照する側のファイル名（例：`.claude/settings.json` の hooks エントリ、SKILL.md の References）
2. 同目的の既存ファイルがないことの確認結果
3. 読み書きするデータの構造（フィールド名・型。合成値で例示）
4. ユーザーの指示の原文

無人実行（cron・CI 等）では対話応答ができないため、環境変数で該当 hook を無効化する:

```bash
export ECC_DISABLED_HOOKS="pre:bash:gateguard-fact-force,pre:edit-write:gateguard-fact-force"
```

（通常セッションで常用しないこと。GateGuard の「書く前に調べる」強制は品質保護として機能している）

## セットアップ完了後の運用導線（ECC 環境）

mvh-setup は「静的な導入」で終わる。継続運用は ECC 側の機能に接続する:

- `/ecc:harness-audit` -- 定期採点。スコアカードより厳密な 42 チェック
- ECC `context-budget` スキル -- CLAUDE.md・rules・スキルのコンテキスト消費の監査
- `/ecc:hookify`（引数なし）-- 会話履歴から「hook で予防すべき挙動」を発見して hook 化
- ECC `config-gc` スキル -- `~/.claude` 側の定期掃除

これらを Item 10（Periodic audit schedule）の実行手段としてスコアカードの Next Steps に記載するとよい。
