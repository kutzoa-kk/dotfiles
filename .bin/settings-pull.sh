#!/bin/zsh
# settings-pull.sh — 稼働 settings.json から恒久設定(③)だけを git(dotdir) へ吸い上げる。
# 除外: orca hooks(command が .orca/ を参照) / model / 通知2フラグ / effortLevel(セッション値の逆流防止)。
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOTDIR_ROOT="$(cd "${SCRIPT_DIR}/../dotdir" && pwd)"
RUNTIME="${SP_RUNTIME:-$HOME/.claude/settings.json}"
GIT_SETTINGS="${SP_GIT:-${DOTDIR_ROOT}/.claude/settings.json}"
MODE="interactive"
[[ "${1:-}" == "--dry-run" ]] && MODE="dry"
[[ "${1:-}" == "--yes" ]] && MODE="yes"

python3 - "$RUNTIME" "$GIT_SETTINGS" "$MODE" <<'PY'
import json, sys, copy, difflib
runtime_p, git_p, mode = sys.argv[1], sys.argv[2], sys.argv[3]
EXCLUDE = {'model','agentPushNotifEnabled','inputNeededNotifEnabled','effortLevel'}
runtime = json.load(open(runtime_p))
git = json.load(open(git_p))

# クリーン版 = runtime から除外キーを外し、hooks の orca 参照要素を除去
clean = copy.deepcopy(runtime)
for k in EXCLUDE:
    clean.pop(k, None)
new_hooks = {}
for event, blocks in clean.get('hooks', {}).items():
    kept = []
    for block in blocks:
        hb = [h for h in block.get('hooks', []) if '.orca/' not in json.dumps(h)]
        if hb:
            nb = dict(block); nb['hooks'] = hb; kept.append(nb)
    if kept:
        new_hooks[event] = kept
clean['hooks'] = new_hooks

# merge: git を土台に clean の③キーで更新。effortLevel は git 値を保持。②キーは念のため落とす
result = dict(git)
for k, v in clean.items():
    result[k] = v
result['effortLevel'] = git.get('effortLevel', result.get('effortLevel'))
for k in ('model','agentPushNotifEnabled','inputNeededNotifEnabled'):
    result.pop(k, None)

def dump(o): return json.dumps(o, indent=2, ensure_ascii=False).splitlines()
diff = list(difflib.unified_diff(dump(git), dump(result), 'git(before)', 'git(after)', lineterm=''))
if not diff:
    print('差分なし。吸い上げる恒久変更はありません。'); sys.exit(0)
print('\n'.join(diff))
if mode == 'dry':
    print('\n[dry-run] 書き込みませんでした。'); sys.exit(0)
if mode == 'interactive':
    sys.stderr.write('\nこの差分を dotdir へ書き込みますか? [y/N]: '); sys.stderr.flush()
    if sys.stdin.readline().strip().lower() not in ('y','yes'):
        print('中止しました。'); sys.exit(0)
with open(git_p, 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False); f.write('\n')
print(f'\n書き込みました: {git_p}')
print('git status/diff を確認し、意図どおりならコミットしてください（誤りは git checkout で戻せます）。')
PY
