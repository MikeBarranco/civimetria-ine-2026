"""
04_grupos_ciudadanos.py

Construye la unidad que se segmenta: el grupo ciudadano, es decir, las personas
de un mismo sexo y grupo de edad que viven en un mismo municipio (segun su
credencial). Ejemplo: mujeres de 25 a 29 anios de Tijuana. Cada grupo tiene su
tamano (lista nominal) y su participacion en las seis elecciones federales.

Por que esta unidad: el reto pide tipos de ciudadania segun su comportamiento de
participacion, caracterizados por edad, sexo, escolaridad, region e historial.
El CCPC no tiene datos de personas, pero si de estos grupos, que son lo mas
cercano a personas que permite la fuente sin perder el territorio.

Para cada grupo se calcula, solo con anios validos (ver 02):
- participacion presidencial (2012, 2018, 2024) e intermedia (2009, 2015, 2021);
- nivel: promedio de las dos;
- brecha: presidencial menos intermedia (que tanto depende de la eleccion);
- tendencia: cambio de 2009 a 2024 sin el efecto presidencial.

Entran al modelo los grupos con al menos dos elecciones de cada tipo y 50 personas
o mas en la lista nominal; por debajo de eso un porcentaje cambia mucho con
unos cuantos votos. El sexo no binario (solo 2024, muy pocos registros) no forma
grupos propios.

Uso:
    python src/04_grupos_ciudadanos.py
"""
import sys
import pandas as pd
from comun import ANIOS, INTERMEDIAS, PRESIDENCIALES, PROCESADOS, SEXO, tendencia_ajustada

TAMANO_MINIMO = 50


def main() -> int:
    cel = pd.read_csv(PROCESADOS / "participacion_municipio_sexo_edad.csv",
                      dtype={"cve_muni": str, "sexo": str})
    cel = cel[cel["anio_valido"] & cel["sexo"].isin(SEXO)]
    cel["part"] = 100 * cel["SV"] / (cel["SV"] + cel["NV"])
    clave = ["cve_muni", "sexo", "grupo_edad"]

    g = cel.pivot_table(index=clave, columns="anio", values="part").reindex(columns=ANIOS)
    # tamano: lista nominal del anio valido mas reciente
    g["lista_nominal"] = cel.sort_values("anio").groupby(clave)["LN"].last()
    g["part_presidencial"] = g[PRESIDENCIALES].mean(axis=1)
    g["part_intermedia"] = g[INTERMEDIAS].mean(axis=1)
    g["nivel"] = (g["part_presidencial"] + g["part_intermedia"]) / 2
    g["brecha"] = g["part_presidencial"] - g["part_intermedia"]
    g["tendencia"] = tendencia_ajustada(g[ANIOS])
    g["en_modelo"] = ((g[PRESIDENCIALES].notna().sum(axis=1) >= 2)
                      & (g[INTERMEDIAS].notna().sum(axis=1) >= 2)
                      & (g["lista_nominal"] >= TAMANO_MINIMO))
    g = g.rename(columns={a: f"part_{a}" for a in ANIOS}).reset_index()

    mun = pd.read_csv(PROCESADOS / "municipio_enriquecido.csv", dtype={"cve_muni": str})
    contexto = ["cve_muni", "entidad", "municipio", "pct_urbano", "pct_localidades_menores_5mil",
                "pct_sin_educacion_basica", "grado_promedio_escolaridad", "pct_poblacion_indigena",
                "pct_afromexicana", "grado_marginacion"]
    g = g.merge(mun[contexto], on="cve_muni", how="left")
    g.to_csv(PROCESADOS / "grupos_ciudadanos.csv", index=False, encoding="utf-8")

    dentro = g[g["en_modelo"]]
    print("== GRUPOS CIUDADANOS ==")
    print(f"grupos: {len(g):,}; en el modelo: {len(dentro):,}")
    print(f"personas en el modelo: {dentro['lista_nominal'].sum():,} "
          f"({100 * dentro['lista_nominal'].sum() / g['lista_nominal'].sum():.1f}% de la lista nominal)")
    print(dentro[["nivel", "brecha", "tendencia"]].describe().round(1).to_string())
    print("guardado en:", PROCESADOS / "grupos_ciudadanos.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
