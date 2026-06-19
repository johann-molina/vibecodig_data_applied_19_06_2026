"""Genera dashboard.html desde el star schema en modern/output/.
100% autocontenido: CSS inline, SIN JavaScript, SIN CDN -> no puede fallar al renderizar en vivo.
Correr desde la raíz del repo:  python3 modern/build_dashboard.py
"""
import duckdb, html, os

con = duckdb.connect()

def q(sql):
    return con.execute(sql).fetchall()

# ---- KPIs ----
kpi = q("""
    SELECT round(sum(Total_Including_Tax),0)        AS ingresos,
           count(*)                                  AS lineas,
           count(DISTINCT Customer_Key)              AS clientes,
           round(avg(Total_Including_Tax),2)         AS ticket
    FROM 'modern/output/fact_sale.parquet'
""")[0]

by_cat = q("""
    SELECT coalesce(dc.Category,'(sin categoría)') AS k, round(sum(f.Total_Including_Tax),0) AS v
    FROM 'modern/output/fact_sale.parquet' f
    JOIN 'modern/output/dim_customer.parquet' dc USING (Customer_Key)
    GROUP BY 1 ORDER BY 2 DESC
""")

by_month = q("""
    SELECT strftime(Invoice_Date,'%Y-%m') AS k, round(sum(Total_Including_Tax),0) AS v
    FROM 'modern/output/fact_sale.parquet'
    GROUP BY 1 ORDER BY 1
""")

top_items = q("""
    SELECT ds.Stock_Item AS k, round(sum(f.Total_Including_Tax),0) AS v
    FROM 'modern/output/fact_sale.parquet' f
    JOIN 'modern/output/dim_stockitem.parquet' ds USING (Stock_Item_Key)
    GROUP BY 1 ORDER BY 2 DESC LIMIT 6
""")

def bars(rows, accent):
    mx = max((r[1] for r in rows), default=1) or 1
    out = []
    for k, v in rows:
        pct = max(2, round(100 * v / mx))
        out.append(
            f'<div class="row"><div class="lbl">{html.escape(str(k))}</div>'
            f'<div class="track"><div class="bar" style="width:{pct}%;background:{accent}"></div></div>'
            f'<div class="val">S/ {v:,.0f}</div></div>'
        )
    return "\n".join(out)

def kpi_card(label, value):
    return f'<div class="card"><div class="k">{value}</div><div class="t">{label}</div></div>'

HTML = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WideWorldImporters DW — Ventas</title>
<style>
  :root {{ --bg:#0f172a; --panel:#1e293b; --ink:#e2e8f0; --muted:#94a3b8; --line:#334155; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
          background:var(--bg); color:var(--ink); padding:28px; }}
  h1 {{ font-size:22px; margin:0 0 2px; }}
  .sub {{ color:var(--muted); font-size:13px; margin-bottom:22px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }}
  .card .k {{ font-size:26px; font-weight:700; }}
  .card .t {{ color:var(--muted); font-size:12px; margin-top:4px; text-transform:uppercase; letter-spacing:.04em; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
  .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px 20px; }}
  .panel.wide {{ grid-column:1 / -1; }}
  .panel h2 {{ font-size:14px; margin:0 0 14px; color:var(--ink); font-weight:600; }}
  .row {{ display:flex; align-items:center; gap:10px; margin:7px 0; font-size:13px; }}
  .lbl {{ width:140px; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .track {{ flex:1; background:#0b1220; border-radius:6px; overflow:hidden; height:18px; }}
  .bar {{ height:100%; border-radius:6px; }}
  .val {{ width:96px; text-align:right; font-variant-numeric:tabular-nums; }}
  footer {{ color:var(--muted); font-size:11px; margin-top:22px; }}
</style></head>
<body>
  <h1>WideWorldImporters DW — Ventas</h1>
  <div class="sub">Generado por el pipeline moderno (DuckDB) · ingeniería inversa del ETL legacy · datos de demostración</div>

  <div class="kpis">
    {kpi_card("Ingresos (con IGV)", f"S/ {kpi[0]:,.0f}")}
    {kpi_card("Líneas de venta", f"{kpi[1]:,}")}
    {kpi_card("Clientes", f"{kpi[2]:,}")}
    {kpi_card("Ticket promedio", f"S/ {kpi[3]:,.2f}")}
  </div>

  <div class="grid">
    <div class="panel"><h2>Ingresos por categoría de cliente</h2>{bars(by_cat, "#38bdf8")}</div>
    <div class="panel"><h2>Top productos por ingreso</h2>{bars(top_items, "#a78bfa")}</div>
    <div class="panel wide"><h2>Ingresos por mes</h2>{bars(by_month, "#34d399")}</div>
  </div>

  <footer>Star schema: Fact.Sale × Dimension.Customer / StockItem / Supplier — Taller Claude Code, Sesión 3.</footer>
</body></html>
"""

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(HTML)
# copia de referencia (versionada) como respaldo
os.makedirs("reference", exist_ok=True)
with open("reference/dashboard_reference.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"dashboard.html generado · ingresos S/ {kpi[0]:,.0f} · {kpi[1]} líneas · {len(by_month)} meses")
