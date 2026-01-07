#!/bin/zsh

# Install npm global packages
# This script installs npm packages listed in .npm-global-packages.txt

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed or not in PATH"
    echo "Please install Node.js first (nvm is recommended)"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PACKAGES_FILE="${REPO_ROOT}/.npm-global-packages.txt"

# Check if packages file exists
if [ ! -f "$PACKAGES_FILE" ]; then
    echo "Warning: .npm-global-packages.txt not found at ${PACKAGES_FILE}"
    exit 0
fi

echo "Installing npm global packages..."

# Read packages from file and install them
while IFS= read -r package; do
    # Skip empty lines and comments
    [[ -z "$package" ]] && continue
    [[ "$package" =~ ^[[:space:]]*# ]] && continue
    
    echo "Installing: $package"
    npm install -g "$package" || echo "Warning: Failed to install $package"
done < "$PACKAGES_FILE"

echo "npm global packages installation completed."

