# Plan A — Modernizar ETL legacy a Python + DuckDB

**Fecha:** 2026-06-19
**Autor:** Johann Molina (jmolina@inszoneins.com) + Claude
**Estado:** Diseño aprobado, pendiente de plan de implementación

## Objetivo

Rellenar los 4 stubs en `modern/` con código Python + DuckDB que reproduzca el comportamiento de los stored procedures `Integration.MigrateStaged*Data` del DW WideWorldImporters, hasta que `modern/verify.py` cuadre EXACTO contra las cifras oficiales del DW:

- **`Fact.Sale`**: 228,265 filas, Total Including Tax = **S/ 198,043,439.45**.
- **Dimensiones**: shape razonable (estado-actual) vs `data/_verify_dw.json`.

## Alcance

**Solo 4 entidades** (regla dura de CLAUDE.md):
1. `Dimension.Customer` → `modern/dim_customer.py`
2. `Dimension.[Stock Item]` → `modern/dim_stockitem.py`
3. `Dimension.Supplier` → `modern/dim_supplier.py`
4. `Fact.Sale` → `modern/fact_sale.py`

**Fuera de alcance:** otras dimensiones de WWI (Date, City, Employee, PaymentMethod, TransactionType), `Fact.Order/Purchase/StockHolding/Transaction`, tests unitarios, reescribir el scaffolding existente.

## Reglas duras (heredadas de CLAUDE.md)

1. **Solo lectura sobre el legacy.** En este Plan A los SPs se leen del disco (`legacy_sql/*.sql`), no por MCP.
2. **Target = Python + DuckDB puro.** Sin pandas. Una sola dependencia: `duckdb`. Usar `con.execute(...).fetchall()/.fetchone()`, **NUNCA `.df()`**.
3. **El código lee `data/*.parquet` y escribe `modern/output/`.** No se conecta al SQL Server en runtime.
4. **Set-based, sin cursores.** El T-SQL fila-a-fila se expresa con SQL de DuckDB + window functions si hace falta.
5. **No tocar el scaffolding ya hecho:** `modern/run_pipeline.py`, `modern/verify.py`, `modern/build_dashboard.py`.

## Arquitectura

### Rama y worktrees

```
main
 └─ feature/plan-a-modernize           (rama integradora)
     ├─ wt-dim-customer/   ← rama feature/plan-a-modernize-customer
     ├─ wt-dim-stockitem/  ← rama feature/plan-a-modernize-stockitem
     └─ wt-dim-supplier/   ← rama feature/plan-a-modernize-supplier
```

- Los **3 worktrees de dims** corren en paralelo (sin dependencias entre sí).
- Tras mergear las 3 dims a `feature/plan-a-modernize`, `fact_sale` se construye en el workspace principal (depende de las dims).
- `verify.py` y `build_dashboard.py` se corren en `feature/plan-a-modernize` al final.
- Merge final `feature/plan-a-modernize → main` solo si `verify.py` cuadra exacto.

### Orquestación con superpowers

| Fase | Skill | Output |
|---|---|---|
| 1. Brainstorm (este doc) | `brainstorming` | Spec aprobado |
| 2. Plan | `writing-plans` | Plan en `docs/superpowers/plans/2026-06-19-plan-a-modernize.md` |
| 3. Worktrees | `using-git-worktrees` | 3 worktrees creados |
| 4. Dims en paralelo | `dispatching-parallel-agents` | 3 subagentes, uno por dim |
| 5. Review por dim | `requesting-code-review` | Aprobación spec + code quality |
| 6. Merge dims | manual | `feature/plan-a-modernize` con 3 dims |
| 7. Fact | `subagent-driven-development` | `modern/fact_sale.py` |
| 8. Verify | manual (`verify.py`) | Cifras exactas |
| 9. Dashboard | manual (`build_dashboard.py`) | `dashboard.html` |
| 10. Finish | `finishing-a-development-branch` | PR o merge a `main` |

## Componentes

### Por cada entidad, el subagente produce

| Input | Output |
|---|---|
| `legacy_sql/MigrateStaged<E>Data.sql` (fuente de verdad de las reglas) | `modern/<entidad>.py` |
| `data/src_*.parquet` (fuentes WWI) | `modern/output/<entidad>.parquet` |
| `reference/lineage.md` (clave) | (verificación de linaje) |

### Forma canónica del `modern/<entidad>.py`

