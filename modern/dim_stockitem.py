"""dim_stockitem — TODO (Paso 4 del README).

  SP legacy : legacy_sql/MigrateStagedStockItemData.sql
  Linaje    : Warehouse.StockItems + Colors + PackageTypes (x2: Selling/Buying) -> Dimension.[Stock Item]
  Debe      : leer data/src_*.parquet  y  escribir modern/output/dim_stockitem.parquet

  ¿Atascado? -> resultado-final/modern/dim_stockitem.py
"""

def build():
    raise NotImplementedError(
        "Falta construir dim_stockitem (Paso 4). Lee legacy_sql/MigrateStagedStockItemData.sql. "
        "¿Atascado? -> resultado-final/modern/dim_stockitem.py"
    )

if __name__ == "__main__":
    build()
