# CLAUDE.md — Reglas del proyecto (Taller Claude Code · Sesión 3)

## Qué es esto
Modernizamos el **ETL legacy de WideWorldImporters** (stored procedures T-SQL del esquema
`Integration` en `WideWorldImportersDW`) reescribiéndolo a **Python + DuckDB**, haciendo
**ingeniería inversa en vivo** con Claude Code.

## El modelo mental (decirlo en clase)
- **Docker = el sistema legacy.** SQL Server 2022 con `WideWorldImporters` (OLTP) +
  `WideWorldImportersDW` (DW) + los stored procedures de ETL.
- **El host (WSL2) = el mundo moderno.** Claude Code, este repo, git/worktrees/PRs,
  Python + DuckDB, el dashboard.
- **El MCP = el puente**, host → contenedor por `localhost:1433`, **solo lectura**.

Es una metáfora literal de la modernización real: lo viejo encapsulado, lo nuevo afuera,
un puente de solo-lectura entre ambos.

## Reglas duras (no negociables)
1. **El MCP es READ-ONLY.** Nunca escribimos en SQL Server. Solo `SELECT`, leer definiciones
   de SPs y describir esquemas. El SQL Server es la fuente de verdad legacy, no se toca.
2. **Target moderno = Python + DuckDB puro.** Sin pandas, sin otras dependencias. DuckDB lee
   parquet/CSV nativo y hace todo el SQL. (Una sola dependencia: `duckdb`.) En Python usar
   `con.execute(...).fetchall()/.fetchone()`, **NUNCA `.df()`** (requiere pandas, que no está).
3. **Para runs deterministas, primero exportar la fuente a `data/*.parquet`** (ver
   `setup/export_source.sql`). El código DuckDB lee de `data/`, NO se conecta a SQL Server en
   tiempo de ejecución. Así el pipeline corre igual con o sin la BD viva.
4. **Salidas a `modern/output/`** (parquet/CSV). El dashboard lee de ahí.
5. **Verificación = contrastar contra la "clave de respuestas":** las tablas `Dimension.*` /
   `Fact.*` ya pobladas en `WideWorldImportersDW` + el linaje documentado en
   `reference/lineage.md`. No hace falta ejecutar el SP: el DW ya trae el resultado legacy.
6. **Alcance bloqueado a 4 entidades:** `Customer`, `StockItem`, `Supplier` (dimensiones) y
   `Sale` (hecho). WWI tiene ~26 procs y 2 bases — NO abarcar más. Una entidad por worktree.
7. **Código de enseñanza:** legible, set-based, sin cursores. Cada `.py` empieza con un
   docstring que explica el linaje y las reglas de negocio en lenguaje claro.

## Convenciones
- Una entidad por rama: `feat/dim-customer`, `feat/dim-stockitem`, `feat/dim-supplier`, `feat/fact-sale`.
- Cada modernización abre un PR; el cuerpo del PR = la explicación en lenguaje claro del SP legacy.
- Archivos modernos: `modern/<entidad>.py`. Orquestador: `modern/run_pipeline.py`.
- Ejecutar con `uv run python modern/run_pipeline.py`.

## Cómo leer un stored procedure por MCP
```sql
-- definición del SP:
SELECT OBJECT_DEFINITION(OBJECT_ID('Integration.MigrateStagedCustomerData'));
-- listar los SPs de ETL:
SELECT s.name AS esquema, o.name AS proc
FROM sys.procedures o JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE s.name = 'Integration' ORDER BY o.name;
-- describir una tabla fuente:
SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Customers' AND TABLE_SCHEMA = 'Sales';
```
