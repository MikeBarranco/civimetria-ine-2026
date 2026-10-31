"""
07_robustez.py

Pruebas para saber si los perfiles y el indice de prioridad dependen de
decisiones arbitrarias. Todas comparan contra el resultado de 05 y 06.

1. Remuestreo (bootstrap): se ajusta el modelo con muestras al azar de grupos y se
   mide, por perfil, cuanto se conserva (indice de Jaccard; arriba de 0.75 se
   considera estable). Se reporta la mediana y en cuantos remuestreos es estable.
2. Semillas: el modelo con 10 semillas distintas.
3. Otro metodo: agrupamiento jerarquico de Ward sobre una muestra de 6 mil grupos.
4. Otras decisiones del analisis, cada una por separado:
   - grupos de 200 personas o mas en lugar de 50;
   - sin recortar valores extremos;
   - usar participacion presidencial e intermedia en lugar de nivel y brecha.
   Se mide el porcentaje de personas que queda en el mismo perfil.
5. Pesos del indice de prioridad municipal: todas las combinaciones de 0.1 en 0.1.
6. Validacion temporal: con lo observado de 2009 a 2018, se mide que tanto se
   anticipa lo que pasa en 2021 (una eleccion que esas variables no vieron).
7. Validacion externa: la eleccion judicial de 2025 no entra al modelo. Se mide si
   los perfiles, hechos con 2009-2024, ordenan bien quien voto en ella.

Salidas en resultados/tablas: robustez_perfiles.csv, robustez_decisiones.csv,
robustez_pesos.csv, validacion_temporal.csv, validacion_judicial2025.csv.

Uso:
    python src/07_robustez.py
"""
import itertools
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score
from comun import PERFILES, PROCESADOS, TABLAS, kmeans, matriz, nombra

SEMILLA = 42
REMUESTREOS = 30
K = len(PERFILES)
TOP = 100


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    union = np.logical_or(a, b).sum()
    return np.logical_and(a, b).sum() / union if union else 0.0


def correlacion(a, b, w) -> float:
    """Correlacion de Pearson ponderada."""
    a, b = a - np.average(a, weights=w), b - np.average(b, weights=w)
    return float(np.sum(w * a * b) / np.sqrt(np.sum(w * a * a) * np.sum(w * b * b)))


def validacion_temporal(grupos: pd.DataFrame) -> pd.DataFrame:
    """Variables calculadas solo con 2009-2018 frente a lo observado en 2021."""
    cols = ["part_2009", "part_2012", "part_2015", "part_2018", "part_2021"]
    d = grupos[grupos[cols].notna().all(axis=1) & (grupos["lista_nominal"] >= 50)]
    pres = d[["part_2012", "part_2018"]].mean(axis=1)
    inter = d[["part_2009", "part_2015"]].mean(axis=1)
    w = d["lista_nominal"].to_numpy(dtype=float)
    pruebas = [
        ("nivel 2009-2018 frente a participacion 2021", (pres + inter) / 2, d["part_2021"]),
        ("participacion intermedia 2009 y 2015 frente a 2021", inter, d["part_2021"]),
        ("brecha 2009-2018 frente a la caida de 2018 a 2021", pres - inter, d["part_2018"] - d["part_2021"]),
    ]
    return pd.DataFrame([{"prueba": n, "correlacion": correlacion(x.to_numpy(), y.to_numpy(), w)}
                         for n, x, y in pruebas])


