#!/usr/bin/env bash
# Restaura WideWorldImporters (OLTP) y WideWorldImportersDW (DW) en el SQL Server de Docker.
# Uso (desde la carpeta setup/):  bash restore.sh
# Requiere: docker + docker compose. Pensado para WSL2.
#
# >>> PROBADO end-to-end. Dos gotchas reales ya resueltos aquí:
#  1) El OLTP Full trae un filegroup In-Memory cuyo nombre lógico es 'WWI_InMemory_Data_1'.
#  2) El DW *Full* FALLA al restaurar en SQL Server 2022 Linux (Hekaton: "Msg 41311 - File error
#     during C code generation" -> DB en estado SUSPECT). Solución: usar el DW *Standard*, que NO
#     trae filegroup In-Memory pero SÍ todas las tablas, datos y los stored procedures Integration.*.
set -euo pipefail

PW="${MSSQL_SA_PASSWORD:-Taller2026!Claude}"
REL="https://github.com/Microsoft/sql-server-samples/releases/download/wide-world-importers-v1.0"
BAK_DIR="$(dirname "$0")/backups"
mkdir -p "$BAK_DIR"

echo "==> 1/4 Descargando .bak (si faltan)..."
[ -f "$BAK_DIR/WideWorldImporters-Full.bak" ]       || curl -fL --retry 3 -o "$BAK_DIR/WideWorldImporters-Full.bak"       "$REL/WideWorldImporters-Full.bak"
[ -f "$BAK_DIR/WideWorldImportersDW-Standard.bak" ] || curl -fL --retry 3 -o "$BAK_DIR/WideWorldImportersDW-Standard.bak" "$REL/WideWorldImportersDW-Standard.bak"

echo "==> 2/4 Levantando SQL Server..."
docker compose up -d
echo "    esperando a que SQL Server acepte conexiones..."
sql() { docker exec wwi-sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$PW" -C -b "$@"; }
for i in $(seq 1 40); do sql -Q "SELECT 1" >/dev/null 2>&1 && { echo "    listo"; break; }; sleep 3; done

echo "==> 3/4 Restaurando WideWorldImporters (OLTP, Full)..."
sql -Q "RESTORE DATABASE WideWorldImporters FROM DISK='/var/opt/mssql/backups/WideWorldImporters-Full.bak'
  WITH MOVE 'WWI_Primary'          TO '/var/opt/mssql/data/WideWorldImporters.mdf',
       MOVE 'WWI_UserData'         TO '/var/opt/mssql/data/WideWorldImporters_UserData.ndf',
       MOVE 'WWI_Log'              TO '/var/opt/mssql/data/WideWorldImporters.ldf',
       MOVE 'WWI_InMemory_Data_1'  TO '/var/opt/mssql/data/WideWorldImporters_InMemory_Data_1',
       REPLACE, RECOVERY;"

echo "==> 4/4 Restaurando WideWorldImportersDW (DW, Standard — sin In-Memory)..."
sql -Q "RESTORE DATABASE WideWorldImportersDW FROM DISK='/var/opt/mssql/backups/WideWorldImportersDW-Standard.bak'
  WITH MOVE 'WWI_Primary'  TO '/var/opt/mssql/data/WideWorldImportersDW.mdf',
       MOVE 'WWI_UserData' TO '/var/opt/mssql/data/WideWorldImportersDW_UserData.ndf',
       MOVE 'WWI_Log'      TO '/var/opt/mssql/data/WideWorldImportersDW.ldf',
       REPLACE, RECOVERY;"

echo "==> Verificación: bases ONLINE + SPs de ETL en el DW"
sql -Q "SELECT name, state_desc FROM sys.databases WHERE name LIKE 'WideWorld%'" -W
sql -d WideWorldImportersDW -Q "SELECT s.name+'.'+o.name FROM sys.procedures o JOIN sys.schemas s ON o.schema_id=s.schema_id WHERE s.name='Integration' ORDER BY o.name;" -h -1

echo ""
echo "LISTO. Ambas bases deben decir ONLINE. (Si necesitas el OLTP sin In-Memory, también existe"
echo "WideWorldImporters-Standard.bak con 3 archivos lógicos: WWI_Primary/WWI_UserData/WWI_Log.)"
