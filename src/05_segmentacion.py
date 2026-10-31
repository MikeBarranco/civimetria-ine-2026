"""
05_segmentacion.py

Agrupa los grupos ciudadanos (04) en perfiles segun su comportamiento de
participacion, y despues describe cada perfil con edad, sexo, escolaridad,
region e historial. Asi lo pide el reto: segmentar con los datos de
participacion y caracterizar con las demas variables.

Metodo:
- Variables del agrupamiento: nivel, brecha presidencial-intermedia y tendencia.
  Responden tres preguntas sobre como participa un grupo: cuanto, que tan parejo
  entre tipos de eleccion y hacia donde va. Se recortan a los percentiles 1 y 99
  y se estandarizan.
- k-means ponderado por lista nominal: cada grupo pesa segun las personas que
  tiene, para que los perfiles describan personas y no grupos chicos.
- Numero de perfiles: se comparan k = 3 a 7 con silueta, Calinski-Harabasz y
  Davies-Bouldin (sobre una muestra de 10 mil grupos tomada en proporcion a su
  tamano) y con estabilidad por remuestreo. La tabla queda en
  resultados/tablas/eleccion_k.csv y la decision se explica en K_FINAL.
- Los nombres se asignan con reglas fijas (ver REGLAS_NOMBRE en comun.py).

Uso:
    python src/05_segmentacion.py
"""
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)
from comun import (ANIOS, EDADES, FEATURES, PERFILES, PROCESADOS, SEXO, TABLAS,
                   kmeans, matriz, nombra, promedio)

SEMILLA = 42
MUESTRA = 10_000
REMUESTREOS = 30
# k = 3 queda fuera del rango de 4 a 6 que pide el reto. k = 4 tiene una silueta
# un poco mayor, pero junta en un solo perfil a quienes votan en presidenciales y
# faltan en intermedias con quienes casi no votan en ninguna, que piden estrategias
# distintas. k = 5 los separa y es igual o mas estable en el remuestreo. Asi quedan
# los tres comportamientos clasicos de la literatura (constantes, intermitentes,
# ocasionales) mas dos que solo se ven con historial: grupos cuya participacion va
# en ascenso y grupos cuya participacion va en descenso.
K_FINAL = 5


def metricas_k(X: np.ndarray, w: np.ndarray) -> pd.DataFrame:
    rng = np.random.default_rng(SEMILLA)
    muestra = rng.choice(len(X), MUESTRA, replace=False, p=w / w.sum())
    filas = []
    for k in range(3, 8):
        etiq = kmeans(X, w, k, SEMILLA, n_init=20).labels_
        aris = []
        for b in range(REMUESTREOS):
            idx = rng.choice(len(X), len(X), replace=True)
            aris.append(adjusted_rand_score(etiq, kmeans(X[idx], w[idx], k, b).predict(X)))
        Xm, em = X[muestra], etiq[muestra]
        filas.append({"k": k, "silueta": silhouette_score(Xm, em),
                      "calinski_harabasz": calinski_harabasz_score(Xm, em),
                      "davies_bouldin": davies_bouldin_score(Xm, em),
                      "estabilidad_ari_media": np.mean(aris), "estabilidad_ari_min": np.min(aris)})
        print(f"  k={k} listo", flush=True)
    return pd.DataFrame(filas)


def resumen_perfil(g: pd.DataFrame, total: float) -> dict:
    personas = g["lista_nominal"].sum()
    fila = {"personas": int(personas), "pct_personas": 100 * personas / total,
            "grupos": len(g), "municipios_presentes": g["cve_muni"].nunique()}
    for c in FEATURES + ["part_presidencial", "part_intermedia"] + [f"part_{a}" for a in ANIOS]:
        fila[c] = promedio(g, c)
    fila["pct_hombres"] = 100 * g.loc[g["sexo"] == "0", "lista_nominal"].sum() / personas
    for e in EDADES:
        fila[f"pct_{e}"] = 100 * g.loc[g["grupo_edad"] == e, "lista_nominal"].sum() / personas
    for c in ["pct_urbano", "pct_localidades_menores_5mil", "pct_sin_educacion_basica",
              "grado_promedio_escolaridad", "pct_poblacion_indigena", "pct_afromexicana"]:
        fila[c] = promedio(g, c)
    fila["votos_recuperables_intermedia"] = int((g["lista_nominal"] * g["brecha"].clip(lower=0) / 100).sum())
    fila["no_votarian_intermedia"] = int((g["lista_nominal"] * (100 - g["part_intermedia"]) / 100).sum())
    ent = g.groupby("entidad")["lista_nominal"].sum().sort_values(ascending=False)
    fila["entidades_principales"] = "; ".join(f"{e} {100 * v / personas:.0f}%" for e, v in ent.head(4).items())
    return fila


