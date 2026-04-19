# Configuration

## Tunable Parameters

These constants in `scripts/update.py` can be adjusted:

| Variable | Default | Purpose |
|----------|---------|---------|
| `INSTALL_TIMEOUT` | 90 | Seconds to wait for npm install |
| `PROCESS_KILL_WAIT` | 3 | Seconds to wait after killing processes |
| `MAX_RETRIES` | 2 | Retry attempts for installation |
| `ORPHAN_AGE_THRESHOLD` | 30 | Seconds before considering a process orphan |

## Proxy Configuration

The script reads proxy settings from standard environment variables:

- `HTTPS_PROXY` — preferred
- `HTTP_PROXY` — fallback

### Setting proxy on different platforms:

**Linux/macOS:**
```bash
export HTTPS_PROXY=http://127.0.0.1:7890
```

**Windows CMD:**
```cmd
set HTTPS_PROXY=http://127.0.0.1:7890
```

**Windows PowerShell:**
```powershell
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
```

If neither variable is set, the script connects directly.

## Platform Notes

### Windows
- Uses `%TEMP%` for temporary files
- Color output requires Windows Terminal or Git Bash
- Process cleanup may require Administrator privileges
- Use `py` (Python Launcher) instead of `python` if available

### WSL
- Works like native Linux
- Uses `/tmp` for temporary files
- Full process management support via psutil

### Linux
- Full support with all features
- Uses `/tmp` for temporary files
- Best experience with psutil installed

### macOS
- Full support with all features
- Uses `/tmp` for temporary files
- Best experience with psutil installed

## Optional Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `psutil` | Process management (orphan detection, CPU checks) | `pip install psutil` |
| `requests` | Better HTTP handling | `pip install requests` |
| `filelock` | Cross-platform file locking | `pip install filelock` |

All are optional. The script degrades gracefully without them.
