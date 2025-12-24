#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Link dotfiles from repository root (files only, directories are handled separately)
for dotfile in "${REPO_ROOT}"/.??* ; do
    [[ "$dotfile" == "${REPO_ROOT}/.git" ]] && continue
    [[ "$dotfile" == "${REPO_ROOT}/.github" ]] && continue
    [[ "$dotfile" == "${REPO_ROOT}/.DS_Store" ]] && continue
    [[ "$dotfile" == "${REPO_ROOT}/.ssh" ]] && continue  # Handle .ssh separately
    [[ "$dotfile" == "${REPO_ROOT}/.cursor" ]] && continue  # Handle .cursor separately
    [[ "$dotfile" == "${REPO_ROOT}/.config" ]] && continue  # Handle .config separately
    [[ "$dotfile" == "${REPO_ROOT}/.bin" ]] && continue  # Skip .bin directory (scripts)
    
    # Only link files, not directories
    [[ -d "$dotfile" ]] && continue
    
    ln -fnsv "$dotfile" "$HOME"
done

# Link .ssh directory (if exists)
if [ -d "${REPO_ROOT}/.ssh" ]; then
    echo "Linking .ssh directory..."
    if [ ! -d "$HOME/.ssh" ]; then
        mkdir -p "$HOME/.ssh"
        chmod 700 "$HOME/.ssh"
    fi
    
    for sshfile in "${REPO_ROOT}"/.ssh/* ; do
        [[ ! -e "$sshfile" ]] && continue
        filename=$(basename "$sshfile")
        ln -fnsv "$sshfile" "$HOME/.ssh/$filename"
    done
fi

# Link .cursor directory (merge approach: link files only, preserve existing directory)
if [ -d "${REPO_ROOT}/.cursor" ]; then
    echo "Linking .cursor configuration files..."
    if [ ! -d "$HOME/.cursor" ]; then
        mkdir -p "$HOME/.cursor"
    fi
    
    for cursorfile in "${REPO_ROOT}"/.cursor/* ; do
        [[ ! -e "$cursorfile" ]] && continue
        [[ -d "$cursorfile" ]] && continue  # Skip directories
        filename=$(basename "$cursorfile")
        ln -fnsv "$cursorfile" "$HOME/.cursor/$filename"
    done
fi

# Link .config/git directory (merge approach: link files only, preserve existing directory)
if [ -d "${REPO_ROOT}/.config/git" ]; then
    echo "Linking .config/git configuration files..."
    if [ ! -d "$HOME/.config/git" ]; then
        mkdir -p "$HOME/.config/git"
    fi
    
    for gitfile in "${REPO_ROOT}"/.config/git/* ; do
        [[ ! -e "$gitfile" ]] && continue
        [[ -d "$gitfile" ]] && continue  # Skip directories
        filename=$(basename "$gitfile")
        ln -fnsv "$gitfile" "$HOME/.config/git/$filename"
    done
fi
