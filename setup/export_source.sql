-- Export de las tablas FUENTE (OLTP) que necesitan las 4 entidades del taller.
-- Objetivo: dejar data/*.parquet para que el código DuckDB corra DETERMINISTA, sin depender
-- de la BD viva en tiempo de ejecución (regla #3 de CLAUDE.md).
--
-- Cómo usarlo en prep (elige una vía):
--   A) Por MCP (recomendado): pídele a Claude que ejecute cada SELECT por el MCP de SQL Server
--      y guarde el resultado como parquet en data/ usando DuckDB. Tablas chicas → rápido.
--   B) Con bcp/sqlcmd a CSV y luego DuckDB CSV -> parquet.
--
-- Estas SELECT son la "extracción" cruda; la TRANSFORMACIÓN (joins, SCD2, surrogate keys) la
-- hará el código moderno en DuckDB — que es justo lo que Claude reconstruye del SP legacy.

-- ============ CUSTOMER ============
-- fuente: Sales.Customers + Sales.BuyingGroups + Sales.CustomerCategories
SELECT * FROM WideWorldImporters.Sales.Customers;            -- -> data/src_customers.parquet
SELECT * FROM WideWorldImporters.Sales.BuyingGroups;         -- -> data/src_buyinggroups.parquet
SELECT * FROM WideWorldImporters.Sales.CustomerCategories;   -- -> data/src_customercategories.parquet

-- ============ STOCKITEM ============
-- fuente: Warehouse.StockItems + Warehouse.Colors + Warehouse.PackageTypes
SELECT * FROM WideWorldImporters.Warehouse.StockItems;       -- -> data/src_stockitems.parquet
SELECT * FROM WideWorldImporters.Warehouse.Colors;           -- -> data/src_colors.parquet
SELECT * FROM WideWorldImporters.Warehouse.PackageTypes;     -- -> data/src_packagetypes.parquet

-- ============ SUPPLIER ============
-- fuente: Purchasing.Suppliers + Purchasing.SupplierCategories
SELECT * FROM WideWorldImporters.Purchasing.Suppliers;           -- -> data/src_suppliers.parquet
SELECT * FROM WideWorldImporters.Purchasing.SupplierCategories;  -- -> data/src_suppliercategories.parquet

-- ============ SALE (hecho) ============
-- fuente: Sales.Invoices + Sales.InvoiceLines  (InvoiceLines es la grande, ~228k filas)
SELECT * FROM WideWorldImporters.Sales.Invoices;             -- -> data/src_invoices.parquet
SELECT * FROM WideWorldImporters.Sales.InvoiceLines;         -- -> data/src_invoicelines.parquet

-- ============ CLAVE DE RESPUESTAS (para verificar) ============
-- el resultado legacy ya poblado en el DW — NO se modela, solo se compara contra tu salida:
-- SELECT COUNT(*) FROM WideWorldImportersDW.Dimension.Customer;
-- SELECT TOP 20 * FROM WideWorldImportersDW.Dimension.Customer ORDER BY [Customer Key];
-- SELECT COUNT(*) FROM WideWorldImportersDW.Fact.Sale;
