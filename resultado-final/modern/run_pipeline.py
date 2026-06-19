"""Orquesta el pipeline moderno: dimensiones primero, hecho después (igual que el ETL legacy).
Correr desde la raíz del repo:  uv run python modern/run_pipeline.py   (o python3)
"""
import os
import dim_customer, dim_stockitem, dim_supplier, fact_sale

os.makedirs("modern/output", exist_ok=True)

print("== Pipeline moderno (DuckDB) ==")
dim_customer.build()
dim_stockitem.build()
dim_supplier.build()
fact_sale.build()      # depende de las dimensiones
print("OK -> modern/output/*.parquet")