def validacion_judicial(todos: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Participacion en la eleccion judicial 2025 por perfil y que tanto la explica el perfil."""
    clave = ["cve_muni", "sexo", "grupo_edad"]
    pj = pd.read_csv(PROCESADOS / "participacion_judicial2025_sexo_edad.csv", dtype={"cve_muni": str, "sexo": str})
    pj = pj[pj["anio_valido"]].merge(todos.reset_index()[clave + ["perfil", "nivel", "part_intermedia"]], on=clave)
    pj = pj[pj["perfil"].notna() & (pj["SV"] + pj["NV"] > 0)]
    pj["part_pj"] = 100 * pj["SV"] / (pj["SV"] + pj["NV"])
    w = (pj["SV"] + pj["NV"]).to_numpy(dtype=float)
    por_perfil = pj.groupby("perfil")[["SV", "NV"]].sum()
    tabla = pd.DataFrame({"participacion_judicial_2025": 100 * por_perfil["SV"] / por_perfil.sum(axis=1)})
    tabla = tabla.reindex(PERFILES).reset_index()
    media = pj["perfil"].map(tabla.set_index("perfil")["participacion_judicial_2025"])
    total = np.average(pj["part_pj"], weights=w)
    r2 = 1 - np.sum(w * (pj["part_pj"] - media) ** 2) / np.sum(w * (pj["part_pj"] - total) ** 2)
    datos = {"grupos": len(pj), "participacion_nacional": 100 * pj["SV"].sum() / w.sum(),
             "r2_perfil": r2,
             "r_nivel": correlacion(pj["nivel"].to_numpy(), pj["part_pj"].to_numpy(), w),
             "r_intermedia": correlacion(pj["part_intermedia"].to_numpy(), pj["part_pj"].to_numpy(), w)}
    return tabla, datos


def coincidencia(df: pd.DataFrame, nuevo: pd.Series) -> float:
    """Porcentaje de personas que quedan en el mismo perfil."""
    comun = df.index.intersection(nuevo.index)
    igual = df.loc[comun, "perfil"] == nuevo.loc[comun]
    return 100 * df.loc[comun, "lista_nominal"][igual].sum() / df.loc[comun, "lista_nominal"].sum()


def main() -> int:
    grupos = pd.read_csv(PROCESADOS / "grupos_ciudadanos.csv", dtype={"cve_muni": str, "sexo": str})
    perf = pd.read_csv(PROCESADOS / "grupos_perfiles.csv", dtype={"cve_muni": str, "sexo": str})
    clave = ["cve_muni", "sexo", "grupo_edad"]
    todos = grupos.merge(perf[clave + ["perfil"]], on=clave, how="left").set_index(clave)
    df = todos[todos["en_modelo"]]
    X, w = matriz(df), df["lista_nominal"].to_numpy(dtype=float)
    etiq = df["perfil"].to_numpy()
    rng = np.random.default_rng(SEMILLA)

    print("== 1. REMUESTREO ==")
    jac = {p: [] for p in PERFILES}
    aris = []
    for b in range(REMUESTREOS):
        idx = rng.choice(len(X), len(X), replace=True)
        nuevo = kmeans(X[idx], w[idx], K, b).predict(X)
        aris.append(adjusted_rand_score(etiq, nuevo))
        for p in PERFILES:
            jac[p].append(max(jaccard(etiq == p, nuevo == g) for g in range(K)))
    tabla = pd.DataFrame({"perfil": PERFILES,
                          "jaccard_mediana": [np.median(jac[p]) for p in PERFILES],
                          "pct_remuestreos_estable": [100 * np.mean(np.array(jac[p]) >= 0.75) for p in PERFILES]})
    print(tabla.round(3).to_string(index=False))
    print(f"ARI mediana {np.median(aris):.3f}; {np.sum(np.array(aris) >= 0.75)} de {REMUESTREOS} "
          f"remuestreos recuperan la misma particion (ARI >= 0.75)")

    sem = [adjusted_rand_score(etiq, kmeans(X, w, K, s).labels_) for s in range(10)]
    print(f"\n== 2. SEMILLAS == ARI medio {np.mean(sem):.3f}, minimo {np.min(sem):.3f}")

    muestra = rng.choice(len(X), 6000, replace=False, p=w / w.sum())
    ward = AgglomerativeClustering(n_clusters=K, linkage="ward").fit_predict(X[muestra])
    cruce = pd.crosstab(etiq[muestra], ward)
    tabla["coincidencia_ward"] = [100 * cruce.loc[p].max() / cruce.loc[p].sum() for p in PERFILES]
    a_ward = adjusted_rand_score(etiq[muestra], ward)
    print(f"\n== 3. WARD == ARI {a_ward:.3f}; coincidencia por perfil (%):")
    print(tabla[["perfil", "coincidencia_ward"]].round(0).to_string(index=False))
    tabla.to_csv(TABLAS / "robustez_perfiles.csv", index=False, encoding="utf-8")

    print("\n== 4. OTRAS DECISIONES ==")
    variantes = {
        "grupos de 200 personas o mas": (df[df["lista_nominal"] >= 200], {}),
        "sin recortar extremos": (df, {"recorte": False}),
        "presidencial e intermedia en vez de nivel y brecha":
            (df, {"features": ["part_presidencial", "part_intermedia", "tendencia"]}),
    }
    filas = [{"prueba": "remuestreo, ARI mediana", "valor": np.median(aris)},
             {"prueba": "remuestreo, % con ARI >= 0.75", "valor": 100 * np.mean(np.array(aris) >= 0.75)},
             {"prueba": "semillas, ARI minimo", "valor": np.min(sem)},
             {"prueba": "Ward, ARI", "valor": a_ward}]
    for nombre, (d, opciones) in variantes.items():
        Xv = matriz(d, **opciones)
        etiq_v = kmeans(Xv, d["lista_nominal"].to_numpy(dtype=float), K, SEMILLA, n_init=20).labels_
        pct = coincidencia(df, pd.Series(nombra(d, etiq_v), index=d.index))
        filas.append({"prueba": f"{nombre}, % de personas en el mismo perfil", "valor": pct})
        print(f"  {nombre}: {pct:.1f}% de las personas quedan en el mismo perfil")
    pd.DataFrame(filas).to_csv(TABLAS / "robustez_decisiones.csv", index=False, encoding="utf-8")

    print("\n== 5. PESOS DEL INDICE DE PRIORIDAD ==")
    mun = pd.read_csv(PROCESADOS / "municipio_focalizacion.csv", dtype={"cve_muni": str})
    mun = mun[mun["prioridad"].notna()]
    comp = pd.DataFrame({
        "deficit": (100 - mun["part_intermedia"]).rank(pct=True),
        "tamano": mun["lista_nominal"].rank(pct=True),
        "recuperable": mun["brecha_pres_inter"].clip(lower=0).rank(pct=True),
    })
    base = mun["prioridad"]
    top_base = set(base.nlargest(TOP).index)
    grid = [round(x, 1) for x in np.arange(0.1, 0.81, 0.1)]
    pesos = []
    for w1, w2 in itertools.product(grid, grid):
        w3 = round(1 - w1 - w2, 1)
        if w3 < 0.1:
            continue
        p = w1 * comp["deficit"] + w2 * comp["tamano"] + w3 * comp["recuperable"]
        pesos.append({"peso_deficit": w1, "peso_tamano": w2, "peso_recuperable": w3,
                      "spearman": spearmanr(base, p).correlation,
                      f"top{TOP}_conservados": len(top_base & set(p.nlargest(TOP).index))})
    pesos = pd.DataFrame(pesos)
    pesos.to_csv(TABLAS / "robustez_pesos.csv", index=False, encoding="utf-8")
    cerca = pesos[(pesos[["peso_deficit", "peso_tamano", "peso_recuperable"]] - [0.4, 0.3, 0.3])
                  .abs().max(axis=1) <= 0.1 + 1e-9]
    print(f"{len(pesos)} combinaciones: Spearman minimo {pesos['spearman'].min():.3f}, "
          f"mediana {pesos['spearman'].median():.3f}")
    print(f"a 0.1 o menos de los pesos elegidos ({len(cerca)}): Spearman minimo {cerca['spearman'].min():.3f}, "
          f"se conservan al menos {cerca[f'top{TOP}_conservados'].min()} de los {TOP} primeros")

    print("\n== 6. VALIDACION TEMPORAL (correlacion ponderada) ==")
    val = validacion_temporal(todos.reset_index())
    print(val.round(3).to_string(index=False))
    val.to_csv(TABLAS / "validacion_temporal.csv", index=False, encoding="utf-8")

    print("\n== 7. VALIDACION EXTERNA: ELECCION JUDICIAL 2025 ==")
    pj, datos = validacion_judicial(todos)
    print(pj.round(1).to_string(index=False))
    print(f"grupos: {datos['grupos']:,}; participacion: {datos['participacion_nacional']:.1f}%")
    print(f"el perfil explica {100 * datos['r2_perfil']:.0f}% de la variacion entre grupos; correlacion con "
          f"el nivel 2009-2024 {datos['r_nivel']:.2f}, con la participacion intermedia {datos['r_intermedia']:.2f}")
    pj.to_csv(TABLAS / "validacion_judicial2025.csv", index=False, encoding="utf-8")
    print("\nguardado en:", TABLAS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
