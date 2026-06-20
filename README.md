# Taller Claude Code · Sesión 3 (Avanzado) — Ingeniería inversa de un ETL legacy

Bienvenido/a. En este taller vas a tomar un **ETL real hecho con stored procedures** (la base de
ejemplo *WideWorldImporters* de Microsoft), hacerle **ingeniería inversa con Claude Code** y
**reescribirlo a Python + DuckDB** — terminando en un dashboard. Todo paso a paso; nadie se pierde.

> Este repo es el **punto de partida**. Haz `git clone` y sigue los pasos de abajo en orden.
> Si en algún momento te atascas, la solución completa está en la carpeta **`resultado-final/`**.

---

## 🎯 Qué vamos a hacer (el panorama)

```
   LEGACY (lo viejo)                      MODERNO (lo que construyes)
   SQL Server + WideWorldImporters        Python + DuckDB
   stored procedures Integration.*  ──►   modern/*.py  ──►  verificación  ──►  dashboard.html
        (los lees y entiendes)            (los reescribes)   (vs el DW real)    (el resultado)
```

Vas a modernizar **4 entidades**: 3 dimensiones (`Customer`, `StockItem`, `Supplier`) y 1 hecho
(`Sale`). Al final, tu pipeline en DuckDB debe **dar los mismos números** que el Data Warehouse
original de Microsoft (lo verificamos automáticamente).

---

## ✅ Requisitos

**Lectura obligatoria antes de empezar:** [`REQUISITOS.md`](REQUISITOS.md) tiene la lista
completa (qué instalar, por OS, cómo verificar) **y un prompt listo para pegarle a Claude Code
y que te instale lo que te falte automáticamente.**

**Resumen mínimo:**
- **Camino A:** Claude Code · Python 3.11+ · `uv` · `git`
- **Camino B (con MCP en vivo):** todo lo de arriba + Docker + Node.js + el MCP server.

---

## 🗺️ Estructura del repo

```
README.md          ← esta guía (empieza aquí)
REQUISITOS.md      ← qué tener instalado (Claude Code, uv, Docker, npm...) y cómo  ← LÉELO PRIMERO
CLAUDE.md          ← reglas del proyecto (Claude Code las lee solo)
setup/             ← docker-compose + restore.sh + export_source (montar el SQL Server legacy)
setup/MCP.md       ← cómo configurar el MCP de SQL Server (Camino B)  ← LÉELO si vas a usar MCP
legacy_sql/        ← los 4 stored procedures REALES que vas a reversear  ← LÉELOS
reference/         ← lineage.md = la "clave de respuestas" oficial de Microsoft
.claude/commands/  ← el comando /modernize-sp
data/              ← datos fuente ya exportados (parquet) → puedes correr SIN SQL Server
modern/            ← AQUÍ construyes tú: dim_customer.py, dim_stockitem.py, dim_supplier.py, fact_sale.py
                     (ya vienen run_pipeline.py, verify.py y build_dashboard.py — esos NO los tocas)
resultado-final/   ← repo COMPLETO ya resuelto (clave de respuestas si te atascas)
```

---

## 🚦 Dos caminos (elige según tu tiempo)

- **Camino A — Rápido (recomendado para seguir el taller).** Sin SQL Server. Los datos fuente ya
  están en `data/*.parquet`. Solo necesitas Python + DuckDB. **Empieza en el Paso 3.**
- **Camino B — Completo.** Levantas el SQL Server real en Docker y conectas Claude por MCP para
  leer los stored procedures en vivo. Más impresionante, más setup. **Haz Pasos 1 y 2 primero.**

---

## Paso 0 · Clonar e instalar

```bash
git clone <URL-DEL-REPO>
cd repo-para-clonar
```

Instalá `duckdb` (única dependencia). **Elegí UNA de estas tres formas** según tu setup:

```bash
# Opción A (recomendada) - con uv:
uv venv && uv pip install duckdb
# luego: uv run python modern/run_pipeline.py   (usa el venv automáticamente)

# Opción B - venv estándar:
python3 -m venv .venv && source .venv/bin/activate && pip install duckdb
# (en Windows PowerShell: .venv\Scripts\Activate.ps1)

# Opción C - pip directo (puede fallar en Linux/macOS modernos por PEP 668):
pip install duckdb
# si falla con "externally-managed-environment", usá Opción A o B
```

