@AGENTS.md

# Claude Code 固有の指示

上の共通方針（Codex・agy と共有）に加えて、Claude Code では次に従う。

## 日本語の書き方

- `@japanese-style-guide.md` の禁止表現を避け、推奨表現を使う
- ユーザーが表現へ不満・言い換え要望を示したら、応答前に `japanese-style-guide.md` の対応表へ1行追記する（再発防止）

## 依頼の解釈（Intent Gate）

- 依頼が曖昧（複数解釈可・成功基準不明・影響範囲不明）なら、着手前に解釈・前提・成功基準を1〜3行で宣言する
- 解釈の分岐が結果を大きく変えるときは AskUserQuestion で確認（推測で大きな作業を進めない）
- 依頼の解釈は decision-patterns.md の判断パターンに従う

## サブエージェントの費用

- 並列サブエージェントはトークン約15倍。単純タスクは1体・ツール呼び出し3〜10回

## 品質階段（検証の強さの使い分け）

- 設計判断の分岐・確信の持てない技術判断・不可逆操作の前 → second-opinion スキル（Codex・agy 外注。Claude トークン温存）
- 重要タスク（不可逆・本番反映・論文の数値）の完了前 → adversarial-verifier Agent で反証検証
- 最重要の難問のみ → deep-reason Workflow（agent 7体分のコスト。起動前にコストを一言明示）
- 実装・調査の単体作業も Codex/agy への委譲を優先し、Claude 並列は高価値タスク限定
- アドバイザー（Fable）に相談する：大きな計画に着手を決める前、同じエラーが2回目に出たとき、長時間のタスクを完了と報告する前

@RTK.md
@japanese-style-guide.md
@decision-patterns.md
