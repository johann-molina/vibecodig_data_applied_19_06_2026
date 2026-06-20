# REQUIREMENTS — what you need installed before the workshop

> **Shortcut:** if you already have Claude Code installed, open this repo and paste this to Claude:
> *"Read REQUISITOS.md, detect what's missing on my system, and help me install it step by step."*
> It will check them one by one and guide you. If Claude Code isn't installed yet, follow the steps below.

---

## Quick table

| Tool | What for | Required? | Verify |
|---|---|---|---|
| **Claude Code** | The workshop driver | ✅ YES | `claude --version` |
| **Python 3.11+** | Run the DuckDB pipeline | ✅ YES | `python3 --version` |
| **uv** | Manage venv (PEP 668) | ⭐ Highly recommended | `uv --version` |
| **git** | Clone repo + worktrees | ✅ YES | `git --version` |
| **Docker** | Spin up the legacy SQL Server | ⚠️ Path B only | `docker --version` |
| **Node.js + npm** | SQL Server MCP server | ⚠️ Path B only | `npm --version` |
| **gh** (GitHub CLI) | Open PRs in the capstone | ⭐ Recommended | `gh --version` |
| **tmux** | 2 parallel panes | ⭐ Recommended | `tmux -V` |

> **Path A (no SQL Server) — minimum:** Claude Code + Python 3.11+ + uv + git. That's it, everything runs.
> **Path B (with live MCP) — add:** Docker + Node.js + the MCP server (`npm install -g @executeautomation/database-server`).

---

## Install by operating system

### Linux / WSL2 (Ubuntu/Debian)

```bash
# 1. Claude Code (Anthropic CLI)
curl -fsSL https://claude.ai/install.sh | bash
# then: claude login

# 2. Python 3.11+ (usually included; double-check)
python3 --version    # if <3.11:  sudo apt install python3.11

# 3. uv (fast Python manager, recommended to avoid PEP 668)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. git
sudo apt install -y git

# 5. Docker (Path B)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # logout/login afterwards
# WSL2: install Docker Desktop on Windows and enable integration with your distro

# 6. Node.js + npm (Path B - for the MCP server)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# 7. gh (GitHub CLI - for PRs)
sudo apt install -y gh
gh auth login

# 8. tmux
sudo apt install -y tmux
```

### macOS (with Homebrew)

```bash
# 1. Claude Code
brew install anthropic/tap/claude   # or curl -fsSL https://claude.ai/install.sh | bash

# 2-8 in one brew:
brew install python@3.11 uv git docker node gh tmux
# Docker on macOS: install Docker Desktop from docker.com
```

### Windows

> **Strong recommendation:** use **WSL2** (Windows Subsystem for Linux) and follow the Linux/WSL2 instructions above. The workshop assumes a Unix-like environment.

```powershell
# Enable WSL2 (PowerShell as administrator)
wsl --install -d Ubuntu
# Reboot, open Ubuntu, and follow the Linux/WSL2 section
```

If you don't want WSL: use [chocolatey](https://chocolatey.org/) or [scoop](https://scoop.sh/) to install the tools. The Docker section requires Docker Desktop.

---

## All-in-one verification

After installing, paste this into your terminal:

```bash
echo "=== Tool verification ==="
for tool in claude python3 uv git docker npm gh tmux; do
  if command -v $tool >/dev/null 2>&1; then
    echo "✅ $tool: $($tool --version 2>&1 | head -1)"
  else
    echo "❌ $tool: NOT installed"
  fi
done
echo "=== End ==="
```

It should show ✅ for at least: `claude`, `python3`, `uv`, `git`. The rest depending on which Path you'll do.

---

## Workshop-specific setup (after you have everything above)

```bash
# 1. Clone this repo
git clone <REPO-URL> && cd repo-para-clonar

# 2. Create venv with duckdb (the only required dependency)
uv venv && uv pip install duckdb

# 3. (Path B only) Spin up SQL Server + restore WideWorldImporters
cd setup && bash restore.sh && cd ..
#   ~10-15 min the first time (downloads ~180MB of backups)

# 4. (Path B only) Install the MCP server and configure it in Claude Code
npm install -g @executeautomation/database-server
# Then follow setup/MCP.md to create .mcp.json

# 5. Verify the pipeline runs (Path A, with stubs you'll see the guide message):
uv run python modern/run_pipeline.py
```

---

## How to ask Claude Code to install everything for you

Once you have **Claude Code** installed, open this folder and paste this prompt:

> ```
> Read REQUISITOS.md. Check which tools I have installed using the verification script.
> Identify what's missing for my operating system (detect it with `uname` or equivalent).
> Guide me step by step to install what's missing, confirming before each `sudo` or
> important change. Let's start with Path A (minimum), then decide if we go to Path B.
> ```

Claude should detect your OS, run the verification, and install whatever's missing interactively.

---

## Plan B if something won't install

- **`pip install duckdb` fails** ("externally-managed-environment"): use `uv pip install duckdb` or create a venv (`python3 -m venv .venv && source .venv/bin/activate && pip install duckdb`).
- **Docker won't start**: the workshop runs on **Path A** without Docker. The `data/*.parquet` files are already versioned in the repo.
- **MCP won't connect**: you fall back to Path A (offline). The demo still matches to the cent.
- **`gh` asks to log in mid-workshop**: run `gh auth login` beforehand, not live.
- **Unstable internet**: the repo is 100% offline after you clone it (data + scripts versioned). Only Docker needs to download images the first time.
