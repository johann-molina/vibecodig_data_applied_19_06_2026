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
