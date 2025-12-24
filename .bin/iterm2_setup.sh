#!/bin/zsh

# Check operating system
if [ "$(uname)" != "Darwin" ] ; then
	echo "Not macOS!"
	exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ITERM2_PLIST="${REPO_ROOT}/iterm2/com.googlecode.iterm2.plist"

# Check if iTerm2 plist file exists
if [ ! -f "${ITERM2_PLIST}" ]; then
    echo "Error: iTerm2 plist file not found at ${ITERM2_PLIST}"
    exit 1
fi

# Check if iTerm2 is installed
if [ ! -d "/Applications/iTerm.app" ]; then
    echo "Warning: iTerm2 is not installed. Please install it first using: make brew"
    echo "Do you want to continue anyway? [y/N]"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        exit 1
    fi
fi

echo -e "\033[0;34mSetting up iTerm2 preferences...\033[0m"

# Import iTerm2 preferences
# Note: This will overwrite existing iTerm2 preferences
defaults import com.googlecode.iterm2 "${ITERM2_PLIST}" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "\033[0;32miTerm2 preferences imported successfully.\033[0m"
    echo "Note: You may need to restart iTerm2 for changes to take effect."
else
    echo -e "\033[0;31mError: Failed to import iTerm2 preferences.\033[0m"
    exit 1
fi

