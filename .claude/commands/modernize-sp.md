---
description: Ingeniería inversa de un stored procedure de ETL legacy (WideWorldImporters) y reescritura a Python + DuckDB, con verificación contra el DW y PR.
argument-hint: <entidad: customer | stockitem | supplier | sale>
---

Vas a modernizar UNA entidad del ETL legacy de WideWorldImporters: **$ARGUMENTS**

Trabajas con el SQL Server legacy **solo por MCP y solo lectura**. El target moderno es
**Python + DuckDB puro** (sin pandas). Sigue `CLAUDE.md`.

Haz estos pasos en orden:

1. **LEER el legacy por MCP.** Encuentra y lee la definición de los stored procedures
   `Integration.Get<Entidad>Updates` y `Integration.MigrateStaged<Entidad>Data` (usa
   `OBJECT_DEFINITION`). Lee también el esquema de las tablas fuente y de la tabla destino
   `Dimension.<Entidad>` o `Fact.<Entidad>`.

2. **EXPLICAR en lenguaje claro** (esto es el oro del taller). Escribe:
   - qué tablas fuente lee y qué tabla destino escribe (el linaje, en una línea),
   - las reglas de negocio y transformaciones (SCD Type 2: `valid_from`/`valid_to`,
     resolución de surrogate keys, lookups, valores especiales),
   - qué hace el SP que un humano tardaría en descifrar.

3. **VERIFICAR tu lectura** contra la clave de respuestas: `reference/lineage.md` + las filas
   reales de `Dimension.<Entidad>`/`Fact.<Entidad>` en `WideWorldImportersDW` (por MCP).
   Si tu explicación no calza con los datos reales, corrígela.

4. **EXPORTAR la fuente** (si no existe ya) a `data/<entidad>_*.parquet` con el script de
   `setup/export_source.sql`, para que el código corra determinista sin la BD viva.

5. **REESCRIBIR** como `modern/<entidad>.py` con DuckDB:
   - SQL de DuckDB para la lógica set-based (mapea casi 1:1 desde el T-SQL),
   - lee de `data/*.parquet`, escribe a `modern/output/<entidad>.parquet`,
   - **sin cursores ni loops** — la lógica fila-a-fila se expresa como SQL set-based
     (p. ej. SCD2 con `LEAD()`/window functions en vez de cursor),
   - docstring arriba con la explicación del paso 2.

6. **COMPROBAR** que el `modern/<entidad>.py` corre (`uv run python modern/<entidad>.py`) y
   que el conteo/forma de filas es razonable vs `Dimension.<Entidad>` del DW.

7. **PR.** Crea la rama `feat/<entidad>` si no estás en ella, commitea, y abre PR con `gh`.
   El cuerpo del PR = la explicación en lenguaje claro del paso 2 (para que el revisor vea
   la lógica legacy en palabras).

Mantén el alcance **solo a esta entidad**. No toques las otras.
