import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
from similitud import cargar_abiertas, rankear_tiendas, VARIABLES_NUMERICAS, VARIABLES_CATEGORICAS, PESOS_BASE

st.set_page_config(page_title="Tiendas hermanas", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px; }
    [data-testid="stMetricValue"] { color: #123B5D; }
    .hero { background: linear-gradient(120deg,#123B5D 0%,#1B6B7A 100%); padding: 2rem 2.2rem; border-radius: 18px; color: white; margin-bottom: 1.3rem; box-shadow: 0 8px 24px rgba(18,59,93,.18); }
    .hero h1 { color: white; font-size: 2.25rem; margin: 0 0 .35rem 0; }
    .hero p { color: #E7F5F6; margin: 0; font-size: 1.05rem; }
    .section-title { color: #123B5D; font-size: 1.35rem; font-weight: 700; margin: .8rem 0 .35rem; }
    .small-note { color: #64748B; font-size: .88rem; }
    div[data-testid="stDataFrame"] { border: 1px solid #DCE6EC; border-radius: 12px; }
    .stButton > button[kind="primary"] { background: #1B6B7A; border: none; border-radius: 10px; font-weight: 700; padding: .65rem 1rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def leer_excel(uploaded, local_path):
    source = uploaded if uploaded is not None else local_path
    return pd.read_excel(source, sheet_name="JUN")


def numero_opcional(label, key, help_text=None):
    texto = st.text_input(label, key=key, help=help_text, placeholder="Dejar vacío si no se conoce")
    if not texto.strip():
        return None
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        st.warning(f"{label}: escribe un número válido o déjalo vacío.")
        return None


def limpiar_texto(valor):
    return "" if valor is None else str(valor).strip()


st.markdown("""
<div class="hero">
  <h1>Buscador de tiendas hermanas</h1>
  <p>Encuentra tiendas abiertas comparables para evaluar un nuevo proyecto con datos de entorno, formato y desempeño.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Configuración")
    archivo = st.file_uploader("Cargar Excel actualizado", type=["xlsx"])
    ruta_local = ROOT / "data" / "Book.xlsx"
    st.caption("Fuente: hoja JUN · Solo se consideran tiendas con estado ABIERTA.")

try:
    raw = leer_excel(archivo, str(ruta_local))
    abiertas = cargar_abiertas(raw)
except Exception as exc:
    st.error(f"No se pudo leer la hoja JUN: {exc}")
    st.stop()

with st.sidebar:
    st.success(f"{len(abiertas):,} tiendas abiertas disponibles")
    with st.expander("Variables del motor", expanded=False):
        st.write("**Numéricas:** " + ", ".join(VARIABLES_NUMERICAS))
        st.write("**Categóricas:** " + ", ".join(VARIABLES_CATEGORICAS))
        st.write("Se excluyen CR, NAME, ARRENDADOR, ZONA, FECHA APE, DIAS OP, MESOP y TE.")

modo = st.radio("Tipo de análisis", ["Nuevo proyecto", "Tienda abierta existente"], horizontal=True)
propuesta = {}

if modo == "Tienda abierta existente":
    st.markdown('<div class="section-title">Selecciona una tienda de referencia</div>', unsafe_allow_html=True)
    opciones = abiertas["CR"].astype(str) + " — " + abiertas["NAME"].astype(str)
    elegido = st.selectbox("Tienda de referencia", opciones, label_visibility="collapsed")
    cr = elegido.split(" — ", 1)[0]
    fila = abiertas[abiertas["CR"].astype(str).eq(cr)].iloc[0]
    propuesta = fila.to_dict()
    st.info(f"Comparando contra: **{fila['NAME']}** · CR **{fila['CR']}** · {fila['MUN']}")
else:
    st.markdown('<div class="section-title">Datos del nuevo proyecto</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-note">Completa solo lo que conozcas. Los campos vacíos no penalizan la similitud.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        propuesta["DEPARTAMENTO"] = st.selectbox("Departamento", [""] + sorted(abiertas["DEPARTAMENTO"].dropna().unique().tolist()))
        propuesta["MUN"] = st.selectbox("Municipio", [""] + sorted(abiertas["MUN"].dropna().unique().tolist()))
        propuesta["UPZ/COMUNA"] = st.text_input("UPZ / Comuna")
        propuesta["ESTRATO"] = st.number_input("Estrato", min_value=1, max_value=6, value=None, step=1, placeholder="Opcional")
        propuesta["TIPO DE LOCAL"] = st.selectbox("Tipo de local", [""] + sorted(abiertas["TIPO DE LOCAL"].dropna().unique().tolist()))
    with c2:
        propuesta["AREA"] = numero_opcional("Área (m²)", "area_nueva")
        propuesta["VT"] = numero_opcional("Viviendas a 300 m (VT)", "vt_nueva")
        propuesta["ET"] = numero_opcional("Empleos a 300 m (ET)", "et_nueva")
        propuesta["TR15MIN"] = numero_opcional("Tráfico cada 15 minutos", "tr15_nueva")
        propuesta["COSTO M2"] = numero_opcional("Costo por m²", "costo_m2_nuevo")
    with c3:
        propuesta["Y"] = numero_opcional("Latitud / Y", "y_nueva", "Ejemplo Bogotá: 4.65")
        propuesta["X"] = numero_opcional("Longitud / X", "x_nueva", "Ejemplo Bogotá: -74.08")
        propuesta["GENERADOR"] = st.selectbox("Generador", [""] + sorted(abiertas["GENERADOR"].dropna().unique().tolist()))
        propuesta["SEG26"] = st.selectbox("Segmento SEG26", [""] + sorted(abiertas["SEG26"].dropna().unique().tolist()))
        propuesta["PTH"] = st.selectbox("Potencial de hambre (PTH)", [""] + sorted(abiertas["PTH"].dropna().unique().tolist()))

    st.markdown("#### Venta proyectada")
    st.caption("Se compara contra VU6M: ventas operativas acumuladas de los últimos seis meses. Déjala vacía si aún no existe.")
    propuesta["VU6M"] = numero_opcional("Venta proyectada (últimos 6 meses)", "venta_proyectada", "Valor monetario sin símbolos; por ejemplo 1200000")

st.divider()
st.markdown('<div class="section-title">Personaliza la importancia de las variables</div>', unsafe_allow_html=True)
st.caption("Los pesos son iniciales y se pueden calibrar con la validación del equipo.")
with st.expander("Ajustar pesos del modelo", expanded=False):
    grupos = {
        "Entorno y formato": ["ESTRATO", "AREA", "VT", "ET", "TR15MIN", "TIPO DE LOCAL", "GENERADOR", "PTH"],
        "Ubicación": ["DEPARTAMENTO", "MUN", "UPZ/COMUNA", "Y", "X"],
        "Desempeño": ["VU6M", "COSTO M2"],
        "Segmentación": ["SEG26", "TIE26"],
    }
    pesos = PESOS_BASE.copy()
    for grupo, variables in grupos.items():
        st.markdown(f"**{grupo}**")
        gc = st.columns(4)
        for i, col in enumerate(variables):
            with gc[i % 4]:
                pesos[col] = st.slider(col, 0.0, 0.20, float(PESOS_BASE.get(col, 0.03)), 0.005, key=f"peso_{col}")

n = st.slider("Número de tiendas hermanas a mostrar", 3, 20, 10)
if st.button("Encontrar tiendas hermanas", type="primary", use_container_width=True):
    ranking, detalle = rankear_tiendas(abiertas, propuesta, top_n=n, pesos=pesos)
    if ranking.empty:
        st.warning("Completa al menos una característica para calcular la similitud.")
    else:
        st.success(f"Se encontraron {len(ranking)} tiendas hermanas entre {len(abiertas):,} tiendas abiertas.")
        top = ranking.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mejor coincidencia", str(top["NAME"]).strip())
        m2.metric("Similitud", f"{top['SIMILITUD']:.1f}%")
        m3.metric("Tiendas comparadas", f"{len(abiertas):,}")
        m4.metric("Variables utilizadas", int(top["VARIABLES_USADAS"]))

        tab1, tab2, tab3 = st.tabs(["Ranking", "Mapa", "Explicación"])
        with tab1:
            vista = ranking[[c for c in ["CR", "NAME", "SIMILITUD", "MUN", "UPZ/COMUNA", "AREA", "ESTRATO", "TRAFICO UM", "VU6M", "MARGEN U6M", "RENTA", "TIPO DE LOCAL", "PTH"] if c in ranking.columns]].copy()
            vista = vista.rename(columns={"NAME": "Tienda", "SIMILITUD": "Similitud", "MUN": "Municipio", "AREA": "Área", "VU6M": "Ventas 6M", "MARGEN U6M": "Margen 6M"})
            st.dataframe(vista, use_container_width=True, hide_index=True, column_config={"Similitud": st.column_config.ProgressColumn("Similitud", min_value=0, max_value=100, format="%.1f%%")})
            st.download_button("Descargar ranking CSV", vista.to_csv(index=False).encode("utf-8-sig"), "tiendas_hermanas.csv", "text/csv")

        with tab2:
            puntos = ranking[["Y", "X", "NAME", "SIMILITUD", "CR"]].copy() if "Y" in ranking and "X" in ranking else pd.DataFrame()
            puntos["Y"] = pd.to_numeric(puntos["Y"], errors="coerce")
            puntos["X"] = pd.to_numeric(puntos["X"], errors="coerce")
            puntos = puntos.dropna(subset=["Y", "X"])
            fig = go.Figure()
            if not puntos.empty:
                fig.add_trace(go.Scattermapbox(lat=puntos["Y"], lon=puntos["X"], mode="markers+text", text=puntos["NAME"].astype(str).str.strip(), textposition="top center", textfont=dict(size=11, color="#123B5D"), marker=dict(size=12, color="#1B6B7A"), customdata=np.c_[puntos["CR"], puntos["SIMILITUD"]], hovertemplate="<b>%{text}</b><br>CR: %{customdata[0]}<br>Similitud: %{customdata[1]}%<extra></extra>", name="Tiendas hermanas"))
            proyecto_y = propuesta.get("Y")
            proyecto_x = propuesta.get("X")
            if proyecto_y is not None and proyecto_x is not None and not pd.isna(proyecto_y) and not pd.isna(proyecto_x):
                fig.add_trace(go.Scattermapbox(lat=[proyecto_y], lon=[proyecto_x], mode="markers+text", text=["NUEVO PROYECTO"], textposition="bottom center", textfont=dict(size=13, color="#C2410C"), marker=dict(size=18, color="#F97316", symbol="star"), hovertemplate="<b>NUEVO PROYECTO</b><extra></extra>", name="Nuevo proyecto"))
            if len(fig.data):
                center_lat = float(proyecto_y) if proyecto_y is not None and not pd.isna(proyecto_y) else float(puntos["Y"].mean())
                center_lon = float(proyecto_x) if proyecto_x is not None and not pd.isna(proyecto_x) else float(puntos["X"].mean())
                fig.update_layout(mapbox=dict(style="open-street-map", center=dict(lat=center_lat, lon=center_lon), zoom=10), margin=dict(l=0, r=0, t=10, b=0), height=650, legend=dict(orientation="h", y=1.02))
                st.plotly_chart(fig, use_container_width=True)
                if proyecto_y is None or proyecto_x is None:
                    st.info("Para mostrar el punto del nuevo proyecto, captura Latitud / Y y Longitud / X.")
            else:
                st.info("No hay coordenadas válidas para mostrar el mapa.")

        with tab3:
            st.markdown(f"**{str(top['NAME']).strip()} ({top['CR']})** obtuvo **{top['SIMILITUD']:.1f}%** de similitud usando **{int(top['VARIABLES_USADAS'])} variables**.")
            d = detalle.iloc[0].drop(labels=["SIMILITUD"], errors="ignore").sort_values().head(10)
            st.caption("Distancia baja significa mayor coincidencia con el nuevo proyecto o con la tienda de referencia.")
            st.dataframe(pd.DataFrame({"Variable": d.index, "Distancia (%)": d.values}), use_container_width=True, hide_index=True)

with st.expander("Vista de control de tiendas abiertas"):
    st.dataframe(abiertas.head(50), use_container_width=True, hide_index=True)
    st.caption("Mantén el Excel y el repositorio en modo privado si la información es sensible.")
