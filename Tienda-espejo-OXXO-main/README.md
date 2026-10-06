# 🏪 Tienda Espejo Inteligente — Inteligencia de Expansión

Herramienta de Inteligencia de Expansión para encontrar tiendas operativas similares a una nueva propuesta usando una red neuronal auto-supervisada.

## 🆕 Capacidades de la solución neuronal

✅ **Red neuronal auto-supervisada** - Autoencoder denoising con embedding latente  
✅ **Nuevas variables** - Viviendas Totales y Empleos Totales  
✅ **Prevención de sobreajuste** - Regularización L2, ruido controlado y parada temprana  
✅ **Estadísticas descriptivas** - Promedios y desviaciones del Top 10  
✅ **Visualizaciones mejoradas** - Nueva pestaña con análisis del modelo  
✅ **Mayor precisión** - Considera todas las dimensiones simultáneamente  
✅ **Red neuronal auto-supervisada** - Autoencoder denoising con L2 y parada temprana  
✅ **Base oficial** - `TiendaEspejo.xlsx`, hoja `DATA`, con compatibilidad para `VU6M`/`TRU6`  

---

## 📋 Requisitos

### Python y Librerías

```bash
pip install streamlit pandas numpy scikit-learn plotly openpyxl
```

**Versiones recomendadas:**
- Python 3.8+
- streamlit >= 1.28.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- scikit-learn >= 1.3.0
- plotly >= 5.14.0
- openpyxl >= 3.1.0

---

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación

```bash
streamlit run app_mejorado.py
```

### 3. Abrir en el navegador

La aplicación se abrirá automáticamente en:
```
http://localhost:8501
```

---

## 📊 Formato del Archivo de Datos

Tu archivo Excel debe contener las siguientes columnas:

### Columnas Obligatorias

| Columna | Tipo | Descripción |
|---------|------|-------------|
| CR | Texto | Código de tienda |
| NAME | Texto | Nombre de la tienda |
| SEG26 | Texto | Segmento comercial |
| ZONA | Texto | Zona geográfica |
| MUN | Texto | Municipio |
| ESTRATO | Numérico | Estrato socioeconómico (1-6) |
| TIPO DE LOCAL | Texto | Tipo de establecimiento |
| AREA | Numérico | Área en m² |
| GENERADOR | Texto | Tipo de generador |
| VT | Numérico | Ventas totales |
| ET | Numérico | Entradas totales (tráfico) |
| RENTA | Numérico | Renta mensual |

### Columnas Nuevas (Recomendadas)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| VIVIENDAS | Numérico | Viviendas en área de influencia |
| EMPLEOS | Numérico | Empleos en área de influencia |

> **Nota:** Si tu archivo no tiene las columnas VIVIENDAS y EMPLEOS, deberás ingresarlas manualmente en el formulario. Se recomienda agregarlas al archivo para mejor precisión.

### Nombres Alternativos Aceptados

- `VIVIENDAS_TOTALES` → se renombra a `VIVIENDAS`
- `EMPLEOS_TOTALES` → se renombra a `EMPLEOS`

---

## 📖 Cómo Usar la Aplicación

### Paso 1: Cargar Datos
1. En la barra lateral, marca "Usar datos precargados" o
2. Sube tu archivo Excel usando el botón de carga

### Paso 2: Configurar Pesos
1. Ajusta los sliders en la barra lateral según la importancia de cada característica
2. Los pesos se normalizan automáticamente para sumar 100%
3. El segmento tiene un peso fijo del 30%

### Paso 3: Ingresar Datos de la Nueva Tienda
Completa el formulario con:
- **Características principales**: Segmento, Zona, Municipio, Estrato, Tipo de Local, Generador
- **Métricas numéricas**: 
  - Área (m²)
  - **Viviendas Totales** (nueva variable)
  - **Empleos Totales** (nueva variable)

### Paso 4: Buscar Tienda Espejo
1. Haz clic en "🔍 Buscar Tienda Espejo"
2. Revisa los resultados en las diferentes pestañas
3. Descarga el Top 20 en formato CSV si lo necesitas

---

## 📊 Interpretación de Resultados

### Score de Similitud

| Rango | Interpretación | Uso Recomendado |
|-------|----------------|-----------------|
| 90-100% | Coincidencia casi perfecta | Proyección directa de VT/ET |
| 80-89% | Muy similar | Excelente referencia |
| 70-79% | Buena similitud | Referencia con ajustes menores |
| 60-69% | Similitud moderada | Usar con precaución |
| <60% | Baja similitud | Considerar múltiples referencias |

