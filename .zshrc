# Python
export PIPENV_VENV_IN_PROJECT=true
export PIPENV_NO_INHERIT=True
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# gcc
export PATH="/usr/local/opt/avr-gcc@8/bin:$PATH"
#Java
export PATH="/usr/local/opt/openjdk@11/bin:$PATH"
export CPPFLAGS="-I/usr/local/opt/openjdk@11/include"

# Homebrew
# export PATH=$HOME/.nodebrew/current/bin:$PATH
# export PATH="/usr/local/sbin:$PATH"
# alias brew="PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin brew"

# alias
alias get_idf='. $HOME/code/esp/esp-idf/export.sh'


# zsh-completions(補完機能)の設定
if [ -e /usr/local/share/zsh-completions ]; then
    fpath=(/usr/local/share/zsh-completions $fpath)
fi
autoload -U compinit
compinit -u

##### zsh の設定 #####
 
# すっきりしたプロンプト表示 (不要ならコメントアウト)
PROMPT='%~ %# '

# 色を使用出来るようにする
autoload -Uz colors
colors

# cd なしでもディレクトリ移動
setopt auto_cd
 
# ビープ音の停止
setopt no_beep
 
# ビープ音の停止(補完時)
setopt nolistbeep
 
# cd [TAB] で以前移動したディレクトリを表示
setopt auto_pushd
 
# ヒストリ (履歴) を保存、数を増やす
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
 
# 同時に起動した zsh の間でヒストリを共有する
setopt share_history
 
# 直前と同じコマンドの場合はヒストリに追加しない
setopt hist_ignore_dups

# 同じコマンドをヒストリに残さない
setopt hist_ignore_all_dups
 
# スペースから始まるコマンド行はヒストリに残さない
setopt hist_ignore_space
 
# ヒストリに保存するときに余分なスペースを削除する
setopt hist_reduce_blanks

# export PATH=/opt/kendryte-toolchain/bin:$PATH

LDFLAGS="-L/usr/local/opt/bzip2/lib"
CPPFLAGS="-I/usr/local/opt/bzip2/include"
