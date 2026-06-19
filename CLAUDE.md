# CLAUDE.md — Guía del proyecto (Taller Claude Code · Sesión 3, Avanzado)

> Claude: este archivo te orienta. El usuario está siguiendo el `README.md` paso a paso.
> Tu trabajo es ayudarlo a **modernizar un ETL legacy** (stored procedures) a **Python + DuckDB**,
> sin que se pierda. Respeta las reglas duras de abajo y sigue el plan de 7 pasos.

## Qué es esto
Tomamos el ETL real de **WideWorldImporters** (Microsoft): los stored procedures
`Integration.MigrateStaged*Data` que cargan el Data Warehouse desde el OLTP. Les hacemos
ingeniería inversa y los reescribimos como scripts modernos en `modern/`.

Metáfora: **Docker = el legacy** (SQL Server + WWI) · **host = lo moderno** (Python + DuckDB) ·
**MCP = el puente** (solo lectura).

## Reglas duras (NO negociables)
1. **Solo lectura sobre el legacy.** Si hay MCP/SQL Server, solo `SELECT` y leer definiciones de SPs. Nunca escribir.
2. **Target = Python + DuckDB puro.** Sin pandas ni otras dependencias. Una sola: `duckdb`.
   En Python usa `con.execute(...).fetchall()/.fetchone()`, **NUNCA `.df()`** (requiere pandas, que no está).
3. **El código lee de `data/*.parquet`** (ya exportados) y **escribe a `modern/output/`**. NO se
   conecta al SQL Server en tiempo de ejecución → corre con o sin la BD viva.
4. **Alcance: solo 4 entidades** — `Customer`, `StockItem`, `Supplier` (dimensiones SCD2) y `Sale` (hecho). No abarcar más.
5. **Código de enseñanza:** legible, set-based (sin cursores). Cada `modern/<entidad>.py` empieza con
   un docstring que explica el linaje y las reglas en lenguaje claro.

## Plan paso a paso (lo que el usuario va a pedirte)
1. **Entender el legacy:** lee `legacy_sql/MigrateStaged<Entidad>Data.sql` y explícalo en lenguaje
   claro (de dónde lee, a dónde escribe, qué transforma; SCD Type 2 / resolución de surrogate keys).
2. **Verificar el linaje** contra `reference/lineage.md` (la clave de respuestas oficial de Microsoft).
3. **Reescribir** la entidad como `modern/<entidad>.py` con DuckDB:
   - lee los `data/src_*.parquet` que correspondan; escribe `modern/output/<entidad>.parquet`;
   - dimensiones = SCD2/estado-actual con surrogate key; hecho = resolver `*_Key` hacia las dimensiones + medidas;
   - **el T-SQL set-based mapea casi 1:1 a SQL de DuckDB** (sin cursores).
4. **Correr** `python modern/run_pipeline.py` y revisar que no haya errores.
5. **Verificar** `python modern/verify.py` → las medidas del hecho deben cuadrar EXACTO con el DW
   (228,265 filas · S/ 198,043,439.45). Las dimensiones se comparan en forma (estado-actual vs histórico SCD2).
6. **Dashboard** `python modern/build_dashboard.py` → `dashboard.html`.
7. Si el usuario se atasca, indícale la solución en `resultado-final/modern/<entidad>.py`.

## El comando `/modernize-sp <entidad>`
Está en `.claude/commands/modernize-sp.md`. Hace los pasos 1–3 para UNA entidad
(`customer` | `stockitem` | `supplier` | `sale`). Úsalo cuando el usuario lo invoque.

## Datos y archivos clave
- `data/src_*.parquet` — fuentes ya exportadas (nombres de columna reales de WWI).
- `data/_verify_dw.json` — cifras reales del DW (las usa `verify.py`).
- `legacy_sql/*.sql` — los stored procedures reales (la verdad legacy).
- `reference/lineage.md` — linaje + reglas + cifras (clave de respuestas).
- `modern/run_pipeline.py`, `verify.py`, `build_dashboard.py` — scaffolding YA hecho (no reescribir).

## (Camino B) Leer un stored procedure por MCP
**Setup del MCP de SQL Server:** ver `setup/MCP.md` (incluye ejemplo de `.mcp.json`, smoke test
y cómo asegurar read-only). Una vez configurado:
```sql
SELECT OBJECT_DEFINITION(OBJECT_ID('Integration.MigrateStagedCustomerData'));   -- definición
SELECT s.name+'.'+o.name FROM sys.procedures o JOIN sys.schemas s ON o.schema_id=s.schema_id
WHERE s.name='Integration' ORDER BY o.name;                                      -- listar SPs
```
