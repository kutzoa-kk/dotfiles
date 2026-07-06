# settings.json 一本化 設計書

作成: 2026-07-06 · 状態: **実装完了**（commit bd4630a〜49c4517。git=種／稼働=ライブ／`make settings-pull`）· 対象: dotfiles の Claude Code 設定リンク戦略

## 目的

`dotdir/.claude/settings.json`（git 実体）と `~/.claude/settings.json`（稼働）の乖離（DRIFT-01/02/03）を解消し、次の3条件を満たす：

1. **`make link` を安全化** — 全実行しても稼働 settings.json（orca hooks・個人設定）を破壊しない
2. **git を恒久設定の正（種）にする** — 新マシンで `make link` すれば意図した設定が入る
3. **稼働→git の吸い上げ経路を持つ** — 恒久変更を git に取り込める（orca hooks・一時値は除外）

## 前提となる制約（なぜ symlink による一本化が不可能か）

`~/.claude/settings.json` を dotdir へシンボリックリンクしても持続しない。理由：

- **アトミック書き込みがリンクを壊す**：Claude Code（`/model`・`/config`）も orca（起動時 hooks 注入）も、設定保存を「temp に書いて `rename` で被せる」方式で行う。`rename()` はリンク自体を新しい実ファイルで置き換えるため、リンク先（dotdir）に書き込まれず、リンクが実ファイルへ化ける。スクラッチパッドで実証済み（in-place 追記はリンク先へ届く／アトミック書き込みはリンクを実ファイル化）。
- **動かぬ証拠**：`link.sh:226` は settings.json を symlink するのに、稼働側は実ファイル（11.1K）。＝一度リンク後にアトミック書き込みが置換した。
- **仮に届いても望ましくない**：orca hooks は `/Users/kkmclab/.orca/agent-hooks/claude-hook.sh`（マシン固有パス）を指し、`model`/`effortLevel` はセッション毎に変わる。git に流れれば他マシンで壊れ、毎セッションのコミット汚染になる。

## 所有モデル（設定キーを3層に分ける）

| 層 | 対象キー | 所有者 | git 追跡 |
|----|---------|--------|:---:|
| ① orca 注入 | hooks の orca 参照（7イベント）+ StopFailure イベント | orca が起動時に注入 | ✕ 非追跡 |
| ② 個人・可変 | `model`・`agentPushNotifEnabled`・`inputNeededNotifEnabled` | Claude Code がセッションで書く | ✕ 非追跡 |
| ③ 恒久・意図 | `enabledPlugins`・`extraKnownMarketplaces`・非 orca hooks・permissions・`effortLevel` 等 | 人が意図して決める | ○ 追跡（git が正） |

`effortLevel` は③に含め、git 既定を **`xhigh`** とする（ユーザー決定 2026-07-06）。

## Part 1 — `link.sh` の安全化（seed-if-absent / preserve-if-present）

