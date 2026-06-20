# REQUISITOS — qué necesitás instalado antes del taller

> **Atajo:** si ya tenés Claude Code instalado, abrí este repo y pegale a Claude:
> *"Lee REQUISITOS.md, detectá qué falta en mi sistema y ayudame a instalarlo paso a paso."*
> Te va a verificar uno por uno y te guía. Si Claude Code aún no está instalado, seguí abajo.

---

## Tabla rápida

| Herramienta | Para qué | ¿Obligatorio? | Verificación |
|---|---|---|---|
| **Claude Code** | El driver del taller | ✅ SÍ | `claude --version` |
| **Python 3.11+** | Correr el pipeline DuckDB | ✅ SÍ | `python3 --version` |
| **uv** | Manejar venv (PEP 668) | ⭐ Muy recomendado | `uv --version` |
| **git** | Clonar repo + worktrees | ✅ SÍ | `git --version` |
| **Docker** | Levantar SQL Server legacy | ⚠️ Solo Camino B | `docker --version` |
| **Node.js + npm** | MCP server SQL Server | ⚠️ Solo Camino B | `npm --version` |
| **gh** (GitHub CLI) | Abrir PRs en el capstone | ⭐ Recomendado | `gh --version` |
| **tmux** | 2 paneles paralelos | ⭐ Recomendado | `tmux -V` |

> **Camino A (sin SQL Server) — mínimo:** Claude Code + Python 3.11+ + uv + git. Listo, corre todo.
> **Camino B (con MCP en vivo) — agregar:** Docker + Node.js + el MCP server (`npm install -g @executeautomation/database-server`).

---

## Instalación por sistema operativo

### Linux / WSL2 (Ubuntu/Debian)

```bash
# 1. Claude Code (Anthropic CLI)
curl -fsSL https://claude.ai/install.sh | bash
# después: claude login

# 2. Python 3.11+ (suele venir; verificalo)
python3 --version    # si <3.11:  sudo apt install python3.11

# 3. uv (gestor de Python rápido, recomendado para evitar PEP 668)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. git
sudo apt install -y git

# 5. Docker (Camino B)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # logout/login después
# WSL2: instalá Docker Desktop en Windows y habilita la integración con tu distro

# 6. Node.js + npm (Camino B - para el MCP server)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# 7. gh (GitHub CLI - para PRs)
sudo apt install -y gh
gh auth login

# 8. tmux
sudo apt install -y tmux
```

### macOS (con Homebrew)

```bash
# 1. Claude Code
brew install anthropic/tap/claude   # o curl -fsSL https://claude.ai/install.sh | bash

# 2-8 en un solo brew:
brew install python@3.11 uv git docker node gh tmux
# Docker en macOS: instalá Docker Desktop desde docker.com
```

### Windows

> **Recomendación fuerte:** usá **WSL2** (Windows Subsystem for Linux) y seguí las instrucciones de Linux/WSL2 arriba. El taller asume entorno tipo Unix.

```powershell
# Activar WSL2 (PowerShell como administrador)
wsl --install -d Ubuntu
# Reiniciar, abrir Ubuntu, y seguir la sección Linux/WSL2
```

Si no querés WSL: usá [chocolatey](https://chocolatey.org/) o [scoop](https://scoop.sh/) para instalar las herramientas. La sección Docker requiere Docker Desktop.

---

## Verificación todo-en-uno

Después de instalar, pegá esto en tu terminal:

```bash
echo "=== Verificación de herramientas ==="
for tool in claude python3 uv git docker npm gh tmux; do
  if command -v $tool >/dev/null 2>&1; then
    echo "✅ $tool: $($tool --version 2>&1 | head -1)"
  else
    echo "❌ $tool: NO instalado"
  fi
done
echo "=== Fin ==="
```

Debería mostrar ✅ en al menos: `claude`, `python3`, `uv`, `git`. Los demás según el Camino que vayas a hacer.

---

## Setup específico del taller (después de tener todo lo de arriba)

```bash
# 1. Clonar este repo
git clone <URL-DEL-REPO> && cd repo-para-clonar

# 2. Crear venv con duckdb (única dependencia obligatoria)
uv venv && uv pip install duckdb

# 3. (Solo Camino B) Levantar SQL Server + restaurar WideWorldImporters
cd setup && bash restore.sh && cd ..
#   ~10-15 min la primera vez (descarga ~180MB de backups)

# 4. (Solo Camino B) Instalar el MCP server y configurarlo en Claude Code
npm install -g @executeautomation/database-server
# Luego seguí setup/MCP.md para crear .mcp.json

# 5. Verificar que el pipeline corre (Camino A, con stubs vas a ver el mensaje guía):
uv run python modern/run_pipeline.py
```

---

## Cómo pedirle a Claude Code que te instale todo

Una vez que tengas **Claude Code** instalado, abrí esta carpeta y pegale este prompt:

> ```
> Lee REQUISITOS.md. Verificá qué herramientas tengo instaladas con el script de verificación.
> Identificá qué falta para mi sistema operativo (detectalo con `uname` o equivalente).
> Guiame paso a paso para instalar lo que falta, confirmando antes de cada `sudo` o cambio
> importante. Empezamos por el Camino A (mínimo), después decidimos si vamos al Camino B.
> ```

Claude debería detectar tu OS, correr la verificación, e instalar lo que te falte de forma interactiva.

---

## Plan B si algo no instala

- **`pip install duckdb` falla** ("externally-managed-environment"): usá `uv pip install duckdb` o creá un venv (`python3 -m venv .venv && source .venv/bin/activate && pip install duckdb`).
- **Docker no puede iniciar**: el taller corre en **Camino A** sin Docker. Los `data/*.parquet` ya están versionados en el repo.
- **MCP no conecta**: caés a Camino A (offline). El demo cuadra igual al céntimo.
- **`gh` pide login en medio del taller**: corré `gh auth login` antes, no en vivo.
- **Conexión a internet inestable**: el repo es 100% offline después de clonarlo (datos + scripts versionados). Solo Docker para descargar las imágenes la primera vez.
