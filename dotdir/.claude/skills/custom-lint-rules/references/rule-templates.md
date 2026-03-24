# Rule Templates

カテゴリ×ツール別のルールテンプレート集。プロジェクト固有の値（パス、型名等）を埋めて使用する。

---

## 1. Grep-ability（検索発見性）

### 1.1 No Default Export

**目的**: named export を強制し、エージェントが正確な名前で grep できるようにする。

#### ast-grep (TypeScript)

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
  WHY: Named exports are grep-able. AI agents and developers can search for
       exact symbol names across the codebase. Default exports allow arbitrary
       renaming at import site, making search unreliable.
  FIX: Convert to named export.
  EXAMPLE:
    // Bad:
    export default class UserService { }
    // Good:
    export class UserService { }
```

#### ESLint

```javascript
// eslint-rules/rules/no-default-export.js
module.exports = {
  meta: {
    type: "suggestion",
    docs: { description: "Disallow default exports for grep-ability" },
    messages: {
      noDefaultExport: [
        "ERROR: Default export detected.",
        "WHY: Named exports are grep-able. AI agents and developers can search",
        "     for exact symbol names. Default exports allow arbitrary renaming",
        "     at import site, making search unreliable.",
        "FIX: Convert to named export.",
        "EXAMPLE:",
        "  // Bad: export default class UserService { }",
        "  // Good: export class UserService { }",
      ].join("\n"),
    },
    schema: [],
  },
  create(context) {
    return {
      ExportDefaultDeclaration(node) {
        context.report({ node, messageId: "noDefaultExport" });
      },
    };
  },
};
```

### 1.2 Consistent Error Classes

**目的**: エラー型を統一し、grep でエラーハンドリングを追跡可能にする。

#### ast-grep (TypeScript)

```yaml
id: error-class-naming
language: typescript
severity: error
rule:
  pattern: class $NAME extends Error { $$$BODY }
constraints:
  NAME:
    not:
      regex: '.+Error$'
message: |
  ERROR: Error class name must end with "Error".
  WHY: Consistent error naming enables grep-based error tracking.
       `grep -r "NotFoundError" .` finds all throw/catch sites instantly.
  FIX: Rename the class to end with "Error".
  EXAMPLE:
    // Bad:
    class NotFound extends Error { }
    // Good:
    class NotFoundError extends Error { }
```

### 1.3 Explicit DTO Types

**目的**: inline type の代わりに名前付き DTO を強制し、型定義を grep 可能にする。

#### ast-grep (TypeScript)

```yaml
id: no-inline-request-type
language: typescript
severity: warning
rule:
  pattern: "async $NAME($PARAM: { $$$FIELDS })"
message: |
  ERROR: Inline type in function parameter.
  WHY: Named DTO types are grep-able and reusable. Inline types cannot be
       searched by name, making it hard to find all usages of a data shape.
  FIX: Extract to a named interface or type alias.
  EXAMPLE:
    // Bad:
    async createUser(data: { name: string; email: string }) { }
    // Good:
    async createUser(data: CreateUserDto) { }
```

### 1.4 Go Error Variable Convention

#### ast-grep (Go)

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
  WHY: Go convention is ErrXxx for sentinel errors. This enables
       `grep -r "^var Err" .` to find all error definitions.
  FIX: Rename to Err<Description>.
  EXAMPLE:
    // Bad: var notFound = errors.New("not found")
    // Good: var ErrNotFound = errors.New("not found")
```

---

## 2. Glob-ability（構造予測性）

### 2.1 File Naming Convention

**目的**: ファイルが予測可能な命名に従うことを保証する。

#### ESLint (custom rule)

```javascript
// eslint-rules/rules/file-naming-convention.js
const path = require("path");

const CONVENTIONS = {
  controllers: /\.controller\.[tj]sx?$/,
  services: /\.service\.[tj]sx?$/,
  repositories: /\.repository\.[tj]sx?$/,
  dtos: /\.dto\.[tj]sx?$/,
  entities: /\.entity\.[tj]sx?$/,
};

module.exports = {
  meta: {
    type: "suggestion",
    docs: { description: "Enforce file naming conventions by directory" },
    messages: {
      wrongNaming: [
        "ERROR: File in '{{dir}}' directory does not match naming convention.",
        "WHY: Consistent naming enables glob-based file discovery.",
        "     Agents use patterns like `src/**/*.service.ts` to find all services.",
        "FIX: Rename this file to match the pattern: {{pattern}}",
        "EXAMPLE:",
        "  // Bad: src/users/services/handler.ts",
        "  // Good: src/users/services/users.service.ts",
      ].join("\n"),
    },
    schema: [],
  },
  create(context) {
    const filename = context.getFilename();
    const dir = path.basename(path.dirname(filename));

    return {
      Program(node) {
        const convention = CONVENTIONS[dir];
        if (convention && !convention.test(filename)) {
          context.report({
            node,
            messageId: "wrongNaming",
            data: { dir, pattern: convention.toString() },
          });
        }
      },
    };
  },
};
```

