<div align="center">

# ⬆️ Claude Code Updater

**One-command Claude Code updater with automatic error recovery, cross-platform**

[![GitHub release](https://img.shields.io/github/v/release/circleone1980/claude-code-updater?include_prereleases&label=version)](https://github.com/circleone1980/claude-code-updater/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20WSL%20%7C%20Linux%20%7C%20macOS-lightgrey)]()
[![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue.svg)]()

English · [简体中文](README.md)

</div>

---

## ✨ Features

- 🌍 **Cross-platform** — Windows / WSL / Linux / macOS
- 🔍 **Auto version detection** — GitHub API with npm fallback
- 🔒 **File locking** — Prevents concurrent update conflicts
- 🧹 **Smart cleanup** — Kills orphan processes, removes corrupted dirs
- 🔄 **Retry on failure** — Automatic retry with cleanup on network errors
- 🌐 **Proxy support** — Via `HTTPS_PROXY` environment variable
- ✅ **Install verification** — Confirms version after update
- 🪙 **Zero AI tokens** — The script does all the work, no AI analysis needed

## 📦 Installation

### Option 1: Install as a Claude Code Skill (Recommended)

```bash
git clone https://github.com/circleone1980/claude-code-updater.git
cd claude-code-updater
make install
```

Or manually:

```bash
# Git Bash / Linux / macOS
cp -r update-claude-code ~/.claude/skills/

# Windows CMD
xcopy /E /I update-claude-code %USERPROFILE%\.claude\skills\update-claude-code
```

### Option 2: Run Standalone

```bash
git clone https://github.com/circleone1980/claude-code-updater.git
cd claude-code-updater
py update-claude-code/scripts/update.py
```

## 🚀 Usage

### In Claude Code

Once installed as a skill, simply tell Claude:

> `update claude` · `check for updates` · `upgrade claude code`

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
# Linux / macOS / Git Bash
export HTTPS_PROXY=http://127.0.0.1:7890

# Windows PowerShell
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
```

## 🛠️ How It Works

```
 🔒 Acquire file lock → 🧹 Kill orphan processes → 🔍 Detect current version
         ↓
 🌐 Fetch latest version (GitHub → npm fallback)
         ↓
 ⚖️ Compare versions → ⏭️ Already latest? → ✅ Done
         ↓
 📦 npm install (with timeout & retry)
         ↓
 ✅ Verify version → 🔓 Release lock
```

## 🖥️ Platform Support

| Platform | Status | Notes |
|:---:|:---:|:---|
| 🪟 Windows | ✅ | Native + Git Bash + PowerShell |
| 🐧 WSL | ✅ | Full process management |
| 🐧 Linux | ✅ | All major distributions |
| 🍎 macOS | ✅ | macOS 10.15+ |

## 📋 Requirements

**Required:**
- Python 3.6+
- npm
- Claude Code (installed)

**Optional (improves reliability):**
```bash
pip install psutil requests filelock
```

| Package | Purpose |
|:---|:---|
| `psutil` | Orphan process detection & cleanup |
| `requests` | More robust HTTP handling |
| `filelock` | Cross-platform file locking |

## ⚙️ Configuration

See [configuration.md](update-claude-code/references/configuration.md) for timeout, retry settings, and platform notes.

## 🔧 Troubleshooting

See [troubleshooting.md](update-claude-code/references/troubleshooting.md) for common issues.

## 👨‍💻 Development

```bash
make validate   # Validate SKILL.md format
make test       # Syntax check update.py
make package    # Package as .skill
make clean      # Remove build artifacts
```

## 📄 License

[MIT](LICENSE)
