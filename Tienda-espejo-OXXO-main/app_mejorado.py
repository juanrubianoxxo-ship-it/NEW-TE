import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances
from scipy.spatial.distance import cdist
import io
import plotly.express as px
import plotly.graph_objects as go
import os
from modelo_neuronal import calcular_tienda_espejo_neuronal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_BASE = os.path.join(BASE_DIR, 'TiendaEspejo.xlsx')

# Configuración de la página
if os.path.exists('favicon.png'):
    page_icon_config = "favicon.png"
elif os.path.exists('logo_oxxo.png'):
    page_icon_config = "logo_oxxo.png"
else:
    page_icon_config = "🏪"

st.set_page_config(
    page_title="Modelo de Tienda Espejo OXXO",
    page_icon=page_icon_config,
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado con identidad visual OXXO
st.markdown("""
<style>
:root { --oxxo-red:#ED1C24; --oxxo-red-dark:#B5121B; --oxxo-yellow:#FFD100; --oxxo-dark:#171717; }
.stApp { background:linear-gradient(180deg,#fffdf5 0%,#fff 45%,#fff8e5 100%); }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.2rem; max-width:1440px; }
.main-header { position:relative; overflow:hidden; background:linear-gradient(118deg,#B5121B 0%,#ED1C24 54%,#F52D31 100%); padding:2.15rem 2.5rem 2rem; border-radius:22px; margin-bottom:1.5rem; box-shadow:0 14px 30px rgba(181,18,27,.24); border-bottom:10px solid var(--oxxo-yellow); }
.main-header:before { content:""; position:absolute; width:290px; height:290px; right:-100px; top:-140px; border:28px solid rgba(255,209,0,.28); border-radius:50%; }
.main-header:after { content:""; position:absolute; width:160px; height:160px; right:105px; bottom:-108px; border:18px solid rgba(255,255,255,.12); border-radius:50%; }
.brand-kicker { color:var(--oxxo-yellow); font-size:.78rem; font-weight:800; letter-spacing:.18em; text-transform:uppercase; margin-bottom:.35rem; }
.main-header h1 { position:relative; z-index:1; color:white; font-size:2.65rem; line-height:1.05; font-weight:900; margin:0; text-shadow:2px 3px 0 rgba(0,0,0,.12); }
.main-header p { position:relative; z-index:1; color:white; font-size:1.08rem; margin:.7rem 0 0; max-width:720px; }
.logo-wrap { background:#fff; border:8px solid var(--oxxo-yellow); border-radius:18px; padding:.45rem; box-shadow:0 10px 22px rgba(0,0,0,.14); }
.stButton>button,.stFormSubmitButton>button { background:linear-gradient(135deg,#ED1C24,#B5121B); color:white; border:0; border-radius:12px; padding:.72rem 1.5rem; font-weight:900; box-shadow:0 6px 0 #8f1017,0 10px 20px rgba(237,28,36,.22); transition:all .2s; }
.stButton>button:hover,.stFormSubmitButton>button:hover { background:linear-gradient(135deg,#ff3038,#ED1C24); transform:translateY(-2px); box-shadow:0 8px 0 #8f1017,0 14px 24px rgba(237,28,36,.25); }
[data-testid="stMetric"] { background:#fff; border:1px solid #f0dfb0; border-top:6px solid var(--oxxo-red); border-radius:14px; padding:.7rem .9rem; box-shadow:0 5px 15px rgba(80,40,0,.08); }
[data-testid="stMetricValue"] { color:var(--oxxo-red-dark); font-weight:900; }
[data-testid="stMetricLabel"] { color:#6b5540; font-weight:700; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#171717 0%,#252525 72%,#3b1115 100%) !important; border-right:5px solid var(--oxxo-yellow); }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:var(--oxxo-yellow); font-weight:900; }
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span { color:#fff !important; }
[data-testid="stSidebar"] .stCheckbox label,[data-testid="stSidebar"] .stSlider label,[data-testid="stSidebar"] .stFileUploader label { color:#fff !important; }
[data-testid="stSidebar"] .streamlit-expanderHeader { background:#2a2a2a; color:var(--oxxo-yellow) !important; }
.stTabs [data-baseweb="tab-list"] { background:#fff4c8; border-radius:14px; padding:5px; gap:5px; }
.stTabs [data-baseweb="tab"] { background:transparent; border-radius:10px; padding:10px 16px; color:#6c4b38; font-weight:800; }
.stTabs [aria-selected="true"] { background:var(--oxxo-red); color:white; }
.streamlit-expanderHeader { background:#fff4c8; border-radius:12px; color:var(--oxxo-red-dark); font-weight:800; }
.dataframe { border:2px solid var(--oxxo-red) !important; border-radius:10px; }
.stSuccess { background:#fff4c8; color:#4b2c1b; border-left:7px solid var(--oxxo-red); border-radius:10px; }
hr { border-color:var(--oxxo-yellow); border-width:3px; }
[data-testid="stSidebar"] hr { border-color:var(--oxxo-red); border-width:2px; }
.metric-card { background:white; padding:1rem; border-radius:14px; border-left:7px solid var(--oxxo-red); box-shadow:0 6px 18px rgba(0,0,0,.08); margin:.5rem 0; }
.stDownloadButton>button { background:var(--oxxo-yellow); color:#171717; border:0; border-radius:10px; font-weight:900; box-shadow:0 4px 0 #c79f00; }
.stDownloadButton>button:hover { background:#ffe263; }
div[data-baseweb="input"],div[data-baseweb="select"] { border-radius:10px; }
div[data-testid="stForm"] { background:#fff; border:1px solid #f0dfb0; border-top:8px solid var(--oxxo-yellow); border-radius:16px; padding:1.1rem; box-shadow:0 8px 22px rgba(80,40,0,.07); }
[data-testid="stSidebar"] .stMarkdown { color:#fff; }
[data-testid="stSidebar"] .stCaption { color:#ccc !important; }
</style>
""", unsafe_allow_html=True)

# Header
col_logo, col_title = st.columns([1.05, 4], vertical_alignment="center")
with col_logo:
    logo_path = os.path.join(BASE_DIR, "logo_oxxo.png")
    if os.path.exists(logo_path):
        st.markdown("<div class='logo-wrap'>", unsafe_allow_html=True)
        st.image(logo_path, width=165)
        st.markdown("</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("""
        <div class='main-header'>
            <div class='brand-kicker'>Planeación comercial · OXXO Colombia</div>
            <h1>Modelo de Tienda Espejo</h1>
            <p>Encuentra la tienda operativa más similar y convierte datos en decisiones de ubicación.</p>
            <span class='hero-pill'>● Similitud inteligente con red neuronal</span>
        </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# MODELO ESTADÍSTICO
# Columnas reales del Excel: VENTAS_OU6M (ventas últimos 6 meses), TRAFICO_U6M (tráfico últimos 6 meses)
# ──────────────────────────────────────────────
def calcular_tienda_espejo_estadistico(df, nueva_tienda, pesos=None):
    """
    Distancia euclidiana ponderada normalizada.
    Variables numéricas: ESTRATO, AREA, VIVIENDAS, EMPLEOS, VENTAS_OU6M, TRAFICO_U6M
    Variables categóricas: ZONA, TIPO DE LOCAL, GENERADOR, MUN
    """
    if pesos is None:
        pesos = {
            'SEG26': 0.30,
            'ZONA': 0.10,
            'ESTRATO': 0.08,
            'TIPO DE LOCAL': 0.07,
            'AREA': 0.08,
            'GENERADOR': 0.07,
            'MUN': 0.06,
            'VIVIENDAS': 0.06,
            'EMPLEOS': 0.06,
            'VENTAS_OU6M': 0.12,
            'TRAFICO_U6M': 0.10
        }

    df_filtrado = df[df['SEG26'] == nueva_tienda['SEG26']].copy()

    if len(df_filtrado) == 0:
        return None, "No se encontraron tiendas en el mismo segmento"

    # ── Variables numéricas ──
    vars_numericas = ['ESTRATO', 'AREA', 'VIVIENDAS', 'EMPLEOS', 'VENTAS_OU6M', 'TRAFICO_U6M']

    for v in vars_numericas:
        if v not in df_filtrado.columns:
            df_filtrado[v] = 0

    X_num_df = df_filtrado[vars_numericas].fillna(0)
    X_num_nueva = np.array([[
        nueva_tienda['ESTRATO'],
        nueva_tienda['AREA'],
        nueva_tienda['VIVIENDAS'],
        nueva_tienda['EMPLEOS'],
        nueva_tienda['VENTAS_OU6M'],
        nueva_tienda['TRAFICO_U6M']
    ]])

    scaler = StandardScaler()
    X_num_df_scaled = scaler.fit_transform(X_num_df)
    X_num_nueva_scaled = scaler.transform(X_num_nueva)

    # ── Variables categóricas ──
    vars_categoricas = ['ZONA', 'TIPO DE LOCAL', 'GENERADOR', 'MUN']
    X_cat_df = np.zeros((len(df_filtrado), len(vars_categoricas)))
    for i, var in enumerate(vars_categoricas):
        X_cat_df[:, i] = (df_filtrado[var] == nueva_tienda[var]).astype(int)
    X_cat_nueva = np.ones((1, len(vars_categoricas)))

    # ── Combinar ──
    X_df_completo = np.hstack([X_num_df_scaled, X_cat_df])
    X_nueva_completo = np.hstack([X_num_nueva_scaled, X_cat_nueva])

    # ── Pesos (orden: ESTRATO, AREA, VIVIENDAS, EMPLEOS, VENTAS_OU6M, TRAFICO_U6M, ZONA, TIPO, GEN, MUN) ──
    peso_vector = np.array([
        pesos.get('ESTRATO', 0.08),
        pesos.get('AREA', 0.08),
        pesos.get('VIVIENDAS', 0.06),
        pesos.get('EMPLEOS', 0.06),
        pesos.get('VENTAS_OU6M', 0.12),
        pesos.get('TRAFICO_U6M', 0.10),
        pesos.get('ZONA', 0.10),
        pesos.get('TIPO DE LOCAL', 0.07),
        pesos.get('GENERADOR', 0.07),
        pesos.get('MUN', 0.06),
    ])

    X_df_ponderado = X_df_completo * np.sqrt(peso_vector)
    X_nueva_ponderado = X_nueva_completo * np.sqrt(peso_vector)

    distancias = euclidean_distances(X_nueva_ponderado, X_df_ponderado)[0]

    max_dist = np.max(distancias)
    min_dist = np.min(distancias)
    if max_dist > min_dist:
        distancias_norm = (distancias - min_dist) / (max_dist - min_dist)
        similitud_scores = (1 - distancias_norm) * 100
    else:
        similitud_scores = np.full_like(distancias, 100.0)

    df_resultado = df_filtrado.copy()
    df_resultado['DISTANCIA'] = distancias
    df_resultado['SIMILITUD'] = similitud_scores
    df_resultado = df_resultado.sort_values('SIMILITUD', ascending=False)

    return df_resultado, None


def calcular_estadisticas(df_resultado, nueva_tienda):
    top_10 = df_resultado.head(10)

    renta_col = None
    for col in df_resultado.columns:
        if 'RENTA' in col.upper():
            renta_col = col
            break

    stats = {
        'VT_promedio': top_10['VT'].mean(),
        'VT_std': top_10['VT'].std(),
        'ET_promedio': top_10['ET'].mean(),
        'ET_std': top_10['ET'].std(),
        'VENTAS_OU6M_promedio': top_10['VENTAS_OU6M'].mean() if 'VENTAS_OU6M' in top_10.columns else 0,
        'VENTAS_OU6M_std': top_10['VENTAS_OU6M'].std() if 'VENTAS_OU6M' in top_10.columns else 0,
        'TRAFICO_U6M_promedio': top_10['TRAFICO_U6M'].mean() if 'TRAFICO_U6M' in top_10.columns else 0,
        'TRAFICO_U6M_std': top_10['TRAFICO_U6M'].std() if 'TRAFICO_U6M' in top_10.columns else 0,
        'RENTA_promedio': top_10[renta_col].mean() if renta_col and renta_col in top_10.columns else 0,
        'RENTA_std': top_10[renta_col].std() if renta_col and renta_col in top_10.columns else 0,
        'AREA_promedio': top_10['AREA'].mean(),
        'similitud_promedio': top_10['SIMILITUD'].mean(),
        'renta_col': renta_col if renta_col else 'RENTA',
    }
    return stats


def cargar_datos_excel(origen):
    """Carga TiendaEspejo.xlsx y unifica los nombres de sus métricas."""
    if isinstance(origen, str) and os.path.basename(origen) == 'TiendaEspejo.xlsx':
        datos = pd.read_excel(origen, sheet_name='DATA')
    else:
        datos = pd.read_excel(origen)
    datos.columns = datos.columns.astype(str).str.strip()
    renombres = {
        'TRU6': 'TRAFICO_U6M',
        'VU6M': 'VENTAS_OU6M',
        'VENTAS OUM': 'VENTAS_OUM',
        'TRAFICO UM': 'TRAFICO_UM',
    }
    datos = datos.rename(columns={k: v for k, v in renombres.items() if k in datos.columns})
    if 'VENTAS_OU6M' not in datos.columns:
        ventas_base = datos['VENTAS_OUM'] if 'VENTAS_OUM' in datos.columns else pd.Series(0, index=datos.index)
        datos['VENTAS_OU6M'] = pd.to_numeric(ventas_base, errors='coerce').fillna(0)
    if 'TRAFICO_U6M' not in datos.columns:
        trafico_base = datos['TRAFICO_UM'] if 'TRAFICO_UM' in datos.columns else pd.Series(0, index=datos.index)
        datos['TRAFICO_U6M'] = pd.to_numeric(trafico_base, errors='coerce').fillna(0)
    requeridas = ['CR', 'NAME', 'SEG26', 'ZONA', 'MUN', 'ESTRATO',
                  'TIPO DE LOCAL', 'AREA', 'VT', 'ET', 'GENERADOR']
    faltantes = [col for col in requeridas if col not in datos.columns]
    if faltantes:
        raise ValueError(
            f"La hoja DATA no contiene las columnas requeridas: {', '.join(faltantes)}"
        )
    return datos


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("📂 Cargar Datos")

    modelo_seleccionado = st.radio(
        "🧠 Motor de similitud",
        ["Red neuronal (autoencoder)", "Modelo estadístico (distancia)"],
        index=0,
        help="La red neuronal aprende un embedding auto-supervisado; no necesita etiquetas de pares similares."
    )

    # La base queda integrada en el repositorio: no se solicita carga manual.
    if not os.path.exists(ARCHIVO_BASE):
        st.error("No se encontró TiendaEspejo.xlsx junto a la aplicación.")
        st.stop()
    try:
        df = cargar_datos_excel(ARCHIVO_BASE)
        st.markdown(f"""
            <div style='background-color: #ED1C24; padding: 0.8rem; border-radius: 5px;
                        color: white; border-left: 4px solid #FFD100;'>
                ✅ <strong>{len(df)}</strong> tiendas cargadas desde la hoja DATA
            </div>
        """, unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"No fue posible cargar la hoja DATA de TiendaEspejo.xlsx: {exc}")
        st.stop()

    if df is not None:
        st.divider()
        st.header("⚙️ Configuración de Pesos")
        st.caption("Ajusta la importancia de cada característica")
        st.markdown("""
            <div style='background-color: #FFD100; padding: 0.8rem; border-radius: 5px; 
                        color: #1a1a1a; border-left: 4px solid #ED1C24;'>
                💡 Los pesos se normalizan automáticamente para sumar 100%
            </div>
        """, unsafe_allow_html=True)

        peso_seg       = st.slider("Segmento (filtro obligatorio)", 0, 100, 30, disabled=True)
        peso_zona      = st.slider("Zona geográfica", 0, 100, 10)
        peso_estrato   = st.slider("Estrato socioeconómico", 0, 100, 8)
        peso_tipo      = st.slider("Tipo de Local", 0, 100, 7)
        peso_area      = st.slider("Área (m²)", 0, 100, 8)
        peso_generador = st.slider("Generador", 0, 100, 7)
        peso_mun       = st.slider("Municipio", 0, 100, 6)
        peso_viviendas = st.slider("Viviendas Totales (VT)", 0, 100, 6)
        peso_empleos   = st.slider("Empleos Totales (ET)", 0, 100, 6)

        st.markdown("---")
        st.markdown("**📊 Variables de Rendimiento**")
        peso_VENTAS_OU6M = st.slider("💰 Venta Proyectada", 0, 100, 12)
        peso_TRAFICO_U6M = st.slider("🚶 Tráfico Proyectado", 0, 100, 10)

        total = (peso_zona + peso_estrato + peso_tipo + peso_area + peso_generador +
                 peso_mun + peso_viviendas + peso_empleos + peso_VENTAS_OU6M + peso_TRAFICO_U6M)

        if total > 0:
            pesos = {
                'SEG26': 0.30,
                'ZONA':          peso_zona      / total * 0.70,
                'ESTRATO':       peso_estrato   / total * 0.70,
                'TIPO DE LOCAL': peso_tipo      / total * 0.70,
                'AREA':          peso_area      / total * 0.70,
                'GENERADOR':     peso_generador / total * 0.70,
                'MUN':           peso_mun       / total * 0.70,
                'VIVIENDAS':     peso_viviendas / total * 0.70,
                'EMPLEOS':       peso_empleos   / total * 0.70,
                'VENTAS_OU6M':          peso_VENTAS_OU6M      / total * 0.70,
                'TRAFICO_U6M':          peso_TRAFICO_U6M      / total * 0.70,
            }
        else:
            pesos = None

        with st.expander("Ver pesos normalizados"):
            if pesos:
                for key, val in pesos.items():
                    st.write(f"**{key}:** {val*100:.1f}%")


# ──────────────────────────────────────────────
# CONTENIDO PRINCIPAL
# ──────────────────────────────────────────────
if df is not None:

    df['VIVIENDAS'] = df['VT']
    df['EMPLEOS']   = df['ET']

    # Columnas VENTAS_OU6M y TRAFICO_U6M: si no existen en el Excel, iniciar en 0
    if 'VENTAS_OU6M' not in df.columns:
        df['VENTAS_OU6M'] = 0
        st.warning("⚠️ No se encontró la columna **VENTAS_OU6M** (Ventas últimos 6 meses) en el Excel. Se usará 0.")
    if 'TRAFICO_U6M' not in df.columns:
        df['TRAFICO_U6M'] = 0
        st.warning("⚠️ No se encontró la columna **TRAFICO_U6M** (Tráfico últimos 6 meses) en el Excel. Se usará 0.")

    renta_col_disponible = None
    for col in df.columns:
        if 'RENTA' in col.upper():
            renta_col_disponible = col
            break
    if renta_col_disponible is None:
        df['RENTA'] = 0
        renta_col_disponible = 'RENTA'

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("<h2 class='section-title'>Nueva tienda propuesta</h2>", unsafe_allow_html=True)

        with st.form("form_nueva_tienda"):
            nombre_nueva = st.text_input("Nombre de la tienda propuesta", "Mi Nueva Tienda")

            st.markdown("##### Características Principales")
            segmento   = st.selectbox("Segmento (SEG26)",   options=sorted(df['SEG26'].unique()))
            zona       = st.selectbox("Zona",               options=sorted(df['ZONA'].unique()))
            municipio  = st.selectbox("Municipio",          options=sorted(df['MUN'].unique()))
            estrato    = st.selectbox("Estrato",            options=sorted(df['ESTRATO'].unique()))
            tipo_local = st.selectbox("Tipo de Local",      options=sorted(df['TIPO DE LOCAL'].unique()))
            generador  = st.selectbox("Generador",          options=sorted(df['GENERADOR'].unique()))

            st.markdown("##### Métricas Numéricas")
            col_a, col_b = st.columns(2)
            with col_a:
                area      = st.number_input("Área (m²)",         min_value=0.0, value=100.0, step=10.0)
                viviendas = st.number_input("Viviendas Totales", min_value=0,   value=1000,  step=100)
                empleos   = st.number_input("Empleos Totales",   min_value=0,   value=500,   step=50)
            with col_b:
                VENTAS_OU6M = st.number_input(
                    "💰 Venta Proyectada ($)",
                    min_value=0.0, value=0.0, step=1000.0,
                    help="Venta proyectada para la nueva tienda. Se compara contra VENTAS_OU6M del Excel."
                )
                TRAFICO_U6M = st.number_input(
                    "🚶 Tráfico Proyectado (personas)",
                    min_value=0, value=0, step=100,
                    help="Tráfico estimado para la nueva tienda. Se compara contra TRAFICO_U6M del Excel."
                )

            submitted = st.form_submit_button("🔍 Buscar Tienda Espejo", use_container_width=True)

    with col2:
        st.markdown("<h2 class='section-title'>Resultado espejo</h2>", unsafe_allow_html=True)

        if submitted:
            nueva_tienda = {
                'NAME':      nombre_nueva,
                'SEG26':     segmento,
                'ZONA':      zona,
                'MUN':       municipio,
                'ESTRATO':   estrato,
                'TIPO DE LOCAL': tipo_local,
                'AREA':      area,
                'GENERADOR': generador,
                'VIVIENDAS': viviendas,
                'EMPLEOS':   empleos,
                'VENTAS_OU6M':      VENTAS_OU6M,
                'TRAFICO_U6M':      TRAFICO_U6M,
            }

            if modelo_seleccionado == "Red neuronal (autoencoder)":
                resultado, error = calcular_tienda_espejo_neuronal(df, nueva_tienda, pesos)
                etiqueta_modelo = "red neuronal autoencoder"
            else:
                resultado, error = calcular_tienda_espejo_estadistico(df, nueva_tienda, pesos)
                etiqueta_modelo = "modelo estadístico"

            if error:
                st.error(error)
            else:
                stats     = calcular_estadisticas(resultado, nueva_tienda)
                renta_col = stats['renta_col']

                st.success(f"✅ Tiendas espejo encontradas usando {etiqueta_modelo}")

                mejor = resultado.iloc[0]
                st.markdown("### 🏆 Mejor tienda espejo encontrada")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Nombre", mejor['NAME'])
                    st.metric("Código", mejor['CR'])
                with c2:
                    st.metric("Similitud",  f"{mejor['SIMILITUD']:.1f}%")
                    st.metric("Distancia",  f"{mejor['DISTANCIA']:.3f}")
                with c3:
                    st.metric("Viviendas (VT)", f"{mejor['VT']:,.0f}")
                    st.metric("Empleos (ET)",   f"{mejor['ET']:,.0f}")
                with c4:
                    VENTAS_OU6M_val = mejor['VENTAS_OU6M'] if 'VENTAS_OU6M' in mejor.index else 0
                    TRAFICO_U6M_val = mejor['TRAFICO_U6M'] if 'TRAFICO_U6M' in mejor.index else 0
                    st.metric("💰 Ventas U6M",  f"${VENTAS_OU6M_val:,.0f}")
                    st.metric("🚶 Tráfico U6M", f"{TRAFICO_U6M_val:,.0f}")

                with st.expander("📊 Ver detalles completos de la mejor tienda", expanded=False):
                    col_det1, col_det2 = st.columns(2)
                    with col_det1:
                        st.write(f"**Segmento:** {mejor['SEG26']}")
                        st.write(f"**Zona:** {mejor['ZONA']}")
                        st.write(f"**Municipio:** {mejor['MUN']}")
                        st.write(f"**Estrato:** {mejor['ESTRATO']}")
                        st.write(f"**💰 Ventas Últ. 6 Meses (VENTAS_OU6M):** ${VENTAS_OU6M_val:,.0f}")
                    with col_det2:
                        st.write(f"**Tipo de Local:** {mejor['TIPO DE LOCAL']}")
                        st.write(f"**Generador:** {mejor['GENERADOR']}")
                        st.write(f"**Viviendas (VT):** {mejor['VT']:,.0f}")
                        st.write(f"**Empleos (ET):** {mejor['ET']:,.0f}")
                        st.write(f"**🚶 Tráfico Últ. 6 Meses (TRAFICO_U6M):** {TRAFICO_U6M_val:,.0f}")

                st.divider()

                # Estadísticas Top 10
                st.markdown("### 📈 Estadísticas del Top 10")
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    st.metric("Viviendas Prom (VT)", f"{stats['VT_promedio']:,.0f}")
                    st.caption(f"±{stats['VT_std']:,.0f}")
                with col_s2:
                    st.metric("Empleos Prom (ET)", f"{stats['ET_promedio']:,.0f}")
                    st.caption(f"±{stats['ET_std']:,.0f}")
                with col_s3:
                    st.metric("💰 Ventas U6M Prom", f"${stats['VENTAS_OU6M_promedio']:,.0f}")
                    st.caption(f"±{stats['VENTAS_OU6M_std']:,.0f}")
                with col_s4:
                    st.metric("🚶 Tráfico U6M Prom", f"{stats['TRAFICO_U6M_promedio']:,.0f}")
                    st.caption(f"Similitud: {stats['similitud_promedio']:.1f}%")

                st.divider()

                # Top 10
                st.markdown("### 📋 Top 5 Alternativas")

                columnas_mostrar = ['CR', 'NAME', 'ZONA', 'MUN', 'ESTRATO',
                                    'TIPO DE LOCAL', 'AREA', 'VT', 'ET',
                                    'VENTAS_OU6M', 'TRAFICO_U6M', 'SIMILITUD', 'DISTANCIA']

                if renta_col in resultado.columns and renta_col not in columnas_mostrar:
                    columnas_mostrar.insert(-2, renta_col)

                columnas_mostrar = [c for c in columnas_mostrar if c in resultado.columns]

                top_10     = resultado.head(5)[columnas_mostrar]
                top_10_display = top_10.copy()

                top_10_display['SIMILITUD'] = top_10_display['SIMILITUD'].apply(lambda x: f"{x:.1f}%")
                top_10_display['DISTANCIA'] = top_10_display['DISTANCIA'].apply(lambda x: f"{x:.3f}")
                top_10_display['AREA']      = top_10_display['AREA'].apply(lambda x: f"{x:.1f}")
                top_10_display['VT']        = top_10_display['VT'].apply(lambda x: f"{x:,.0f}")
                top_10_display['ET']        = top_10_display['ET'].apply(lambda x: f"{x:,.0f}")
                if 'VENTAS_OU6M' in top_10_display.columns:
                    top_10_display['VENTAS_OU6M']  = top_10_display['VENTAS_OU6M'].apply(lambda x: f"${x:,.0f}")
                if 'TRAFICO_U6M' in top_10_display.columns:
                    top_10_display['TRAFICO_U6M']  = top_10_display['TRAFICO_U6M'].apply(lambda x: f"{x:,.0f}")
                if renta_col in top_10_display.columns:
                    top_10_display[renta_col] = top_10_display[renta_col].apply(lambda x: f"${x:,.0f}")

                top_10_display = top_10_display.rename(columns={
                    'VT':   'Viviendas (VT)',
                    'ET':   'Empleos (ET)',
                    'VENTAS_OU6M': '💰 Ventas U6M ($)',
                    'TRAFICO_U6M': '🚶 Tráfico U6M'
                })

                st.dataframe(top_10_display, use_container_width=True, hide_index=True)

                csv = resultado.head(5).to_csv(index=False)
                st.download_button(
                    label="📥 Descargar Top 5 (CSV)",
                    data=csv,
                    file_name=f"tiendas_espejo_{nombre_nueva.replace(' ', '_')}.csv",
                    mime="text/csv"
                )

                st.divider()

                # Visualizaciones
                st.markdown("### 📊 Análisis Visual")

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "Comparación de Métricas",
                    "Ventas & Tráfico U6M",
                    "Distribución Geográfica",
                    "Análisis de Similitud",
                    "Modelo Estadístico"
                ])

                with tab1:
                    top_5 = resultado.head(5)
                    fig_metricas = go.Figure()
                    fig_metricas.add_trace(go.Bar(name='Viviendas (VT)', x=top_5['NAME'], y=top_5['VT'], marker_color='#ED1C24'))
                    fig_metricas.add_trace(go.Bar(name='Empleos (ET)',   x=top_5['NAME'], y=top_5['ET'], marker_color='#FFD100'))
                    fig_metricas.update_layout(title='Top 5 - Viviendas vs Empleos', barmode='group', height=400,
                                               plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_metricas, use_container_width=True)

                with tab2:
                    top_10_raw = resultado.head(10)

                    # Ventas U6M por tienda
                    if 'VENTAS_OU6M' in top_10_raw.columns:
                        fig_venta = go.Figure()
                        fig_venta.add_trace(go.Bar(
                            name='Ventas Últ. 6 Meses ($)',
                            x=top_10_raw['NAME'],
                            y=top_10_raw['VENTAS_OU6M'],
                            marker_color='#ED1C24'
                        ))
                        if VENTAS_OU6M > 0:
                            fig_venta.add_hline(
                                y=VENTAS_OU6M,
                                line_dash="dash",
                                line_color="#FFD100",
                                annotation_text=f"Tu propuesta: ${VENTAS_OU6M:,.0f}",
                                annotation_position="top left"
                            )
                        fig_venta.update_layout(
                            title='💰 Ventas Últimos 6 Meses – Tiendas Espejo (Top 10)',
                            xaxis_tickangle=-45, height=400,
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_venta, use_container_width=True)

                    # Tráfico U6M por tienda
                    if 'TRAFICO_U6M' in top_10_raw.columns:
                        fig_traf = go.Figure()
                        fig_traf.add_trace(go.Bar(
                            name='Tráfico Últ. 6 Meses',
                            x=top_10_raw['NAME'],
                            y=top_10_raw['TRAFICO_U6M'],
                            marker_color='#FFD100'
                        ))
                        if TRAFICO_U6M > 0:
                            fig_traf.add_hline(
                                y=TRAFICO_U6M,
                                line_dash="dash",
                                line_color="#ED1C24",
                                annotation_text=f"Tu propuesta: {TRAFICO_U6M:,}",
                                annotation_position="top left"
                            )
                        fig_traf.update_layout(
                            title='🚶 Tráfico Últimos 6 Meses – Tiendas Espejo (Top 10)',
                            xaxis_tickangle=-45, height=400,
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_traf, use_container_width=True)

                    # Scatter Ventas vs Tráfico
                    if 'VENTAS_OU6M' in top_10_raw.columns and 'TRAFICO_U6M' in top_10_raw.columns:
                        fig_vt = px.scatter(
                            top_10_raw,
                            x='TRAFICO_U6M',
                            y='VENTAS_OU6M',
                            size='AREA',
                            color='SIMILITUD',
                            hover_data=['NAME', 'ZONA'],
                            title='Ventas vs Tráfico U6M (Tamaño = Área, Color = Similitud)',
                            labels={'TRAFICO_U6M': 'Tráfico Últ. 6 Meses', 'VENTAS_OU6M': 'Ventas U6M ($)'},
                            color_continuous_scale=['#C41E3A', '#ED1C24', '#FFD100', '#28a745']
                        )
                        if VENTAS_OU6M > 0 or TRAFICO_U6M > 0:
                            fig_vt.add_trace(go.Scatter(
                                x=[TRAFICO_U6M], y=[VENTAS_OU6M],
                                mode='markers',
                                marker=dict(color='blue', size=14, symbol='star'),
                                name='Tu propuesta'
                            ))
                        fig_vt.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_vt, use_container_width=True)

                with tab3:
                    colors_oxxo = ['#ED1C24', '#FFD100', '#C41E3A', '#FFA500', '#FF6B6B']
                    dist_zona = top_10_raw['ZONA'].value_counts()
                    fig_zona = px.pie(values=dist_zona.values, names=dist_zona.index,
                                     title='Distribución por Zona', color_discrete_sequence=colors_oxxo)
                    fig_zona.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_zona, use_container_width=True)

                    dist_estrato = top_10_raw['ESTRATO'].value_counts().sort_index()
                    fig_estrato = px.bar(x=dist_estrato.index, y=dist_estrato.values,
                                        title='Distribución por Estrato',
                                        labels={'x': 'Estrato', 'y': 'Cantidad'},
                                        color=dist_estrato.values,
                                        color_continuous_scale=['#FFD100', '#FFA500', '#ED1C24', '#C41E3A'])
                    fig_estrato.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_estrato, use_container_width=True)

                with tab4:
                    fig_sim = px.bar(top_10_raw, x='NAME', y='SIMILITUD',
                                     title='% Similitud - Top 10',
                                     labels={'NAME': 'Tienda', 'SIMILITUD': 'Similitud (%)'},
                                     color='SIMILITUD',
                                     color_continuous_scale=['#C41E3A', '#ED1C24', '#FFD100', '#28a745'])
                    fig_sim.update_layout(xaxis_tickangle=-45, height=400,
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_sim, use_container_width=True)

                    st.markdown("#### 📋 Comparación con Tienda Espejo")
                    VENTAS_OU6M_val2 = mejor.get('VENTAS_OU6M', 0)
                    TRAFICO_U6M_val2 = mejor.get('TRAFICO_U6M', 0)
                    comparacion = pd.DataFrame({
                        'Característica': ['Segmento', 'Zona', 'Municipio', 'Estrato',
                                           'Tipo de Local', 'Generador', 'Área',
                                           'Viviendas (VT)', 'Empleos (ET)',
                                           '💰 Venta Proyectada ($)', '🚶 Tráfico Proyectado'],
                        'Tu Propuesta': [
                            nueva_tienda['SEG26'], nueva_tienda['ZONA'], nueva_tienda['MUN'],
                            nueva_tienda['ESTRATO'], nueva_tienda['TIPO DE LOCAL'], nueva_tienda['GENERADOR'],
                            f"{nueva_tienda['AREA']:.1f} m²",
                            f"{nueva_tienda['VIVIENDAS']:,}", f"{nueva_tienda['EMPLEOS']:,}",
                            f"${nueva_tienda['VENTAS_OU6M']:,.0f}",
                            f"{nueva_tienda['TRAFICO_U6M']:,}"
                        ],
                        'Tienda Espejo': [
                            mejor['SEG26'], mejor['ZONA'], mejor['MUN'],
                            mejor['ESTRATO'], mejor['TIPO DE LOCAL'], mejor['GENERADOR'],
                            f"{mejor['AREA']:.1f} m²",
                            f"{mejor['VT']:,.0f}", f"{mejor['ET']:,.0f}",
                            f"${VENTAS_OU6M_val2:,.0f}",
                            f"{TRAFICO_U6M_val2:,.0f}"
                        ],
                        'Coincide / Diferencia': [
                            '✅' if nueva_tienda['SEG26'] == mejor['SEG26'] else '❌',
                            '✅' if nueva_tienda['ZONA'] == mejor['ZONA'] else '❌',
                            '✅' if nueva_tienda['MUN'] == mejor['MUN'] else '❌',
                            '✅' if nueva_tienda['ESTRATO'] == mejor['ESTRATO'] else '❌',
                            '✅' if nueva_tienda['TIPO DE LOCAL'] == mejor['TIPO DE LOCAL'] else '❌',
                            '✅' if nueva_tienda['GENERADOR'] == mejor['GENERADOR'] else '❌',
                            f"{abs(nueva_tienda['AREA'] - mejor['AREA']):.1f} m²",
                            f"{abs(nueva_tienda['VIVIENDAS'] - mejor['VT']):,.0f}",
                            f"{abs(nueva_tienda['EMPLEOS'] - mejor['ET']):,.0f}",
                            f"${abs(nueva_tienda['VENTAS_OU6M'] - VENTAS_OU6M_val2):,.0f}",
                            f"{abs(nueva_tienda['TRAFICO_U6M'] - TRAFICO_U6M_val2):,.0f}"
                        ]
                    })
                    st.dataframe(comparacion, use_container_width=True, hide_index=True)

                with tab5:
                    info_modelo = resultado.attrs.get('modelo_info', {})
                    if modelo_seleccionado == "Red neuronal (autoencoder)" and info_modelo:
                        st.markdown("#### 🧠 Red neuronal: autoencoder denoising")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Dimensión latente", info_modelo.get('dim_latente', 0))
                        m2.metric("Iteraciones", info_modelo.get('iteraciones', 0))
                        m3.metric("Tiendas entrenadas", info_modelo.get('muestras', 0))
                        m4.metric("Error de reconstrucción", f"{info_modelo.get('error_reconstruccion', 0):.4f}")
                        st.info("La red aprende una representación comprimida de las tiendas y compara distancias en ese embedding. Usa L2, ruido denoising y parada temprana para reducir el sobreajuste. El segmento se filtra antes del entrenamiento.")
                    else:
                        st.markdown("#### 🔬 Modelo Estadístico: Distancia Euclidiana Ponderada")
                    st.markdown("""
                    **Metodología:**
                    1. **Filtrado** por segmento (SEG26)
                    2. **Normalización** de variables numéricas (StandardScaler μ=0, σ=1)
                    3. **Codificación** de variables categóricas
                    4. **Ponderación** configurable por el usuario
                    5. **Distancia** en espacio estadístico o embedding neuronal
                    6. **Similitud** en escala 0-100%
                    
                    **Variables numéricas:** ESTRATO, ÁREA, VIVIENDAS, EMPLEOS, **VENTAS_OU6M** (Ventas Últ. 6 Meses), **TRAFICO_U6M** (Tráfico Últ. 6 Meses)
                    
                    **Variables categóricas:** ZONA, TIPO DE LOCAL, GENERADOR, MUNICIPIO
                    """)

                    fig_dist = px.histogram(resultado.head(50), x='DISTANCIA', nbins=20,
                                            title='Distribución de Distancias (Top 50)',
                                            color_discrete_sequence=['#ED1C24'])
                    fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_dist, use_container_width=True)

                    fig_rel = px.scatter(resultado.head(30), x='DISTANCIA', y='SIMILITUD',
                                         hover_data=['NAME'],
                                         title='Distancia vs Similitud (Top 30)',
                                         color_discrete_sequence=['#ED1C24'])
                    fig_rel.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_rel, use_container_width=True)

else:
    st.info("👈 Por favor, carga un archivo Excel en la barra lateral para comenzar")
    st.markdown("""
    ### 📖 Cómo usar esta herramienta:
    1. **Carga tu archivo Excel** en la barra lateral (o usa los datos precargados)
    2. **Completa los datos** de la nueva tienda, incluyendo **VENTAS_OU6M** y **TRAFICO_U6M**
    3. **Ajusta los pesos** en el sidebar
    4. **Haz clic en "Buscar Tienda Espejo"**
    
    ### 📊 Columnas requeridas en el Excel:
    - **VENTAS_OU6M** — Ventas acumuladas de los últimos 6 meses por tienda
    - **TRAFICO_U6M** — Tráfico acumulado de los últimos 6 meses por tienda
    
    Asegúrate de que tu archivo Excel incluya estas columnas con esos nombres exactos.
    """)

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #ED1C24 0%, #C41E3A 100%); border-radius: 10px;'>
        <h3 style='color: #FFD100; margin: 0;'>🏪 Modelo de Tienda Espejo OXXO</h3>
        <p style='color: white; margin: 0.5rem 0 0 0;'>v4.0 | Oxxo Colombia | Juan C. Rubiano</p>
    </div>
""", unsafe_allow_html=True)
