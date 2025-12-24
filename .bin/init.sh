#!/bin/zsh

# Install brew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
if [ "$(uname -m)" = "arm64" ] ; then
  (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> /Users/${USER}/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Install xcode
# Check if command line tools are installed
if ! xcode-select --print-path &> /dev/null; then
  # Install command line tools
  echo "Command line tools not found. Installing..."
  xcode-select --install
else
  echo "Command line tools are already installed."
fi

# Install Rosetta 2 for Apple Silicon
# Check if Rosetta 2 is installed
if [[ $(sysctl -n machdep.cpu.brand_string) != *"Apple M"* ]]; then
  echo "Rosetta 2 is already installed."
  exit 0
fi

# Install Rosetta 2
/usr/sbin/softwareupdate --install-rosetta --agree-to-license
if [ $? -ne 0 ]; then
  echo "Error: Failed to install Rosetta 2."
  exit 1
fi

echo "Rosetta 2 has been installed successfully."
exit 0
