#!/usr/bin/env python3
"""
Claude Code Updater - Cross-Platform Version
Supports: Windows, WSL, Linux, macOS
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
from pathlib import Path
from typing import Optional

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

INSTALL_TIMEOUT = 90  # seconds
PROCESS_KILL_WAIT = 3  # seconds
MAX_RETRIES = 2
ORPHAN_AGE_THRESHOLD = 30  # seconds

VERSION_PATTERN = re.compile(r'(\d+\.\d+\.\d+)')


def extract_version(text: str) -> Optional[str]:
    match = VERSION_PATTERN.search(text)
    return match.group(1) if match else None


def _get_proxies() -> dict:
    """Get proxy dict from environment variables"""
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
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
        return (
            hasattr(sys.stdout, 'isatty') and
            sys.stdout.isatty() and
            (platform.system() != 'Windows' or 'WT_SESSION' in os.environ)
        )

    @classmethod
    def colorize(cls, color, text):
        if cls.is_color_supported():
            return f"{color}{text}{cls.NC}"
        return text


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def log_info(message):
    print(Colors.colorize(Colors.BLUE, f"[INFO] {message}"), file=sys.stderr)

def log_success(message):
    print(Colors.colorize(Colors.GREEN, f"[OK] {message}"), file=sys.stderr)

def log_warn(message):
    print(Colors.colorize(Colors.YELLOW, f"[WARN] {message}"), file=sys.stderr)

def log_error(message):
    print(Colors.colorize(Colors.RED, f"[ERROR] {message}"), file=sys.stderr)


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
    if v1 == v2:
        return 'eq'

    parts1 = [int(x) for x in v1.split('.')]
    parts2 = [int(x) for x in v2.split('.')]

    max_len = max(len(parts1), len(parts2))
    parts1.extend([0] * (max_len - len(parts1)))
    parts2.extend([0] * (max_len - len(parts2)))

    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return 'lt'
        elif p1 > p2:
            return 'gt'

    return 'eq'


# =============================================================================
# VERSION DETECTION
# =============================================================================

def get_version_npm() -> Optional[str]:
    try:
        result = subprocess.run(
            ['npm', 'view', '@anthropic-ai/claude-code', 'version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            if version and VERSION_PATTERN.match(version):
                return version
    except Exception:
        pass
    return None


def get_version_github() -> Optional[str]:
    from urllib.request import urlopen, Request

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
                import urllib.request
                proxy_handler = urllib.request.ProxyHandler(proxies)
                opener = urllib.request.build_opener(proxy_handler)
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
# PROCESS CLEANUP
# =============================================================================

def get_process_age(proc) -> float:
    try:
        if HAS_PSUTIL:
            return time.time() - proc.create_time()
        else:
            return ORPHAN_AGE_THRESHOLD + 1
    except Exception:
        return 0


def is_orphan_process(proc) -> bool:
    try:
        if HAS_PSUTIL:
            parent = proc.parent()
            if parent is None:
                return True
            if parent.pid == 1:
                return True
            try:
                parent.status()
                return False
            except psutil.NoSuchProcess:
                return True
        else:
            return False
    except Exception:
        return False


def kill_orphan_processes():
    log_info("Scanning for orphan npm install processes...")

    if not HAS_PSUTIL:
        log_warn("psutil not available, skipping process cleanup")
        log_warn("Install with: pip install psutil")
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
                age = get_process_age(proc)
                name = proc.info.get('name', 'unknown')

                log_info(f"Found process {pid} ({name}) running for {int(age)}s")

                if age < ORPHAN_AGE_THRESHOLD:
                    log_info(f"  → Skipping: process is young ({int(age)}s < {ORPHAN_AGE_THRESHOLD}s)")
                    continue

                if not is_orphan_process(proc):
                    log_info("  → Skipping: process has living parent")
                    continue

                try:
                    cpu = proc.cpu_percent(interval=0.1)
                    if cpu > 0:
                        log_info(f"  → Skipping: process is using CPU ({cpu:.1f}%)")
                        continue
                except Exception:
                    pass

                log_warn(f"  → KILLING: orphan process {pid} (age: {int(age)}s)")

                try:
                    proc.kill()
                    killed_count += 1
                except psutil.AccessDenied:
                    log_warn(f"  → Access denied, cannot kill process {pid}")
                except psutil.NoSuchProcess:
                    pass

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            log_warn(f"Error checking process: {e}")

    if killed_count > 0:
        log_info(f"Killed {killed_count} orphan process(es)")
        time.sleep(PROCESS_KILL_WAIT)


# =============================================================================
# DIRECTORY CLEANUP
# =============================================================================

def cleanup_npm_dirs():
    log_info("Cleaning up npm installation directories...")

    try:
        result = subprocess.run(
            ['npm', 'root', '-g'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            npm_root = Path(result.stdout.strip()) / '@anthropic-ai'

            if npm_root.exists():
                for item in npm_root.iterdir():
                    if item.name.startswith('.claude-code-') or item.name == 'claude-code':
                        log_warn(f"Removing: {item}")
                        shutil.rmtree(item, ignore_errors=True)

        subprocess.run(
            ['npm', 'cache', 'clean', '--force', '@anthropic-ai/claude-code'],
            capture_output=True,
            timeout=10
        )
    except Exception as e:
        log_warn(f"Cleanup warning: {e}")


# =============================================================================
# INSTALLATION
# =============================================================================

def do_install(target_version: str) -> bool:
    install_cmd = f'npm install -g @anthropic-ai/claude-code@{target_version}'
    log_info(f"Installing version {target_version} (timeout: {INSTALL_TIMEOUT}s)...")

    log_path = os.path.join(tempfile.gettempdir(), f'claude-update-{os.getpid()}.log')

    try:
        env = os.environ.copy()

        log_fd = open(log_path, 'w')
        proc = subprocess.Popen(
            install_cmd.split(),
            stdout=log_fd,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )

        try:
            proc.wait(timeout=INSTALL_TIMEOUT)

            if proc.returncode == 0:
                os.unlink(log_path)
                return True

            log_error(f"Install failed with exit code {proc.returncode}")

            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(line.rstrip(), file=sys.stderr)
            except Exception:
                pass

            return False

        except subprocess.TimeoutExpired:
            log_error(f"Install timed out after {INSTALL_TIMEOUT}s")

            proc.kill()
            proc.wait()

            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        print(line.rstrip(), file=sys.stderr)
            except Exception:
                pass

            return False

    finally:
        try:
            log_fd.close()
        except Exception:
            pass
        try:
            os.unlink(log_path)
        except Exception:
            pass


def install_with_retry(target_version: str) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        kill_orphan_processes()
        cleanup_npm_dirs()
        time.sleep(1)

        if do_install(target_version):
            return True

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

        if actual_version:
            comparison = compare_versions(actual_version, expected_version)
            if comparison == 'eq':
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

        kill_orphan_processes()

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

        if install_with_retry(latest_version):
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