### 2.2 Co-location Check (Shell Script)

**目的**: テストファイルがソースファイルの隣にあることを確認する。

```bash
#!/bin/bash
# check-colocation.sh
MISSING=0

for src in $(find src -name "*.ts" ! -name "*.test.ts" ! -name "*.spec.ts" \
  ! -name "*.d.ts" ! -name "index.ts" ! -path "*/node_modules/*"); do
  test_file="${src%.ts}.test.ts"
  spec_file="${src%.ts}.spec.ts"
  if [[ ! -f "$test_file" && ! -f "$spec_file" ]]; then
    echo "ERROR: No co-located test for $src"
    echo "WHY: Co-located tests enable glob discovery: glob('**/*.test.ts')"
    echo "FIX: Create $test_file"
    MISSING=$((MISSING + 1))
  fi
done

echo "Missing co-located tests: $MISSING"
exit $([[ $MISSING -gt 0 ]] && echo 1 || echo 0)
```

---

## 3. Architecture Boundaries（依存方向）

### 3.1 No Cross-Layer Import (TypeScript)

#### ast-grep

```yaml
id: no-domain-to-infra-import
language: typescript
severity: error
rule:
  pattern: import { $$$NAMES } from '$PATH'
constraints:
  PATH:
    regex: '(\.\.\/)+infrastructure\/'
message: |
  ERROR: Domain layer imports from infrastructure layer.
  WHY: Domain must not depend on infrastructure (Dependency Inversion).
       Domain defines interfaces; infrastructure implements them.
       Reversing this makes domain untestable and tightly coupled.
  FIX: Define an interface in domain/repositories/ and import that instead.
  EXAMPLE:
    // Bad:
    import { PrismaClient } from '../infrastructure/prisma'
    // Good:
    import { UserRepository } from './repositories/user.repository'
```

```yaml
id: no-service-to-api-import
language: typescript
severity: error
rule:
  pattern: import { $$$NAMES } from '$PATH'
constraints:
  PATH:
    regex: '(\.\.\/)+api\/'
message: |
  ERROR: Service layer imports from API layer.
  WHY: Services must not depend on API/presentation layer.
       Services contain business logic reusable across multiple
       entry points (REST, GraphQL, CLI, queue workers).
  FIX: Move shared types to a common location or pass data as parameters.
  EXAMPLE:
    // Bad:
    import { UserRequest } from '../api/types'
    // Good:
    import { CreateUserInput } from '../domain/types'
```

#### ESLint (custom rule)

```javascript
// eslint-rules/rules/layer-imports.js
const LAYER_ORDER = ["api", "service", "domain", "infrastructure"];

function getLayer(filePath) {
  for (const layer of LAYER_ORDER) {
    if (filePath.includes("/" + layer + "/") || filePath.includes("\\" + layer + "\\")) {
      return layer;
    }
  }
  return null;
}

const ALLOWED_IMPORTS = {
  api: ["service", "domain"],
  service: ["domain"],
  domain: [],
  infrastructure: ["domain"],
};

module.exports = {
  meta: {
    type: "problem",
    docs: { description: "Enforce layer import boundaries" },
    messages: {
      crossLayerImport: [
        "ERROR: {{sourceLayer}} layer imports from {{targetLayer}} layer.",
        "WHY: Layer boundaries enforce the dependency rule:",
        "     API -> Service -> Domain <- Infrastructure.",
        "     Violating this creates tight coupling and circular dependencies.",
        "FIX: Import from an allowed layer instead.",
        "     {{sourceLayer}} can import from: {{allowed}}.",
        "EXAMPLE:",
        "  // Bad: import from '{{badPath}}'",
        "  // Good: import from domain interfaces or allowed layers",
      ].join("\n"),
    },
    schema: [],
  },
  create(context) {
    const sourceLayer = getLayer(context.getFilename());
    if (!sourceLayer) return {};

    return {
      ImportDeclaration(node) {
        const importPath = node.source.value;
        const resolved = require("path").resolve(
          require("path").dirname(context.getFilename()),
          importPath
        );
        const targetLayer = getLayer(resolved);

        if (
          targetLayer &&
          targetLayer !== sourceLayer &&
          !ALLOWED_IMPORTS[sourceLayer]?.includes(targetLayer)
        ) {
          context.report({
            node,
            messageId: "crossLayerImport",
            data: {
              sourceLayer,
              targetLayer,
              allowed: (ALLOWED_IMPORTS[sourceLayer] || []).join(", ") || "none",
              badPath: importPath,
            },
          });
        }
      },
    };
  },
};
```

