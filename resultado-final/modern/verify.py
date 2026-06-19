"""Verificación: salida del pipeline moderno (DuckDB)  vs  el DW legacy real (clave de respuestas).
Lee data/_verify_dw.json (cifras reales de WideWorldImportersDW capturadas por MCP/export).
Las MEDIDAS del hecho deben cuadrar EXACTO; las dimensiones se comparan en forma (estado actual).
Correr desde la raíz del repo:  python3 modern/verify.py
"""
import duckdb, json, os

con = duckdb.connect()
dw = json.load(open("data/_verify_dw.json"))

def m(sql):
    return con.execute(sql).fetchone()[0]

checks = []
def check(nombre, modern, legacy, exact=True, tol=0.01):
    if isinstance(legacy, float) or isinstance(modern, float):
        ok = abs(float(modern) - float(legacy)) <= tol if exact else True
    else:
        ok = (modern == legacy) if exact else True
    checks.append((nombre, modern, legacy, ok, exact))

F = "'modern/output/fact_sale.parquet'"
check("Fact.Sale · filas",            m(f"SELECT count(*) FROM {F}"),                         dw["fact_sale_rows"])
check("Fact.Sale · Total c/IGV",      round(m(f"SELECT sum(Total_Including_Tax) FROM {F}"),2), round(dw["fact_sale_total_incl"],2))
check("Fact.Sale · Total s/IGV",      round(m(f"SELECT sum(Total_Excluding_Tax) FROM {F}"),2), round(dw["fact_sale_total_excl"],2))
check("Fact.Sale · Cantidad",         m(f"SELECT sum(Quantity) FROM {F}"),                    dw["fact_sale_quantity"])
check("Fact.Sale · Profit",           round(m(f"SELECT sum(Profit) FROM {F}"),2),             round(dw["fact_sale_profit"],2))
# dimensiones: estado actual vs histórico SCD2 del DW -> se reporta, no se exige igualdad
check("Dimension.Customer · filas (forma)",  m("SELECT count(*) FROM 'modern/output/dim_customer.parquet'"),  dw["dim_customer_rows"], exact=False)
check("Dimension.StockItem · filas (forma)", m("SELECT count(*) FROM 'modern/output/dim_stockitem.parquet'"), dw["dim_stockitem_rows"], exact=False)
check("Dimension.Supplier · filas (forma)",  m("SELECT count(*) FROM 'modern/output/dim_supplier.parquet'"),  dw["dim_supplier_rows"], exact=False)

w = max(len(c[0]) for c in checks)
print(f"\n{'VERIFICACIÓN: moderno (DuckDB)  vs  DW legacy real'}")
print("-" * (w + 46))
allok = True
for nombre, modern, legacy, ok, exact in checks:
    mark = "✅" if ok else ("•" if not exact else "❌")
    if not exact and not ok:
        mark = "•"
    if exact and not ok:
        allok = False
    mod_s = f"{modern:,}" if isinstance(modern, int) else f"{modern:,.2f}"
    leg_s = f"{legacy:,}" if isinstance(legacy, int) else f"{legacy:,.2f}"
    rel = "==" if exact else "~"
    print(f"{mark} {nombre:<{w}}  moderno={mod_s:>18}  {rel} legacy={leg_s:>18}")
print("-" * (w + 46))
print("RESULTADO: " + ("✅ TODAS las medidas exactas cuadran con el DW real"
                       if allok else "❌ hay diferencias en medidas exactas — revisar"))
print("(• = dimensión en estado-actual vs histórico SCD2 del DW: se compara forma, no igualdad)")
