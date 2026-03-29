#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOTDIR_ROOT="$(cd "${SCRIPT_DIR}/../dotdir" && pwd)"

# Link dotfiles from repository root (files only, directories are handled separately)
for dotfile in "${REPO_ROOT}"/.??* ; do
    [[ "$dotfile" == "${REPO_ROOT}/.git" ]] && continue
    [[ "$dotfile" == "${REPO_ROOT}/.github" ]] && continue
    [[ "$dotfile" == "${REPO_ROOT}/.DS_Store" ]] && continue
    [[ "$dotfile" == "${REPO_ROOT}/.claude" ]] && continue
    [[ "$dotfile" == "${REPO_ROOT}/.bin" ]] && continue  # Skip .bin directory (scripts)
    
    # Only link files, not directories
    [[ -d "$dotfile" ]] && continue
    
    ln -fnsv "$dotfile" "$HOME"
done

# Link .ssh directory (if exists)
if [ -d "${DOTDIR_ROOT}/.ssh" ]; then
    echo "Linking .ssh directory..."
    if [ ! -d "$HOME/.ssh" ]; then
        mkdir -p "$HOME/.ssh"
        chmod 700 "$HOME/.ssh"
    fi
    
    for sshfile in "${DOTDIR_ROOT}"/.ssh/* ; do
        [[ ! -e "$sshfile" ]] && continue
        filename=$(basename "$sshfile")
        ln -fnsv "$sshfile" "$HOME/.ssh/$filename"
    done
fi

# Link .config/git directory (merge approach: link files only, preserve existing directory)
if [ -d "${DOTDIR_ROOT}/.config/git" ]; then
    echo "Linking .config/git configuration files..."
    if [ ! -d "$HOME/.config/git" ]; then
        mkdir -p "$HOME/.config/git"
    fi
    
    for gitfile in "${DOTDIR_ROOT}"/.config/git/* ; do
        [[ ! -e "$gitfile" ]] && continue
        [[ -d "$gitfile" ]] && continue  # Skip directories
        filename=$(basename "$gitfile")
        ln -fnsv "$gitfile" "$HOME/.config/git/$filename"
    done
fi

# Link .config/gh directory (config.yml only, exclude hosts.yml which contains auth tokens)
if [ -d "${DOTDIR_ROOT}/.config/gh" ]; then
    echo "Linking .config/gh configuration files..."
    if [ ! -d "$HOME/.config/gh" ]; then
        mkdir -p "$HOME/.config/gh"
    fi

    if [ -f "${DOTDIR_ROOT}/.config/gh/config.yml" ]; then
        ln -fnsv "${DOTDIR_ROOT}/.config/gh/config.yml" "$HOME/.config/gh/config.yml"
    fi
fi

# Link .cursor directory (merge approach: link files only, preserve existing directory)
if [ -d "${DOTDIR_ROOT}/.cursor" ]; then
    echo "Linking .cursor configuration files..."
    if [ ! -d "$HOME/.cursor" ]; then
        mkdir -p "$HOME/.cursor"
    fi
    
    # Directories to link (list of directory names to link instead of skip)
    LINK_DIRECTORIES=()
    EXCLUDE_FILES=("README.md" "cursor-extensions.txt" "User")

    for cursorfile in "${DOTDIR_ROOT}"/.cursor/* ; do
        [[ ! -e "$cursorfile" ]] && continue
        filename=$(basename "$cursorfile")

        # ファイルがEXCLUDE_FILESに含まれていたらリンクしない
        should_exclude=false
        for exfile in "${EXCLUDE_FILES[@]}"; do
            if [[ "$filename" == "$exfile" ]]; then
                should_exclude=true
                break
            fi
        done
        [[ "$should_exclude" == true ]] && continue

        if [[ -d "$cursorfile" ]]; then
            # Check if this directory should be linked
            should_link=false
            for link_dir in "${LINK_DIRECTORIES[@]}"; do
                if [[ "$filename" == "$link_dir" ]]; then
                    should_link=true
                    break
                fi
            done

            if [[ "$should_link" == true ]]; then
                # Link directory
                ln -fnsv "$cursorfile" "$HOME/.cursor/$filename"
            fi
            # 他のディレクトリはスキップ（必要ならLINK_DIRECTORIESへ追加）
        else
            # 対象外でなければリンク
            ln -fnsv "$cursorfile" "$HOME/.cursor/$filename"
        fi
    done
fi

# Link Cursor User directory (settings.json, keybindings.json, snippets)
CURSOR_USER_DIR="${HOME}/Library/Application Support/Cursor/User"
if [ -d "${DOTDIR_ROOT}/.cursor/User" ]; then
    echo "Linking Cursor User configuration files..."
    if [ ! -d "$CURSOR_USER_DIR" ]; then
        mkdir -p "$CURSOR_USER_DIR"
    fi
    
    # Link settings.json
    if [ -f "${DOTDIR_ROOT}/.cursor/User/settings.json" ]; then
        ln -fnsv "${DOTDIR_ROOT}/.cursor/User/settings.json" "${CURSOR_USER_DIR}/settings.json"
    fi
    
    # Link keybindings.json
    if [ -f "${DOTDIR_ROOT}/.cursor/User/keybindings.json" ]; then
        ln -fnsv "${DOTDIR_ROOT}/.cursor/User/keybindings.json" "${CURSOR_USER_DIR}/keybindings.json"
    fi
    
    # Link snippets directory
    if [ -d "${DOTDIR_ROOT}/.cursor/User/snippets" ]; then
        ln -fnsv "${DOTDIR_ROOT}/.cursor/User/snippets" "${CURSOR_USER_DIR}/snippets"
    fi
fi

# Link VSCode User directory (settings.json, keybindings.json, snippets)
VSCODE_USER_DIR="${HOME}/Library/Application Support/Code/User"
if [ -d "${DOTDIR_ROOT}/.vscode/User" ]; then
    echo "Linking VSCode User configuration files..."
    if [ ! -d "$VSCODE_USER_DIR" ]; then
        mkdir -p "$VSCODE_USER_DIR"
    fi

    # Link settings.json
    if [ -f "${DOTDIR_ROOT}/.vscode/User/settings.json" ]; then
        ln -fnsv "${DOTDIR_ROOT}/.vscode/User/settings.json" "${VSCODE_USER_DIR}/settings.json"
    fi

    # Link keybindings.json
    if [ -f "${DOTDIR_ROOT}/.vscode/User/keybindings.json" ]; then
        ln -fnsv "${DOTDIR_ROOT}/.vscode/User/keybindings.json" "${VSCODE_USER_DIR}/keybindings.json"
    fi

    # Link snippets directory (remove existing dir first to replace with symlink)
    if [ -d "${DOTDIR_ROOT}/.vscode/User/snippets" ]; then
        if [ -d "${VSCODE_USER_DIR}/snippets" ] && [ ! -L "${VSCODE_USER_DIR}/snippets" ]; then
            rm -rf "${VSCODE_USER_DIR}/snippets"
        fi
        ln -fnsv "${DOTDIR_ROOT}/.vscode/User/snippets" "${VSCODE_USER_DIR}/snippets"
    fi
fi

# Link .codex directory (Codex configuration)
# This will link configuration files when they exist in the dotfiles repository
if [ -d "${DOTDIR_ROOT}/.codex" ]; then
    echo "Linking .codex configuration files..."
    if [ ! -d "$HOME/.codex" ]; then
        mkdir -p "$HOME/.codex"
    fi
    
    for codexfile in "${DOTDIR_ROOT}"/.codex/* ; do
        [[ ! -e "$codexfile" ]] && continue
        [[ -d "$codexfile" ]] && continue  # Skip directories (like skills)
        [[ "$codexfile" == "${DOTDIR_ROOT}/.codex/README.md" ]] && continue  # Skip README
        filename=$(basename "$codexfile")
        ln -fnsv "$codexfile" "$HOME/.codex/$filename"
    done
    
    # Link .codex/skills directory if it exists (user-installed skills)
    if [ -d "${DOTDIR_ROOT}/.codex/skills" ]; then
        if [ ! -d "$HOME/.codex/skills" ]; then
            mkdir -p "$HOME/.codex/skills"
        fi
        
        # Link only user skills, not system skills
        for skilldir in "${DOTDIR_ROOT}"/.codex/skills/* ; do
            [[ ! -e "$skilldir" ]] && continue
            [[ ! -d "$skilldir" ]] && continue
            skillname=$(basename "$skilldir")
            # Skip system skills (they start with .system or are system-managed)
            [[ "$skillname" =~ ^\. ]] && continue
            ln -fnsv "$skilldir" "$HOME/.codex/skills/$skillname"
        done
    fi
fi

# Link .claude directory (ClaudeCode configuration)
if [ -d "${DOTDIR_ROOT}/.claude" ]; then
    echo "Linking .claude configuration files..."
    if [ ! -d "$HOME/.claude" ]; then
        mkdir -p "$HOME/.claude"
    fi
    
    # Directories to link (list of directory names to link instead of skip)
    LINK_DIRECTORIES=("commands" "agents" "scripts" "assets" "skills" "rules")
    
    for claudefile in "${DOTDIR_ROOT}"/.claude/* ; do
        [[ ! -e "$claudefile" ]] && continue
        filename=$(basename "$claudefile")
        
        if [[ -d "$claudefile" ]]; then
            # Check if this directory should be linked
            should_link=false
            for link_dir in "${LINK_DIRECTORIES[@]}"; do
                if [[ "$filename" == "$link_dir" ]]; then
                    should_link=true
                    break
                fi
            done
            
            if [[ "$should_link" == true ]]; then
                # Link directory
                ln -fnsv "$claudefile" "$HOME/.claude/$filename"
            fi
            # Other directories are skipped (can be added to LINK_DIRECTORIES if needed)
        else
            # Link files
            ln -fnsv "$claudefile" "$HOME/.claude/$filename"
        fi
    done
fi

# Link .gemini directory (Gemini configuration)
if [ -d "${DOTDIR_ROOT}/.gemini" ]; then
    echo "Linking .gemini configuration files..."
    if [ ! -d "$HOME/.gemini" ]; then
        mkdir -p "$HOME/.gemini"
    fi
    
    for geminifile in "${DOTDIR_ROOT}"/.gemini/* ; do
        [[ ! -e "$geminifile" ]] && continue
        [[ -d "$geminifile" ]] && continue  # Skip directories
        [[ "$geminifile" == "${DOTDIR_ROOT}/.gemini/README.md" ]] && continue  # Skip README
        filename=$(basename "$geminifile")
        ln -fnsv "$geminifile" "$HOME/.gemini/$filename"
    done
fi

