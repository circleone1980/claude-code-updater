<div align="center">

# ⬆️ Claude Code Updater

**一键更新 Claude Code，跨平台自动处理所有错误**

[![GitHub release](https://img.shields.io/github/v/release/circleone1980/claude-code-updater?include_prereleases&label=版本)](https://github.com/circleone1980/claude-code-updater/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20WSL%20%7C%20Linux%20%7C%20macOS-lightgrey)]()
[![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue.svg)]()

[English](README.en.md) · 简体中文

</div>

---

## ✨ 特性

- 🌍 **跨平台** — Windows / WSL / Linux / macOS 全覆盖
- 🔍 **自动版本检测** — GitHub API 优先，npm 回退
- 🔒 **文件锁** — 防止并发更新冲突
- 🧹 **智能清理** — 自动清理僵尸进程和损坏目录
- 🔄 **失败重试** — 网络异常自动重试，带清理机制
- 🌐 **代理支持** — 通过 `HTTPS_PROXY` 环境变量配置
- ✅ **安装验证** — 更新后自动校验版本号
- 🪙 **零 Token 消耗** — 脚本完成所有工作，无需 AI 介入分析

## 📦 安装

### 方式一：作为 Claude Code 技能安装（推荐）

```bash
git clone https://github.com/circleone1980/claude-code-updater.git
cd claude-code-updater
make install
```

或手动安装：

```bash
# Git Bash / Linux / macOS
cp -r update-claude-code ~/.claude/skills/

# Windows CMD
xcopy /E /I update-claude-code %USERPROFILE%\.claude\skills\update-claude-code
```

### 方式二：独立运行

```bash
git clone https://github.com/circleone1980/claude-code-updater.git
cd claude-code-updater
py update-claude-code/scripts/update.py
```

## 🚀 使用

### 在 Claude Code 中

安装为技能后，直接对 Claude 说：

> `更新 claude` · `检查更新` · `update claude code`

Claude 会自动调用更新脚本。

### 命令行直接运行

```bash
# Git Bash / Linux / macOS
py ~/.claude/skills/update-claude-code/scripts/update.py

# Windows CMD / PowerShell
py %USERPROFILE%\.claude\skills\update-claude-code\scripts\update.py
```

### 使用代理

```bash
# Linux / macOS / Git Bash
export HTTPS_PROXY=http://127.0.0.1:7890

# Windows PowerShell
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
```

## 🛠️ 工作原理

```
 🔒 获取文件锁 → 🧹 清理僵尸进程 → 🔍 检测当前版本
      ↓
 🌐 获取最新版本（GitHub → npm 回退）
      ↓
 ⚖️ 版本比较 → ⏭️ 已是最新？→ ✅ 退出
      ↓
 📦 npm install（带超时和重试）
      ↓
 ✅ 验证版本 → 🔓 释放锁
```

## 🖥️ 平台支持

| 平台 | 状态 | 说明 |
|:---:|:---:|:---|
| 🪟 Windows | ✅ | 原生 + Git Bash + PowerShell |
| 🐧 WSL | ✅ | 完整进程管理 |
| 🐧 Linux | ✅ | 所有主流发行版 |
| 🍎 macOS | ✅ | macOS 10.15+ |

## 📋 依赖

**必需：**
- Python 3.6+
- npm
- Claude Code（已安装）

**可选（提升可靠性）：**
```bash
pip install psutil requests filelock
```

| 包 | 作用 |
|:---|:---|
| `psutil` | 僵尸进程检测与清理 |
| `requests` | 更健壮的 HTTP 处理 |
| `filelock` | 跨平台文件锁 |

## ⚙️ 配置

详见 [configuration.md](update-claude-code/references/configuration.md) — 超时时间、重试次数、平台备注等。

## 🔧 故障排除

详见 [troubleshooting.md](update-claude-code/references/troubleshooting.md) — 权限错误、锁文件、网络超时等。

## 👨‍💻 开发

```bash
make validate   # 验证 SKILL.md 格式
make test       # 语法检查 update.py
make package    # 打包为 .skill
make clean      # 清理构建产物
```

## 📄 许可证

[MIT](LICENSE)
