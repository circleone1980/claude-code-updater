---
name: update-claude-code
description: Use this skill when the user wants to update, upgrade, or check the version of Claude Code. Handles Windows exe file locks by renaming before install. Works while Claude is running on Windows. Trigger phrases include update claude, upgrade claude code, check for updates, or any mention of Claude Code version concerns.
---

# Claude Code Updater

## Quick Start

Run the updater script:

```
py ~/.claude/skills/update-claude-code/scripts/update.py
```

On Windows CMD/PowerShell:
```
py %USERPROFILE%\.claude\skills\update-claude-code\scripts\update.py
```

The script handles everything: version detection, file lock handling, installation, verification.

## How It Works (Windows)

When Claude is running on Windows, `claude.exe` is locked and npm install fails with EBUSY.
The script works around this by:

1. Renaming locked `claude.exe` → `claude.exe.old` (Windows allows renaming running exe)
2. Running `npm install -g --force` (succeeds because original path is now free)
3. Cleaning up `.old` files after successful install

This allows updating Claude **without closing the current session**.

## What It Handles Automatically

| Issue | Resolution |
|-------|------------|
| Windows EBUSY file lock | Renames exe files before install |
| GitHub API timeout/rate limit | Falls back to npm registry |
| ENOTEMPTY directory conflict | Removes conflicting directories |
| Zombie npm processes | Kills orphan processes holding files |
| Installation timeout | Retries with cleanup |
| Corrupted installation | Full cleanup before reinstall |
| Concurrent updates | File locking prevents conflicts |
| Cross-platform paths | Uses OS-appropriate temp directories |
| Volta npm shim | Works with or without Volta |

## Exit Codes

- **Exit 0**: Success (updated or already up to date)
- **Exit 1**: Failed (script prints error + manual install command)

## Reporting Results

**On success (exit 0):** Report the version change:
- "Already up to date (X.Y.Z)"
- "Updated: X.Y.Z -> A.B.C"

**On failure (exit 1):** The script already printed the error and manual install command. Tell the user the update failed and show the manual command.

## Proxy Configuration

The script reads proxy settings from standard environment variables:
- `HTTPS_PROXY` or `HTTP_PROXY`

Set these before running if you need a proxy. No hardcoded proxy values.

## Optional Dependencies

For improved reliability, install these optional packages:

```
pip install psutil requests filelock
```

The script works without them but with reduced process management and locking capabilities.

## References

- See `references/troubleshooting.md` for common issues and fixes
- See `references/configuration.md` for tunable parameters and platform notes
