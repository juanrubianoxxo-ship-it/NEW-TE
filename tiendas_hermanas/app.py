import sys
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
from similitud import (cargar_abiertas, rankear_tiendas, VARIABLES_NUMERICAS,
                       VARIABLES_CATEGORICAS, PESOS_BASE)

st.set_page_config(page_title="Tiendas hermanas", page_icon="🏪", layout="wide")

@st.cache_data
def leer_excel(uploaded, local_path):
    source = uploaded if uploaded is not None else local_path
    return pd.read_excel(source, sheet_name="JUN")


def formato_num(v):
    if pd.isna(v):
        return "Sin dato"
    return f"{v:,.0f}" if isinstance(v, (int, float, np.integer, np.floating)) else str(v)


def numero_opcional(label, key, step=1.0, help_text=None):
    texto = st.text_input(label, key=key, help=help_text,
                          placeholder="Dejar vacío si no se conoce")
    if not texto.strip():
        return None
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        st.warning(f"{label}: escribe un número válido o déjalo vacío.")
        return None

st.title("Buscador de tiendas hermanas")
st.caption("MVP: compara una nueva propuesta con tiendas ABIERTAS de la hoja JUN.")

with st.sidebar:
    st.header("Fuente de datos")
    archivo = st.file_uploader("Cargar un Excel actualizado", type=["xlsx"])
    ruta_local = ROOT / "data" / "Book.xlsx"
    st.info("La aplicación usa exclusivamente la hoja JUN y filtra ESTADO = ABIERTA.")

try:
    raw = leer_excel(archivo, str(ruta_local))
    abiertas = cargar_abiertas(raw)
except Exception as exc:
    st.error(f"No se pudo leer la hoja JUN: {exc}")
    st.stop()

st.sidebar.success(f"{len(abiertas):,} tiendas abiertas disponibles")

with st.sidebar.expander("Variables consideradas", expanded=False):
    st.write("**Numéricas:** " + ", ".join(VARIABLES_NUMERICAS))
    st.write("**Categóricas:** " + ", ".join(VARIABLES_CATEGORICAS))
    st.write("Se excluyen CR, NAME, ARRENDADOR, ZONA, FECHA APE, DIAS OP y MESOP.")

modo = st.radio("¿Cómo quieres definir la referencia?", ["Nueva propuesta", "Tienda abierta existente"], horizontal=True)
propuesta = {}

if modo == "Tienda abierta existente":
    opciones = abiertas["CR"].astype(str) + " — " + abiertas["NAME"].astype(str)
    elegido = st.selectbox("Selecciona la tienda de referencia", opciones)
    cr = elegido.split(" — ", 1)[0]
    fila = abiertas[abiertas["CR"].astype(str).eq(cr)].iloc[0]
    propuesta = fila.to_dict()
    st.success(f"Referencia seleccionada: {fila['NAME']} ({fila['CR']})")
else:
    st.subheader("Características conocidas de la nueva tienda")
    st.caption("Completa los campos disponibles. Los campos vacíos no penalizan el cálculo.")
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
        propuesta["Y"] = numero_opcional("Latitud / Y", "y_nueva")
        propuesta["X"] = numero_opcional("Longitud / X", "x_nueva")
        propuesta["GENERADOR"] = st.selectbox("Generador", [""] + sorted(abiertas["GENERADOR"].dropna().unique().tolist()))
        propuesta["SEG26"] = st.selectbox("Segmento SEG26", [""] + sorted(abiertas["SEG26"].dropna().unique().tolist()))
        propuesta["PTH"] = st.selectbox("Potencial de hambre (PTH)", [""] + sorted(abiertas["PTH"].dropna().unique().tolist()))

