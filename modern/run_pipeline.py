"""Orquesta el pipeline moderno: dimensiones primero, hecho después (igual que el ETL legacy).
Correr desde la raíz del repo:  python modern/run_pipeline.py   (o: uv run python modern/run_pipeline.py)
"""
import os
import dim_customer, dim_stockitem, dim_supplier, fact_sale

os.makedirs("modern/output", exist_ok=True)

print("== Pipeline moderno (DuckDB) ==")
for nombre, modulo in [("dim_customer", dim_customer), ("dim_stockitem", dim_stockitem),
                       ("dim_supplier", dim_supplier), ("fact_sale", fact_sale)]:
    try:
        modulo.build()
    except NotImplementedError as e:
        print(f"\n⏳ Aún falta construir: modern/{nombre}.py")
        print(f"   → {e}")
        print("   (Es el Paso 4 del README. Cuando lo tengas, vuelve a correr este comando.)")
        raise SystemExit(1)
print("OK -> modern/output/*.parquet")
