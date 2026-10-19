# Tiendas Hermanas

Aplicación Streamlit para encontrar tiendas comparables. La arquitectura usa dos fuentes relacionadas por `CR`:

- `data/Book.xlsx`: fuente maestra de tiendas y hoja principal `JUN`.
- `data/LibroVentas.xlsx`: fuente complementaria de desempeño e históricos. La app usa `BD U6M`, `BD UM`, `HISTORICO VENTAS` y `HISTORICO CON`. No usa `INFO TIENDAS`.

## Ejecutar

```bash
cd tiendas_hermanas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Funciones incorporadas

- Ranking de tiendas hermanas usando el catálogo de `Book.xlsx`.
- Cruce de desempeño de `LibroVentas.xlsx` mediante `CR`.
- Lectura de ventas, ticket, tráfico, contribución, margen, renta y batting de U6M y UM.
- Lectura de históricos mensuales de ventas y contribución.
- Indicador de cobertura de datos del ranking.
- Pestaña de desempeño para las tiendas recomendadas.
- Serie mensual promedio de ventas de las tiendas hermanas.
- Carga opcional de un `Book.xlsx` y un `LibroVentas.xlsx` actualizados desde la interfaz.
- Descarga del ranking a CSV.
- Mapa y explicación de variables.

## Recomendación de operación

Mantener los libros reales en OneDrive/SharePoint privado y el código en un repositorio privado de GitHub. Esta versión incluye copias locales como respaldo para ejecución, pero no implementa todavía la descarga autenticada desde OneDrive. Antes de producción se deben agregar autenticación, auditoría, control de fecha de corte y validación automática del esquema.
