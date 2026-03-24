# Error Message Guide

教育的エラーメッセージの書き方ガイド。このスキルで生成する全ルールのエラーメッセージは以下の原則に従う。

## Why Instructive Error Messages Matter

標準 lint エラー:
```
error: Import from restricted path '../infrastructure/database'
```

教育的 lint エラー:
```
ERROR: Cross-layer import from infrastructure layer detected.
WHY: Domain/service layers must not depend on infrastructure directly.
     This violates the Dependency Inversion Principle and makes the
     codebase harder to test and refactor. See ADR-005.
FIX: Import via the domain interface instead.
EXAMPLE:
  // Bad:
  import { PrismaClient } from '../infrastructure/prisma'
  // Good:
  import { UserRepository } from '../domain/repositories'
```

AI エージェントが後者のエラーに遭遇した場合、即座に：
1. 何が間違っているかを理解する（ERROR）
2. なぜそのルールがあるかを理解する（WHY）
3. 具体的にどう修正すべきかを知る（FIX + EXAMPLE）

これにより、エージェントは追加の質問なしに自己修正できる。

---

## Mandatory Structure

全エラーメッセージは以下の 4 セクションを含む：

### 1. ERROR (何が間違っているか)

```
ERROR: <簡潔な問題の説明> [オプション: file:line]
```

**ルール**:
- 1 行で問題を正確に説明する
- 技術的に正確であること（推測ではなく事実）
- 違反したコードの具体的な部分を特定する
- 可能であればメタ変数を使って具体的な名前を表示する

**良い例**:
```
ERROR: Default export detected in UserService.
ERROR: Domain layer imports from infrastructure layer.
ERROR: Error class 'NotFound' does not end with "Error".
ERROR: SQL query built with string interpolation.
ERROR: Possible hardcoded secret in variable 'API_KEY'.
```

**悪い例**:
```
ERROR: Bad import.                    # 曖昧すぎる
ERROR: This is not allowed.           # 何が許可されていないか不明
ERROR: Fix this.                      # 何を修正すべきか不明
```

### 2. WHY (なぜこのルールが存在するか)

```
WHY: <ルールの理由> [オプション: ADR/ドキュメントへのリンク]
```

**ルール**:
- ルールが存在する技術的・ビジネス的理由を説明する
- 違反した場合の具体的な結果を述べる
- 可能であれば ADR（Architecture Decision Record）にリンクする
- CWE（Common Weakness Enumeration）番号を含める（セキュリティルールの場合）

**良い例**:
```
WHY: Named exports are grep-able. AI agents and developers can search for
     exact symbol names across the codebase. Default exports allow arbitrary
     renaming at import site, making search unreliable.

WHY: Domain must not depend on infrastructure (Dependency Inversion).
     Domain defines interfaces; infrastructure implements them.
     Reversing this makes domain untestable and tightly coupled. See ADR-005.

WHY: Hardcoded secrets get committed to version control and are
     extremely difficult to rotate once exposed (CWE-798).
```

**悪い例**:
```
WHY: Because it's bad.                     # 理由になっていない
WHY: Team convention.                      # なぜその convention なのか
WHY: Linter says so.                       # 循環論法
```

### 3. FIX (具体的な修正手順)

```
FIX: <具体的な修正手順>
```

**ルール**:
- 具体的で実行可能な手順を提供する
- 1-3 ステップに収める
- コード変更が必要な場合は EXAMPLE セクションで示す
- 代替案がある場合は列挙する

**良い例**:
```
FIX: Convert to named export.

FIX: Define an interface in domain/repositories/ and import that instead.

FIX: Use environment variables or a secret manager.
     1. Remove the hardcoded value
     2. Add the variable to .env (and .env.example)
     3. Read via process.env.VARIABLE_NAME
```

**悪い例**:
```
FIX: Fix the code.                        # 具体性がない
FIX: Don't do this.                       # 代替案がない
FIX: Rewrite the module.                  # 過度に大きなスコープ
```

### 4. EXAMPLE (コード例)

```
EXAMPLE:
  // Bad:
  <違反コード>
  // Good:
  <正しいコード>
```

**ルール**:
- Bad と Good の両方を必ず含める
- 最小限のコードで違いを示す
- 実際のプロジェクトで使われそうなコードにする
- メタ変数を使える場合は、ユーザーの実際のコードに近い例にする

