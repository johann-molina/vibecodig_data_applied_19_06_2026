# Clave de respuestas — Linaje real de WideWorldImportersDW

> **Verdad de tierra** para verificar en vivo. Combina el catálogo oficial de Microsoft con lo
> que confirmé leyendo los SPs y los datos reales (ver `legacy_sql/*.sql` extraídos de la BD).
> Tenlo abierto durante el taller: si Claude explica una regla con confianza pero mal, lo cazas.

## Cómo es el ETL real (confirmado en la BD)
- Los procedimientos de ETL son los **`Integration.MigrateStaged<Entidad>Data`** (16 en total).
  **NO existen procedimientos `Get*Updates`** como objetos en la BD: el EXTRACT/TRANSFORM (llenar
  las tablas `Integration.*_Staging` desde el OLTP) lo hace el **paquete SSIS** `Daily ETL`.
- Por eso el SP solo muestra la **mitad de carga**:
  - **Dimensiones** (`MigrateStagedCustomerData`, `...StockItemData`, `...SupplierData`):
    **SCD Type 2** → "cierra la fila vigente (`Valid To` = nueva `Valid From`) e inserta las
    nuevas versiones" desde staging. (Ver `legacy_sql/MigrateStagedCustomerData.sql`.)
  - **Hecho** (`MigrateStagedSaleData`): **resolución point-in-time de surrogate keys** — por cada
    dimensión hace `WHERE [Last Modified When] > [Valid From] AND <= [Valid To]`, luego delete+insert.
- El rewrite moderno reconstruye **end-to-end** (OLTP → dim/hecho), o sea SSIS+staging+migrate juntos.

## Las 4 entidades del taller — linaje (OLTP real → DW)

| Entidad (DW) | Tipo | Tablas fuente (OLTP) | Columnas destino clave |
|---|---|---|---|
| **Dimension.Customer** | Dim SCD2 | `Sales.Customers` + `Sales.CustomerCategories` + `Sales.BuyingGroups` + `Application.People` (Primary Contact) + self-join (Bill To) | `[Customer Key]` (surrogate), `[WWI Customer ID]`, Customer, `[Bill To Customer]`, Category, `[Buying Group]`, `[Primary Contact]`, `[Postal Code]`, `[Valid From/To]` |
| **Dimension.[Stock Item]** | Dim SCD2 | `Warehouse.StockItems` + `Warehouse.Colors` + `Warehouse.PackageTypes` (x2: Selling=UnitPackage, Buying=OuterPackage) | `[Stock Item Key]`, `[WWI Stock Item ID]`, `[Stock Item]`, Color, `[Selling/Buying Package]`, Brand, Size, `[Unit Price]`, `[Tax Rate]`… |
| **Dimension.Supplier** | Dim SCD2 | `Purchasing.Suppliers` + `Purchasing.SupplierCategories` + `Application.People` | `[Supplier Key]`, `[WWI Supplier ID]`, Supplier, Category, `[Primary Contact]`, `[Supplier Reference]`, `[Payment Days]` |
| **Fact.Sale** | Hecho | `Sales.Invoices` + `Sales.InvoiceLines` | `*_Key` (resueltas a dims), `[WWI Invoice ID]`, Quantity, `[Unit Price]`, `[Tax Rate]`, `[Total Excluding/Including Tax]`, `[Tax Amount]`, Profit |

Mapeo de medidas del hecho (confirmado): `Total Including Tax = InvoiceLines.ExtendedPrice` ·
`Total Excluding Tax = ExtendedPrice - TaxAmount` · `Profit = LineProfit` · grano = línea de factura.

## Cifras reales del DW (clave de respuestas — verificadas)
| Tabla | Filas | Notas |
|---|---|---|
| **Fact.Sale** | **228,265** | = `Sales.InvoiceLines` (grano 1:1) |
| Fact.Sale · Total Including Tax | **198,043,439.45** | el pipeline moderno cuadra al céntimo |
| Fact.Sale · Total Excluding Tax | **172,261,341.20** | |
| Fact.Sale · Quantity (suma) | **8,950,628** | |
| Fact.Sale · Profit (suma) | **85,729,180.90** | |
| Dimension.Customer | 403 | histórico SCD2 (OLTP tiene 663 clientes actuales) |
| Dimension.[Stock Item] | 672 | histórico SCD2 (OLTP tiene 227 productos actuales) |
| Dimension.Supplier | 28 | histórico SCD2 (OLTP tiene 13 proveedores actuales) |

> **Por qué las dimensiones no cuadran en conteo:** el DW acumula **versiones históricas** (SCD2)
> de varias corridas del ETL; el OLTP solo tiene el estado actual. El rewrite moderno reproduce
> la **forma y la lógica**, no el histórico exacto. Las **medidas del hecho sí cuadran EXACTO**
> (no dependen de qué versión de dimensión se use) — y eso es la verificación estrella.

## Notas de verificación en vivo (por MCP)
```sql
SELECT COUNT(*) FROM Fact.Sale;                          -- 228265
SELECT SUM([Total Including Tax]) FROM Fact.Sale;        -- 198043439.45
SELECT TOP 5 * FROM Dimension.Customer ORDER BY [Customer Key];
-- ver una dimensión con varias versiones SCD2:
SELECT [WWI Stock Item ID], COUNT(*) FROM Dimension.[Stock Item] GROUP BY 1 HAVING COUNT(*)>1;
```
