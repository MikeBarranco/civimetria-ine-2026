"""
06_focalizacion_municipal.py

Pasa los perfiles al territorio para decidir donde actuar: por municipio, cuantas
personas hay de cada perfil, cuantos votos se podrian recuperar en una eleccion
intermedia y un indice de prioridad.

- votos_recuperables_intermedia: suma, sobre los grupos ciudadanos del municipio,
  de lista nominal x brecha presidencial-intermedia. Estima cuantas personas
  votan en presidenciales y no en intermedias. La siguiente eleccion federal
  (junio de 2027) es intermedia.
- prioridad (0 a 100): deficit de participacion en intermedias (40%), tamano de
  la lista nominal (30%) y brecha presidencial-intermedia (30%), cada uno en rango
  percentil para que ningun municipio extremo domine. Los pesos son un criterio
  del equipo; 07_robustez.py muestra que el orden casi no cambia si se mueven.
  Solo se calcula para municipios con historial suficiente (ver 02).

Uso:
    python src/06_focalizacion_municipal.py
"""
import sys
import pandas as pd
from comun import PERFILES, PROCESADOS

PESOS = {"deficit": 0.4, "tamano": 0.3, "recuperable": 0.3}


def main() -> int:
    mun = pd.read_csv(PROCESADOS / "municipio_enriquecido.csv", dtype={"cve_muni": str, "cve_inegi": str})
    grupos = pd.read_csv(PROCESADOS / "grupos_ciudadanos.csv", dtype={"cve_muni": str, "sexo": str})
    perf = pd.read_csv(PROCESADOS / "grupos_perfiles.csv", dtype={"cve_muni": str, "sexo": str})

    personas = perf.pivot_table(index="cve_muni", columns="perfil", values="lista_nominal",
                                aggfunc="sum", fill_value=0).reindex(columns=PERFILES, fill_value=0)
    pct = 100 * personas.div(personas.sum(axis=1), axis=0)
    df = mun.set_index("cve_muni")
    df = df.join(personas.add_prefix("personas_")).join(pct.add_prefix("pct_"))
    df["perfil_mayoritario"] = personas.idxmax(axis=1)

    g = grupos[grupos["en_modelo"]]
    df["votos_recuperables_intermedia"] = (
        (g["lista_nominal"] * g["brecha"].clip(lower=0) / 100).groupby(g["cve_muni"]).sum().round())
    df["no_votarian_intermedia"] = (df["lista_nominal"] * (100 - df["part_intermedia"]) / 100).round()

    con = df["historial_suficiente"]
    comp = pd.DataFrame({
        "deficit": (100 - df.loc[con, "part_intermedia"]).rank(pct=True),
        "tamano": df.loc[con, "lista_nominal"].rank(pct=True),
        "recuperable": df.loc[con, "brecha_pres_inter"].clip(lower=0).rank(pct=True),
    })
    prioridad = 100 * sum(PESOS[c] * comp[c] for c in PESOS)
    df.loc[con, "rank_prioridad"] = prioridad.rank(ascending=False, method="first")
    df.loc[con, "prioridad"] = prioridad.round(1)

    df = df.reset_index().sort_values("rank_prioridad", na_position="last")
    df.to_csv(PROCESADOS / "municipio_focalizacion.csv", index=False, encoding="utf-8")

    total = df["votos_recuperables_intermedia"].sum()
    acum = df.sort_values("votos_recuperables_intermedia", ascending=False)["votos_recuperables_intermedia"].cumsum()
    print("== FOCALIZACION MUNICIPAL ==")
    print(f"votos recuperables en intermedias (estimado): {total / 1e6:.1f} millones")
    for n in (50, 100, 200):
        print(f"  los {n} municipios con mas votos recuperables concentran {100 * acum.iloc[n - 1] / total:.1f}%")
    print(f"municipios sin prioridad (historial insuficiente): {int((~con).sum())}")
    print("\nperfil mayoritario por municipio:", df["perfil_mayoritario"].value_counts().to_dict())
    print("\n15 municipios con mas prioridad:")
    print(df.head(15)[["entidad", "municipio", "lista_nominal", "part_intermedia", "brecha_pres_inter",
                       "prioridad", "votos_recuperables_intermedia", "perfil_mayoritario"]]
          .round(1).to_string(index=False))
    print("\nguardado en:", PROCESADOS / "municipio_focalizacion.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
