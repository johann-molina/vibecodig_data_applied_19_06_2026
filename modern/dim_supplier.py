"""dim_supplier — TODO (Paso 4 del README).

  SP legacy : legacy_sql/MigrateStagedSupplierData.sql
  Linaje    : Purchasing.Suppliers + SupplierCategories + People (contacto) -> Dimension.Supplier
  Debe      : leer data/src_*.parquet  y  escribir modern/output/dim_supplier.parquet

  ¿Atascado? -> resultado-final/modern/dim_supplier.py
"""

def build():
    raise NotImplementedError(
        "Falta construir dim_supplier (Paso 4). Lee legacy_sql/MigrateStagedSupplierData.sql. "
        "¿Atascado? -> resultado-final/modern/dim_supplier.py"
    )

if __name__ == "__main__":
    build()
