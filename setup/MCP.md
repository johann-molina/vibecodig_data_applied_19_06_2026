# Configurar el MCP de SQL Server (Camino B)

> **¿Cuándo necesitas esto?** Solo si quieres el "wow" del taller: que Claude se conecte por MCP
> a un SQL Server real y lea los stored procedures en vivo. Para el **Camino A** (offline, desde
> `data/*.parquet`) **NO** necesitas MCP — sáltate este archivo y ve al Paso 3 del `README.md`.

## Pre-requisitos
- Docker corriendo y `bash setup/restore.sh` ya ejecutado (ambas BDs en `ONLINE`).
- Credenciales del contenedor (definidas en `setup/docker-compose.yml`):
  - host: `localhost` · puerto: `1433` · usuario: `sa` · password: `Taller2026!Claude`
  - bases: `WideWorldImporters` (OLTP) y `WideWorldImportersDW` (DW)

## Elegir un MCP server de SQL Server
Hay varios. Cualquiera sirve **mientras sea solo-lectura**. Estos son los más usados:

| Server | Lenguaje | Notas |
|---|---|---|
| **`@executeautomation/database-server`** | Node | Soporta MSSQL/MySQL/Postgres/SQLite. `npx` directo, fácil de probar. |
| **`mcp-mssql`** (pip) | Python | Específico SQL Server. `pip install` o `uvx`. |
| **MSSQL MCP oficial de Microsoft** | .NET | Empuja desde Microsoft (búscalo en `github.com/microsoft`). Más pesado. |

> No probamos los 3 acá. El que **ya quedó testeado** en este taller es uno genérico tipo
> `@executeautomation/database-server`. Si usas otro, ajusta `command`/`args` del ejemplo de abajo.

## Configuración en Claude Code

Primero, instalá el MCP server globalmente (testeado):
```bash
npm install -g @executeautomation/database-server
```

Claude Code lee MCP servers desde `.mcp.json` (en la raíz del repo) o desde tu config global.
Crea `.mcp.json` en la raíz del proyecto con el siguiente contenido (sintaxis del binario
`ea-database-server` v1.1.0, **flag `--sqlserver`** no `--mssql`):

```json
{
  "mcpServers": {
    "wwi-dw": {
      "command": "npx",
      "args": [
        "-y",
        "@executeautomation/database-server",
        "--sqlserver",
        "--server", "localhost",
        "--port", "1433",
        "--database", "WideWorldImportersDW",
        "--user", "sa",
        "--password", "Taller2026!Claude"
      ]
    },
    "wwi-oltp": {
      "command": "npx",
      "args": [
        "-y",
        "@executeautomation/database-server",
        "--sqlserver",
        "--server", "localhost",
        "--port", "1433",
        "--database", "WideWorldImporters",
        "--user", "sa",
        "--password", "Taller2026!Claude"
      ]
    }
  }
}
```

> ⚠️ `.mcp.json` puede contener credenciales — está en `.gitignore` por defecto. Si quieres
> versionarlo, **usa variables de entorno** (`"--password", "${MSSQL_SA_PASSWORD}"`) y deja la
> contraseña fuera del archivo.

## Reiniciar Claude Code y aprobar el server
1. Cierra y abre Claude Code en la raíz del repo (lee `.mcp.json` al arrancar).
2. Aprueba el server cuando te pida permiso la primera vez.
3. Confirma con `/mcp` (lista los servers conectados).

## Smoke test (3 queries que deben funcionar)
Pídele esto a Claude en orden:

1. **Listar los SPs del esquema Integration:**
   > "Por MCP, lista los procedimientos del esquema `Integration` en `WideWorldImportersDW`."

   Debería devolver ~16 procs `MigrateStaged*Data`, `GetLineageKey`, etc.

2. **Leer la definición de un SP:**
   > "Lee la definición de `Integration.MigrateStagedCustomerData` por MCP y resúmela."

   Debería leer y explicar el SCD Type 2 (cierra fila vigente, inserta nueva).

3. **Contar filas del DW (la verificación):**
   > "Por MCP cuenta `Fact.Sale` en `WideWorldImportersDW`."

   Debe dar **228,265**. Si no cuadra, hay un problema de conexión o de base seleccionada.

## Read-only — cómo asegurarlo

El MCP server no impone read-only por sí mismo. Tres capas de defensa, en orden de
recomendación:

1. **Crea un login dedicado de solo lectura** en SQL Server y úsalo en `.mcp.json` en lugar
   de `sa`:
   ```sql
   CREATE LOGIN claude_ro WITH PASSWORD = 'Lectura2026!';
   USE WideWorldImportersDW;
   CREATE USER claude_ro FOR LOGIN claude_ro;
   ALTER ROLE db_datareader ADD MEMBER claude_ro;
   GRANT VIEW DEFINITION TO claude_ro;  -- para OBJECT_DEFINITION sobre los SPs
   USE WideWorldImporters; -- repetir en la otra base
   CREATE USER claude_ro FOR LOGIN claude_ro;
   ALTER ROLE db_datareader ADD MEMBER claude_ro;
   GRANT VIEW DEFINITION TO claude_ro;
   ```
   Con `db_datareader`, cualquier `INSERT/UPDATE/DELETE` fallará con error de permisos.

2. **Snapshot / backup del volumen Docker** antes del taller. Si algo se escribe por error,
   levantas un contenedor limpio y restauras. Es local, es rápido.

3. **Recordatorio en `CLAUDE.md`** (ya está): regla #1 "El MCP es READ-ONLY".

## Si algo falla
- **`/mcp` no muestra el server →** revisa que `.mcp.json` esté en la raíz del repo y que
  reiniciaste Claude Code.
- **Timeout al conectar →** ¿`docker compose ps` muestra `wwi-sqlserver` corriendo?
  ¿`docker exec wwi-sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P
  "Taller2026!Claude" -C -Q "SELECT 1"` responde?
- **"login failed for user sa" →** la password en `.mcp.json` no coincide con la del
  `docker-compose.yml` (o con `MSSQL_SA_PASSWORD` si la cambiaste).
- **Plan B si nada conecta →** sigue el **Camino A**: `data/*.parquet` ya están versionados,
  los SPs reales están en `legacy_sql/*.sql`. El taller corre completo sin MCP. La diferencia
  es solo perderse el "Claude leyendo el SP en vivo desde la BD".