```python
"""<entidad> — linaje + reglas en lenguaje claro.

  SP legacy : legacy_sql/MigrateStaged<E>Data.sql
  Linaje    : <tablas fuente> -> <tabla destino>
  Lee       : data/src_*.parquet
  Escribe   : modern/output/<entidad>.parquet
"""
import duckdb
from pathlib import Path

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

def build():
    con = duckdb.connect()
    # SQL set-based que mapea 1:1 desde el T-SQL.
    con.execute(f"""
        COPY (
            SELECT ...
            FROM read_parquet('data/src_x.parquet') x
            JOIN read_parquet('data/src_y.parquet') y ON ...
        ) TO '{OUT / "<entidad>.parquet"}' (FORMAT PARQUET)
    """)

if __name__ == "__main__":
    build()
```

### Data flow

```
data/src_customers + customercategories + buyinggroups + people ─┐
                                                                  ├→ dim_customer  ─┐
data/src_stockitems + colors + packagetypes ─────────────────────┐│                  │
                                                                  ├→ dim_stockitem ─┤
data/src_suppliers + suppliercategories + people ────────────────┐│                  ├→ fact_sale → verify → dashboard
                                                                  ├→ dim_supplier  ─┘
data/src_invoices + invoicelines ──────────────────────────────────────────────────┘
```

## Reglas de transformación por entidad

### `dim_customer` (de `MigrateStagedCustomerData.sql`)
- Linaje: `Sales.Customers` + `CustomerCategories` + `BuyingGroups` + `People` (contacto principal) + self-join a `Customers` (Bill-To).
- SCD Type 2 en el legacy; aquí **modelamos estado-actual** (la última versión vigente por `Customer Key`).
- Surrogate key `Customer Key` generada con `row_number()` ordenando por `Customer ID`.

### `dim_stockitem` (de `MigrateStagedStockItemData.sql`)
- Linaje: `Warehouse.StockItems` + `Colors` + `PackageTypes` (dos joins: Selling/Buying).
- Surrogate key `Stock Item Key` generada igual que customer.

### `dim_supplier` (de `MigrateStagedSupplierData.sql`)
- Linaje: `Purchasing.Suppliers` + `SupplierCategories` + `People`.
- Surrogate key `Supplier Key` análogo.

### `fact_sale` (de `MigrateStagedSaleData.sql`)
- Linaje: `Sales.Invoices` + `Sales.InvoiceLines`. Grano = **línea de factura**.
- Resolución de surrogate keys: join contra `modern/output/dim_*.parquet` por la business key.
- Medidas:
  - `Total Including Tax` = `ExtendedPrice`
  - `Total Excluding Tax` = `ExtendedPrice - TaxAmount`
  - `Profit` = `LineProfit`
- **Conteo esperado: 228,265 filas. Suma de `Total Including Tax`: S/198,043,439.45.**

## Criterios de éxito (hard gates)

1. ✅ `python modern/<entidad>.py` corre sin error y produce `modern/output/<entidad>.parquet` (por cada una de las 4).
2. ✅ `python modern/run_pipeline.py` corre las 4 sin error.
3. ✅ `python modern/verify.py` reporta `Fact.Sale` = **228,265** filas y **S/198,043,439.45**, sin diferencias.
4. ✅ Dims con shape razonable vs `data/_verify_dw.json`.
5. ✅ `python modern/build_dashboard.py` genera `dashboard.html`.

Si cualquiera falla, **no se mergea** a `main`.

## Error handling

- **Subagente bloqueado (>2 intentos sin éxito):** invocar `systematic-debugging` para root-cause. Si tampoco resuelve, último recurso: copiar de `resultado-final/modern/<entidad>.py` documentando la causa raíz del bloqueo en el plan.
- **`verify.py` no cuadra:** `systematic-debugging`. Comparar con la solución de `resultado-final/` solo después de intentar diagnosticar.
- **Worktree con conflictos al mergear:** resolver manualmente, no usar `--force`.

## Testing

No se escriben tests unitarios (fuera de alcance del taller). El **test único** es `verify.py` cuadrando exacto contra cifras oficiales del DW. Esto reemplaza el ciclo TDD del workflow estándar de superpowers.

## Lo que NO hace este plan

- No usa MCP / SQL Server en runtime (eso es Camino B, fuera de alcance).
- No crea nuevos slash commands ni nuevos skills (reusa `/modernize-sp` existente como referencia y los skills de superpowers).
- No reescribe `run_pipeline.py`, `verify.py`, ni `build_dashboard.py`.
- No agrega dimensiones más allá de las 3 elegidas.
- No agrega tests unitarios.

## Siguiente paso

Invocar `writing-plans` para producir el plan de implementación con tareas concretas (2-5 minutos cada una, archivos exactos, código completo, pasos de verificación).
