# Claude Code Workshop · Session 3 (Advanced) — Reverse-engineering a legacy ETL

Welcome. In this workshop you'll take a **real ETL built with stored procedures** (Microsoft's
*WideWorldImporters* sample database), **reverse-engineer it with Claude Code** and
**rewrite it in Python + DuckDB** — ending in a dashboard. Step by step; nobody gets lost.

> This repo is the **starting point**. `git clone` it and follow the steps below in order.
> If you get stuck at any point, the complete solution lives in the **`resultado-final/`** folder.

---

## 🎯 What we're going to do (the big picture)

```
   LEGACY (the old)                        MODERN (what you build)
   SQL Server + WideWorldImporters         Python + DuckDB
   stored procedures Integration.*  ──►    modern/*.py  ──►  verification  ──►  dashboard.html
        (you read and understand them)     (you rewrite them) (vs the real DW)   (the result)
```

You'll modernize **4 entities**: 3 dimensions (`Customer`, `StockItem`, `Supplier`) and 1 fact
(`Sale`). At the end, your DuckDB pipeline must **produce the same numbers** as the original
Microsoft Data Warehouse (we verify automatically).

---

## ✅ Requirements

**Required reading before starting:** [`REQUISITOS.md`](REQUISITOS.md) has the full
list (what to install, by OS, how to verify) **and a ready-made prompt you can paste into
Claude Code so it installs whatever's missing automatically.**

**Minimum summary:**
- **Path A:** Claude Code · Python 3.11+ · `uv` · `git`
- **Path B (with live MCP):** all of the above + Docker + Node.js + the MCP server.

---

## 🗺️ Repo layout

```
README.md          ← this guide (start here)
REQUISITOS.md      ← what to install (Claude Code, uv, Docker, npm...) and how  ← READ FIRST
CLAUDE.md          ← project rules (Claude Code reads it on its own)
setup/             ← docker-compose + restore.sh + export_source (spin up the legacy SQL Server)
setup/MCP.md       ← how to set up the SQL Server MCP (Path B)  ← READ if you're using MCP
legacy_sql/        ← the 4 REAL stored procedures you'll reverse-engineer  ← READ THEM
reference/         ← lineage.md = Microsoft's official "answer key"
.claude/commands/  ← the /modernize-sp command
data/              ← source data already exported (parquet) → you can run WITHOUT SQL Server
modern/            ← THIS is where you build: dim_customer.py, dim_stockitem.py, dim_supplier.py, fact_sale.py
                     (run_pipeline.py, verify.py and build_dashboard.py are already there — DON'T touch them)
resultado-final/   ← FULLY solved repo (answer key if you get stuck)
```

---

## 🚦 Two paths (pick based on your time)

- **Path A — Fast (recommended for following the workshop).** No SQL Server. Source data is
  already in `data/*.parquet`. You only need Python + DuckDB. **Start at Step 3.**
- **Path B — Full.** You spin up the real SQL Server in Docker and connect Claude via MCP to
  read the stored procedures live. More impressive, more setup. **Do Steps 1 and 2 first.**

---

## Step 0 · Clone and install

```bash
git clone <REPO-URL>
cd repo-para-clonar
```

Install `duckdb` (the only dependency). **Pick ONE of these three approaches** based on your setup:

```bash
# Option A (recommended) - with uv:
uv venv && uv pip install duckdb
# then: uv run python modern/run_pipeline.py   (uses the venv automatically)

# Option B - standard venv:
python3 -m venv .venv && source .venv/bin/activate && pip install duckdb
# (on Windows PowerShell: .venv\Scripts\Activate.ps1)

# Option C - pip direct (may fail on modern Linux/macOS due to PEP 668):
pip install duckdb
# if it fails with "externally-managed-environment", use Option A or B
```

> **Tip:** If you use `uv run python ...`, replace `python` with `uv run python` in every
> command below. If you use a standard venv, make sure it's activated before each `python`.

## Step 1 · (Path B only) Spin up the legacy in Docker

```bash
cd setup
bash restore.sh              # downloads WWI and restores OLTP + Data Warehouse in SQL Server
cd ..
```
When it finishes it should report both databases **ONLINE** and list the `Integration.*` stored procedures.

**After restoring, configure the SQL Server MCP in Claude Code** following
[`setup/MCP.md`](setup/MCP.md) (step by step, with a `.mcp.json` example and smoke test).

## Step 2 · (Path B only) Export the source data

> On **Path A** skip this step: `data/*.parquet` are already in the repo.

```bash
uv pip install pymssql           # or:  pip install pymssql  (in the venv you set up in Step 0)
uv run python setup/export_source.py    # regenerates data/*.parquet from the SQL Server
# (without uv:  python setup/export_source.py  with the venv activated)
```
*(Alternative via MCP: configure your SQL Server MCP to `localhost:1433` in read-only mode and ask
Claude to run the SELECTs in `setup/export_source.sql`, saving them as parquet in `data/`.)*

## Step 3 · Understand the legacy (read a stored procedure)

```bash
cat legacy_sql/MigrateStagedCustomerData.sql
```
Ask yourself (or ask Claude): **where does it read from? where does it write to? what does it transform?**
Hint: it's an **SCD Type 2** (it closes the current version and inserts the new one). The official
lineage lives in `reference/lineage.md`.

## Step 4 · Modernize the 4 entities (the core)

Build each file in `modern/` by rewriting the SP to **pure DuckDB** (no pandas). The files are
already there as **templates** telling you what to do. Two ways:

- **With Claude Code (recommended):** `/modernize-sp customer` (then `stockitem`, `supplier`, `sale`).
- **By hand:** follow the lineage in `reference/lineage.md` and the SP in `legacy_sql/`.

Suggested order: `dim_customer` → `dim_stockitem` → `dim_supplier` → `fact_sale` (the fact uses the dimensions).

> 🆘 **Stuck on one?** Copy the solution from `resultado-final/modern/<file>.py` and keep going.

## Step 5 · Run the pipeline

```bash
python modern/run_pipeline.py     # runs the 4 entities in order -> modern/output/*.parquet
```
If any entity is missing, the message will tell you which one to build.

## Step 6 · Verify against the real DW (the headline moment)

```bash
python modern/verify.py
```
It must print **✅ ALL exact measures match the real DW**:
`Fact.Sale = 228,265 rows · Total with VAT = S/ 198,043,439.45` — **to the cent**.
*(Dimensions are current-state vs the DW's SCD2 history: we compare shape, not equality. That's expected.)*

## Step 7 · The dashboard (the payoff)

```bash
python modern/build_dashboard.py  # generates dashboard.html (inline SVG/CSS, no dependencies)
```
Open `dashboard.html` in your browser. 🎉

---

## 🆘 If you get lost at any point
Look at the **`resultado-final/`** folder: it has the full, solved repo (all 4 `modern/*.py`, the
generated dashboard, everything running). Copy what you need and keep going:
```bash
cp resultado-final/modern/dim_customer.py  modern/dim_customer.py
# (and/or whichever ones you need)
python modern/run_pipeline.py && python modern/verify.py
```

## 📏 Rules (summary — details in `CLAUDE.md`)
1. The MCP/SQL Server is **read-only**: we never write to the legacy.
2. Modern target = **pure Python + DuckDB** (no pandas; use `.fetchall()`, not `.df()`).
3. Code reads from `data/*.parquet` and writes to `modern/output/`.
4. Scope: **only these 4 entities**.

## Credits
The **WideWorldImporters** sample database is © Microsoft (`microsoft/sql-server-samples`),
used as realistic legacy material. Educational content — BREIT Workshop.