**現状**: `link.sh:205-228` は dotdir/.claude/* を走査し、ディレクトリは許可リスト方式、**ファイルは無条件 `ln -fnsv`**（226行）。→ `make link` 全実行が settings.json を git 版リンクで上書きし、稼働の orca hooks・個人設定を破壊する。

**変更**: 外部ツールが書き換えるファイル用の保全リストを設ける。

```bash
# ファイル分岐に追加
PRESERVE_FILES=("settings.json")   # 外部ツールが書き換える＝リンクせず保全
...
else  # ファイル
    is_preserve=false
    for pf in "${PRESERVE_FILES[@]}"; do
        [[ "$filename" == "$pf" ]] && is_preserve=true && break
    done
    if [[ "$is_preserve" == true ]]; then
        if [[ ! -e "$HOME/.claude/$filename" ]]; then
            cp "$claudefile" "$HOME/.claude/$filename"      # 種を蒔く（新マシン）
            echo "seeded (copy): $filename"
        else
            echo "preserved (exists): $filename"            # 既存を保全
        fi
    else
        ln -fnsv "$claudefile" "$HOME/.claude/$filename"
    fi
fi
```

- **稼働側に無ければ** dotdir から `cp` で実ファイルとして種を蒔く（新マシンでベースラインが入る。実ファイルなので以後のアトミック書き込みも安全）
- **稼働側に有れば触らない**（orca hooks・個人設定を保全）
- 結果: `make link` 全実行が安全になり、前セッションの「個別 `ln` で回避」策が不要に

エッジ: 既存が正常な symlink の場合 `-e` は真＝保全。壊れた symlink（`-e` 偽）は種蒔きに進むが、現状は実ファイルのため該当しない。

## Part 2 — git の種を整備（③のみ取り込む）

`dotdir/.claude/settings.json` を編集：

- `effortLevel`: `"high"` → `"xhigh"`
- `enabledPlugins` に `"toolcall-recover@nam-tech-studio": true` を追加（実績ある恒久プラグイン）
- `extraKnownMarketplaces` に `"nam-tech-studio"` を追加（`{ source: { source: "github", repo: "nam-tech-studio/toolcall-recover" } }`）
- **追加しない**: `model`・通知2フラグ（②）、orca hooks・StopFailure（①）

結果: git 種が恒久意図を反映。`make link` の種蒔きが正しいベースラインを配る。

## Part 3 — `settings-pull`（稼働→git のフィルタ吸い上げ）

**新規**: `.bin/settings-pull.sh`（JSON 安全のため python3 実装）+ `make settings-pull` ターゲット。

**処理**:
1. 稼働 `~/.claude/settings.json` と git `dotdir/.claude/settings.json` を読む
2. 稼働から「クリーン版」を作る（除外）:
   - top-level: `model`・`agentPushNotifEnabled`・`inputNeededNotifEnabled`・`effortLevel`（①②＋ effortLevel はセッション値の逆流を防ぐため除外。git 既定は Part 2 が保持）
   - hooks: 各イベント内で `command` が `.orca/` を参照する要素を除去 → 空になったイベントは削除（StopFailure が orca 専用なら消える）
3. git 設定へ merge（git を土台に、クリーン版の③キーで更新）。`effortLevel` は git 値を保持
4. 差分表示 → 確認 → dotdir へ書き込み（書き込み前に dotdir 設定をバックアップ）
5. 「git status 確認・コミット」を促す

**用途**: プラグイン有効化など恒久変更をした時に走らせ、git に取り込む。symlink による自動反映の代替＝明示的で汚染しない。

## Part 4 — 運用メモ（ドキュメント）

`docs/settings-ownership.md` を新規作成し、所有モデルと運用を記す：git=種／稼働=ライブ実ファイル／orca=hooks 注入／settings.json は決して symlink しない／`make link` は seed-if-absent・preserve-if-present／恒久変更は `make settings-pull` で吸い上げ。リポジトリ `CLAUDE.md` の Change Guidelines から参照を張る。

## テスト方針

- **Part 1**: バックアップの上で (a) 稼働 settings.json を退避 → link の settings 分岐実行 → 種が dotdir と一致することを確認 → 復元。(b) ファイル在時に実行 → inode/mtime 不変を確認
- **Part 2**: JSON 妥当性 + 追加キー存在を python で assert
- **Part 3**: 稼働 settings.json の**コピー**に対して実行 → orca hooks 除去・②キー不在・`effortLevel` は git 値保持・`enabledPlugins` 反映・差分表示・未確認では非書き込み、を確認
- **全体**: 実装後に `make link` を実際に全実行し、稼働 settings.json が保全されることを最終確認

## スコープ外（YAGNI）

- 他の監査所見（serena 二重登録 DUP-002、Context7/deepwiki、ブラウザ MCP 3系統）は別タスク
- `settings.local.json` 分割はユーザー判断で不採用
- session 終了 hook による pull 自動化（当面は手動コマンドで十分）
