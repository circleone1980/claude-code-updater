# Troubleshooting

## "EBUSY: resource busy or locked" on Windows

This happens when Claude is running and npm tries to overwrite `claude.exe`.
The script handles this automatically by renaming locked files before install.
If it still fails:

1. Close all Claude Code sessions
2. Run the updater again
3. Or manually: `npm install -g @anthropic-ai/claude-code@latest`

## "Permission denied" errors

- **Windows**: Run as Administrator
- **Linux/macOS**: Use `sudo` if npm global directory requires elevated privileges

## "psutil not available" warning

This is normal and non-blocking. Install for better process management:

```bash
pip install psutil
```

Without psutil, the script skips orphan process cleanup.

## Lock file issues

If the script reports another update is running but it's not:

1. Delete the lock file:
   - Windows: `%TEMP%\claude-update.lock`
   - Linux/macOS: `/tmp/claude-update.lock`
2. Run the script again

## Network timeout

The script tries GitHub API first, then falls back to npm registry.

If both fail:
1. Check your internet connection
2. If behind a proxy, set `HTTPS_PROXY` environment variable
3. Try manual install:
   ```bash
   npm install -g @anthropic-ai/claude-code@latest
   ```

## "Claude Code not found"

Ensure Claude Code is installed globally:

```bash
npm install -g @anthropic-ai/claude-code
```

Verify with:
```bash
claude --version
```

## Leftover .old files

After updates on Windows, `claude.exe.old` files may remain if Claude was running.
The script cleans these on the next update run. To clean manually:

```bash
# Find and remove .old files
find "$(npm root -g)/@anthropic-ai" -name "*.old" -delete
```

## ENOTEMPTY or directory conflicts

The script cleans up partial installations automatically. If it persists:

1. Find your npm global root: `npm root -g`
2. Remove `@anthropic-ai/claude-code` directory manually
3. Run the updater again
