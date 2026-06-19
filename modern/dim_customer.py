"""dim_customer — TODO (Paso 4 del README).

Modernizar el stored procedure legacy a Python + DuckDB.
  SP legacy : legacy_sql/MigrateStagedCustomerData.sql   (léelo: es la lógica SCD Type 2)
  Linaje    : Sales.Customers + CustomerCategories + BuyingGroups + People (contacto)
              + self-join a Customers (bill-to)  ->  Dimension.Customer
  Debe      : leer data/src_*.parquet  y  escribir modern/output/dim_customer.parquet

Cómo construirlo:
  - En vivo: /modernize-sp customer
  - O a mano (DuckDB puro, sin pandas).
  - ¿Atascado? copia la solución: resultado-final/modern/dim_customer.py
"""

def build():
    raise NotImplementedError(
        "Falta construir dim_customer (Paso 4 del README). "
        "Lee legacy_sql/MigrateStagedCustomerData.sql. "
        "¿Atascado? -> resultado-final/modern/dim_customer.py"
    )

if __name__ == "__main__":
    build()
