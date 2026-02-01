---
marp: true
theme: default
paginate: true
---

<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  theme: {
    extend: {
      colors: {
        navy: '#1B4565',
        teal: '#3E9BA4',
        'bg-secondary': '#F5F5F5',
        'text-secondary': '#4A4A4A',
        'text-muted': '#6B6B6B',
      },
      fontSize: {
        'em-3xl': ['3em', { lineHeight: '1.1' }],
        'em-2xl': ['2em', { lineHeight: '1.2' }],
        'em-xl': ['1.5em', { lineHeight: '1.3' }],
        'em-lg': ['1.25em', { lineHeight: '1.5' }],
        'em-base': ['1em', { lineHeight: '1.6' }],
      }
    }
  }
}
</script>

<!-- Title Slide -->

<div class="flex flex-col items-center justify-center h-full text-center">
  <h1 class="text-em-3xl text-navy mb-4">dotfiles2</h1>
  <p class="text-em-xl text-text-secondary">macOS開発環境の自動構築</p>
  <p class="text-em-base text-text-muted mt-8">Shell / Git / SSH / AI Tools</p>
</div>

---

<!-- Overview -->

<div class="flex items-center h-full">
  <div class="border-l-4 border-teal pl-8">
    <p class="text-em-base text-text-muted mb-2">01</p>
    <h2 class="text-em-2xl text-navy">Overview</h2>
  </div>
</div>

---

<!-- What is dotfiles2? -->

<h2 class="text-em-2xl text-navy mb-8">What is dotfiles2?</h2>

<div class="grid grid-cols-2 gap-8 items-start">
  <div>
    <p class="text-em-lg text-text-secondary mb-6">
      macOS環境を<span class="text-teal font-bold">一発で再現</span>できるdotfilesリポジトリ
    </p>
    <div class="space-y-3">
      <div class="flex items-start">
        <span class="text-teal mr-4">●</span>
        <span class="text-em-lg">シェル設定（zsh, p10k）</span>
      </div>
      <div class="flex items-start">
        <span class="text-teal mr-4">●</span>
        <span class="text-em-lg">Git / SSH 設定</span>
      </div>
      <div class="flex items-start">
        <span class="text-teal mr-4">●</span>
        <span class="text-em-lg">AIツール統合</span>
      </div>
      <div class="flex items-start">
        <span class="text-teal mr-4">●</span>
        <span class="text-em-lg">Homebrew パッケージ管理</span>
      </div>
    </div>
  </div>
  <div class="bg-gray-900 rounded-lg p-6 text-white font-mono text-em-base">
    <pre><code># 新しいMacで実行
git clone repo
cd dotfiles2
make all</code></pre>
  </div>
</div>

---

<!-- Directory Structure -->

<h2 class="text-em-2xl text-navy mb-6">Directory Structure</h2>

<div class="grid grid-cols-2 gap-6">
  <div class="bg-bg-secondary rounded-lg p-6">
    <h3 class="text-em-lg text-navy mb-4">Root Level</h3>
    <div class="font-mono text-em-base text-text-secondary space-y-1">
      <p>.zshrc, .zprofile</p>
      <p>.p10k.zsh</p>
      <p>.gitconfig</p>
      <p>.Brewfile</p>
    </div>
  </div>
  <div class="bg-bg-secondary rounded-lg p-6">
    <h3 class="text-em-lg text-navy mb-4">dotdir/</h3>
    <div class="font-mono text-em-base text-text-secondary space-y-1">
      <p>.claude/ <span class="text-teal">← AI Agent</span></p>
      <p>.codex/  <span class="text-teal">← OpenAI</span></p>
      <p>.cursor/ <span class="text-teal">← Editor</span></p>
      <p>.gemini/ <span class="text-teal">← Google AI</span></p>
      <p>.ssh/, .config/git/</p>
    </div>
  </div>
</div>

<div class="mt-6 bg-bg-secondary rounded-lg p-4">
  <p class="text-em-base text-text-secondary"><span class="text-navy font-bold">.bin/</span> — セットアップスクリプト群（link.sh, brew.sh, etc.）</p>
</div>

---

<!-- Setup Commands -->

<h2 class="text-em-2xl text-navy mb-8">Setup Commands</h2>

<div class="space-y-4">
  <div class="grid grid-cols-3 gap-4 items-center bg-bg-secondary rounded-lg p-4">
    <code class="text-em-lg text-teal font-mono">make all</code>
    <span class="col-span-2 text-em-base text-text-secondary">フルセットアップ（init → link → brew → macos → iterm2）</span>
  </div>
  <div class="grid grid-cols-3 gap-4 items-center bg-bg-secondary rounded-lg p-4">
    <code class="text-em-lg text-teal font-mono">make link</code>
    <span class="col-span-2 text-em-base text-text-secondary">シンボリックリンク作成</span>
  </div>
  <div class="grid grid-cols-3 gap-4 items-center bg-bg-secondary rounded-lg p-4">
    <code class="text-em-lg text-teal font-mono">make brew</code>
    <span class="col-span-2 text-em-base text-text-secondary">Homebrewパッケージインストール</span>
  </div>
  <div class="grid grid-cols-3 gap-4 items-center bg-bg-secondary rounded-lg p-4">
    <code class="text-em-lg text-teal font-mono">make cursor</code>
    <span class="col-span-2 text-em-base text-text-secondary">Cursor拡張機能インストール</span>
  </div>
</div>

---

<!-- Symlink Strategy -->

<h2 class="text-em-2xl text-navy mb-6">Symlink Strategy</h2>

