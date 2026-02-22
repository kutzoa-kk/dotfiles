# zsh configuration file

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# zinit initialization
if [ -f /opt/homebrew/opt/zinit/zinit.zsh ]; then
    source /opt/homebrew/opt/zinit/zinit.zsh
elif [ -f /usr/local/opt/zinit/zinit.zsh ]; then
    source /usr/local/opt/zinit/zinit.zsh
fi

# zinit
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit

# Load a few important annexes, without Turbo
# (this is currently required for annexes)
zinit light-mode for \
    zdharma-continuum/z-a-patch-dl \
    zdharma-continuum/z-a-as-monitor \
    zdharma-continuum/z-a-bin-gem-node

# Plugins
zinit light zsh-users/zsh-autosuggestions
zinit light zdharma-continuum/fast-syntax-highlighting
zinit load zdharma-continuum/history-search-multi-word

# fzf
zinit ice from"gh-r" as"program"
zinit load junegunn/fzf-bin

# zsh-completions
# Note: We handle compinit manually with -u flag to ignore insecure directories
zinit wait lucid blockf for zsh-users/zsh-completions

# Powerlevel10k theme
zinit ice depth=1
zinit light romkatv/powerlevel10k

# zsh-completions (Homebrew path)
if [ -e /usr/local/share/zsh-completions ]; then
    fpath=(/usr/local/share/zsh-completions $fpath)
fi
if [ -e /opt/homebrew/share/zsh-completions ]; then
    fpath=(/opt/homebrew/share/zsh-completions $fpath)
fi

# Completion settings
# Initialize completion system
# Use -u to ignore insecure directories (common with Homebrew installations)
# This is safe for Homebrew-managed completion directories
autoload -Uz compinit
compinit -u
# Replay completion functions for zinit plugins
zicdreplay 2>/dev/null || true

# completion options
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'    # 補完候補で、大文字・小文字を区別しないで補完出来るようにするが、大文字を入力した場合は区別する
zstyle ':completion:*' ignore-parents parent pwd ..    # ../ の後は今いるディレクトリを補間しない
zstyle ':completion:*:default' menu select=1           # 補間候補一覧上で移動できるように
zstyle ':completion:*:cd:*' ignore-parents parent pwd  # 補間候補にカレントディレクトリは含めない

# History settings
HISTFILE=~/.zsh_history
HISTSIZE=1000000
SAVEHIST=1000000

setopt share_history           # 履歴を他のシェルとリアルタイム共有する
setopt hist_ignore_all_dups    # 同じコマンドをhistoryに残さない
setopt hist_ignore_space       # historyに保存するときに余分なスペースを削除する
setopt hist_reduce_blanks      # historyに保存するときに余分なスペースを削除する
setopt hist_save_no_dups       # 重複するコマンドが保存されるとき、古い方を削除する
setopt inc_append_history      # 実行時に履歴をファイルにに追加していく

# Search history
autoload history-search-end
zle -N history-beginning-search-backward-end history-search-end
zle -N history-beginning-search-forward-end history-search-end
bindkey "^p" history-beginning-search-backward-end
bindkey "^n" history-beginning-search-forward-end

# Directory navigation
setopt AUTO_CD
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS

# Aliases
alias ll='ls -lah'
alias la='ls -la'
alias l='ls -l'
alias ..='cd ..'
alias ...='cd ../..'

# Homebrew (if installed)
if [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -f /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

# Powerlevel10k configuration
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

ZSH_THEME="ys"


# pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)" 2>/dev/null || true

# nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# uv (Python package manager)
eval "$(uv generate-shell-completion zsh)" 2>/dev/null || true
eval "$(uvx --generate-shell-completion zsh)" 2>/dev/null || true

# pipx
export PATH="$PATH:$HOME/.local/bin"
export DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"

export NANOBANANA_MODEL=gemini-3-pro-image-preview