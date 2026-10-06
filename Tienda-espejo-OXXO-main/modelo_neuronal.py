"""Modelo neuronal auto-supervisado para encontrar tiendas espejo.

No requiere etiquetas de pares similares. Aprende un embedding comprimido de
las tiendas mediante un autoencoder denoising y compara la propuesta nueva en
ese espacio. La regularización, el ruido de entrada y la parada temprana son
importantes porque la base disponible es pequeña.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = [
    "ESTRATO", "AREA", "VIVIENDAS", "EMPLEOS", "VENTAS_OU6M", "TRAFICO_U6M"
]
CATEGORICAL_FEATURES = ["ZONA", "TIPO DE LOCAL", "GENERADOR", "MUN"]


def _as_clean_frame(df: pd.DataFrame, nueva_tienda: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye una matriz consistente y evita NaN/columnas inexistentes."""
    candidates = df.copy()
    proposal = pd.DataFrame([nueva_tienda])
    for col in NUMERIC_FEATURES:
        if col not in candidates:
            candidates[col] = 0.0
        if col not in proposal:
            proposal[col] = 0.0
        candidates[col] = pd.to_numeric(candidates[col], errors="coerce").fillna(0.0)
        proposal[col] = pd.to_numeric(proposal[col], errors="coerce").fillna(0.0)
    for col in CATEGORICAL_FEATURES:
        if col not in candidates:
            candidates[col] = "SIN_DATO"
        if col not in proposal:
            proposal[col] = "SIN_DATO"
        candidates[col] = candidates[col].fillna("SIN_DATO").astype(str)
        proposal[col] = proposal[col].fillna("SIN_DATO").astype(str)
    return candidates, proposal


def _encoder():
    try:
        one_hot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # scikit-learn < 1.2
        one_hot = OneHotEncoder(handle_unknown="ignore", sparse=False)
    return ColumnTransformer(
        [("num", StandardScaler(), NUMERIC_FEATURES),
         ("cat", one_hot, CATEGORICAL_FEATURES)],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


def _hidden_embedding(model: MLPRegressor, X: np.ndarray) -> np.ndarray:
    """Obtiene la salida de la capa latente del MLP de sklearn."""
    return _relu(X @ model.coefs_[0] + model.intercepts_[0])


def calcular_tienda_espejo_neuronal(
    df: pd.DataFrame,
    nueva_tienda: dict,
    pesos: dict | None = None,
    random_state: int = 42,
) -> tuple[pd.DataFrame | None, str | None]:
    """Encuentra vecinos usando un autoencoder denoising con embedding latente.

    El segmento se usa como filtro de comparabilidad, no como variable que la
    red pueda memorizar. Las ponderaciones se aplican antes del entrenamiento.
    La similitud se calcula con una escala robusta de distancias, no con el
    mínimo/máximo del lote, para que el score sea estable entre consultas.
    """
    if "SEG26" not in df.columns or "SEG26" not in nueva_tienda:
        return None, "Falta la columna SEG26 para filtrar el segmento."
    filtrado = df[df["SEG26"].astype(str) == str(nueva_tienda["SEG26"])].copy()
    if filtrado.empty:
        return None, "No se encontraron tiendas en el mismo segmento."

    candidatos, propuesta = _as_clean_frame(filtrado, nueva_tienda)
    preprocessor = _encoder()
    X = preprocessor.fit_transform(candidatos[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
    X_new = preprocessor.transform(propuesta[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
    X = np.asarray(X, dtype=np.float64)
    X_new = np.asarray(X_new, dtype=np.float64)

    # Pesos por bloque: el peso numérico aplica a una variable y el categórico
    # a todas sus categorías one-hot. El segmento ya fue filtrado.
    default_weights = {
        "ESTRATO": .08, "AREA": .08, "VIVIENDAS": .06, "EMPLEOS": .06,
        "VENTAS_OU6M": .12, "TRAFICO_U6M": .10, "ZONA": .10,
        "TIPO DE LOCAL": .07, "GENERADOR": .07, "MUN": .06,
    }
    weights = {**default_weights, **(pesos or {})}
    feature_weights = np.array([weights.get(c, 0.05) for c in NUMERIC_FEATURES], dtype=float)
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_sizes = [len(cats) for cats in cat_encoder.categories_]
    expanded = np.concatenate([feature_weights, *[
        np.repeat(weights.get(c, 0.05), size) for c, size in zip(CATEGORICAL_FEATURES, cat_sizes)
    ]])
    expanded = np.sqrt(np.maximum(expanded, 1e-8))
    X *= expanded
    X_new *= expanded

    n_samples, n_features = X.shape
    latent_dim = int(max(3, min(12, n_features // 3 if n_features >= 9 else 3)))
    # Con pocas filas no se separa validación para no dejar una muestra inútil.
    use_validation = n_samples >= 30
    model = MLPRegressor(
        hidden_layer_sizes=(latent_dim,),
        activation="relu",
        solver="adam",
        alpha=0.02,                 # L2: reduce pesos memorísticos
        # Con validación, el lote debe caber también en el subconjunto de
        # entrenamiento; así evitamos advertencias y gradientes inestables.
        batch_size=min(16, max(4, n_samples // 4)),
        learning_rate_init=0.0015,
        max_iter=2400,
        early_stopping=use_validation,
        validation_fraction=0.20 if use_validation else 0.10,
        n_iter_no_change=70,
        tol=1e-6,
        random_state=random_state,
    )

    # Ruido denoising determinista para mejorar generalización sin inventar
    # observaciones: el target sigue siendo la representación limpia original.
    rng = np.random.default_rng(random_state)
    X_noisy = X + rng.normal(0, 0.025, size=X.shape)
    model.fit(X_noisy, X)

    embedding = _hidden_embedding(model, X)
    embedding_new = _hidden_embedding(model, X_new)
    distances = np.linalg.norm(embedding - embedding_new, axis=1)
    scale = float(np.percentile(distances, 75))
    if not np.isfinite(scale) or scale <= 1e-9:
        scale = 1.0
    scores = 100.0 * np.exp(-distances / scale)
    scores = np.clip(scores, 0.0, 100.0)

    resultado = filtrado.copy()
    resultado["DISTANCIA"] = distances
    resultado["SIMILITUD_NEURONAL"] = scores
    # La antigüedad se incorpora como confianza, no como sustituto de la
    # similitud: una tienda nueva no debe dominar el Top por casualidad.
    if "ANTIGUEDAD_MESES" in resultado.columns:
        edad = pd.to_numeric(resultado["ANTIGUEDAD_MESES"], errors="coerce").fillna(0).clip(lower=0)
        edad_max = float(edad.max())
        if edad_max > 0:
            madurez = np.sqrt(edad / edad_max)
            resultado["SIMILITUD"] = scores * (0.92 + 0.08 * madurez.to_numpy())
        else:
            resultado["SIMILITUD"] = scores
    else:
        resultado["SIMILITUD"] = scores
    resultado = resultado.sort_values(["SIMILITUD", "DISTANCIA"], ascending=[False, True])
    resultado.attrs["modelo_info"] = {
        "tipo": "Autoencoder neuronal denoising",
        "muestras": n_samples,
        "features": n_features,
        "dim_latente": latent_dim,
        "iteraciones": int(getattr(model, "n_iter_", 0)),
        "convergencia": int(getattr(model, "n_iter_", 0)) < 2400,
        "error_reconstruccion": float(getattr(model, "loss_", np.nan)),
        "validacion": use_validation,
        "alpha_l2": 0.02,
        "ruido_entrenamiento": 0.025,
    }
    return resultado, None
