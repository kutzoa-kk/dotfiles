#!/bin/zsh

# Dotfiles setup script for new machine migration
# This script sets up a new machine with all dotfiles configurations

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check operating system
if [ "$(uname)" != "Darwin" ]; then
    echo -e "${RED}Error: This script is designed for macOS only.${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Dotfiles Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to run a script and handle errors
run_script() {
    local script_name=$1
    local description=$2
    local script_path="${SCRIPT_DIR}/${script_name}"
    
    if [ ! -f "$script_path" ]; then
        echo -e "${RED}Error: Script not found: ${script_path}${NC}"
        return 1
    fi
    
    echo -e "${BLUE}→ ${description}${NC}"
    if zsh "$script_path"; then
        echo -e "${GREEN}✓ ${description} completed${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ ${description} failed${NC}"
        echo ""
        return 1
    fi
}

# Step 1: Install Homebrew and prerequisites
echo -e "${YELLOW}Step 1: Installing Homebrew and prerequisites...${NC}"
run_script "init.sh" "Homebrew installation"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install Homebrew. Please check the error above.${NC}"
    exit 1
fi

# Ensure Homebrew is in PATH (especially for Apple Silicon)
if [ "$(uname -m)" = "arm64" ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
elif [ -f /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null || true
fi

# Step 2: Create symbolic links for dotfiles
echo -e "${YELLOW}Step 2: Creating symbolic links for dotfiles...${NC}"
run_script "link.sh" "Dotfiles linking"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Some dotfiles may not have been linked.${NC}"
fi

# Step 3: Install Homebrew packages
echo -e "${YELLOW}Step 3: Installing Homebrew packages...${NC}"
run_script "brew.sh" "Homebrew packages installation"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Some packages may not have been installed.${NC}"
fi

# Step 4: Apply macOS system preferences
echo -e "${YELLOW}Step 4: Applying macOS system preferences...${NC}"
run_script "macos_setup.sh" "macOS system preferences"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Some system preferences may not have been applied.${NC}"
fi

# Step 5: Apply iTerm2 preferences (if iTerm2 is installed)
echo -e "${YELLOW}Step 5: Applying iTerm2 preferences...${NC}"
if [ -d "/Applications/iTerm.app" ] || brew list --cask iterm2 &>/dev/null; then
    run_script "iterm2_setup.sh" "iTerm2 preferences"
else
    echo -e "${YELLOW}Skipping iTerm2 setup (iTerm2 not installed yet).${NC}"
    echo -e "${YELLOW}You can run 'make iterm2' later to apply iTerm2 preferences.${NC}"
    echo ""
fi

# Step 6: GitHub setup (optional)
echo -e "${YELLOW}Step 6: GitHub SSH setup (optional)...${NC}"
echo -e "${BLUE}Do you want to set up GitHub SSH keys? [y/N]${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    run_script "github.sh" "GitHub SSH setup"
else
    echo -e "${YELLOW}Skipping GitHub setup.${NC}"
    echo -e "${YELLOW}You can run 'make github' later to set up GitHub.${NC}"
    echo ""
fi

# Final message
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Restart your terminal or run: ${YELLOW}source ~/.zshrc${NC}"
echo -e "2. If you skipped iTerm2 setup, run: ${YELLOW}make iterm2${NC}"
echo -e "3. If you skipped GitHub setup, run: ${YELLOW}make github${NC}"
echo ""

