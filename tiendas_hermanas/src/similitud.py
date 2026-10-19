import numpy as np
import pandas as pd

VARIABLES_NUMERICAS = [
    "ESTRATO", "AREA", "VT", "ET", "TR15MIN", "Y", "X", "TRAFICO UM", "TRU6",
    "TICKET UM", "TICKET U6M", "VENTAS OUM", "VU6M", "CONTRIBUCION UM", "CONTRIBUCION U6M",
    "MARGEN UM", "MARGEN U6M", "RENTA", "RU6M", "COSTO M2"
]
VARIABLES_CATEGORICAS = ["DEPARTAMENTO", "MUN", "UPZ/COMUNA", "TIPO DE LOCAL", "GENERADOR", "SEG26", "TIE26", "PTH"]
PESOS_BASE = {
    "ESTRATO": .06, "AREA": .10, "VT": .08, "ET": .08, "TR15MIN": .08, "Y": .02, "X": .02,
    "TRAFICO UM": .06, "TRU6": .06, "TICKET UM": .04, "TICKET U6M": .04, "VENTAS OUM": .06,
    "VU6M": .07, "CONTRIBUCION UM": .04, "CONTRIBUCION U6M": .04, "MARGEN UM": .04,
    "MARGEN U6M": .05, "RENTA": .03, "RU6M": .03, "COSTO M2": .03, "DEPARTAMENTO": .025,
    "MUN": .05, "UPZ/COMUNA": .04, "TIPO DE LOCAL": .04, "GENERADOR": .03, "SEG26": .03,
    "TIE26": .03, "PTH": .025,
}


def limpiar_monetarias(df):
    out = df.copy()
    monetarias = ["TICKET UM", "TICKET U6M", "VENTAS OUM", "VU6M", "CONTRIBUCION UM", "CONTRIBUCION U6M", "MARGEN UM", "MARGEN U6M", "RENTA", "RU6M"]
    for col in monetarias:
        if col in out:
            if out[col].dtype == "object":
                out[col] = out[col].astype(str).str.replace(r"[^0-9.\-]", "", regex=True).replace({"": np.nan, "nan": np.nan}).astype(float)
            else:
                out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in VARIABLES_NUMERICAS:
        if col in out and col not in monetarias:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in VARIABLES_CATEGORICAS:
        if col in out:
            out[col] = out[col].fillna("Sin dato").astype(str).str.strip()
    return out


def cargar_abiertas(df):
    out = limpiar_monetarias(df)
    if "ESTADO" not in out or "CR" not in out:
        raise ValueError("Book debe contener las columnas CR y ESTADO")
    out["ESTADO"] = out["ESTADO"].fillna("").astype(str).str.strip().str.upper()
    out["CR"] = out["CR"].astype(str).str.strip()
    return out[out["ESTADO"].eq("ABIERTA")].copy()


def _normalizar_cr(df):
    out = df.copy().rename(columns={df.columns[0]: "CR"})
    out["CR"] = out["CR"].astype(str).str.strip()
    return out[~out["CR"].isin(["", "nan", "None", "Etiquetas de fila"])].copy()


def _leer_resumen(path, hoja, sufijo):
    raw = _normalizar_cr(pd.read_excel(path, sheet_name=hoja, header=3))
    mapa = {"Trafico Prom. Tienda": f"TRAFICO_{sufijo}", "Ticket Contable": f"TICKET_{sufijo}", "$ Ventas Operativas Prom. Tienda": f"VENTAS_{sufijo}", "$ Contribución Directa Prom. Tienda": f"CONTRIBUCION_{sufijo}", "$ Margen Neto Prom. Tienda": f"MARGEN_{sufijo}", "$ Rentas Prom. Tienda": f"RENTA_{sufijo}", "% Cumplimiento al Batting": f"BATTING_{sufijo}"}
    raw = raw.rename(columns=mapa)
    keep = ["CR"] + [c for c in mapa.values() if c in raw]
    out = raw[keep].drop_duplicates("CR")
    for c in keep[1:]: out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def _leer_historico(path, hoja, metrica):
    raw = pd.read_excel(path, sheet_name=hoja, header=None)
    if raw.shape[0] < 5: return pd.DataFrame(columns=["CR", "MES", metrica])
    meses = raw.iloc[3, 1:].tolist()
    data = raw.iloc[4:, :len(meses) + 1].copy().rename(columns={0: "CR"})
    data = _normalizar_cr(data)
    data.columns = ["CR"] + [str(x).strip() if pd.notna(x) else f"col_{i}" for i, x in enumerate(meses)]
    long = data.melt(id_vars="CR", var_name="MES", value_name=metrica)
    long[metrica] = pd.to_numeric(long[metrica], errors="coerce")
    return long.dropna(subset=[metrica])