### 3.2 No Cross-Module Internal Import (TypeScript)

#### ast-grep

```yaml
id: no-cross-module-internal
language: typescript
severity: error
rule:
  pattern: import { $$$NAMES } from '$PATH'
constraints:
  PATH:
    regex: '\.\./[a-z-]+/(services|repositories|entities)/'
message: |
  ERROR: Importing internal module of another feature.
  WHY: Each feature module exposes a public API via its index.ts barrel.
       Importing internals creates hidden coupling between features,
       making them impossible to refactor independently.
  FIX: Import from the module's public barrel file (index.ts) instead.
  EXAMPLE:
    // Bad:
    import { UserService } from '../users/services/user.service'
    // Good:
    import { UserService } from '../users'
```

### 3.3 Go Layer Boundaries

#### golangci-lint (depguard)

```yaml
# .golangci.yml
linters-settings:
  depguard:
    rules:
      domain-no-infra:
        files:
          - "**/domain/**"
        deny:
          - pkg: "myapp/internal/infrastructure"
            desc: |
              ERROR: Domain imports infrastructure package.
              WHY: Domain must not depend on infrastructure (Dependency Inversion).
              FIX: Define an interface in domain/ and implement it in infrastructure/.
          - pkg: "database/sql"
            desc: |
              ERROR: Domain imports database/sql directly.
              WHY: Domain should be persistence-agnostic.
              FIX: Use repository interface defined in domain/repository.go.
```

### 3.4 Python Layer Boundaries

#### pylint custom checker

```python
# pylint_custom/checkers/layer_imports.py
import astroid
from pylint.checkers import BaseChecker

LAYER_ORDER = {"api": 0, "service": 1, "domain": 2, "infrastructure": 3}
ALLOWED = {
    "api": {"service", "domain"},
    "service": {"domain"},
    "domain": set(),
    "infrastructure": {"domain"},
}

class LayerImportChecker(BaseChecker):
    name = "layer-imports"
    msgs = {
        "C9001": (
            "ERROR: %s layer imports from %s layer.\n"
            "WHY: Layer boundaries enforce dependency direction.\n"
            "     API -> Service -> Domain <- Infrastructure.\n"
            "FIX: Import from an allowed layer. %s can import from: %s.",
            "cross-layer-import",
            "Cross-layer import violates architecture boundaries.",
        ),
    }

    def visit_importfrom(self, node: astroid.ImportFrom):
        if not node.modname:
            return
        source_layer = self._detect_layer(node.root().file)
        target_layer = self._detect_layer_from_module(node.modname)
        if (
            source_layer
            and target_layer
            and source_layer != target_layer
            and target_layer not in ALLOWED.get(source_layer, set())
        ):
            allowed = ", ".join(ALLOWED.get(source_layer, set())) or "none"
            self.add_message(
                "cross-layer-import",
                node=node,
                args=(source_layer, target_layer, source_layer, allowed),
            )

    @staticmethod
    def _detect_layer(filepath):
        for layer in LAYER_ORDER:
            if f"/{layer}/" in str(filepath):
                return layer
        return None

    @staticmethod
    def _detect_layer_from_module(modname):
        for layer in LAYER_ORDER:
            if f".{layer}." in modname or modname.startswith(f"{layer}."):
                return layer
        return None

def register(linter):
    linter.register_checker(LayerImportChecker(linter))
```

---

## 4. Security/Privacy

### 4.1 No Hardcoded Secrets

#### ast-grep (TypeScript)

```yaml
id: no-hardcoded-api-key
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
    regex: '(?i)(api_?key|secret|token|password|auth|credential)'
  VALUE:
    regex: '.{8,}'
message: |
  ERROR: Possible hardcoded secret in variable '$NAME'.
  WHY: Hardcoded secrets get committed to version control and are
       extremely difficult to rotate once exposed (CWE-798).
  FIX: Use environment variables or a secret manager.
  EXAMPLE:
    // Bad:
    const API_KEY = 'sk-abc123...'
    // Good:
    const API_KEY = process.env.API_KEY
```

#### ast-grep (Python)

