# Protected Configuration Files

Lint Config Guard が保護する設定ファイルの完全なリスト。

## JavaScript / TypeScript

### ESLint

| Pattern | Description |
|---------|-------------|
| `.eslintrc` | Legacy config (no extension) |
| `.eslintrc.js` | Legacy JS config |
| `.eslintrc.cjs` | Legacy CommonJS config |
| `.eslintrc.mjs` | Legacy ESM config |
| `.eslintrc.json` | Legacy JSON config |
| `.eslintrc.yml` | Legacy YAML config |
| `.eslintrc.yaml` | Legacy YAML config |
| `eslint.config.js` | Flat config (ESLint 9+) |
| `eslint.config.mjs` | Flat config ESM |
| `eslint.config.cjs` | Flat config CommonJS |
| `eslint.config.ts` | Flat config TypeScript |
| `eslint.config.mts` | Flat config TypeScript ESM |
| `eslint.config.cts` | Flat config TypeScript CommonJS |
| `.eslintignore` | Ignore patterns |

### Biome

| Pattern | Description |
|---------|-------------|
| `biome.json` | Biome config |
| `biome.jsonc` | Biome config (with comments) |

### Prettier

| Pattern | Description |
|---------|-------------|
| `.prettierrc` | Prettier config (no extension) |
| `.prettierrc.js` | JS config |
| `.prettierrc.cjs` | CommonJS config |
| `.prettierrc.mjs` | ESM config |
| `.prettierrc.json` | JSON config |
| `.prettierrc.yml` | YAML config |
| `.prettierrc.yaml` | YAML config |
| `.prettierrc.toml` | TOML config |
| `prettier.config.js` | JS config (alternative) |
| `prettier.config.cjs` | CommonJS config (alternative) |
| `prettier.config.mjs` | ESM config (alternative) |
| `prettier.config.ts` | TypeScript config |

### Oxlint

| Pattern | Description |
|---------|-------------|
| `oxlint.json` | Oxlint config |
| `.oxlintrc.json` | Oxlint config (alternative) |

### TypeScript

| Pattern | Description |
|---------|-------------|
| `tsconfig.json` | TypeScript config |
| `tsconfig.*.json` | Extended configs (e.g., tsconfig.build.json) |

## Python

### Ruff

| Pattern | Description |
|---------|-------------|
| `ruff.toml` | Standalone Ruff config |
| `.ruff.toml` | Hidden Ruff config |
| `pyproject.toml` | `[tool.ruff]` section |

### Pylint

| Pattern | Description |
|---------|-------------|
| `.pylintrc` | Pylint config (hidden) |
| `pylintrc` | Pylint config (no dot) |
| `pyproject.toml` | `[tool.pylint]` section |

### Mypy

| Pattern | Description |
|---------|-------------|
| `mypy.ini` | Standalone Mypy config |
| `.mypy.ini` | Hidden Mypy config |
| `setup.cfg` | `[mypy]` section |
| `pyproject.toml` | `[tool.mypy]` section |

## Go

### golangci-lint

| Pattern | Description |
|---------|-------------|
| `.golangci.yml` | golangci-lint config (YAML) |
| `.golangci.yaml` | golangci-lint config (YAML alternative) |
| `.golangci.json` | golangci-lint config (JSON) |
| `.golangci.toml` | golangci-lint config (TOML) |

## Rust

### Clippy

| Pattern | Description |
|---------|-------------|
| `clippy.toml` | Clippy config |
| `.clippy.toml` | Hidden Clippy config |

### Cargo Lints

| Pattern | Description |
|---------|-------------|
| `Cargo.toml` | `[lints]` / `[lints.clippy]` section |

## Git Hooks

### Lefthook

| Pattern | Description |
|---------|-------------|
| `lefthook.yml` | Lefthook config |
| `lefthook.yaml` | Lefthook config (alternative) |
| `lefthook-local.yml` | Local overrides |
| `lefthook-local.yaml` | Local overrides (alternative) |

### Husky

| Pattern | Description |
|---------|-------------|
| `.husky/*` | All files in .husky/ directory |

## Shell Script Glob Patterns

フックスクリプトで使用するパターンのまとめ:

```bash
# Exact filename matches
PROTECTED_EXACT=(
  ".eslintrc"
  ".eslintignore"
  "biome.json"
  "biome.jsonc"
  ".prettierrc"
  "oxlint.json"
  "ruff.toml"
  ".ruff.toml"
  ".pylintrc"
  "pylintrc"
  "mypy.ini"
  ".mypy.ini"
  ".golangci.yml"
  ".golangci.yaml"
  ".golangci.json"
  ".golangci.toml"
  "clippy.toml"
  ".clippy.toml"
  "tsconfig.json"
  "lefthook.yml"
  "lefthook.yaml"
  "lefthook-local.yml"
  "lefthook-local.yaml"
  "pyproject.toml"
  "setup.cfg"
  "Cargo.toml"
)

# Glob pattern matches (basename)
PROTECTED_PATTERNS=(
  ".eslintrc.*"
  "eslint.config.*"
  ".prettierrc.*"
  "prettier.config.*"
  "oxlint.*"
  ".oxlintrc.*"
  "tsconfig.*.json"
)

# Directory-based matches (path contains)
PROTECTED_DIRS=(
  ".husky/"
)
```
