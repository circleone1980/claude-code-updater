#!/usr/bin/env python3
"""
Claude Code Updater - Cross-Platform Version
Supports: Windows, WSL, Linux, macOS

Windows: Renames locked exe files before npm install to avoid EBUSY errors.
Other platforms: Standard npm install.
"""

import sys
import os
import re
import shutil
import subprocess
import time
import json
import tempfile
import platform
import urllib.request
from pathlib import Path
from typing import Optional, List

# Try to import optional dependencies
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from filelock import FileLock
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# =============================================================================
# CONFIGURATION
# =============================================================================

INSTALL_TIMEOUT = 120  # seconds (increased for large platform packages)
PROCESS_KILL_WAIT = 3  # seconds
MAX_RETRIES = 2
ORPHAN_AGE_THRESHOLD = 30  # seconds

VERSION_PATTERN = re.compile(r'(\d+\.\d+\.\d+)')

# Locked exe paths relative to npm root (Windows only)
LOCKED_EXE_RELPATHS = [
    Path('@anthropic-ai') / 'claude-code' / 'bin' / 'claude.exe',
    Path('@anthropic-ai') / 'claude-code' / 'node_modules' / '@anthropic-ai' / 'claude-code-win32-x64' / 'claude.exe',
]


def extract_version(text: str) -> Optional[str]:
    match = VERSION_PATTERN.search(text)
    return match.group(1) if match else None


def _get_proxies() -> dict:
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY') or \
            os.environ.get('https_proxy') or os.environ.get('http_proxy')
    if proxy:
        return {'http': proxy, 'https': proxy}
    return {}


# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

    @classmethod
    def is_color_supported(cls):
        if not (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()):
            return False
        if platform.system() == 'Windows':
            return 'WT_SESSION' in os.environ or 'MSYSTEM' in os.environ
        return True

    @classmethod
    def colorize(cls, color, text):
        if cls.is_color_supported():
            return f"{color}{text}{cls.NC}"
        return text


# =============================================================================
# LOGGING
# =============================================================================

def log_info(message):
    print(Colors.colorize(Colors.BLUE, f"[INFO] {message}"), file=sys.stderr)

def log_success(message):
    print(Colors.colorize(Colors.GREEN, f"[OK] {message}"), file=sys.stderr)

def log_warn(message):
    print(Colors.colorize(Colors.YELLOW, f"[WARN] {message}"), file=sys.stderr)

def log_error(message):
    print(Colors.colorize(Colors.RED, f"[ERROR] {message}"), file=sys.stderr)


# =============================================================================
# VERSION DETECTION
# =============================================================================