def main() -> int:
    TABLAS.mkdir(parents=True, exist_ok=True)
    grupos = pd.read_csv(PROCESADOS / "grupos_ciudadanos.csv", dtype={"cve_muni": str, "sexo": str})
    df = grupos[grupos["en_modelo"]].reset_index(drop=True)
    X, w = matriz(df), df["lista_nominal"].to_numpy(dtype=float)

    print("== ELECCION DEL NUMERO DE PERFILES ==")
    met = metricas_k(X, w)
    met.to_csv(TABLAS / "eleccion_k.csv", index=False, encoding="utf-8")
    print(met.round(3).to_string(index=False))

    km = kmeans(X, w, K_FINAL, SEMILLA, n_init=50)
    df["perfil"] = nombra(df, km.labels_)
    # Claridad: 1 - (distancia al centro propio / distancia al segundo centro mas cercano).
    # Cerca de 0, el grupo esta en la frontera entre dos perfiles.
    nombre_de = dict(zip(km.labels_, df["perfil"]))
    dist = km.transform(X)
    orden = np.argsort(dist, axis=1)
    filas = np.arange(len(dist))
    df["perfil_cercano"] = [nombre_de[i] for i in orden[:, 1]]
    df["claridad"] = 1 - dist[filas, orden[:, 0]] / dist[filas, orden[:, 1]]
    frontera = df.loc[df["claridad"] < 0.1, "lista_nominal"].sum() / df["lista_nominal"].sum()

    total = df["lista_nominal"].sum()
    resumen = pd.DataFrame([{"perfil": p, **resumen_perfil(df[df["perfil"] == p], total)} for p in PERFILES])
    mayoria = df.groupby(["cve_muni", "perfil"])["lista_nominal"].sum().unstack().idxmax(axis=1)
    resumen["municipios_donde_es_mayoria"] = resumen["perfil"].map(mayoria.value_counts()).fillna(0).astype(int)

    # A que perfil pertenece cada grupo de sexo y edad (porcentaje de sus personas)
    reparto = df.pivot_table(index=["sexo", "grupo_edad"], columns="perfil", values="lista_nominal",
                             aggfunc="sum").reindex(columns=PERFILES)
    reparto = 100 * reparto.div(reparto.sum(axis=1), axis=0)
    reparto.index = reparto.index.set_levels([SEXO[s] for s in reparto.index.levels[0]], level=0)

    print("\n== PERFILES ==")
    ver = ["perfil", "personas", "pct_personas", "part_presidencial", "part_intermedia", "brecha",
           "tendencia", "pct_hombres", "pct_18-24", "pct_25-29", "pct_60+", "pct_localidades_menores_5mil",
           "grado_promedio_escolaridad", "pct_poblacion_indigena", "pct_afromexicana",
           "municipios_donde_es_mayoria"]
    print(resumen[ver].round(1).to_string(index=False))
    print("\n== REPARTO DE CADA SEXO Y EDAD ENTRE PERFILES (%) ==")
    print(reparto.round(0).to_string())
    print(f"\npersonas en grupos de frontera entre dos perfiles (claridad < 0.1): {100 * frontera:.1f}%")

    df[["cve_muni", "sexo", "grupo_edad", "lista_nominal", "perfil", "perfil_cercano", "claridad"]].to_csv(
        PROCESADOS / "grupos_perfiles.csv", index=False, encoding="utf-8")
    resumen.to_csv(PROCESADOS / "perfiles_resumen.csv", index=False, encoding="utf-8")
    reparto.round(1).to_csv(TABLAS / "reparto_sexo_edad.csv", encoding="utf-8")
    print("\nguardado: grupos_perfiles.csv, perfiles_resumen.csv, tablas/eleccion_k.csv, "
          "tablas/reparto_sexo_edad.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
