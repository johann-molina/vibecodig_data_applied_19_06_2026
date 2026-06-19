"""fact_sale — TODO (Paso 4 del README).

  SP legacy : legacy_sql/MigrateStagedSaleData.sql   (resolución de surrogate keys + medidas)
  Linaje    : Sales.Invoices + Sales.InvoiceLines  ->  Fact.Sale   (grano = línea de factura)
  Medidas   : Total Including Tax = ExtendedPrice · Total Excluding Tax = ExtendedPrice - TaxAmount · Profit = LineProfit
  Depende de: dim_customer y dim_stockitem (run_pipeline las corre primero)
  Debe      : leer data/src_*.parquet (+ dims en modern/output/)  y  escribir modern/output/fact_sale.parquet

  ¿Atascado? -> resultado-final/modern/fact_sale.py
"""

def build():
    raise NotImplementedError(
        "Falta construir fact_sale (Paso 4). Lee legacy_sql/MigrateStagedSaleData.sql. "
        "¿Atascado? -> resultado-final/modern/fact_sale.py"
    )

if __name__ == "__main__":
    build()
