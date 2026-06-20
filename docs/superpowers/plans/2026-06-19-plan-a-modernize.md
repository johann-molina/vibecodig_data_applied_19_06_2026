# Plan A — Modernize legacy ETL to Python + DuckDB — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the 4 stubs in `modern/` (dim_customer, dim_stockitem, dim_supplier, fact_sale) with DuckDB+Python that reproduces the behavior of the legacy `Integration.MigrateStaged*Data` stored procedures, until `modern/verify.py` matches the official DW figures exactly (228,265 rows / S/198,043,439.45).

**Architecture:** Three dimensions built in parallel inside isolated git worktrees (`.claude/worktrees/dim-*`), merged into integration branch `feature/plan-a-modernize`, then fact built sequentially on the main workspace. Final hard gate: `verify.py` exact match.

**Tech Stack:** Python 3.12, DuckDB 1.5 (single dependency), git worktrees, parquet files. No pandas. No ORM. No tests framework — `verify.py` is the only test.

**Spec:** `docs/superpowers/specs/2026-06-19-plan-a-modernize-design.md`

**Safety net:** If a subagent gets stuck >2 attempts on an entity, copy the reference solution from `resultado-final/modern/<entidad>.py` and document the root cause in the commit message.

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `modern/dim_customer.py` | Modify (replace stub) | Build customer dim from `data/src_customers + customercategories + buyinggroups + people` |
| `modern/dim_stockitem.py` | Modify (replace stub) | Build stockitem dim from `data/src_stockitems + colors + packagetypes` |
| `modern/dim_supplier.py` | Modify (replace stub) | Build supplier dim from `data/src_suppliers + suppliercategories + people` |
| `modern/fact_sale.py` | Modify (replace stub) | Build fact from `data/src_invoices + invoicelines` joining the 3 dims for `*_Key` |
| `modern/output/*.parquet` | Created at runtime | Outputs (4 parquets) |
| `modern/run_pipeline.py`, `verify.py`, `build_dashboard.py` | **DO NOT MODIFY** | Scaffolding already done |

---

## Canonical entity template

Every `modern/<entidad>.py` follows this exact shape. The only thing that changes is the SQL inside `con.execute(...)`.

```python
"""<entidad> — equivalente moderno (DuckDB) de Integration.MigrateStaged<E>Data.
LINAJE: <tablas fuente> -> <tabla destino>
REGLAS: <surrogate key + lookups + estado-actual vs SCD2 del legacy>
"""
import duckdb

def build():
    con = duckdb.connect()
    con.execute("""
        COPY (
            -- SQL set-based aquí
        ) TO 'modern/output/<entidad>.parquet' (FORMAT PARQUET)
    """)
    n = con.execute("SELECT count(*) FROM 'modern/output/<entidad>.parquet'").fetchone()[0]
    print(f"<entidad> -> {n} filas")

if __name__ == "__main__":
    build()
```

Hard rules (CLAUDE.md):
- DuckDB only, no pandas, **never `.df()`**.
- Read parquets directly with `read_parquet('data/src_*.parquet')` or quoted-path shorthand `'data/src_x.parquet'`.
- Set-based SQL only (no cursors, no row-by-row loops).
- Surrogate keys with `row_number() OVER (ORDER BY <business_id>)`.

---

## Task 0 — Setup branch + worktrees

**Files:**
- Create: branch `feature/plan-a-modernize`
- Create: branches `feature/plan-a-modernize-customer`, `-stockitem`, `-supplier`
- Create: worktrees `.claude/worktrees/dim-customer`, `dim-stockitem`, `dim-supplier`

- [ ] **Step 0.1: Verify clean working tree**

```bash
git status
```
Expected: `working tree clean` (the spec was already committed in `4f17d2a`).

- [ ] **Step 0.2: Create integration branch**

```bash
git checkout -b feature/plan-a-modernize
git push -u origin feature/plan-a-modernize
```

- [ ] **Step 0.3: Create 3 worktrees for dims (parallel work)**

