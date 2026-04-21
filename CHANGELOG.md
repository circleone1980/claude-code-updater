# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-04-21

### Fixed
- Windows EBUSY error when updating while Claude is running (rename locked exe before install)
- Removed ineffective Volta bypass logic (`volta which npm` returns Volta-managed path)
- Fixed `log_fd` uninitialized variable in `do_install` finally block
- Proxy env var case-insensitive detection (added `https_proxy`/`http_proxy`)

### Changed
- Git Bash color support (added `MSYSTEM` env var check)
- Installation timeout increased to 120s for large platform packages
- Simplified process cleanup (removed redundant age/CPU checks)
- Auto-rollback renamed files on install failure

## [1.0.0] - 2026-04-19

### Added
- Cross-platform Claude Code updater (Windows, WSL, Linux, macOS)
- Automatic version detection and comparison
- GitHub API + npm registry fallback for version lookup
- Proxy support via HTTPS_PROXY/HTTP_PROXY environment variables
- Orphan npm process cleanup (with psutil)
- Corrupted directory cleanup before install
- File locking to prevent concurrent updates
- Configurable timeout, retry, and orphan age thresholds
- Installation verification with retry
- Optional dependencies: psutil, requests, filelock
