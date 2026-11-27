# 説明文を ADR に変換する

ADR の雛形・状態の移り方・ファイル名・執筆規約は adr-authoring スキル（`~/.claude/skills/adr-authoring/`）にまとめています。変換して ADR を書くときは、そのスキルの `references/guideline.md` と `references/template.md` を読んでから書きます。このファイルには、監査の観点から見た変換の例と、ADR が腐りにくい理由だけを置きます。

## Prose -> ADR 変換例

### 変換前（腐る説明文）

```markdown
## キャッシュの方針

ランキング機能に必要なデータ構造を持つため、Memcached ではなく Redis を使うことにした。
接続プールの上限は 50 にしている。
```

### 変換後（ADR）

```markdown
# ADR-0004: キャッシュに Redis を使う

- **Status**: Accepted
- **Date**: 2025-03-15
- **Scope**: API サービスのキャッシュ

## Context

ランキング機能では、順位つきの集合（sorted set）をキャッシュに持つ必要がある。Memcached はキーと値の組しか持てない。

## Decision

キャッシュに Redis を使う。

### 決定しないこと

- 接続プールの大きさ。`config/redis.yml` で決める

## Consequences

### Positive

- ランキングを Redis の機能だけで組める

### Negative

- 単純なキーと値の保存では、Memcached よりメモリを多く使う
```

変換では、決定日と状態を持たせ、いつの決定かを読み手が判断できるようにします。あわせて、接続数のような実装の値は Decision に入れず、設定ファイルを正本にします（adr-authoring の規約 D-4）。変換前の「上限は 50」は、設定を変えた時点で腐る記述でした。

## Agent-Friendly Properties of ADRs

ADR が agent にとって安全な理由：

| Property | Why it helps agents |
|----------|-------------------|
| **Status field** | Agent は `Superseded` や `Deprecated` を無視できる |
| **Date field** | Agent は情報の鮮度を判断できる |
| **Immutable history** | 採用後の本文は書き換えないため、git blame が正確 |
| **Structured format** | パースしやすく、意味を正確に抽出できる |
| **Explicit scope** | 1つの決定 = 1つのファイル。混在しない |