<div class="overflow-auto">
  <table class="w-full text-em-base">
    <thead>
      <tr class="bg-navy text-white">
        <th class="p-3 text-left">Source</th>
        <th class="p-3 text-left">Target</th>
        <th class="p-3 text-left">Strategy</th>
      </tr>
    </thead>
    <tbody class="text-text-secondary">
      <tr class="border-b">
        <td class="p-3 font-mono">Root .??*</td>
        <td class="p-3 font-mono">$HOME</td>
        <td class="p-3">Direct link</td>
      </tr>
      <tr class="border-b bg-bg-secondary">
        <td class="p-3 font-mono">dotdir/.ssh/*</td>
        <td class="p-3 font-mono">~/.ssh/</td>
        <td class="p-3">File-by-file merge</td>
      </tr>
      <tr class="border-b">
        <td class="p-3 font-mono">dotdir/.claude/*</td>
        <td class="p-3 font-mono">~/.claude/</td>
        <td class="p-3">Files + specific dirs</td>
      </tr>
      <tr class="border-b bg-bg-secondary">
        <td class="p-3 font-mono">dotdir/.cursor/User/</td>
        <td class="p-3 font-mono">~/Library/.../Cursor/</td>
        <td class="p-3">settings.json, keybindings</td>
      </tr>
    </tbody>
  </table>
</div>

---

<!-- AI Tools Integration -->

<h2 class="text-em-2xl text-navy mb-8 text-center">AI Tools Integration</h2>

<div class="grid grid-cols-4 gap-4">
  <div class="bg-bg-secondary rounded-lg p-4 text-center">
    <span class="text-em-2xl block mb-2">🤖</span>
    <h3 class="text-em-lg text-navy mb-2">Claude</h3>
    <p class="text-em-base text-text-secondary">Commands, Agents, Scripts, MCP</p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-4 text-center">
    <span class="text-em-2xl block mb-2">💻</span>
    <h3 class="text-em-lg text-navy mb-2">Codex</h3>
    <p class="text-em-base text-text-secondary">Config, User Skills</p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-4 text-center">
    <span class="text-em-2xl block mb-2">✏️</span>
    <h3 class="text-em-lg text-navy mb-2">Cursor</h3>
    <p class="text-em-base text-text-secondary">Settings, Keybindings, Extensions</p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-4 text-center">
    <span class="text-em-2xl block mb-2">✨</span>
    <h3 class="text-em-lg text-navy mb-2">Gemini</h3>
    <p class="text-em-base text-text-secondary">CLI Settings</p>
  </div>
</div>

<div class="mt-6 text-center">
  <p class="text-em-lg text-text-secondary">AIツール設定は<span class="text-teal font-bold">merge strategy</span>でツール管理ファイルと共存</p>
</div>

---

<!-- Homebrew Packages -->

<h2 class="text-em-2xl text-navy mb-6">Homebrew Packages</h2>

<div class="grid grid-cols-2 gap-6">
  <div>
    <h3 class="text-em-lg text-teal mb-4">CLI Tools</h3>
    <div class="bg-bg-secondary rounded-lg p-4 font-mono text-em-base space-y-1">
      <p>gh, jq, uv, pyenv</p>
      <p>nodebrew, pipx</p>
      <p>zinit, zsh-completions</p>
      <p>ollama, gemini-cli</p>
    </div>
  </div>
  <div>
    <h3 class="text-em-lg text-teal mb-4">Applications</h3>
    <div class="bg-bg-secondary rounded-lg p-4 font-mono text-em-base space-y-1">
      <p>cursor, visual-studio-code</p>
      <p>claude-code, codex, chatgpt</p>
      <p>iterm2, raycast</p>
      <p>slack, zoom, figma</p>
    </div>
  </div>
</div>

<div class="mt-6 text-center">
  <code class="text-em-lg text-navy bg-bg-secondary px-4 py-2 rounded">brew bundle --file=.Brewfile</code>
</div>

---

<!-- Key Design Decisions -->

<h2 class="text-em-2xl text-navy mb-8">Key Design Decisions</h2>

<div class="space-y-4">
  <div class="flex items-start">
    <span class="text-teal mr-4 text-em-xl">✓</span>
    <div>
      <span class="text-em-lg text-navy font-bold">秘密鍵は除外</span>
      <span class="text-em-base text-text-secondary ml-2">— .ssh/の鍵は手動コピー</span>
    </div>
  </div>
  <div class="flex items-start">
    <span class="text-teal mr-4 text-em-xl">✓</span>
    <div>
      <span class="text-em-lg text-navy font-bold">拡張機能リストは別管理</span>
      <span class="text-em-base text-text-secondary ml-2">— cursor-extensions.txtからスクリプトでインストール</span>
    </div>
  </div>
  <div class="flex items-start">
    <span class="text-teal mr-4 text-em-xl">✓</span>
    <div>
      <span class="text-em-lg text-navy font-bold">ランタイムディレクトリ保護</span>
      <span class="text-em-base text-text-secondary ml-2">— キャッシュ等はリンクしない</span>
    </div>
  </div>
  <div class="flex items-start">
    <span class="text-teal mr-4 text-em-xl">✓</span>
    <div>
      <span class="text-em-lg text-navy font-bold">Merge戦略</span>
      <span class="text-em-base text-text-secondary ml-2">— AIツール設定はツール管理ファイルと共存</span>
    </div>
  </div>
</div>

---

<!-- Thank You -->

<div class="flex flex-col items-center justify-center h-full text-center">
  <h2 class="text-em-3xl text-navy mb-6">Thank You</h2>
  <p class="text-em-lg text-text-secondary mb-8">新しいMacでも、いつもの環境を</p>
  <div class="bg-bg-secondary rounded-lg px-8 py-4">
    <code class="text-em-xl text-teal font-mono">make all</code>
  </div>
</div>