### Estadísticas del Top 10

- **VT Promedio ± Desviación**: Rango esperado de ventas
- **ET Promedio ± Desviación**: Rango esperado de tráfico
- **Renta Promedio ± Desviación**: Rango esperado de renta
- **Similitud Promedio**: Qué tan homogéneo es el grupo de tiendas espejo

---

## 🎨 Visualizaciones Disponibles

### Pestaña 1: Comparación de Métricas
- Gráfico de barras VT vs ET (Top 5)
- Scatter plot Renta vs Área
- **Nuevo**: Scatter plot Viviendas vs Empleos

### Pestaña 2: Distribución Geográfica
- Gráfico de torta por Zona
- Gráfico de barras por Estrato

### Pestaña 3: Análisis de Similitud
- Gráfico de barras de similitud (Top 10)
- Tabla comparativa de características

### Pestaña 4: Modelo Estadístico (Nueva)
- Explicación de la metodología
- Distribución de distancias euclidianas
- Relación Distancia vs Similitud

---

## ⚙️ Configuración Avanzada

### Ajuste de Pesos por Tipo de Negocio

**Retail de Proximidad:**
```
Viviendas: 15%
Zona: 15%
Estrato: 12%
Empleos: 5%
```

**Retail de Destino:**
```
Empleos: 15%
Generador: 12%
Zona: 10%
Viviendas: 5%
```

**Ubicaciones Premium:**
```
Estrato: 15%
Zona: 15%
Tipo de Local: 10%
Área: 12%
```

---

## 🔬 Modelo Estadístico

### Algoritmo
1. Filtrado por segmento SEG26
2. Normalización con StandardScaler (Z-score)
3. Codificación binaria de categóricas
4. Aplicación de pesos configurables
5. Cálculo de distancia euclidiana ponderada
6. Inversión y normalización a score 0-100%

### Ventajas
✅ Robusto estadísticamente  
✅ Evita sesgos por escalas  
✅ Multidimensional  
✅ Configurable  
✅ Interpretable  
✅ Reproducible  

Ver `DOCUMENTACION_MODELO.md` para detalles técnicos completos.

---

## 📁 Estructura de Archivos

```
.
├── app_mejorado.py              # Aplicación principal
├── DOCUMENTACION_MODELO.md      # Documentación técnica del modelo
├── README.md                    # Este archivo
├── requirements.txt             # Dependencias
└── data/
    └── TiendaEspejo.xlsx       # Base oficial, hoja DATA
```

---

## 🐛 Solución de Problemas

### Error: "No se encontró columna VIVIENDAS"
**Solución**: Agrega columnas VIVIENDAS y EMPLEOS a tu Excel, o ingrésalas manualmente.

### Error: "No se encontraron tiendas en el mismo segmento"
**Solución**: Verifica que existan tiendas del segmento seleccionado en tu dataset.

### Similitudes muy bajas (<60%)
**Solución**: 
- Ajusta los pesos priorizando características más importantes
- Verifica que la propuesta sea realista vs el dataset
- Considera expandir el dataset con más tiendas

### Los pesos no suman exactamente 100%
**Solución**: Esto es normal, los pesos se normalizan automáticamente al 70% (el 30% restante es del segmento).

---

## 📞 Soporte

Para problemas técnicos o preguntas:
1. Revisa la documentación en `DOCUMENTACION_MODELO.md`
2. Verifica que tu archivo Excel tenga el formato correcto
3. Asegúrate de tener las versiones correctas de las librerías

---

## 📝 Changelog

### v2.0 (Actual)
- ✅ Implementación de modelo estadístico robusto
- ✅ Integración de variables VIVIENDAS y EMPLEOS
- ✅ Normalización con StandardScaler
- ✅ Estadísticas descriptivas del Top 10
- ✅ Nueva pestaña de análisis del modelo
- ✅ Visualizaciones mejoradas
- ✅ Documentación técnica completa

### v1.0
- Modelo básico con pesos simples
- Filtrado por segmento
- Visualizaciones básicas

---

## 📄 Licencia

Proyecto de uso interno para análisis de ubicaciones comerciales.

---

**Desarrollado con ❤️ usando Streamlit**
