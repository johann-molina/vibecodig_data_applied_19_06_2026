"""Dimension.[Stock Item] — equivalente moderno (DuckDB) de Integration.MigrateStagedStockItemData.
LINAJE (WWI real): Warehouse.StockItems + Warehouse.Colors + Warehouse.PackageTypes (x2: selling/buying).
REGLAS: lookups de color y de paquete (Selling = UnitPackage, Buying = OuterPackage); surrogate
[Stock Item Key]. El SP legacy hace SCD2; aquí estado actual. Ver legacy_sql/MigrateStagedStockItemData.sql.
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
