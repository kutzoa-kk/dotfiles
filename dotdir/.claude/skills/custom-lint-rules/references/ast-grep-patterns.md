# ast-grep Universal Patterns

ast-grep はどの言語でも使えるユニバーサル lint ツール。言語固有ツールが複雑すぎる・利用不可の場合のフォールバックとして使用する。

## Setup

```bash
# Install ast-grep via Homebrew or npm
# See: https://ast-grep.github.io/guide/quick-start.html

# Initialize config
cat > sgconfig.yml << 'EOF'
ruleDirs:
  - .ast-grep/rules
EOF

mkdir -p .ast-grep/rules
```

## Running

```bash
# Scan entire project
ast-grep scan

# Scan with specific rule
ast-grep scan --rule .ast-grep/rules/no-default-export.yml

# Scan specific directory
ast-grep scan --rule .ast-grep/rules/no-default-export.yml src/

# Test rules
ast-grep test
```

## Rule File Structure

```yaml
id: rule-id                    # Unique identifier
language: typescript           # typescript, python, go, rust, java, etc.
severity: error                # error, warning, hint, info
rule:
  pattern: <AST pattern>       # What to match
  # Optional combinators:
  any: [...]                   # Match ANY of these patterns (OR)
  all: [...]                   # Match ALL of these patterns (AND)
  not: <pattern>               # Must NOT match this
  has: <pattern>               # Must contain this as descendant
  inside: <pattern>            # Must be inside this ancestor
  follows: <pattern>           # Must follow this sibling
  precedes: <pattern>          # Must precede this sibling
constraints:                   # Regex constraints on metavariables
  $VAR:
    regex: 'pattern'
  $VAR2:
    not:
      regex: 'pattern'
fix: <replacement pattern>     # Optional auto-fix
message: |                     # The instructive error message
  ERROR: ...
  WHY: ...
  FIX: ...
  EXAMPLE: ...
```

## Metavariable Reference

| Syntax | Meaning | Example |
|--------|---------|---------|
| `$VAR` | Single AST node | `$NAME`, `$EXPR` |
| `$$$VARS` | Zero or more nodes | `$$$ARGS`, `$$$BODY` |
| `$$VARS` | One or more nodes (non-greedy) | `$$PARAMS` |

---

## Pattern Cookbook: Grep-ability

### No Default Export (TypeScript)

```yaml
id: no-default-export
language: typescript
severity: error
rule:
  any:
    - pattern: export default $EXPR
    - pattern: export default function $NAME($$$PARAMS) { $$$BODY }
    - pattern: export default class $NAME { $$$BODY }
message: |
  ERROR: Default export detected.
  WHY: Named exports are grep-able. Agents search for exact symbol names.
       Default exports allow arbitrary renaming at import, breaking search.
  FIX: Convert to named export.
  EXAMPLE:
    // Bad: export default class UserService { }
    // Good: export class UserService { }
```

### Consistent Error Suffix (TypeScript)

```yaml
id: error-class-suffix
language: typescript
severity: error
rule:
  pattern: class $NAME extends Error { $$$BODY }
constraints:
  NAME:
    not:
      regex: '.+Error$'
message: |
  ERROR: Error subclass '$NAME' does not end with "Error".
  WHY: Consistent "XxxError" naming lets agents grep for all error types.
  FIX: Rename to ${NAME}Error.
  EXAMPLE:
    // Bad: class NotFound extends Error { }
    // Good: class NotFoundError extends Error { }
```

### Go Error Variable Convention

```yaml
id: error-var-naming-go
language: go
severity: error
rule:
  pattern: var $NAME = errors.New($MSG)
constraints:
  NAME:
    not:
      regex: '^Err[A-Z]'
message: |
  ERROR: Error variable '$NAME' does not follow ErrXxx convention.
  WHY: Go convention is ErrXxx for sentinel errors. Enables
       `grep -r "^var Err" .` to find all error definitions.
  FIX: Rename to Err<Description>.
  EXAMPLE:
    // Bad: var notFound = errors.New("not found")
    // Good: var ErrNotFound = errors.New("not found")
```

### Python __all__ Declaration

```yaml
id: module-needs-all
language: python
severity: warning
rule:
  kind: module
  not:
    has:
      pattern: __all__ = [$$$NAMES]
message: |
  ERROR: Module missing __all__ declaration.
  WHY: __all__ explicitly declares the public API, making it grep-able
       and preventing accidental export of internal symbols.
  FIX: Add __all__ listing all public symbols.
  EXAMPLE:
    # Bad: (no __all__)
    # Good: __all__ = ['UserService', 'UserRepository']
```

---

## Pattern Cookbook: Architecture Boundaries

### Domain Cannot Import Infrastructure (TypeScript)

