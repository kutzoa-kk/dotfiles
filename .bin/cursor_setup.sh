#!/bin/zsh

# Cursor extensions installation script
# This script installs Cursor extensions from cursor-extensions.txt

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../dotdir" && pwd)"
EXTENSIONS_FILE="${REPO_ROOT}/.cursor/cursor-extensions.txt"

# Check if cursor command is available
if ! command -v cursor &> /dev/null; then
    echo -e "${RED}Error: Cursor command not found.${NC}"
    echo -e "${YELLOW}Please install Cursor or ensure it's in your PATH.${NC}"
    exit 1
fi

# Check if extensions file exists
if [ ! -f "$EXTENSIONS_FILE" ]; then
    echo -e "${RED}Error: Extensions file not found: ${EXTENSIONS_FILE}${NC}"
    exit 1
fi

echo -e "${BLUE}Installing Cursor extensions from ${EXTENSIONS_FILE}...${NC}"
echo ""

# Count total extensions
total=$(grep -v '^#' "$EXTENSIONS_FILE" | grep -v '^$' | wc -l | tr -d ' ')
installed=0
failed=0

# Read each line from the extensions file and install
while IFS= read -r extension_id || [ -n "$extension_id" ]; do
    # Skip empty lines and comments
    [[ -z "$extension_id" ]] && continue
    [[ "$extension_id" =~ ^#.*$ ]] && continue
    
    # Trim whitespace
    extension_id=$(echo "$extension_id" | xargs)
    [[ -z "$extension_id" ]] && continue
    
    echo -e "${BLUE}→ Installing: ${extension_id}${NC}"
    
    if cursor --install-extension "$extension_id" &> /dev/null; then
        echo -e "${GREEN}✓ Installed: ${extension_id}${NC}"
        ((installed++))
    else
        echo -e "${RED}✗ Failed to install: ${extension_id}${NC}"
        ((failed++))
    fi
done < "$EXTENSIONS_FILE"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Total extensions: ${total}"
echo -e "${GREEN}Installed: ${installed}${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Failed: ${failed}${NC}"
    exit 1
else
    echo -e "${GREEN}All extensions installed successfully!${NC}"
    exit 0
fi

