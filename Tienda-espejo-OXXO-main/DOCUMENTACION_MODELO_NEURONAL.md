# Modelo neuronal de similitud — Tienda Espejo

## Por qué no es una red supervisada tradicional

La base contiene tiendas operativas, pero no contiene una etiqueta de pares como `tienda A es similar a tienda B`. Entrenar una red supervisada sin esa etiqueta obligaría a inventar objetivos y produciría una precisión falsa. La implementación usa aprendizaje **auto-supervisado**: cada tienda sirve como su propio objetivo de reconstrucción.

## Arquitectura

1. Se filtra por `SEG26`, de modo que las comparaciones se hagan dentro del mismo segmento.
2. Las variables numéricas se estandarizan con `StandardScaler`.
3. Las variables categóricas se convierten con `OneHotEncoder(handle_unknown="ignore")`.
4. Se aplican los pesos de negocio por bloque de variable.
5. Se agrega ruido gaussiano pequeño a la entrada y la red reconstruye la representación limpia: es un **denoising autoencoder**.
6. La capa oculta es el embedding latente de 3–12 dimensiones.
7. La distancia se mide entre el embedding de la propuesta y el embedding de cada tienda.
8. El score usa `100 * exp(-distancia / escala_robusta)`, donde la escala es el percentil 75 de las distancias. Esto evita que el 0% y 100% dependan únicamente de los extremos de cada consulta.

## Controles contra sobreajuste

- Penalización L2 (`alpha=0.02`).
- Parada temprana con 20% de validación cuando hay al menos 30 candidatos.
- Ruido denoising determinista (`seed=42`, desviación `0.025`).
- Una sola capa latente pequeña, limitada a 12 dimensiones.
- `OneHotEncoder` ignora categorías nuevas en vez de fallar.
- Si hay pocas tiendas, se entrena sin separar una validación inútil y la interfaz debe interpretarse con mayor cautela.

## Interpretación correcta

El score es un **ranking de similitud**, no una probabilidad ni una garantía de ventas. Para proyectar VT/ET, se recomienda revisar el Top 5/10, la dispersión de sus resultados y la explicación de diferencias. Las etiquetas futuras de pares similares, si llegan a estar disponibles, permitirían evolucionar a una red Siamese supervisada y evaluar Recall@K/NDCG con validación por tienda.

## Variables

- Numéricas: `ESTRATO`, `AREA`, `VIVIENDAS`, `EMPLEOS`, `VENTAS_OU6M`, `TRAFICO_U6M`.
- Categóricas: `ZONA`, `TIPO DE LOCAL`, `GENERADOR`, `MUN`.
- `SEG26` se usa como filtro de comparabilidad.

## Excel admitido

La app carga `TiendaEspejo.xlsx` desde la hoja `DATA` como base integrada del repositorio. No solicita cargar otro archivo desde la interfaz. Unifica automáticamente:

- `VU6M` → `VENTAS_OU6M`
- `TRU6` → `TRAFICO_U6M`
