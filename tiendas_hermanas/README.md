# Tiendas hermanas

MVP privado para encontrar tiendas similares usando la hoja `JUN` de un archivo Excel. La aplicación filtra exclusivamente `ESTADO = ABIERTA`.

## Ejecutar localmente

```bash
cd /home/ubuntu/tiendas_hermanas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

La aplicación incluye el archivo local `data/Book.xlsx` como respaldo. También permite cargar otro Excel desde la interfaz.

## Flujo actual

- **Nuevo proyecto:** captura características conocidas y, opcionalmente, una venta proyectada de seis meses.
- **Tienda abierta existente:** usa una tienda ABIERTA como referencia y encuentra sus hermanas.
- **Mapa:** muestra el punto del nuevo proyecto como estrella naranja y las tiendas hermanas como puntos turquesa con etiquetas de nombre.
- **Ranking:** presenta porcentaje de similitud, variables usadas y explicación por variable.
- **Descarga:** permite exportar el ranking a CSV.

## Lógica actual

- Limpia campos monetarios que llegan como texto con `$` y separadores.
- Compara variables numéricas mediante distancia robusta usando el rango P10-P90.
- Compara variables categóricas por coincidencia exacta.
- La venta proyectada se compara contra `VU6M`.
- Ignora `CR`, `NAME`, `ARRENDADOR`, `ZONA`, `ESTADO`, `FECHA APE`, `DIA`, `DIAS OP`, `MESOP`, `ME` y `TE`.

## Privacidad

Usar repositorio privado y no publicar el Excel real. Para producción se recomienda mover los datos a una base de datos privada, agregar autenticación y auditar los pesos con el equipo de negocio.

## Próximos pasos

1. Validar con expertos si el ranking refleja una “tienda hermana”.
2. Ajustar pesos y decidir si la coordenada debe funcionar como filtro o como variable.
3. Separar perfil de apertura y desempeño actual para no mezclar tiendas maduras con tiendas nuevas.
4. Agregar autenticación y registro de consultas.
5. Calibrar un modelo predictivo de ventas o margen usando históricos cuando estén disponibles.