**良い例**:
```
EXAMPLE:
  // Bad:
  export default class UserService { }
  // Good:
  export class UserService { }

EXAMPLE:
  // Bad:
  import { PrismaClient } from '../infrastructure/prisma'
  // Good:
  import { UserRepository } from '../domain/repositories'

EXAMPLE:
  # Bad:
  API_KEY = 'sk-abc123...'
  # Good:
  API_KEY = os.environ['API_KEY']
```

---

## Writing Checklist

エラーメッセージを書く前に確認：

- [ ] ERROR は 1 行で問題を正確に述べているか
- [ ] WHY は技術的な理由を含んでいるか（「convention だから」は不十分）
- [ ] WHY は違反の結果（リスク）を述べているか
- [ ] FIX は具体的で実行可能か
- [ ] EXAMPLE は Bad と Good の両方を含むか
- [ ] EXAMPLE は実際のコードに近いか
- [ ] セキュリティルールの場合、CWE 番号を含んでいるか
- [ ] ADR が存在する場合、リンクしているか

---

## Language-Specific Formatting

### TypeScript/JavaScript

```
// Bad: / // Good: コメントスタイル
```

### Python

```
# Bad: / # Good: コメントスタイル
```

### Go

```
// Bad: / // Good: コメントスタイル（Go も // を使用）
```

### Rust

```
// Bad: / // Good: コメントスタイル（Rust も // を使用）
```

---

## ADR Integration

ADR（Architecture Decision Record）が存在する場合、WHY セクションでリンクする：

```
WHY: Domain must not depend on infrastructure (Dependency Inversion).
     See ADR-005: https://github.com/org/repo/docs/adr/005-dependency-direction.md
```

ADR が存在しない場合：

```
WHY: Domain must not depend on infrastructure (Dependency Inversion).
     Consider creating an ADR to document this architectural decision.
```

---

## Message Length Guidelines

| Section | Target Length | Max Length |
|---------|-------------|-----------|
| ERROR | 1 line | 1 line |
| WHY | 2-4 lines | 6 lines |
| FIX | 1-3 lines | 5 lines |
| EXAMPLE | 4-6 lines | 10 lines |
| **Total** | **8-14 lines** | **22 lines** |

エラーメッセージが長すぎるとノイズになる。簡潔さと情報量のバランスを取る。

---

## Anti-Patterns

### 1. Blame-oriented messages

```
# Bad
ERROR: You wrote a bad import.
WHY: You should know better.

# Good
ERROR: Cross-layer import from infrastructure layer.
WHY: Domain layers must not depend on infrastructure.
```

### 2. Vague messages

```
# Bad
ERROR: Style violation.
FIX: Fix it.

# Good
ERROR: Error class 'NotFound' does not end with "Error".
FIX: Rename to NotFoundError.
```

### 3. Missing alternatives

```
# Bad
ERROR: eval() is not allowed.
FIX: Don't use eval().

# Good
ERROR: eval() detected -- enables arbitrary code execution.
FIX: Use safe alternatives:
  - JSON.parse() for data parsing
  - new Map() for dynamic key-value access
```

### 4. Over-engineering the message

```
# Bad (too long, too many options)
ERROR: Default export detected.
WHY: [20 lines of explanation about module systems, CommonJS vs ESM,
     tree-shaking, IDE support, webpack configuration...]
FIX: [10 different approaches to fixing this...]

# Good (focused, actionable)
ERROR: Default export detected.
WHY: Named exports are grep-able. Agents search for exact symbol names.
FIX: Convert to named export.
EXAMPLE:
  // Bad: export default class UserService { }
  // Good: export class UserService { }
```

---

## Template for New Rules

新しいルールのエラーメッセージを書く際のテンプレート：

```
message: |
  ERROR: <1行で問題を記述。メタ変数 '$NAME' 等で具体性を出す>
  WHY: <2-4行で理由を説明。CWE番号やADRリンクを含む>
  FIX: <1-3行で修正方法を説明>
  EXAMPLE:
    // Bad:
    <違反コード — ユーザーが実際に書きそうなもの>
    // Good:
    <正しいコード — 最小限の変更で修正したもの>
```
