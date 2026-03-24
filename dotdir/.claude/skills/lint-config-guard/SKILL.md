---
name: lint-config-guard
description: >
  Linter/formatter設定ファイルをAIエージェントの編集から保護するPreToolUseフックを生成する。
  エージェントがlintエラーに遭遇した際、コードを修正する代わりにlinter設定を緩めようとする問題を防止する。
  使用タイミング：(1)「protect linter config」「lint guard」、(2)「prevent config tampering」、
  (3) エージェントが.eslintrc, biome.json, ruff.toml等を変更しようとした場合、
  (4)「agent modifying eslintrc」「stop agent from disabling rules」、
  (5) エージェントがlinterルールを弱めていることに気づいた場合。
---

# Lint Config Guard

AIエージェントがlinter/formatter/type-checker設定ファイルを変更することを構造的に防止するPreToolUseフックを生成するスキル。

## 設計原則

> "Give humans flexibility, give agents strictness."

- 人間はいつでも設定ファイルを直接編集できる
- エージェントは構造的に品質ゲートを弱めることができない
- エラーメッセージはブロックするだけでなく、正しい対処法を教える

## Workflow

### Step 1: プロジェクトの設定ファイルを検出

プロジェクトルートをスキャンし、保護対象の設定ファイルを特定する。

```bash
# プロジェクトルートで実行
find . -maxdepth 3 -type f \( \
  -name '.eslintrc' -o -name '.eslintrc.*' -o -name 'eslint.config.*' -o -name '.eslintignore' \
  -o -name 'biome.json' -o -name 'biome.jsonc' \
  -o -name '.prettierrc' -o -name '.prettierrc.*' -o -name 'prettier.config.*' \
  -o -name 'oxlint.*' -o -name '.oxlintrc.*' \
  -o -name 'ruff.toml' -o -name '.pylintrc' -o -name 'pylintrc' \
  -o -name 'mypy.ini' \
  -o -name '.golangci.yml' -o -name '.golangci.yaml' \
  -o -name 'clippy.toml' -o -name '.clippy.toml' \
  -o -name 'tsconfig.json' -o -name 'tsconfig.*.json' \
  -o -name 'lefthook.yml' -o -name 'lefthook-local.yml' \
\) 2>/dev/null
```

また、以下のファイル内のセクションも保護対象:
- `pyproject.toml` (`[tool.ruff]`, `[tool.mypy]` セクション)
- `setup.cfg` (`[mypy]` セクション)
- `Cargo.toml` (`[lints]` セクション)
- `.husky/` ディレクトリ内の全ファイル

保護対象ファイルの完全なリストは [references/protected-configs.md](references/protected-configs.md) を参照。

### Step 2: PreToolUse フックスクリプトを生成

検出したファイルに基づいて、フックスクリプトを生成する。テンプレートは [references/hook-script-template.md](references/hook-script-template.md) を参照。

スクリプトの配置先:

```
<project-root>/.claude/scripts/hooks/lint-config-guard.sh
```

```bash
mkdir -p .claude/scripts/hooks
# hook-script-template.md のテンプレートに基づいてスクリプトを生成
chmod +x .claude/scripts/hooks/lint-config-guard.sh
```

### Step 3: settings.json にフックを登録

`.claude/settings.json` の `hooks.PreToolUse` 配列にエントリを追加する。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/scripts/hooks/lint-config-guard.sh \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

**重要**: 既存の `settings.json` がある場合はマージすること。上書きしない。

### Step 4: 動作確認

フックが正しく動作するかテストする。

```bash
# テスト: 保護対象ファイルへの書き込みをシミュレート
echo '{"tool_name":"Edit","tool_input":{"file_path":".eslintrc.js","old_string":"rules: {}","new_string":"rules: {}"}}' \
  | .claude/scripts/hooks/lint-config-guard.sh
# 期待結果: exit code 2, stderrにBLOCKEDメッセージ
```

## Edge Cases

### v1 の方針: 全編集をブロック

シンプルさを優先し、v1 では保護対象ファイルへの全ての編集をブロックする。

- ルールの追加（厳格化）もブロックされる
- ユーザーが明示的に許可する場合は、フックを一時的に無効化するか、ファイルを直接編集する

### 将来の拡張 (v2)

- diff の内容を解析し、ルールの削除/弱体化のみをブロック
- ルールの追加（厳格化）は許可
- `// lint-config-guard: allow` コメントによる一時的な許可

### pyproject.toml / setup.cfg / Cargo.toml

これらのファイルはlint設定以外のセクションも含むため、v1 ではファイル全体をブロックする。
ユーザーへのメッセージで、lint設定以外のセクションの編集が必要な場合は直接編集するよう案内する。

### .husky/ ディレクトリ

`.husky/` 内の全ファイルを保護対象とする。Git hooks はコード品質ゲートの一部であり、エージェントが変更すべきではない。

## エラーメッセージの設計

ブロック時のメッセージは「教える」ことを重視する:

```
BLOCKED: Cannot modify linter configuration [file]
WHY: Modifying linter rules to suppress errors leads to accumulated technical debt.
     The lint rule exists for a reason -- fix the code instead.
FIX: Address the lint violation in the source file.
     If the rule is genuinely wrong for this project, ask the user to modify the config.
```