> **Tip:** Si usás `uv run python ...` reemplaza `python` por `uv run python` en todos los
> comandos de abajo. Si usás venv estándar, asegurate de tenerlo activado antes de cada `python`.

## Paso 1 · (Solo Camino B) Levantar el legacy en Docker

```bash
cd setup
bash restore.sh              # descarga WWI y restaura OLTP + Data Warehouse en SQL Server
cd ..
```
Al terminar debe decir que ambas bases están **ONLINE** y listar los stored procedures `Integration.*`.

**Después de restaurar, configura el MCP de SQL Server en Claude Code** siguiendo
[`setup/MCP.md`](setup/MCP.md) (paso a paso, con ejemplo de `.mcp.json` y smoke test).

## Paso 2 · (Solo Camino B) Exportar los datos fuente

> En el **Camino A** sáltate este paso: los `data/*.parquet` ya están en el repo.

```bash
uv pip install pymssql           # o:  pip install pymssql  (en el venv que armaste en Paso 0)
uv run python setup/export_source.py    # regenera data/*.parquet desde el SQL Server
# (sin uv:  python setup/export_source.py  con el venv activado)
```
*(Alternativa con MCP: configura tu MCP de SQL Server a `localhost:1433` en solo lectura y pídele
a Claude que ejecute los SELECT de `setup/export_source.sql` guardándolos como parquet en `data/`.)*

## Paso 3 · Entender el legacy (lee un stored procedure)

```bash
cat legacy_sql/MigrateStagedCustomerData.sql
```
Pregúntate (o pídeselo a Claude): **¿de dónde lee? ¿a dónde escribe? ¿qué transforma?**
Pista: es un **SCD Type 2** (cierra la versión vigente e inserta la nueva). El linaje oficial está
en `reference/lineage.md`.

## Paso 4 · Modernizar las 4 entidades (lo central)

Construye cada archivo en `modern/` reescribiendo el SP a **DuckDB puro** (sin pandas). Los archivos
ya están como **plantillas** que te dicen qué hacer. Dos formas:

- **Con Claude Code (recomendado):** `/modernize-sp customer` (luego `stockitem`, `supplier`, `sale`).
- **A mano:** sigue el linaje de `reference/lineage.md` y el SP de `legacy_sql/`.

Orden sugerido: `dim_customer` → `dim_stockitem` → `dim_supplier` → `fact_sale` (el hecho usa las dimensiones).

> 🆘 **¿Atascado con alguno?** Copia la solución desde `resultado-final/modern/<archivo>.py` y sigue.

## Paso 5 · Correr el pipeline

```bash
python modern/run_pipeline.py     # corre las 4 entidades en orden -> modern/output/*.parquet
```
Si falta alguna entidad, el mensaje te dirá cuál construir.

## Paso 6 · Verificar contra el DW real (el momento estrella)

```bash
python modern/verify.py
```
Debe salir **✅ TODAS las medidas exactas cuadran con el DW real**:
`Fact.Sale = 228,265 filas · Total con IGV = S/ 198,043,439.45` — **al céntimo**.
*(Las dimensiones son estado-actual vs el histórico SCD2 del DW: se compara forma, no igualdad. Es esperado.)*

## Paso 7 · El dashboard (el resultado)

```bash
python modern/build_dashboard.py  # genera dashboard.html (SVG/CSS inline, sin dependencias)
```
Abre `dashboard.html` en tu navegador. 🎉

---

## 🆘 Si te pierdes en cualquier punto
Mira la carpeta **`resultado-final/`**: tiene el repo completo y resuelto (los 4 `modern/*.py`, el
dashboard generado y todo corriendo). Copia lo que necesites y continúa:
```bash
cp resultado-final/modern/dim_customer.py  modern/dim_customer.py
# (y/o las que necesites)
python modern/run_pipeline.py && python modern/verify.py
```

## 📏 Reglas (resumen — el detalle está en `CLAUDE.md`)
1. El MCP/SQL Server es **solo lectura**: nunca escribimos al legacy.
2. Target moderno = **Python + DuckDB puro** (sin pandas; usa `.fetchall()`, no `.df()`).
3. El código lee de `data/*.parquet` y escribe a `modern/output/`.
4. Alcance: **solo estas 4 entidades**.

## Créditos
Base de datos de ejemplo **WideWorldImporters** © Microsoft (`microsoft/sql-server-samples`),
usada como material legacy realista. Material educativo — BREIT Workshop.
