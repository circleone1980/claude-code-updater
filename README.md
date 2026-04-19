# Claude Code Updater

A cross-platform skill that updates [Claude Code](https://docs.anthropic.com/en/docs/claude-code) to the latest version. Handles network failures, process locks, directory conflicts, and installation corruption automatically.

## Features

- Cross-platform: Windows, WSL, Linux, macOS
- Automatic version detection (GitHub API + npm fallback)
- Proxy support via standard environment variables
- Orphan process cleanup before install
- File locking prevents concurrent updates
- Retries with cleanup on failure
- Installation verification
- Zero AI token consumption for the actual update work

## Installation

### Option 1: Install as a Claude Code Skill

Clone into your skills directory:

```bash
git clone https://github.com/YOUR_USERNAME/claude-code-updater.git
cd claude-code-updater
make install
```

Or manually:

```bash
# Linux/macOS
cp -r update-claude-code ~/.claude/skills/

# Windows (Git Bash)
cp -r update-claude-code ~/.claude/skills/

# Windows CMD
xcopy /E /I update-claude-code %USERPROFILE%\.claude\skills\update-claude-code
```

### Option 2: Run Standalone

```bash
git clone https://github.com/YOUR_USERNAME/claude-code-updater.git
cd claude-code-updater
py update-claude-code/scripts/update.py
```

## Usage

### In Claude Code

Once installed as a skill, simply tell Claude:

```
update claude
check for updates
upgrade claude code
```

Claude will invoke the update script automatically.

### From Command Line

```bash
# Git Bash / Linux / macOS
py ~/.claude/skills/update-claude-code/scripts/update.py

# Windows CMD / PowerShell
py %USERPROFILE%\.claude\skills\update-claude-code\scripts\update.py
```

### With Proxy

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
py ~/.claude/skills/update-claude-code/scripts/update.py
```

## Requirements

**Required:**
- Python 3.6+
- npm
- Claude Code (installed)

**Optional (improves reliability):**
```bash
pip install psutil requests filelock
```

## How It Works

```
1. Acquire file lock (prevents concurrent updates)
2. Kill orphan npm processes (if psutil available)
3. Detect current Claude Code version
4. Fetch latest version from GitHub (fallback to npm)
5. Compare versions → skip if up to date
6. Install via npm with timeout and retry
7. Verify installed version matches target
8. Release lock
```

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Windows | Supported | Native + Git Bash + PowerShell |
| WSL | Supported | Full process management |
| Linux | Supported | All distributions |
| macOS | Supported | macOS 10.15+ |

## Configuration

See `update-claude-code/references/configuration.md` for tunable parameters and platform-specific notes.

## Troubleshooting

See `update-claude-code/references/troubleshooting.md` for common issues.

## Development

```bash
make validate   # Validate SKILL.md format
make test       # Syntax check update.py
make package    # Create .skill package
make clean      # Remove build artifacts
```

## License

MIT
