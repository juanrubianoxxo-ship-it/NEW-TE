import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
from io import BytesIO
from datetime import datetime
import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
from similitud import (PESOS_BASE, VARIABLES_CATEGORICAS, VARIABLES_NUMERICAS,
                       cargar_abiertas, cargar_ventas, enriquecer_book, rankear_tiendas)

st.set_page_config(page_title="Tiendas Hermanas", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")
BOOK_ONEDRIVE_URL = "https://femcom-my.sharepoint.com/:x:/g/personal/juan_rubiano_oxxo_com/IQBBFO2BfMQHRbOUDYjE0DD7Afy4zh6B1pszFdTkjDrERug?download=1"
VENTAS_ONEDRIVE_URL = "https://femcom-my.sharepoint.com/:x:/g/personal/juan_rubiano_oxxo_com/IQA8qrSLq1ftSa6kSWCDsTBzARnyYLeavlgqiKnhuXFfUQA?download=1"
st.markdown("""<style>
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px; }
[data-testid="stMetricValue"] { color: #123B5D; }
.hero { background: linear-gradient(120deg,#123B5D 0%,#1B6B7A 100%); padding: 2rem 2.2rem; border-radius: 18px; color: white; margin-bottom: 1.3rem; }
.hero h1 { color: white; font-size: 2.25rem; margin: 0 0 .35rem 0; }
.hero p { color: #E7F5F6; margin: 0; font-size: 1.05rem; }
.section-title { color: #123B5D; font-size: 1.35rem; font-weight: 700; margin: .8rem 0 .35rem; }
.small-note { color: #64748B; font-size: .88rem; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=900, show_spinner=False)
def descargar_excel(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    if "spreadsheet" not in response.headers.get("content-type", "") and not response.content[:2] == b"PK":
        raise ValueError("La URL no devolvió un archivo Excel descargable")
    return response.content

@st.cache_data(ttl=900, show_spinner=False)
def leer_book_remoto(url):
    return pd.read_excel(BytesIO(descargar_excel(url)), sheet_name="JUN")

@st.cache_data(ttl=900, show_spinner=False)
def leer_ventas_remoto(url):
    return cargar_ventas(BytesIO(descargar_excel(url)))

@st.cache_data
def leer_book_local(path):
    return pd.read_excel(path, sheet_name="JUN")

@st.cache_data
def leer_ventas_local(path):
    return cargar_ventas(path)

def numero_opcional(label, key, help_text=None):
    texto = st.text_input(label, key=key, help=help_text, placeholder="Dejar vacío si no se conoce")
    if not texto.strip(): return None
    try: return float(texto.replace(",", "."))
    except ValueError:
        st.warning(f"{label}: escribe un número válido o déjalo vacío."); return None

st.markdown("""<div class="hero"><h1>Buscador de tiendas hermanas</h1><p>Encuentra tiendas comparables para evaluar nuevos proyectos y mejorar decisiones.</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Actualización de datos")
    with st.expander("Opciones de carga manual", expanded=False):
        book_upload = st.file_uploader("Cargar archivo de características", type=["xlsx"], key="book")
        ventas_upload = st.file_uploader("Cargar archivo de desempeño", type=["xlsx"], key="ventas")
    usar_onedrive = st.checkbox("Actualizar desde OneDrive", value=True)
    st.caption("La información se actualiza automáticamente desde OneDrive.")

try:
    if usar_onedrive and book_upload is None:
        book = leer_book_remoto(BOOK_ONEDRIVE_URL)
        fuente_book = "OneDrive"
    else:
        book = pd.read_excel(book_upload if book_upload is not None else ROOT / "data" / "Book.xlsx", sheet_name="JUN")
        fuente_book = "carga manual/respaldo local"
    abiertas = cargar_abiertas(book)
except Exception as exc:
    st.error(f"No se pudieron leer los datos principales: {exc}"); st.stop()

resumen = pd.DataFrame(); historico = pd.DataFrame(); ventas_error = None
try:
    if usar_onedrive and ventas_upload is None:
        resumen, historico = leer_ventas_remoto(VENTAS_ONEDRIVE_URL)
        fuente_ventas = "OneDrive"
    else:
        resumen, historico = cargar_ventas(ventas_upload if ventas_upload is not None else ROOT / "data" / "LibroVentas.xlsx")
        fuente_ventas = "carga manual/respaldo local"
    abiertas = enriquecer_book(abiertas, resumen)
except Exception as exc:
    ventas_error = str(exc)

with st.sidebar:
    st.success(f"{len(abiertas):,} tiendas ABIERTA disponibles")
    if ventas_error: st.warning(f"No se pudo actualizar toda la información: {ventas_error}")
    elif usar_onedrive and book_upload is None and ventas_upload is None:
        st.success(f"Datos actualizados desde OneDrive · {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    else:
        st.success("Datos cargados correctamente")
    with st.expander("Variables del motor"):
        st.write("**Numéricas:** " + ", ".join(VARIABLES_NUMERICAS))
        st.write("**Categóricas:** " + ", ".join(VARIABLES_CATEGORICAS))

modo = st.radio("Tipo de análisis", ["Nuevo proyecto", "Tienda abierta existente"], horizontal=True)
propuesta = {}
if modo == "Tienda abierta existente":
    st.markdown('<div class="section-title">Selecciona una tienda de referencia</div>', unsafe_allow_html=True)
    opciones = abiertas["CR"].astype(str) + " — " + abiertas["NAME"].astype(str)
    elegido = st.selectbox("Tienda de referencia", opciones, label_visibility="collapsed")
    cr = elegido.split(" — ", 1)[0]
    propuesta = abiertas[abiertas["CR"].astype(str).eq(cr)].iloc[0].to_dict()
    st.info(f"Comparando contra: **{propuesta['NAME']}** · CR **{propuesta['CR']}** · {propuesta['MUN']}")
else:
    st.markdown('<div class="section-title">Datos del nuevo proyecto</div>', unsafe_allow_html=True)
    st.markdown('<div class="small-note">Completa solo lo que conozcas. Los campos vacíos no penalizan.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        propuesta["DEPARTAMENTO"] = st.selectbox("Departamento", [""] + sorted(abiertas["DEPARTAMENTO"].dropna().unique().tolist()))
        propuesta["MUN"] = st.selectbox("Municipio", [""] + sorted(abiertas["MUN"].dropna().unique().tolist()))
        propuesta["UPZ/COMUNA"] = st.text_input("UPZ / Comuna")
        propuesta["ESTRATO"] = st.number_input("Estrato", min_value=1, max_value=6, value=None, step=1)
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
    propuesta["VU6M"] = numero_opcional("Venta proyectada (6 meses)", "venta_proyectada")

st.divider(); st.markdown('<div class="section-title">Importancia de variables</div>', unsafe_allow_html=True)
st.caption("Los pesos son iniciales; la cobertura indica qué tanto del peso pudo calcularse.")
with st.expander("Ajustar pesos del modelo"):
    grupos = {"Entorno y formato": ["ESTRATO", "AREA", "VT", "ET", "TR15MIN", "TIPO DE LOCAL", "GENERADOR", "PTH"], "Ubicación": ["DEPARTAMENTO", "MUN", "UPZ/COMUNA", "Y", "X"], "Desempeño": ["VU6M", "COSTO M2"], "Segmentación": ["SEG26", "TIE26"]}
    pesos = PESOS_BASE.copy()
    for grupo, variables in grupos.items():
        st.markdown(f"**{grupo}**"); gc = st.columns(4)
        for i, col in enumerate(variables):
            with gc[i % 4]: pesos[col] = st.slider(col, 0.0, 0.20, float(PESOS_BASE.get(col, .03)), .005, key=f"peso_{col}")

n = st.slider("Número de tiendas hermanas", 3, 20, 10)
if st.button("Encontrar tiendas hermanas", type="primary", use_container_width=True):
    ranking, detalle = rankear_tiendas(abiertas, propuesta, top_n=n, pesos=pesos)
    if ranking.empty: st.warning("Completa al menos una característica para calcular la similitud.")
    else:
        top = ranking.iloc[0]
        st.success(f"Se encontraron {len(ranking)} tiendas hermanas entre {len(abiertas):,} tiendas abiertas.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mejor coincidencia", str(top["NAME"]).strip()); m2.metric("Similitud", f"{top['SIMILITUD']:.1f}%")
        m3.metric("Cobertura", f"{top['COBERTURA']:.1f}%"); m4.metric("Variables", int(top["VARIABLES_USADAS"]))
        tab1, tab2, tab3, tab4 = st.tabs(["Ranking", "Desempeño", "Mapa", "Explicación"])
        with tab1:
            cols = [c for c in ["CR", "NAME", "SIMILITUD", "COBERTURA", "MUN", "AREA", "ESTRATO", "RENTA", "VENTAS_U6M", "MARGEN_U6M"] if c in ranking]
            vista = ranking[cols].rename(columns={"NAME":"Tienda", "SIMILITUD":"Similitud", "COBERTURA":"Cobertura", "MUN":"Municipio", "AREA":"Área", "VENTAS_U6M":"Ventas 6M", "MARGEN_U6M":"Margen 6M"})
            st.dataframe(vista, use_container_width=True, hide_index=True)
            st.download_button("Descargar ranking CSV", vista.to_csv(index=False).encode("utf-8-sig"), "tiendas_hermanas.csv", "text/csv")
        with tab2:
            if historico.empty: st.info("No hay históricos disponibles.")
            else:
                crs = ranking["CR"].astype(str).tolist(); h = historico[historico["CR"].astype(str).isin(crs)].copy()
                resumen_cols = [c for c in ["CR", "VENTAS_U6M", "VENTAS_UM", "MARGEN_U6M", "MARGEN_UM", "RENTA_U6M", "BATTING_U6M"] if c in ranking]
                if resumen_cols: st.dataframe(ranking[resumen_cols], use_container_width=True, hide_index=True)
                if not h.empty:
                    h["MES"] = h["MES"].astype(str); serie = h.groupby("MES", as_index=False)["VENTAS_HIST"].mean() if "VENTAS_HIST" in h else pd.DataFrame()
                    if not serie.empty: st.line_chart(serie.set_index("MES"))
        with tab3:
            puntos = ranking[["Y", "X", "NAME", "SIMILITUD", "CR"]].copy(); puntos["Y"] = pd.to_numeric(puntos["Y"], errors="coerce"); puntos["X"] = pd.to_numeric(puntos["X"], errors="coerce"); puntos = puntos.dropna(subset=["Y", "X"])
            fig = go.Figure()
            if not puntos.empty: fig.add_trace(go.Scattermapbox(lat=puntos["Y"], lon=puntos["X"], mode="markers+text", text=puntos["NAME"].astype(str).str.strip(), textposition="top center", marker=dict(size=12, color="#1B6B7A"), name="Tiendas hermanas"))
            py, px = propuesta.get("Y"), propuesta.get("X")
            if py is not None and px is not None and not pd.isna(py) and not pd.isna(px): fig.add_trace(go.Scattermapbox(lat=[py], lon=[px], mode="markers+text", text=["NUEVO PROYECTO"], marker=dict(size=18, color="#F97316", symbol="star"), name="Nuevo proyecto"))
            if len(fig.data):
                fig.update_layout(mapbox=dict(style="open-street-map", center=dict(lat=float(py) if py is not None and not pd.isna(py) else float(puntos.Y.mean()), lon=float(px) if px is not None and not pd.isna(px) else float(puntos.X.mean())), zoom=10), margin=dict(l=0,r=0,t=10,b=0), height=650); st.plotly_chart(fig, use_container_width=True)
            else: st.info("No hay coordenadas válidas para mostrar.")
        with tab4:
            st.markdown(f"**{str(top['NAME']).strip()} ({top['CR']})** obtuvo **{top['SIMILITUD']:.1f}%** de similitud con **{int(top['VARIABLES_USADAS'])} variables** y **{top['COBERTURA']:.1f}%** de cobertura ponderada.")
            d = detalle.iloc[0].drop(labels=["SIMILITUD"], errors="ignore").sort_values().head(10)
            st.caption("Distancia baja significa mayor coincidencia."); st.dataframe(pd.DataFrame({"Variable": d.index, "Distancia (%)": d.values}), use_container_width=True, hide_index=True)

with st.expander("Calidad de datos"):
    st.write({"Registros disponibles": len(book), "Tiendas abiertas": len(abiertas), "Tiendas con desempeño": len(resumen), "Registros históricos": len(historico), "Tiendas sin desempeño": int(abiertas["VENTAS_U6M"].isna().sum()) if "VENTAS_U6M" in abiertas else "no cargado"})
    st.dataframe(abiertas.head(50), use_container_width=True, hide_index=True)
