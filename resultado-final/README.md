# resultado-final — La solución completa (clave de respuestas)

Esta carpeta es el repo **ya resuelto**: los 4 `modern/*.py` construidos, el pipeline corriendo y
el dashboard generado. Úsala como referencia si te atascas en el `README.md` principal (el del repo).

## Para correrla tal cual
```bash
cd resultado-final
pip install duckdb                  # única dependencia
python modern/run_pipeline.py       # construye modern/output/*.parquet
python modern/verify.py             # ✅ cuadra EXACTO con el DW real
python modern/build_dashboard.py    # genera dashboard.html
```

## Resultado verificado (datos reales de WWI)
`Fact.Sale` = **228,265 filas** · Total con IGV = **S/ 198,043,439.45** · al céntimo · 0 keys sin resolver.

## ¿Cómo usarla si te atascas?
Copia el archivo que necesites a tu carpeta de trabajo, p. ej.:
```bash
cp resultado-final/modern/dim_customer.py modern/dim_customer.py
```
y sigue con el siguiente paso del `README.md` principal.