```yaml
id: domain-no-infra-import
language: typescript
severity: error
rule:
  pattern: import { $$$NAMES } from '$PATH'
constraints:
  PATH:
    regex: '(\.\.\/)+infrastructure\/'
message: |
  ERROR: Domain layer imports from infrastructure.
  WHY: Dependency Inversion Principle: domain defines interfaces,
       infrastructure implements them. Never the reverse.
  FIX: Import the interface from domain/ instead.
  EXAMPLE:
    // Bad: import { PrismaUserRepo } from '../../infrastructure/prisma'
    // Good: import { UserRepository } from '../repositories'
```

### Service Cannot Import API (TypeScript)

```yaml
id: service-no-api-import
language: typescript
severity: error
rule:
  pattern: import { $$$NAMES } from '$PATH'
constraints:
  PATH:
    regex: '(\.\.\/)+api\/'
message: |
  ERROR: Service layer imports from API/presentation layer.
  WHY: Services must be reusable across entry points (REST, GraphQL, CLI).
  FIX: Define shared types in domain/ or a shared/ layer.
  EXAMPLE:
    // Bad: import { UserRequest } from '../../api/types'
    // Good: import { CreateUserInput } from '../domain/types'
```

### No Cross-Feature Internal Import (TypeScript)

```yaml
id: no-feature-internal-import
language: typescript
severity: error
rule:
  pattern: import { $$$NAMES } from '$PATH'
constraints:
  PATH:
    regex: '\.\./[a-z-]+/(services|repositories|entities|infrastructure)/'
message: |
  ERROR: Importing internal path of another feature module.
  WHY: Feature modules expose public APIs via barrel files (index.ts).
       Importing internals creates hidden coupling.
  FIX: Import from the feature's barrel file.
  EXAMPLE:
    // Bad: import { UserService } from '../users/services/user.service'
    // Good: import { UserService } from '../users'
```

### Go Internal Package Boundary

```yaml
id: no-internal-cross-import-go
language: go
severity: error
rule:
  pattern: import "$PKG"
constraints:
  PKG:
    regex: '.*/internal/(?!shared).*'
message: |
  ERROR: Importing another module's internal package.
  WHY: internal/ packages in Go are private to their parent module.
  FIX: Export via a public package or shared interface.
  EXAMPLE:
    // Bad: import "myapp/users/internal/repo"
    // Good: import "myapp/users"
```

### Python Domain-Infrastructure Boundary

```yaml
id: domain-no-infra-python
language: python
severity: error
rule:
  any:
    - pattern: from infrastructure.$MODULE import $$$NAMES
    - pattern: import infrastructure.$MODULE
message: |
  ERROR: Domain layer imports from infrastructure.
  WHY: Domain must not depend on infrastructure (Dependency Inversion).
  FIX: Define an abstract interface in domain/ and implement in infrastructure/.
  EXAMPLE:
    # Bad: from infrastructure.database import SessionLocal
    # Good: from domain.repositories import UserRepository
```

---

## Pattern Cookbook: Security

### No Hardcoded Secrets (Multi-language)

TypeScript:
```yaml
id: no-hardcoded-secret-ts
language: typescript
severity: error
rule:
  any:
    - pattern: "const $NAME = '$VALUE'"
    - pattern: "let $NAME = '$VALUE'"
    - pattern: 'const $NAME = "$VALUE"'
    - pattern: 'let $NAME = "$VALUE"'
constraints:
  NAME:
    regex: '(?i)(api_?key|secret|token|password|auth_?token|private_?key|credential|conn_?string)'
  VALUE:
    regex: '.{8,}'
message: |
  ERROR: Possible hardcoded secret in '$NAME'.
  WHY: Hardcoded secrets persist in git history (CWE-798).
  FIX: Use environment variables or a secret manager.
  EXAMPLE:
    // Bad: const API_KEY = 'sk-abc123...'
    // Good: const API_KEY = process.env.API_KEY!
```

Python:
```yaml
id: no-hardcoded-secret-py
language: python
severity: error
rule:
  any:
    - pattern: $NAME = '$VALUE'
    - pattern: $NAME = "$VALUE"
constraints:
  NAME:
    regex: '(?i)(api_?key|secret|token|password|auth_?token|private_?key|credential|conn_?string)'
  VALUE:
    regex: '.{8,}'
message: |
  ERROR: Possible hardcoded secret in '$NAME'.
  WHY: Hardcoded secrets are CWE-798 violations.
  FIX: Use environment variables.
  EXAMPLE:
    # Bad: API_KEY = 'sk-abc123...'
    # Good: API_KEY = os.environ['API_KEY']
```

