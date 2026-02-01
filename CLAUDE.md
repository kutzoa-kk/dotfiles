# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

macOS dotfiles repository for development environment configuration. Manages shell, git, SSH, and AI tool settings (Claude, Codex, Cursor, Gemini).

## Commands

```bash
# Full setup (interactive, for new machine)
make setup

# All setup steps non-interactively
make all

# Individual targets
make init          # Homebrew, Xcode CLI Tools, Rosetta 2
make link          # Create symlinks
make brew          # Install packages from .Brewfile
make macos_setup   # Apply macOS system preferences
make iterm2        # Import iTerm2 settings
make npm           # Install npm global packages
make cursor        # Install Cursor extensions
make github        # GitHub SSH key setup
```

## Architecture

### Directory Structure

- **Root level**: Shell configs (`.zshrc`, `.zprofile`, `.p10k.zsh`), `.gitconfig`, `.Brewfile`
- **`dotdir/`**: Tool-specific configs that get symlinked to `$HOME`
  - `.claude/` - ClaudeCode: commands, agents, scripts, assets
  - `.codex/` - Codex config and user skills
  - `.cursor/` - Cursor editor and MCP settings
  - `.gemini/` - Gemini settings
  - `.ssh/` - SSH config (keys not included)
  - `.config/git/` - Git ignore and commit template
- **`.bin/`**: Setup scripts (not symlinked)
- **`iterm2/`**: iTerm2 plist (imported via `defaults`)

### Symlink Strategy (`link.sh`)

The linking logic varies by directory:

| Source | Target | Strategy |
|--------|--------|----------|
| Root `.??*` files | `$HOME` | Direct link (excludes `.git`, `.bin`, directories) |
| `dotdir/.ssh/*` | `~/.ssh/` | File-by-file merge |
| `dotdir/.config/git/*` | `~/.config/git/` | File-by-file merge |
| `dotdir/.cursor/*` | `~/.cursor/` | Files only, User/ handled separately |
| `dotdir/.cursor/User/` | `~/Library/Application Support/Cursor/User/` | settings.json, keybindings.json, snippets |
| `dotdir/.codex/*` | `~/.codex/` | Files + skills/ subdirectories |
| `dotdir/.claude/*` | `~/.claude/` | Files + specific dirs (commands, agents, scripts, assets) |
| `dotdir/.gemini/*` | `~/.gemini/` | Files only |

### Key Design Decisions

- Private keys excluded from `.ssh/` - must be copied manually
- Cursor extensions list (`cursor-extensions.txt`) excluded from linking - installed via script
- User-specific runtime directories preserved (e.g., Cursor caches)
- AI tool configs use merge strategy to coexist with tool-managed files
