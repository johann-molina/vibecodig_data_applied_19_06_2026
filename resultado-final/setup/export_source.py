"""Exporta las tablas FUENTE reales de WideWorldImporters (OLTP) a data/src_*.parquet, y captura
las cifras de verificación del DW real en data/_verify_dw.json.

Vía directa SIN MCP: usa pymssql desde el host -> SQL Server en Docker (localhost:1433).
  uv pip install pymssql        # (o: pip install pymssql)
  python3 setup/export_source.py
Alternativa por MCP: ver setup/export_source.sql (mismas SELECT) y pídele a Claude que las
guarde como parquet en data/. Cualquiera de las dos deja listo el input del pipeline DuckDB.

PROBADO: produce los 11 src_*.parquet y el pipeline cuadra EXACTO contra Fact.Sale del DW.
"""
import pymssql, duckdb, csv, os, json

PW = os.environ.get("MSSQL_SA_PASSWORD", "Taller2026!Claude")
os.makedirs("data", exist_ok=True)
ddb = duckdb.connect()

def conn(db):
    return pymssql.connect(server="127.0.0.1", port=1433, user="sa", password=PW, database=db)

def export(cur, name, sql):
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    tmp = f"data/_{name}.csv"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    ddb.execute(f"COPY (SELECT * FROM read_csv_auto('{tmp}', sample_size=-1)) TO 'data/{name}.parquet' (FORMAT PARQUET)")
    os.remove(tmp)
    print(f"  data/{name}.parquet  ({len(rows)} filas)")

c = conn("WideWorldImporters"); cur = c.cursor()
export(cur, "src_customers", """SELECT CustomerID, CustomerName, BillToCustomerID, CustomerCategoryID,
        BuyingGroupID, PrimaryContactPersonID, DeliveryPostalCode, AccountOpenedDate FROM Sales.Customers""")
export(cur, "src_customercategories", "SELECT CustomerCategoryID, CustomerCategoryName FROM Sales.CustomerCategories")
export(cur, "src_buyinggroups", "SELECT BuyingGroupID, BuyingGroupName FROM Sales.BuyingGroups")
export(cur, "src_people", "SELECT PersonID, FullName FROM Application.People")
export(cur, "src_stockitems", """SELECT StockItemID, StockItemName, SupplierID, ColorID, UnitPackageID,
        OuterPackageID, Brand, Size, LeadTimeDays, QuantityPerOuter, IsChillerStock, Barcode, TaxRate,
        UnitPrice, RecommendedRetailPrice, TypicalWeightPerUnit FROM Warehouse.StockItems""")
export(cur, "src_colors", "SELECT ColorID, ColorName FROM Warehouse.Colors")
export(cur, "src_packagetypes", "SELECT PackageTypeID, PackageTypeName FROM Warehouse.PackageTypes")
export(cur, "src_suppliers", """SELECT SupplierID, SupplierName, SupplierCategoryID, PrimaryContactPersonID,
        SupplierReference, PaymentDays, DeliveryPostalCode FROM Purchasing.Suppliers""")
export(cur, "src_suppliercategories", "SELECT SupplierCategoryID, SupplierCategoryName FROM Purchasing.SupplierCategories")
export(cur, "src_invoices", """SELECT InvoiceID, CustomerID, BillToCustomerID, SalespersonPersonID,
        InvoiceDate, LastEditedWhen, TotalDryItems, TotalChillerItems FROM Sales.Invoices""")
export(cur, "src_invoicelines", """SELECT InvoiceLineID, InvoiceID, StockItemID, Description, PackageTypeID,
        Quantity, UnitPrice, TaxRate, TaxAmount, LineProfit, ExtendedPrice, LastEditedWhen FROM Sales.InvoiceLines""")
c.close()

c = conn("WideWorldImportersDW"); cur = c.cursor()
def scalar(sql): cur.execute(sql); return cur.fetchone()[0]
verify = {
    "fact_sale_rows":       scalar("SELECT COUNT(*) FROM Fact.Sale"),
    "fact_sale_total_incl": float(scalar("SELECT SUM([Total Including Tax]) FROM Fact.Sale")),
    "fact_sale_total_excl": float(scalar("SELECT SUM([Total Excluding Tax]) FROM Fact.Sale")),
    "fact_sale_quantity":   int(scalar("SELECT SUM(Quantity) FROM Fact.Sale")),
    "fact_sale_profit":     float(scalar("SELECT SUM(Profit) FROM Fact.Sale")),
    "dim_customer_rows":    scalar("SELECT COUNT(*) FROM Dimension.Customer"),
    "dim_stockitem_rows":   scalar("SELECT COUNT(*) FROM Dimension.[Stock Item]"),
    "dim_supplier_rows":    scalar("SELECT COUNT(*) FROM Dimension.Supplier"),
}
c.close()
with open("data/_verify_dw.json", "w") as f:
    json.dump(verify, f, indent=2)
print("clave de respuestas -> data/_verify_dw.json:", verify)