st.divider()
with st.expander("Opcional: incluir indicadores actuales o proyectados", expanded=False):
    cols = st.columns(4)
    for i, col in enumerate(["TRAFICO UM", "TRU6", "TICKET UM", "TICKET U6M", "VENTAS OUM", "VU6M", "CONTRIBUCION UM", "CONTRIBUCION U6M", "MARGEN UM", "MARGEN U6M", "RENTA", "RU6M"]):
        with cols[i % 4]:
            propuesta[col] = numero_opcional(col, f"optional_{col}")

st.subheader("Pesos del modelo")
st.caption("Son pesos iniciales de negocio. Se pueden calibrar cuando el equipo valide los resultados.")
with st.expander("Ajustar pesos", expanded=False):
    grupos = {"Entorno y formato": ["ESTRATO", "AREA", "VT", "ET", "TR15MIN", "TIPO DE LOCAL", "GENERADOR", "PTH"],
              "Ubicación": ["DEPARTAMENTO", "MUN", "UPZ/COMUNA", "Y", "X"],
              "Desempeño": ["TRAFICO UM", "TRU6", "TICKET UM", "TICKET U6M", "VENTAS OUM", "VU6M", "CONTRIBUCION UM", "CONTRIBUCION U6M", "MARGEN UM", "MARGEN U6M", "RENTA", "RU6M", "COSTO M2"],
              "Segmentación": ["SEG26", "TIE26"]}
    pesos = PESOS_BASE.copy()
    for grupo, variables in grupos.items():
        st.markdown(f"**{grupo}**")
        gc = st.columns(4)
        for i, col in enumerate(variables):
            with gc[i % 4]:
                pesos[col] = st.slider(col, 0.0, 0.20, float(PESOS_BASE.get(col, 0.03)), 0.005, key=f"peso_{col}")

n = st.slider("Número de resultados", 3, 20, 10)
if st.button("Buscar tiendas hermanas", type="primary", use_container_width=True):
    ranking, detalle = rankear_tiendas(abiertas, propuesta, top_n=n, pesos=pesos)
    if ranking.empty:
        st.warning("Completa al menos una característica para calcular similitud.")
    else:
        st.success(f"Se encontraron {len(ranking)} tiendas similares entre {len(abiertas):,} tiendas abiertas.")
        vista = ranking[[c for c in ["CR", "NAME", "SIMILITUD", "MUN", "UPZ/COMUNA", "AREA", "ESTRATO", "TRAFICO UM", "VU6M", "MARGEN U6M", "RENTA", "TIPO DE LOCAL", "PTH"] if c in ranking.columns]].copy()
        st.dataframe(vista, use_container_width=True, hide_index=True)
        st.download_button("Descargar ranking CSV", vista.to_csv(index=False).encode("utf-8-sig"), "tiendas_hermanas.csv", "text/csv")

        st.subheader("Explicación de la primera tienda")
        primera = ranking.iloc[0]
        st.write(f"**{primera['NAME']} ({primera['CR']})** obtuvo **{primera['SIMILITUD']:.1f}%** de similitud usando {int(primera['VARIABLES_USADAS'])} variables disponibles.")
        d = detalle.iloc[0].drop(labels=["SIMILITUD"], errors="ignore").sort_values().head(8)
        st.caption("Menor distancia = mayor coincidencia. Las variables mostradas son las que más coincidieron.")
        st.dataframe(pd.DataFrame({"Variable": d.index, "Distancia (%)": d.values}), use_container_width=True, hide_index=True)

        if "Y" in ranking and "X" in ranking:
            mapa = ranking[["Y", "X", "NAME", "SIMILITUD"]].dropna().rename(columns={"Y": "lat", "X": "lon"})
            if not mapa.empty:
                st.subheader("Ubicación de las tiendas hermanas")
                st.map(mapa[["lat", "lon"]], size=100)

with st.expander("Vista de control de datos abiertos"):
    st.dataframe(abiertas.head(50), use_container_width=True, hide_index=True)
    st.caption("La información de CR, NAME y los resultados debe mantenerse en un repositorio privado si contiene datos sensibles.")
