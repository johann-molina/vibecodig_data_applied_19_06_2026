"""Dimension.Customer — equivalente moderno (DuckDB) de Integration.MigrateStagedCustomerData.
LINAJE (WWI real): Sales.Customers + Sales.CustomerCategories + Sales.BuyingGroups
                   + Application.People (Primary Contact) + self-join (Bill To Customer).
REGLAS: surrogate [Customer Key] vs business [WWI Customer ID]; el SP legacy hace SCD Type 2
("cierra la fila vigente, inserta la nueva" — ver legacy_sql/MigrateStagedCustomerData.sql).
Aquí construimos el estado ACTUAL desde el OLTP (Valid To = fin de los tiempos): el OLTP no
guarda el histórico de versiones (lo acumula el ETL diario), así que reproducimos la FORMA y la
LÓGICA, no el histórico exacto del DW. Las MEDIDAS del hecho sí se verifican exactas.
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