def cargar_ventas(path):
    xls = pd.ExcelFile(path)
    requeridas = {"BD U6M", "HISTORICO VENTAS", "HISTORICO CON"}
    faltantes = requeridas - set(xls.sheet_names)
    if faltantes: raise ValueError(f"Faltan hojas de LibroVentas: {', '.join(sorted(faltantes))}")
    hoja_mes = "BD M" if "BD M" in xls.sheet_names else "BD UM"
    resumen = _leer_resumen(path, "BD U6M", "U6M").merge(_leer_resumen(path, hoja_mes, "M"), on="CR", how="outer")
    hist = _leer_historico(path, "HISTORICO VENTAS", "VENTAS_HIST").merge(_leer_historico(path, "HISTORICO CON", "CONTRIBUCION_HIST"), on=["CR", "MES"], how="outer")
    return resumen, hist


def enriquecer_book(book, resumen):
    out = book.copy(); out["CR"] = out["CR"].astype(str).str.strip()
    return out.merge(resumen, on="CR", how="left", validate="many_to_one")


def valor_vacio(valor):
    if valor is None: return True
    if isinstance(valor, str): return not valor.strip()
    return bool(pd.isna(valor))


def _dist_num(a, b, escala):
    if pd.isna(a) or pd.isna(b) or escala == 0 or pd.isna(escala): return np.nan
    return min(abs(float(a) - float(b)) / float(escala), 1.0)


def _dist_cat(a, b):
    if pd.isna(a) or pd.isna(b) or str(a) == "Sin dato" or str(b) == "Sin dato": return np.nan
    return 0.0 if str(a).strip().casefold() == str(b).strip().casefold() else 1.0


def rankear_tiendas(df, propuesta, top_n=10, pesos=None):
    base = df.copy(); pesos = pesos or PESOS_BASE; contribuciones = pd.DataFrame(index=base.index); disponibles = {}
    for col in VARIABLES_NUMERICAS:
        if col not in base or col not in propuesta or valor_vacio(propuesta[col]): continue
        escala = base[col].quantile(.90) - base[col].quantile(.10)
        if pd.isna(escala) or escala == 0: escala = base[col].std()
        if pd.isna(escala) or escala == 0: continue
        contribuciones[col] = base[col].apply(lambda x: _dist_num(x, propuesta[col], escala)); disponibles[col] = pesos.get(col, 0.0)
    for col in VARIABLES_CATEGORICAS:
        if col not in base or col not in propuesta or valor_vacio(propuesta[col]): continue
        contribuciones[col] = base[col].apply(lambda x: _dist_cat(x, propuesta[col])); disponibles[col] = pesos.get(col, 0.0)
    if not disponibles: return pd.DataFrame(), pd.DataFrame()
    w = pd.Series(disponibles, dtype=float); weighted = contribuciones.mul(w, axis=1)
    denominador = (~contribuciones.isna()).mul(w, axis=1).sum(axis=1)
    distancia = weighted.sum(axis=1, skipna=True).div(denominador.replace(0, np.nan))
    out = base.copy(); out["DISTANCIA"] = distancia; out["SIMILITUD"] = ((1 - distancia).clip(0, 1) * 100).round(1)
    out["VARIABLES_USADAS"] = contribuciones.notna().sum(axis=1)
    out["COBERTURA"] = ((~contribuciones.isna()).mul(w, axis=1).sum(axis=1) / w.sum() * 100).round(1)
    out = out.sort_values(["SIMILITUD", "VU6M"], ascending=[False, False]).head(top_n)
    detalle = contribuciones.loc[out.index].copy()
    for col in detalle.columns: detalle[col] = (detalle[col] * 100).round(1)
    detalle["SIMILITUD"] = out["SIMILITUD"]
    return out.reset_index(drop=True), detalle.reset_index(drop=True)