Go:
```yaml
id: no-hardcoded-secret-go
language: go
severity: error
rule:
  any:
    - pattern: 'var $NAME = "$VALUE"'
    - pattern: 'const $NAME = "$VALUE"'
    - pattern: '$NAME := "$VALUE"'
constraints:
  NAME:
    regex: '(?i)(apiKey|secret|token|password|authToken|privateKey|credential|connString)'
  VALUE:
    regex: '.{8,}'
message: |
  ERROR: Possible hardcoded secret in '$NAME'.
  WHY: Hardcoded secrets are CWE-798 violations.
  FIX: Use os.Getenv() or config.
  EXAMPLE:
    // Bad: var apiKey = "sk-abc123..."
    // Good: var apiKey = os.Getenv("API_KEY")
```

### No Dangerous Execution (TypeScript)

```yaml
id: no-dangerous-exec-ts
language: typescript
severity: error
rule:
  any:
    - pattern: eval($$$ARGS)
    - pattern: new Function($$$ARGS)
    - pattern: $EL.innerHTML = $VALUE
    - pattern: document.write($$$ARGS)
message: |
  ERROR: Dangerous code execution/injection pattern.
  WHY: eval, new Function, innerHTML, document.write enable XSS (CWE-79)
       and arbitrary code execution (CWE-95).
  FIX: Use safe alternatives.
  EXAMPLE:
    // Bad: eval(userInput); el.innerHTML = data
    // Good: JSON.parse(userInput); el.textContent = data
```

### No eval (Python)

```yaml
id: no-eval-python
language: python
severity: error
rule:
  any:
    - pattern: eval($$$ARGS)
    - pattern: exec($$$ARGS)
message: |
  ERROR: Dangerous code execution (eval/exec).
  WHY: eval/exec execute arbitrary code, enabling injection attacks.
  FIX: Use ast.literal_eval() or json.loads() for data parsing.
  EXAMPLE:
    # Bad: result = eval(user_input)
    # Good: result = json.loads(user_input)
```

### SQL Injection Prevention (TypeScript)

```yaml
id: no-sql-concat-ts
language: typescript
severity: error
rule:
  any:
    - pattern: $DB.query(`$$$SQL${$$$VARS}$$$REST`)
    - pattern: $DB.query($A + $B)
    - pattern: $DB.execute(`$$$SQL${$$$VARS}$$$REST`)
message: |
  ERROR: SQL query with string interpolation/concatenation.
  WHY: SQL injection (CWE-89) -- one of the most exploited vulnerabilities.
  FIX: Use parameterized queries.
  EXAMPLE:
    // Bad: db.query(`SELECT * FROM users WHERE id = ${id}`)
    // Good: db.query('SELECT * FROM users WHERE id = $1', [id])
```

### SQL Injection Prevention (Go)

```yaml
id: no-sql-sprintf-go
language: go
severity: error
rule:
  any:
    - pattern: $DB.Query(fmt.Sprintf($$$ARGS))
    - pattern: $DB.Exec(fmt.Sprintf($$$ARGS))
    - pattern: $DB.QueryRow(fmt.Sprintf($$$ARGS))
message: |
  ERROR: SQL query with fmt.Sprintf.
  WHY: SQL injection (CWE-89) via string formatting.
  FIX: Use parameterized queries.
  EXAMPLE:
    // Bad: db.Query(fmt.Sprintf("SELECT * FROM users WHERE id = %d", id))
    // Good: db.Query("SELECT * FROM users WHERE id = $1", id)
```

### SQL Injection Prevention (Python)

```yaml
id: no-sql-fstring-python
language: python
severity: error
rule:
  any:
    - pattern: cursor.execute(f"$$$SQL")
    - pattern: cursor.execute("$SQL" + $VAR)
    - pattern: cursor.execute("$SQL" % $VAR)
    - pattern: cursor.execute("$SQL".format($$$ARGS))
message: |
  ERROR: SQL query with string formatting.
  WHY: SQL injection (CWE-89).
  FIX: Use parameterized queries with %s or ? placeholders.
  EXAMPLE:
    # Bad: cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    # Good: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

---

## Advanced: Combining Patterns

ast-grep supports boolean combinators for complex rules:

```yaml
id: async-without-try-catch
language: typescript
severity: warning
rule:
  all:                          # ALL conditions must match
    - pattern: await $EXPR      # Await expression
    - not:                      # NOT inside a try-catch
        inside:
          kind: try_statement
    - inside:                   # Inside an async function
        any:
          - kind: function_declaration
          - kind: arrow_function
          - kind: method_definition
message: |
  ERROR: Unhandled await expression outside try-catch.
  WHY: Unhandled async errors crash the process in Node.js.
  FIX: Wrap in try-catch or use .catch() handler.
```

## Testing Rules

### Separate test directory

```
.ast-grep/
  rules/
    no-default-export.yml
  tests/
    no-default-export/
      valid.ts        # Should NOT trigger
      invalid.ts      # Should trigger
```

### Manual verification

```bash
# Create a test file with violations
echo 'export default class Foo {}' > /tmp/test-violation.ts

# Run rule against it
ast-grep scan --rule .ast-grep/rules/no-default-export.yml /tmp/test-violation.ts
```