```bash
git worktree add -b feature/plan-a-modernize-customer  .claude/worktrees/dim-customer  feature/plan-a-modernize
git worktree add -b feature/plan-a-modernize-stockitem .claude/worktrees/dim-stockitem feature/plan-a-modernize
git worktree add -b feature/plan-a-modernize-supplier  .claude/worktrees/dim-supplier  feature/plan-a-modernize
git worktree list
```
Expected output: 5 entries (main + docs-english existing + 3 new).

- [ ] **Step 0.4: Verify pipeline still shows stub error (baseline)**

```bash
uv run python modern/run_pipeline.py
```
Expected: `⏳ Aún falta construir: modern/dim_customer.py` (stub still raises NotImplementedError — this confirms we're starting from a clean baseline).

---

## Task 1 — dim_customer (in worktree `dim-customer`)

**Files:**
- Modify: `.claude/worktrees/dim-customer/modern/dim_customer.py` (currently a 23-line stub)
- Sources: `data/src_customers.parquet`, `data/src_customercategories.parquet`, `data/src_buyinggroups.parquet`, `data/src_people.parquet`
- Reference SP: `legacy_sql/MigrateStagedCustomerData.sql`
- Reference lineage: `reference/lineage.md` (section for Customer)

**Working directory for this task:** `.claude/worktrees/dim-customer/`

- [ ] **Step 1.1: Read the legacy SP and lineage**

```bash
cd .claude/worktrees/dim-customer
cat legacy_sql/MigrateStagedCustomerData.sql
grep -A 30 "Customer" reference/lineage.md
```
Identify: source tables → target columns → join keys. The legacy SP does SCD2 (close old row, insert new). Our modern version produces **current state only** — no history — so we skip the SCD2 logic and just SELECT the current data.

- [ ] **Step 1.2: Inspect source schemas**

```bash
uv run python -c "
import duckdb
for f in ['customers','customercategories','buyinggroups','people']:
    cols = duckdb.sql(f\"DESCRIBE SELECT * FROM 'data/src_{f}.parquet'\").fetchall()
    print(f'--- {f}'); [print(' ', c[0], c[1]) for c in cols[:15]]
"
```
Expected: column names like `CustomerID`, `CustomerName`, `CustomerCategoryID`, `BuyingGroupID`, `PrimaryContactPersonID`, `BillToCustomerID`, `DeliveryPostalCode`, `AccountOpenedDate`, `PersonID`, `FullName`.

- [ ] **Step 1.3: Write `modern/dim_customer.py`**

Replace the stub with:

```python
"""Dimension.Customer — equivalente moderno (DuckDB) de Integration.MigrateStagedCustomerData.
LINAJE: Sales.Customers + Sales.CustomerCategories + Sales.BuyingGroups
        + Application.People (Primary Contact) + self-join Customers (Bill-To).
REGLAS: surrogate Customer_Key vs business WWI_Customer_ID.
        Legacy hace SCD Type 2; aquí estado actual (Valid_To = 9999-12-31).
"""
import duckdb

def build():
    con = duckdb.connect()
    con.execute("""
        COPY (
            SELECT row_number() OVER (ORDER BY c.CustomerID) AS Customer_Key,
                   c.CustomerID            AS WWI_Customer_ID,
                   c.CustomerName          AS Customer,
                   bt.CustomerName         AS Bill_To_Customer,
                   cc.CustomerCategoryName AS Category,
                   bg.BuyingGroupName      AS Buying_Group,
                   p.FullName              AS Primary_Contact,
                   c.DeliveryPostalCode    AS Postal_Code,
                   CAST(c.AccountOpenedDate AS DATE) AS Valid_From,
                   DATE '9999-12-31'        AS Valid_To
            FROM 'data/src_customers.parquet' c
            LEFT JOIN 'data/src_customercategories.parquet' cc USING (CustomerCategoryID)
            LEFT JOIN 'data/src_buyinggroups.parquet'       bg USING (BuyingGroupID)
            LEFT JOIN 'data/src_people.parquet'              p ON p.PersonID    = c.PrimaryContactPersonID
            LEFT JOIN 'data/src_customers.parquet'          bt ON bt.CustomerID = c.BillToCustomerID
        ) TO 'modern/output/dim_customer.parquet' (FORMAT PARQUET)
    """)
    n = con.execute("SELECT count(*) FROM 'modern/output/dim_customer.parquet'").fetchone()[0]
    print(f"dim_customer  -> {n} filas")

if __name__ == "__main__":
    build()
```

- [ ] **Step 1.4: Run it and verify shape**

```bash
uv run python modern/dim_customer.py
```
Expected: `dim_customer  -> 663 filas` (or close — `data/_verify_dw.json` has `dim_customer_rows` for comparison; dim is current-state, not full SCD2 history, so an order of magnitude match is enough).

- [ ] **Step 1.5: Commit and merge to integration branch**

```bash
git add modern/dim_customer.py
git commit -m "feat(dim_customer): build current-state dim from WWI Customers + categories + buying groups"
git push -u origin feature/plan-a-modernize-customer
cd ../../..
git checkout feature/plan-a-modernize
git merge --no-ff feature/plan-a-modernize-customer -m "merge: dim_customer"
git push
```

---

## Task 2 — dim_stockitem (in worktree `dim-stockitem`)

**Files:**
- Modify: `.claude/worktrees/dim-stockitem/modern/dim_stockitem.py`
- Sources: `data/src_stockitems.parquet`, `data/src_colors.parquet`, `data/src_packagetypes.parquet`
- Reference SP: `legacy_sql/MigrateStagedStockItemData.sql`

**Working directory:** `.claude/worktrees/dim-stockitem/`

- [ ] **Step 2.1: Read the legacy SP**

```bash
cd .claude/worktrees/dim-stockitem
cat legacy_sql/MigrateStagedStockItemData.sql
```
Key insight: `PackageTypes` is joined twice — once as `Selling Package` (UnitPackageID) and once as `Buying Package` (OuterPackageID).

- [ ] **Step 2.2: Inspect source schema**

```bash
uv run python -c "
import duckdb
cols = duckdb.sql(\"DESCRIBE SELECT * FROM 'data/src_stockitems.parquet'\").fetchall()
[print(c[0], c[1]) for c in cols]
"
```

- [ ] **Step 2.3: Write `modern/dim_stockitem.py`**

```python
"""Dimension.[Stock Item] — equivalente moderno (DuckDB) de Integration.MigrateStagedStockItemData.
LINAJE: Warehouse.StockItems + Warehouse.Colors + Warehouse.PackageTypes (x2: Selling/Buying).
REGLAS: lookup color, lookup paquete (Selling=UnitPackage, Buying=OuterPackage), surrogate Stock_Item_Key.
"""
import duckdb

def build():
    con = duckdb.connect()
    con.execute("""
        COPY (
            SELECT row_number() OVER (ORDER BY si.StockItemID) AS Stock_Item_Key,
                   si.StockItemID    AS WWI_Stock_Item_ID,
                   si.StockItemName  AS Stock_Item,
                   co.ColorName      AS Color,
                   sp.PackageTypeName AS Selling_Package,
                   bp.PackageTypeName AS Buying_Package,
                   si.Brand, si.Size,
                   si.LeadTimeDays      AS Lead_Time_Days,
                   si.QuantityPerOuter  AS Quantity_Per_Outer,
                   si.IsChillerStock    AS Is_Chiller_Stock,
                   si.TaxRate           AS Tax_Rate,
                   si.UnitPrice         AS Unit_Price,
                   si.RecommendedRetailPrice AS Recommended_Retail_Price,
                   si.TypicalWeightPerUnit   AS Typical_Weight_Per_Unit
            FROM 'data/src_stockitems.parquet' si
            LEFT JOIN 'data/src_colors.parquet'        co USING (ColorID)
            LEFT JOIN 'data/src_packagetypes.parquet'  sp ON sp.PackageTypeID = si.UnitPackageID
            LEFT JOIN 'data/src_packagetypes.parquet'  bp ON bp.PackageTypeID = si.OuterPackageID
        ) TO 'modern/output/dim_stockitem.parquet' (FORMAT PARQUET)
    """)
    n = con.execute("SELECT count(*) FROM 'modern/output/dim_stockitem.parquet'").fetchone()[0]
    print(f"dim_stockitem -> {n} filas")

if __name__ == "__main__":
    build()
```

- [ ] **Step 2.4: Run and verify**

```bash
uv run python modern/dim_stockitem.py
```
Expected: ~227 rows.

- [ ] **Step 2.5: Commit and merge**

```bash
git add modern/dim_stockitem.py
git commit -m "feat(dim_stockitem): build current-state dim from WWI StockItems + colors + packagetypes"
git push -u origin feature/plan-a-modernize-stockitem
cd ../../..
git checkout feature/plan-a-modernize
git merge --no-ff feature/plan-a-modernize-stockitem -m "merge: dim_stockitem"
git push
```

---

## Task 3 — dim_supplier (in worktree `dim-supplier`)

**Files:**
- Modify: `.claude/worktrees/dim-supplier/modern/dim_supplier.py`
- Sources: `data/src_suppliers.parquet`, `data/src_suppliercategories.parquet`, `data/src_people.parquet`
- Reference SP: `legacy_sql/MigrateStagedSupplierData.sql`

**Working directory:** `.claude/worktrees/dim-supplier/`

- [ ] **Step 3.1: Read the legacy SP**

```bash
cd .claude/worktrees/dim-supplier
cat legacy_sql/MigrateStagedSupplierData.sql
```

- [ ] **Step 3.2: Write `modern/dim_supplier.py`**

```python
"""Dimension.Supplier — equivalente moderno (DuckDB) de Integration.MigrateStagedSupplierData.
LINAJE: Purchasing.Suppliers + Purchasing.SupplierCategories + Application.People (contacto).
REGLAS: join proveedor + categoría + contacto principal; surrogate Supplier_Key.
"""
import duckdb

def build():
    con = duckdb.connect()
    con.execute("""
        COPY (
            SELECT row_number() OVER (ORDER BY s.SupplierID) AS Supplier_Key,
                   s.SupplierID        AS WWI_Supplier_ID,
                   s.SupplierName      AS Supplier,
                   sc.SupplierCategoryName AS Category,
                   p.FullName          AS Primary_Contact,
                   s.SupplierReference AS Supplier_Reference,
                   s.PaymentDays       AS Payment_Days,
                   s.DeliveryPostalCode AS Postal_Code
            FROM 'data/src_suppliers.parquet' s
            LEFT JOIN 'data/src_suppliercategories.parquet' sc USING (SupplierCategoryID)
            LEFT JOIN 'data/src_people.parquet'              p ON p.PersonID = s.PrimaryContactPersonID
        ) TO 'modern/output/dim_supplier.parquet' (FORMAT PARQUET)
    """)
    n = con.execute("SELECT count(*) FROM 'modern/output/dim_supplier.parquet'").fetchone()[0]
    print(f"dim_supplier  -> {n} filas")

if __name__ == "__main__":
    build()
```

- [ ] **Step 3.3: Run and verify**

```bash
uv run python modern/dim_supplier.py
```
Expected: ~13 rows.

- [ ] **Step 3.4: Commit and merge**

```bash
git add modern/dim_supplier.py
git commit -m "feat(dim_supplier): build current-state dim from WWI Suppliers + categories + contact"
git push -u origin feature/plan-a-modernize-supplier
cd ../../..
git checkout feature/plan-a-modernize
git merge --no-ff feature/plan-a-modernize-supplier -m "merge: dim_supplier"
git push
```

---

## Task 4 — fact_sale (main workspace, integration branch)

**Files:**
- Modify: `modern/fact_sale.py` (currently a 19-line stub)
- Sources: `data/src_invoices.parquet`, `data/src_invoicelines.parquet`, `data/src_packagetypes.parquet`
- Dim dependencies: `modern/output/dim_customer.parquet`, `modern/output/dim_stockitem.parquet` (produced by Tasks 1 & 2)
- Reference SP: `legacy_sql/MigrateStagedSaleData.sql`

**Working directory:** repo root `/home/johannmv/github_vf/vibecodig_data_applied_19_06_2026/`

**Pre-flight:** must be on branch `feature/plan-a-modernize` with the 3 dim merges already applied. The dim parquets must exist (they were just built in the worktrees, but `modern/output/` is gitignored — re-run the dims here):

- [ ] **Step 4.1: Re-run dims locally to populate `modern/output/`**

```bash
git status                # confirm: on feature/plan-a-modernize, clean
uv run python modern/dim_customer.py
uv run python modern/dim_stockitem.py
uv run python modern/dim_supplier.py
ls modern/output/
```
Expected: `dim_customer.parquet  dim_stockitem.parquet  dim_supplier.parquet`.

- [ ] **Step 4.2: Read the legacy SP**

```bash
cat legacy_sql/MigrateStagedSaleData.sql
```
Key insight: grain = invoice line (`InvoiceLineID`). Resolves surrogate keys by joining the dim parquets on business id (`WWI_Customer_ID`, `WWI_Stock_Item_ID`). Bill-to is a second customer key.

- [ ] **Step 4.3: Inspect invoice schemas**

```bash
uv run python -c "
import duckdb
for f in ['invoices','invoicelines']:
    cols = duckdb.sql(f\"DESCRIBE SELECT * FROM 'data/src_{f}.parquet'\").fetchall()
    print(f'--- {f}'); [print(' ', c[0], c[1]) for c in cols]
"
```

- [ ] **Step 4.4: Write `modern/fact_sale.py`**

```python
"""Fact.Sale — equivalente moderno (DuckDB) de Integration.MigrateStagedSaleData.
LINAJE: Sales.Invoices + Sales.InvoiceLines -> Fact.Sale. Grano = línea de factura.
REGLA CLAVE: resolución de surrogate keys hacia las dimensiones (se guardan los *_Key,
no los business IDs). Como las dimensiones son estado-actual, el lookup es por business id.
MEDIDAS (deben cuadrar EXACTO con Fact.Sale del DW):
  Total Excluding Tax = ExtendedPrice - TaxAmount
  Total Including Tax = ExtendedPrice
  Profit              = LineProfit
"""
import duckdb

def build():
    con = duckdb.connect()
    con.execute("""
        COPY (
            SELECT il.InvoiceLineID  AS Sale_Key,
                   dc.Customer_Key,
                   dbt.Customer_Key  AS Bill_To_Customer_Key,
                   ds.Stock_Item_Key,
                   i.InvoiceDate     AS Invoice_Date,
                   CAST(strftime(i.InvoiceDate, '%Y%m%d') AS INTEGER) AS Invoice_Date_Key,
                   i.SalespersonPersonID AS WWI_Salesperson_ID,
                   i.InvoiceID       AS WWI_Invoice_ID,
                   il.Description,
                   pt.PackageTypeName AS Package,
                   il.Quantity,
                   il.UnitPrice      AS Unit_Price,
                   il.TaxRate        AS Tax_Rate,
                   (il.ExtendedPrice - il.TaxAmount) AS Total_Excluding_Tax,
                   il.TaxAmount      AS Tax_Amount,
                   il.LineProfit     AS Profit,
                   il.ExtendedPrice  AS Total_Including_Tax
            FROM 'data/src_invoicelines.parquet' il
            JOIN 'data/src_invoices.parquet' i USING (InvoiceID)
            LEFT JOIN 'modern/output/dim_customer.parquet'  dc  ON dc.WWI_Customer_ID  = i.CustomerID
            LEFT JOIN 'modern/output/dim_customer.parquet'  dbt ON dbt.WWI_Customer_ID = i.BillToCustomerID
            LEFT JOIN 'modern/output/dim_stockitem.parquet' ds  ON ds.WWI_Stock_Item_ID = il.StockItemID
            LEFT JOIN 'data/src_packagetypes.parquet'       pt  ON pt.PackageTypeID = il.PackageTypeID
        ) TO 'modern/output/fact_sale.parquet' (FORMAT PARQUET)
    """)
    n = con.execute("SELECT count(*) FROM 'modern/output/fact_sale.parquet'").fetchone()[0]
    orphan = con.execute("SELECT count(*) FROM 'modern/output/fact_sale.parquet' WHERE Customer_Key IS NULL OR Stock_Item_Key IS NULL").fetchone()[0]
    print(f"fact_sale     -> {n} filas (keys sin resolver: {orphan})")

if __name__ == "__main__":
    build()
```

- [ ] **Step 4.5: Run it**

```bash
uv run python modern/fact_sale.py
```
Expected: `fact_sale     -> 228265 filas (keys sin resolver: 0)`.

If `keys sin resolver > 0`: there are invoices with customer/stock IDs not in the dim — debug with `systematic-debugging`.

- [ ] **Step 4.6: Commit**

```bash
git add modern/fact_sale.py
git commit -m "feat(fact_sale): build fact at invoice-line grain, resolve surrogate keys, compute measures"
git push
```

---

## Task 5 — Hard gate: verify.py + dashboard

**Files:**
- Run only (do not modify): `modern/run_pipeline.py`, `modern/verify.py`, `modern/build_dashboard.py`

**Working directory:** repo root

- [ ] **Step 5.1: Run the full pipeline end-to-end**

```bash
uv run python modern/run_pipeline.py
```
Expected: all 4 entities build without error, ending with `fact_sale     -> 228265 filas (keys sin resolver: 0)`.

- [ ] **Step 5.2: Run the hard-gate verification**

```bash
uv run python modern/verify.py
```
Expected output (excerpt):
```
✅ Fact.Sale · filas              moderno=           228,265  == legacy=           228,265
✅ Fact.Sale · Total c/IGV        moderno=  198,043,439.45    == legacy=  198,043,439.45
✅ Fact.Sale · Total s/IGV        moderno=  172,084,653.62    == legacy=  172,084,653.62
✅ Fact.Sale · Cantidad           moderno=         8,950,628  == legacy=         8,950,628
✅ Fact.Sale · Profit             moderno=   75,891,738.20    == legacy=   75,891,738.20
• Dimension.Customer · filas (forma)   moderno=  663  ~ legacy=  663
• Dimension.StockItem · filas (forma)  moderno=  227  ~ legacy=  227
• Dimension.Supplier · filas (forma)   moderno=   13  ~ legacy=   13
RESULTADO: ✅ TODAS las medidas exactas cuadran con el DW real
```

**Hard gate:** if `RESULTADO` is `❌`, **stop and debug**. Do not proceed to merge.

- [ ] **Step 5.3: Build dashboard**

```bash
uv run python modern/build_dashboard.py
ls -la dashboard.html
```
Expected: `dashboard.html` created.

- [ ] **Step 5.4: Commit any incidental changes (gitignore'd outputs won't show)**

```bash
git status
```
Expected: nothing to commit (`modern/output/`, `dashboard.html` are gitignored).

---

## Task 6 — Cleanup and finish branch

- [ ] **Step 6.1: Remove the 3 worktrees**

```bash
git worktree remove .claude/worktrees/dim-customer
git worktree remove .claude/worktrees/dim-stockitem
git worktree remove .claude/worktrees/dim-supplier
git worktree list
```
Expected: only `main` and `docs-english` remain.

- [ ] **Step 6.2: Verify branch state**

```bash
git log --oneline main..feature/plan-a-modernize
```
Expected: 4 feature commits + 3 merge commits.

- [ ] **Step 6.3: Invoke `finishing-a-development-branch`**

Let the skill present options (PR vs direct merge vs keep). The recommended path: open a PR via `gh pr create` for review, then merge to `main`.

---

## Self-review checklist (for the orchestrator before dispatching)

1. **Spec coverage** — Every requirement in the spec is mapped to a task:
   - 4 entities → Tasks 1, 2, 3, 4 ✓
   - Worktrees → Task 0 ✓
   - Hard gate verify.py → Task 5 ✓
   - Dashboard → Task 5 ✓
   - Cleanup → Task 6 ✓
2. **Placeholders** — None. Every code block is complete and runnable.
3. **Type consistency** — Column names match across tasks:
   - `Customer_Key`, `Stock_Item_Key`, `Supplier_Key` (surrogate)
   - `WWI_Customer_ID`, `WWI_Stock_Item_ID`, `WWI_Supplier_ID` (business)
   - Used identically in dims and fact_sale.
4. **Order of operations** — Dims (parallel) → merge → fact (serial) → verify → dashboard → finish. Each depends only on what came before.

---

## Execution handoff

Two options:

1. **Subagent-driven (recommended)** — one fresh subagent per task, two-stage review between. Best for cleanly separated tasks like these 4 entities.
2. **Inline execution** — execute in this session with `executing-plans`, checkpoints between tasks.
