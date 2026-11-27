# ADR の雛形

対象のリポジトリに既存の ADR があれば、その形を優先します（F-1）。新しく置くときは、下の雛形を `docs/adr/0000-template.md` として写して使えます。

## 雛形

```markdown
# ADR-NNNN: 決定を一言で表す題

- **Status**: Proposed
- **Date**: YYYY-MM-DD
- **Scope**: この決定が当てはまる範囲（リポジトリ全体、特定のサービス、特定の実験など）

## Context

このプロジェクトで何が起きていて、なぜ決める必要があるか。制約と、確かめた事実（出どころつき）。

## Decision

何を決めたか。実現方式を差し替えても書き換えずに済む粒度で書く（D-4）。

### 決定しないこと

- この ADR では決めないこと。決める場所（委譲先）を実在する名前で書く（D-3）

## Consequences

### Positive

- ...

### Negative

- ...

## Alternatives Considered

| 案 | 採らなかった理由 |
|---|---|
| ... | ... |

## 関連 ADR

- Supersedes ADR-NNNN / Superseded by ADR-NNNN / Related to ADR-NNNN

## References

- 資料・計測結果・公式文書へのパスや URL
```

使わない節（関連 ADR が無いなど）は、節ごと削ってかまいません。`Status` と `Date` は削りません。repo-hygiene-audit は、この2欄で ADR と古い説明文を見分けます。

## 状態の移り方

```
Proposed -> Accepted -> Superseded by ADR-NNNN
                     -> Deprecated
```

| 状態 | 意味 |
|---|---|
| `Proposed` | 検討中。本文を直してよい |
| `Accepted` | 採用済み。本文は書き換えない（E-4） |
| `Superseded by ADR-NNNN` | 新しい ADR に置き換えられた |
| `Deprecated` | 後継なしで無効になった（機能を削った、など） |

## ファイル名

```
docs/adr/
├── README.md                       # 一覧：番号・題・状態
├── 0000-template.md
├── 0001-record-architecture-decisions.md
└── 0002-use-postgresql-for-primary-database.md
```

- 既存の ADR や呼び出し元のスキルが別の形（`ADR-0001-...md` など）を使っていれば、その形に合わせる
- 番号は4桁のゼロ埋めの連番。欠番は再利用しない
- ファイル名は決定内容を短く表すケバブケース
- 一覧（`README.md`）には、番号・題・状態の3列を並べる

## 最初の ADR の作例

ADR を初めて置くリポジトリでは、最初の ADR に「ADR で決定を記録する」こと自体を書きます。

```markdown
# ADR-0001: 設計上の決定を ADR で記録する

- **Status**: Accepted
- **Date**: YYYY-MM-DD
- **Scope**: リポジトリ全体

## Context

設計上の決定が、チャット・PR のコメント・日付のないメモに分かれて残っている。AI のエージェントはリポジトリ内の文章を同じ重みで信じるため、古い説明が残ると誤った判断のもとになる。

## Decision

設計上の重要な決定を、`docs/adr/` に1決定1ファイルの ADR として記録する。書き方は adr-authoring スキルの執筆規約に従う。

### 決定しないこと

- どの決定を「重要」とみなすかの線引き。ADR を書くかどうかは、各 PR のレビューで判断する

## Consequences

### Positive

- 決定と、その日付・状態を後から探せる
- エージェントが、置き換えられた決定を古いものとして扱える

### Negative

- 決定ごとに ADR を書く手間が増える
```
