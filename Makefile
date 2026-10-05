# Run all setup scripts (for new machine migration)
all: init link brew macos_setup iterm2

# Quick setup script (interactive)
setup:
	@echo "\033[0;34mRun setup.sh (interactive setup)\033[0m"
	@.bin/setup.sh
	@echo "\033[0;32mDone.\033[0m"

# run init.sh
init:
	@echo "\033[0;34mRun init.sh\033[0m"
	@.bin/init.sh
	@echo "\033[0;34mDone.\033[0m"

# next create symbolic links
link:
	@echo "\033[0;34mRun link.sh\033[0m"
	@.bin/link.sh
	@echo "\033[0;34mDone.\033[0m"

# Apply only the Codex security-guidance hook adapter (safe to repeat after updates)
.PHONY: codex-security-hooks codex-security-hooks-check codex-security-hooks-dry-run test-codex-security-hooks
codex-security-hooks:
	@python3 .bin/apply-codex-security-guidance.py

codex-security-hooks-check:
	@python3 .bin/apply-codex-security-guidance.py --check

codex-security-hooks-dry-run:
	@python3 .bin/apply-codex-security-guidance.py --dry-run

test-codex-security-hooks:
	@python3 -m unittest discover -s .bin/tests -p 'test_codex_security_guidance.py' -v

# Pull permanent settings from live ~/.claude into git (dotdir)
settings-pull:
	@echo "\033[0;34mRun settings-pull.sh\033[0m"
	@.bin/settings-pull.sh

# Install macOS applications.
brew:
	@echo "\033[0;34mRun brew.sh\033[0m"
	@.bin/brew.sh
	@echo "\033[0;32mDone.\033[0m"

# Set GitHub
github:
	@echo "\033[0;34mRun github.sh\033[0m"
	@.bin/github.sh
	@echo "\033[0;32mDone.\033[0m"

# Set macOS system preferences.
macos_setup:
	@echo "\033[0;34mRun macos_setup.sh\033[0m"
	@.bin/macos_setup.sh
	@echo "\033[0;32mDone.\033[0m"

# Set iTerm2 preferences.
iterm2:
	@echo "\033[0;34mRun iterm2_setup.sh\033[0m"
	@.bin/iterm2_setup.sh
	@echo "\033[0;32mDone.\033[0m"

# Install npm global packages.
npm:
	@echo "\033[0;34mRun npm_install.sh\033[0m"
	@.bin/npm_install.sh
	@echo "\033[0;32mDone.\033[0m"

# Install Cursor extensions.
cursor:
	@echo "\033[0;34mRun cursor_setup.sh\033[0m"
	@.bin/cursor_setup.sh
	@echo "\033[0;32mDone.\033[0m"

# Record human/agent working time to Google Calendar (see .bin/worklog)
.PHONY: worklog-install worklog-uninstall test-worklog
worklog-install:
	@.bin/worklog/install.sh install

worklog-uninstall:
	@.bin/worklog/install.sh uninstall

test-worklog:
	@/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_*.py' -v