```yaml
id: no-hardcoded-secret-python
language: python
severity: error
rule:
  any:
    - pattern: $NAME = '$VALUE'
    - pattern: $NAME = "$VALUE"
constraints:
  NAME:
    regex: '(?i)(api_?key|secret|token|password|auth|credential)'
  VALUE:
    regex: '.{8,}'
message: |
  ERROR: Possible hardcoded secret in variable '$NAME'.
  WHY: Hardcoded secrets in source code are CWE-798 violations.
       They persist in git history even after removal.
  FIX: Use environment variables or a secret manager.
  EXAMPLE:
    # Bad:
    API_KEY = 'sk-abc123...'
    # Good:
    API_KEY = os.environ['API_KEY']
```

#### ast-grep (Go)

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
  FIX: Use environment variables or config.
  EXAMPLE:
    // Bad: var apiKey = "sk-abc123..."
    // Good: var apiKey = os.Getenv("API_KEY")
```

### 4.2 No eval / Dangerous Execution

#### ast-grep (TypeScript)

```yaml
id: no-eval
language: typescript
severity: error
rule:
  any:
    - pattern: eval($$$ARGS)
    - pattern: new Function($$$ARGS)
    - pattern: $EL.innerHTML = $VALUE
    - pattern: document.write($$$ARGS)
message: |
  ERROR: Dangerous code execution pattern detected.
  WHY: eval(), new Function(), innerHTML, document.write() enable XSS attacks
       and arbitrary code execution (CWE-95, CWE-79).
  FIX: Use safe alternatives.
  EXAMPLE:
    // Bad:
    eval(userInput)
    element.innerHTML = userContent
    // Good:
    JSON.parse(userInput)
    element.textContent = userContent
```

#### ast-grep (Python)

```yaml
id: no-eval-python
language: python
severity: error
rule:
  any:
    - pattern: eval($$$ARGS)
    - pattern: exec($$$ARGS)
message: |
  ERROR: Dangerous code execution pattern (eval/exec).
  WHY: eval() and exec() execute arbitrary code, enabling code injection.
  FIX: Use safe alternatives like ast.literal_eval() for data parsing.
  EXAMPLE:
    # Bad: result = eval(user_input)
    # Good: result = ast.literal_eval(user_input)
    # Good: result = json.loads(user_input)
```

### 4.3 Input Validation on Route Handlers

#### ast-grep (TypeScript -- NestJS)

```yaml
id: route-handler-needs-validation
language: typescript
severity: error
rule:
  pattern: |
    @$DECORATOR($$$ARGS)
    async $METHOD(@Body() $PARAM) { $$$BODY }
not:
  has:
    pattern: "@UsePipes($$$)"
constraints:
  DECORATOR:
    regex: '(Get|Post|Put|Patch|Delete)'
message: |
  ERROR: Route handler accepts @Body() without validation pipe.
  WHY: Unvalidated input is the root cause of injection attacks,
       data corruption, and application crashes.
  FIX: Add @UsePipes(new ValidationPipe()) or use a global validation pipe.
  EXAMPLE:
    // Bad:
    @Post()
    async create(@Body() dto: CreateUserDto) { }
    // Good:
    @Post()
    @UsePipes(new ValidationPipe({ whitelist: true }))
    async create(@Body() dto: CreateUserDto) { }
```

### 4.4 SQL Parameterization

#### ast-grep (TypeScript)

```yaml
id: no-sql-string-concat
language: typescript
severity: error
rule:
  any:
    - pattern: $DB.query(`$$$SQL${$$$VARS}$$$REST`)
    - pattern: "$DB.query($SQL + $VAR)"
message: |
  ERROR: SQL query built with string interpolation/concatenation.
  WHY: String-based SQL construction enables SQL injection (CWE-89).
  FIX: Use parameterized queries.
  EXAMPLE:
    // Bad:
    db.query(`SELECT * FROM users WHERE id = ${userId}`)
    // Good:
    db.query('SELECT * FROM users WHERE id = $1', [userId])
```

#### ast-grep (Go)

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
  ERROR: SQL query built with fmt.Sprintf.
  WHY: SQL injection (CWE-89) via string formatting.
  FIX: Use parameterized queries with $1, $2 placeholders.
  EXAMPLE:
    // Bad: db.Query(fmt.Sprintf("SELECT * FROM users WHERE id = %d", id))
    // Good: db.Query("SELECT * FROM users WHERE id = $1", id)
```

#### ast-grep (Python)

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
  ERROR: SQL query built with string formatting.
  WHY: SQL injection (CWE-89) via f-string/format/concatenation.
  FIX: Use parameterized queries with %s or ? placeholders.
  EXAMPLE:
    # Bad: cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    # Good: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```
