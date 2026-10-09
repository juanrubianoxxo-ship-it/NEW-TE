import numpy as np
import pandas as pd

VARIABLES_NUMERICAS = [
    "ESTRATO", "AREA", "VT", "ET", "TR15MIN", "Y", "X",
    "TRAFICO UM", "TRU6", "TICKET UM", "TICKET U6M", "VENTAS OUM",
    "VU6M", "CONTRIBUCION UM", "CONTRIBUCION U6M", "MARGEN UM",
    "MARGEN U6M", "RENTA", "RU6M", "COSTO M2"
]
VARIABLES_CATEGORICAS = [
    "DEPARTAMENTO", "MUN", "UPZ/COMUNA", "TIPO DE LOCAL", "GENERADOR",
    "SEG26", "TIE26", "PTH"
]

PESOS_BASE = {
    "ESTRATO": 0.06, "AREA": 0.10, "VT": 0.08, "ET": 0.08, "TR15MIN": 0.08,
    "Y": 0.02, "X": 0.02, "TRAFICO UM": 0.06, "TRU6": 0.06,
    "TICKET UM": 0.04, "TICKET U6M": 0.04, "VENTAS OUM": 0.06,
    "VU6M": 0.07, "CONTRIBUCION UM": 0.04, "CONTRIBUCION U6M": 0.04,
    "MARGEN UM": 0.04, "MARGEN U6M": 0.05, "RENTA": 0.03,
    "RU6M": 0.03, "COSTO M2": 0.03,
    "DEPARTAMENTO": 0.025, "MUN": 0.05, "UPZ/COMUNA": 0.04,
    "TIPO DE LOCAL": 0.04, "GENERADOR": 0.03, "SEG26": 0.03,
    "TIE26": 0.03, "PTH": 0.025,
}


def limpiar_monetarias(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    monetarias = ["TICKET UM", "TICKET U6M", "VENTAS OUM", "VU6M", "CONTRIBUCION UM",
                  "CONTRIBUCION U6M", "MARGEN UM", "MARGEN U6M", "RENTA", "RU6M"]
    for col in monetarias:
        if col in out.columns:
            if out[col].dtype == "object":
                out[col] = (out[col].astype(str)
                    .str.replace(r"[^0-9.\-]", "", regex=True)
                    .replace({"": np.nan, "nan": np.nan})
                    .astype(float))
            else:
                out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in VARIABLES_NUMERICAS:
        if col in out.columns and col not in monetarias:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in VARIABLES_CATEGORICAS:
        if col in out.columns:
            out[col] = out[col].fillna("Sin dato").astype(str).str.strip()
    return out


def cargar_abiertas(df: pd.DataFrame) -> pd.DataFrame:
    out = limpiar_monetarias(df)
    out["ESTADO"] = out["ESTADO"].fillna("").astype(str).str.strip().str.upper()
    return out[out["ESTADO"].eq("ABIERTA")].copy()


def valor_vacio(valor):
    if valor is None:
        return True
    if isinstance(valor, str):
        return not valor.strip()
    return bool(pd.isna(valor))


def _dist_num(a, b, escala):
    if pd.isna(a) or pd.isna(b) or escala == 0 or pd.isna(escala):
        return np.nan
    return min(abs(float(a) - float(b)) / float(escala), 1.0)


def _dist_cat(a, b):
    if pd.isna(a) or pd.isna(b) or str(a) == "Sin dato" or str(b) == "Sin dato":
        return np.nan
    return 0.0 if str(a).strip().casefold() == str(b).strip().casefold() else 1.0


def rankear_tiendas(df: pd.DataFrame, propuesta: dict, top_n=10, pesos=None):
    """Calcula un ranking explicable: 0 = idéntica, 100 = máxima similitud."""
    base = df.copy()
    pesos = pesos or PESOS_BASE
    contribuciones = pd.DataFrame(index=base.index)
    disponibles = {}

    for col in VARIABLES_NUMERICAS:
        if col not in base.columns or col not in propuesta or valor_vacio(propuesta[col]):
            continue
        escala = base[col].quantile(0.90) - base[col].quantile(0.10)
        if pd.isna(escala) or escala == 0:
            escala = base[col].std()
        if pd.isna(escala) or escala == 0:
            continue
        contribuciones[col] = base[col].apply(lambda x: _dist_num(x, propuesta[col], escala))
        disponibles[col] = pesos.get(col, 0.0)

    for col in VARIABLES_CATEGORICAS:
        if col not in base.columns or col not in propuesta or valor_vacio(propuesta[col]):
            continue
        contribuciones[col] = base[col].apply(lambda x: _dist_cat(x, propuesta[col]))
        disponibles[col] = pesos.get(col, 0.0)

    if not disponibles:
        return pd.DataFrame(), pd.DataFrame()
    w = pd.Series(disponibles, dtype=float)
    weighted = contribuciones.mul(w, axis=1)
    denominador = (~contribuciones.isna()).mul(w, axis=1).sum(axis=1)
    distancia = weighted.sum(axis=1, skipna=True).div(denominador.replace(0, np.nan))

    out = base.copy()
    out["DISTANCIA"] = distancia
    out["SIMILITUD"] = ((1 - distancia).clip(0, 1) * 100).round(1)
    out["VARIABLES_USADAS"] = contribuciones.notna().sum(axis=1)
    out = out.sort_values(["SIMILITUD", "VU6M"], ascending=[False, False]).head(top_n)
    detalle = contribuciones.loc[out.index].copy()
    for col in detalle.columns:
        detalle[col] = (detalle[col] * 100).round(1)
    detalle["SIMILITUD"] = out["SIMILITUD"]
    return out.reset_index(drop=True), detalle.reset_index(drop=True)
