# Troubleshooting

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

The lock file is located in your system's temporary directory.

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

## ENOTEMPTY or directory conflicts

The script cleans up partial installations automatically. If it persists:

1. Find your npm global root: `npm root -g`
2. Remove `@anthropic-ai/claude-code` directory manually
3. Run the updater again
