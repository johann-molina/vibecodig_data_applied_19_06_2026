"""Fact.Sale — equivalente moderno (DuckDB) de Integration.MigrateStagedSaleData.
LINAJE (WWI real): Sales.Invoices + Sales.InvoiceLines -> Fact.Sale. Grano = línea de factura.
REGLA CLAVE: resolución de SURROGATE KEYS hacia las dimensiones (se guardan los *_Key, no los
IDs de negocio). El SP legacy resuelve point-in-time contra las versiones SCD2; como aquí las
dimensiones son estado-actual, el lookup es por business id (equivalente cuando no hay histórico).
Ver legacy_sql/MigrateStagedSaleData.sql.

MEDIDAS (deben cuadrar EXACTO con Fact.Sale del DW):
  Total Excluding Tax = ExtendedPrice - TaxAmount · Total Including Tax = ExtendedPrice · Profit = LineProfit
Depende de dim_customer y dim_stockitem (run_pipeline garantiza el orden).
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
