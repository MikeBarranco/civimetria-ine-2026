"""Rutas, constantes y funciones que comparten los scripts del analisis."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

RAIZ = Path(__file__).resolve().parents[1]
CRUDOS = RAIZ / "datos" / "crudos"
PROCESADOS = RAIZ / "datos" / "procesados"
TABLAS = RAIZ / "resultados" / "tablas"
FIGURAS = RAIZ / "resultados" / "figuras"

ANIOS = [2009, 2012, 2015, 2018, 2021, 2024]
PRESIDENCIALES = [2012, 2018, 2024]
INTERMEDIAS = [2009, 2015, 2021]
EDADES = ["18-24", "25-29", "30-39", "40-49", "50-59", "60+"]
SEXO = {"0": "Hombres", "1": "Mujeres"}


def tendencia_ajustada(Y) -> np.ndarray:
    """Cambio estimado de 2009 a 2024 en cada fila de Y, descontando el efecto presidencial.

    Y tiene una columna por anio de ANIOS y NaN donde no hay dato. Por fila se ajusta
    participacion = a + b * (anio - 2009) / 15 + c * presidencial y se devuelve b.
    Hace falta al menos 4 anios con dato y de los dos tipos de eleccion.
    """
    t = (np.array(ANIOS) - 2009) / 15
    p = np.isin(ANIOS, PRESIDENCIALES).astype(float)
    salida = np.full(len(Y), np.nan)
    for i, y in enumerate(np.asarray(Y, dtype=float)):
        ok = ~np.isnan(y)
        if ok.sum() >= 4 and 0 < p[ok].sum() < ok.sum():
            X = np.column_stack([np.ones(ok.sum()), t[ok], p[ok]])
            salida[i] = np.linalg.lstsq(X, y[ok], rcond=None)[0][1]
    return salida


# Segmentacion de grupos ciudadanos (la usan 05_segmentacion.py y 07_robustez.py)
FEATURES = ["nivel", "brecha", "tendencia"]
PERFILES = ["Intermitentes", "Ocasionales", "En descenso", "En ascenso", "Constantes"]
# Cada perfil se nombra por el rasgo que lo define, en este orden y entre los grupos
# que aun no tienen nombre: el de mayor brecha, el de tendencia mas negativa, el de
# tendencia mas positiva, y de los dos restantes el de mayor y el de menor nivel.
REGLAS_NOMBRE = [("Intermitentes", "brecha", "max"), ("En descenso", "tendencia", "min"),
                 ("En ascenso", "tendencia", "max"), ("Constantes", "nivel", "max"),
                 ("Ocasionales", "nivel", "min")]


def promedio(df, col: str) -> float:
    """Promedio de una columna ponderado por lista nominal, sin contar faltantes."""
    ok = df[col].notna()
    return float(np.average(df.loc[ok, col], weights=df.loc[ok, "lista_nominal"]))


def matriz(df, features=FEATURES, recorte=True) -> np.ndarray:
    """Variables recortadas a los percentiles 1 y 99 y estandarizadas con pesos."""
    X = df[features]
    if recorte:
        X = X.apply(lambda s: s.clip(s.quantile(0.01), s.quantile(0.99)))
    w = df["lista_nominal"].to_numpy()
    media = np.average(X, axis=0, weights=w)
    desv = np.sqrt(np.average((X - media) ** 2, axis=0, weights=w))
    return ((X - media) / desv).to_numpy()


def kmeans(X, w, k: int, semilla: int, n_init: int = 10):
    return KMeans(n_clusters=k, n_init=n_init, random_state=semilla).fit(X, sample_weight=w)


def nombra(df, etiquetas) -> np.ndarray:
    """Convierte las etiquetas de k-means en nombres de perfil segun REGLAS_NOMBRE."""
    d = df.assign(_k=etiquetas)
    libres = d.groupby("_k").apply(lambda g: pd.Series({c: promedio(g, c) for c in FEATURES}),
                                   include_groups=False)
    if len(libres) != len(REGLAS_NOMBRE):
        raise SystemExit(f"Hay {len(libres)} grupos y {len(REGLAS_NOMBRE)} reglas de nombre")
    nombres = {}
    for nombre, col, modo in REGLAS_NOMBRE:
        g = libres[col].idxmax() if modo == "max" else libres[col].idxmin()
        nombres[g] = nombre
        libres = libres.drop(index=g)
    return d["_k"].map(nombres).to_numpy()