def get_current_version() -> Optional[str]:
    try:
        use_shell = platform.system() == 'Windows'
        result = subprocess.run(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5,
            shell=use_shell
        )
        if result.returncode == 0:
            return extract_version(result.stdout + result.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        log_warn(f"Version detection error: {e}")
    return None


def compare_versions(v1: str, v2: str) -> str:
    t1 = tuple(int(x) for x in v1.split('.'))
    t2 = tuple(int(x) for x in v2.split('.'))
    if t1 == t2:
        return 'eq'
    return 'gt' if t1 > t2 else 'lt'


def get_version_npm() -> Optional[str]:
    try:
        result = subprocess.run(
            ['npm', 'view', '@anthropic-ai/claude-code', 'version'],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            if version and VERSION_PATTERN.match(version):
                return version
    except Exception:
        pass
    return None


def get_version_github() -> Optional[str]:
    from urllib.request import urlopen, Request, ProxyHandler, build_opener

    try:
        url = "https://api.github.com/repos/anthropics/claude-code/releases/latest"
        headers = {'User-Agent': 'Claude-Code-Updater'}
        proxies = _get_proxies()

        if HAS_REQUESTS:
            kwargs = {'headers': headers, 'timeout': 5}
            if proxies:
                kwargs['proxies'] = proxies
            response = requests.get(url, **kwargs)
            if response.status_code != 200:
                return None
            data = response.json()
        else:
            request = Request(url, headers=headers)
            if proxies:
                proxy_handler = ProxyHandler(proxies)
                opener = build_opener(proxy_handler)
                response = opener.open(request, timeout=5)
            else:
                response = urlopen(request, timeout=5)
            data = json.loads(response.read().decode())

        return extract_version(data.get('tag_name', ''))
    except Exception:
        pass
    return None


def get_latest_version() -> Optional[str]:
    version = get_version_github()
    if version:
        return version

    log_warn("GitHub API failed, trying npm registry...")
    version = get_version_npm()
    if version:
        return version

    return None


# =============================================================================
# NPM HELPERS
# =============================================================================

def get_npm_root() -> Optional[Path]:
    try:
        result = subprocess.run(
            ['npm', 'root', '-g'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


# =============================================================================
# WINDOWS EXE RENAME (avoids EBUSY during npm install)
# =============================================================================

def rename_locked_exes(npm_root: Path) -> List[Path]:
    """Rename locked .exe files to .exe.old so npm can overwrite them."""
    renamed = []
    for relpath in LOCKED_EXE_RELPATHS:
        exe_path = npm_root / relpath
        if not exe_path.exists():
            continue
        old_path = exe_path.with_suffix('.exe.old')
        try:
            try:
                old_path.unlink()
            except FileNotFoundError:
                pass
            exe_path.rename(old_path)
            log_info(f"Renamed locked file: {relpath.name} -> {relpath.name}.old")
            renamed.append(old_path)
        except Exception as e:
            log_warn(f"Could not rename {relpath}: {e}")
    return renamed


def restore_renamed_exes(renamed: List[Path]):
    """Restore .old files if install fails."""
    for old_path in renamed:
        original = old_path.with_suffix('')  # .exe.old -> .exe
        try:
            if not original.exists() and old_path.exists():
                old_path.rename(original)
                log_info(f"Restored: {original.name}")
        except Exception as e:
            log_warn(f"Could not restore {original}: {e}")


def cleanup_old_files(npm_root: Path):
    """Remove leftover .old files from previous updates."""
    for relpath in LOCKED_EXE_RELPATHS:
        old_path = npm_root / relpath.with_suffix('.exe.old')
        if old_path.exists():
            try:
                old_path.unlink()
                log_info(f"Cleaned up: {old_path.name}")
            except Exception:
                pass


# =============================================================================
# PROCESS CLEANUP
# =============================================================================

def kill_orphan_processes():
    log_info("Scanning for orphan npm install processes...")

    if not HAS_PSUTIL:
        log_warn("psutil not available, skipping process cleanup")
        return

    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if not cmdline:
                continue
            cmdline_str = ' '.join(cmdline).lower()
            if 'npm' in cmdline_str and 'install' in cmdline_str and 'claude-code' in cmdline_str:
                pid = proc.info['pid']
                age = time.time() - proc.info.get('create_time', 0)
                name = proc.info.get('name', 'unknown')

                if age < ORPHAN_AGE_THRESHOLD:
                    continue

                parent = proc.parent()
                if parent and parent.pid != 1:
                    try:
                        parent.status()
                        continue
                    except psutil.NoSuchProcess:
                        pass

                log_warn(f"Killing orphan process {pid} ({name})")
                try:
                    proc.kill()
                    killed_count += 1
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if killed_count > 0:
        log_info(f"Killed {killed_count} orphan process(es)")
        time.sleep(PROCESS_KILL_WAIT)


# =============================================================================
# DIRECTORY CLEANUP
# =============================================================================

def cleanup_npm_temp_dirs(npm_root: Path):
    """Remove stale .claude-code-* temp directories left by npm."""
    anthropic_dir = npm_root / '@anthropic-ai'
    if not anthropic_dir.exists():
        return
    for item in anthropic_dir.iterdir():
        if item.name.startswith('.claude-code-'):
            log_info(f"Removing temp dir: {item.name}")
            shutil.rmtree(item, ignore_errors=True)


# =============================================================================
# INSTALLATION
# =============================================================================

def do_install(target_version: str, npm_root: Path) -> bool:
    install_cmd = ['npm', 'install', '-g', '--force', f'@anthropic-ai/claude-code@{target_version}']
    log_info(f"Installing version {target_version} (timeout: {INSTALL_TIMEOUT}s)...")

    log_path = os.path.join(tempfile.gettempdir(), f'claude-update-{os.getpid()}.log')

    with open(log_path, 'w') as log_fd:
        proc = subprocess.Popen(
            install_cmd,
            stdout=log_fd,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            proc.wait(timeout=INSTALL_TIMEOUT)

            if proc.returncode == 0:
                _safe_unlink(log_path)
                return True

            log_error(f"Install failed with exit code {proc.returncode}")
            _print_log_tail(log_path, 10)
            return False

        except subprocess.TimeoutExpired:
            log_error(f"Install timed out after {INSTALL_TIMEOUT}s")
            proc.kill()
            proc.wait()
            _print_log_tail(log_path, 5)
            return False

        finally:
            _safe_unlink(log_path)


def _print_log_tail(log_path: str, lines: int):
    try:
        with open(log_path, 'r') as f:
            tail = f.readlines()[-lines:]
            for line in tail:
                print(line.rstrip(), file=sys.stderr)
    except Exception:
        pass


def _safe_unlink(path: str):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def install_with_retry(target_version: str, npm_root: Path) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        kill_orphan_processes()
        cleanup_npm_temp_dirs(npm_root)

        renamed = []
        if platform.system() == 'Windows':
            cleanup_old_files(npm_root)
            renamed = rename_locked_exes(npm_root)

        time.sleep(1)

        success = do_install(target_version, npm_root)

        if success:
            # Clean up .old files after successful install
            if platform.system() == 'Windows':
                cleanup_old_files(npm_root)
            return True

        # Restore renamed files on failure
        if renamed:
            log_warn("Install failed, restoring renamed files...")
            restore_renamed_exes(renamed)

        if attempt < MAX_RETRIES:
            log_warn(f"Attempt {attempt} failed, retrying...")
            time.sleep(2)

    return False


# =============================================================================
# VERIFICATION
# =============================================================================

def verify_installation(expected_version: str) -> bool:
    time.sleep(2)

    actual_version = None
    for attempt in range(3):
        actual_version = get_current_version()
        if actual_version and compare_versions(actual_version, expected_version) == 'eq':
            log_success(f"Verified: version {actual_version}")
            return True

        if attempt < 2:
            log_info(f"Verification attempt {attempt + 1} failed, retrying in 3s...")
            time.sleep(3)

    if actual_version:
        log_warn(f"Expected {expected_version}, got {actual_version}")
    else:
        log_error("Could not determine version after install")
    return False


# =============================================================================
# LOCKING
# =============================================================================

class UpdateLock:
    def __init__(self):
        self.lock_file = Path(tempfile.gettempdir()) / 'claude-update.lock'
        self.lock = None
        self.lock_fd = None

    def acquire(self):
        if HAS_FILELOCK:
            self.lock = FileLock(str(self.lock_file), timeout=0)
            try:
                self.lock.acquire(timeout=0.1)
                log_info("Lock acquired")
                return True
            except Exception:
                log_error("Another update is already running")
                log_error(f"If this is incorrect, delete: {self.lock_file}")
                return False
        else:
            if self.lock_file.exists():
                try:
                    age = time.time() - self.lock_file.stat().st_mtime
                    if age < 300:
                        log_error("Another update is already running")
                        log_error(f"If this is incorrect, delete: {self.lock_file}")
                        return False
                except Exception:
                    pass
            try:
                self.lock_fd = open(self.lock_file, 'w')
                self.lock_fd.write(str(os.getpid()))
                self.lock_fd.flush()
                log_info("Lock acquired (simple mode)")
                return True
            except Exception as e:
                log_error(f"Failed to acquire lock: {e}")
                return False

    def release(self):
        try:
            if self.lock:
                self.lock.release()
            if self.lock_fd:
                self.lock_fd.close()
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception:
            pass


# =============================================================================
# MAIN
# =============================================================================

def main():
    lock = UpdateLock()

    try:
        if not lock.acquire():
            sys.exit(1)

        current_version = get_current_version()
        if not current_version:
            log_error("Claude Code not found. Please install it first.")
            sys.exit(1)
        log_info(f"Current version: {current_version}")

        latest_version = get_latest_version()
        if not latest_version:
            log_error("Could not determine latest version. Check internet connection.")
            sys.exit(1)
        log_info(f"Latest version: {latest_version}")

        comparison = compare_versions(current_version, latest_version)

        if comparison == 'eq':
            log_success(f"Already up to date! ({current_version})")
            sys.exit(0)
        elif comparison == 'gt':
            log_success(f"Your version ({current_version}) is newer than release ({latest_version})")
            sys.exit(0)

        log_info(f"Updating: {current_version} -> {latest_version}")

        npm_root = get_npm_root()
        if not npm_root:
            log_error("Could not determine npm global root")
            sys.exit(1)

        if install_with_retry(latest_version, npm_root):
            if verify_installation(latest_version):
                log_success(f"Update complete: {current_version} -> {latest_version}")
                sys.exit(0)

        log_error("Update failed after all retry attempts")
        log_error("")
        log_error("Manual install command:")
        log_error(f"  npm install -g @anthropic-ai/claude-code@{latest_version}")
        sys.exit(1)

    finally:
        lock.release()


if __name__ == '__main__':
    main()
