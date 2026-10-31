"""
10_verificaciones.py

Revisa al final de cada corrida que los resultados cuadren. Si alguna prueba
falla, el script termina con error y ejecutar_todo.py lo reporta.

Uso:
    python src/10_verificaciones.py
"""
import sys
import numpy as np
import pandas as pd
from openpyxl import load_workbook
from comun import FEATURES, FIGURAS, PERFILES, PROCESADOS, TABLAS

REF_ESTUDIOS_INE = {2012: 62.1, 2018: 62.4, 2024: 59.7}
GRAFICAS = ["participacion_nacional.png", "edad_por_eleccion.png", "eleccion_k.png", "mapa_perfiles.png",
            "historial_perfiles.png", "quien_es_cada_perfil.png", "composicion_perfiles.png",
            "concentracion_municipal.png", "validacion_judicial.png"]


def main() -> int:
    leer = {"dtype": {"cve_muni": str, "sexo": str, "cve_inegi": str}}
    cel = pd.read_csv(PROCESADOS / "participacion_municipio_sexo_edad.csv", **leer)
    largo = pd.read_csv(PROCESADOS / "participacion_municipio_largo.csv", **leer)
    enr = pd.read_csv(PROCESADOS / "municipio_enriquecido.csv", **leer)
    grupos = pd.read_csv(PROCESADOS / "grupos_ciudadanos.csv", **leer)
    perf = pd.read_csv(PROCESADOS / "grupos_perfiles.csv", **leer)
    res = pd.read_csv(PROCESADOS / "perfiles_resumen.csv")
    mun = pd.read_csv(PROCESADOS / "municipio_focalizacion.csv", **leer)
    reparto = pd.read_csv(TABLAS / "reparto_sexo_edad.csv", index_col=[0, 1])
    pj = pd.read_csv(PROCESADOS / "participacion_judicial2025_sexo_edad.csv", **leer)

    nac = largo.groupby("anio")[["SV", "NV"]].sum()
    nac = 100 * nac["SV"] / (nac["SV"] + nac["NV"])
    modelo = grupos[grupos["en_modelo"]]
    asignadas = enr["cve_inegi"].dropna()
    j = pj[pj["anio_valido"]]

    pruebas = [
        ("LN = SV + NV + NS en todas las celdas", (cel["LN"] == cel["SV"] + cel["NV"] + cel["NS"]).all()),
        ("sin conteos negativos", (cel[["LN", "SV", "NV", "NS"]] >= 0).all().all()),
        ("sin celdas duplicadas", not cel.duplicated(["cve_muni", "sexo", "grupo_edad", "anio"]).any()),
        ("participacion nacional igual a los estudios del INE (+-0.1)",
         all(abs(nac[a] - v) <= 0.1 for a, v in REF_ESTUDIOS_INE.items())),
        ("cada clave INEGI se usa una sola vez", not asignadas.duplicated().any()),
        ("cruce INE-INEGI siempre dentro de la misma entidad",
         (asignadas.str[:2] == enr.loc[asignadas.index, "cve_muni"].str[:2]).all()),
        ("grupos del modelo sin faltantes en sus variables", modelo[FEATURES].notna().all().all()),
        ("cada grupo del modelo tiene exactamente un perfil",
         len(perf) == len(modelo) and not perf.duplicated(["cve_muni", "sexo", "grupo_edad"]).any()),
        ("hay cinco perfiles con los nombres esperados", sorted(res["perfil"]) == sorted(PERFILES)),
        ("los perfiles suman 100% de las personas del modelo", abs(res["pct_personas"].sum() - 100) < 1e-6),
        ("cada sexo y edad se reparte al 100% entre perfiles", np.allclose(reparto.sum(axis=1), 100, atol=0.5)),
        ("claridad entre 0 y 1", perf["claridad"].between(0, 1).all()),
        ("indice de prioridad entre 0 y 100", mun["prioridad"].dropna().between(0, 100).all()),
        ("lugar de prioridad sin empates", not mun["rank_prioridad"].dropna().duplicated().any()),
        ("votos recuperables municipales = suma de sus grupos",
         abs(mun["votos_recuperables_intermedia"].sum()
             - (modelo["lista_nominal"] * modelo["brecha"].clip(lower=0) / 100).sum()) < len(mun)),
        ("eleccion judicial 2025 entre 12.5% y 13.5% (rango reportado por el INE)",
         12.5 <= 100 * j["SV"].sum() / (j["SV"].sum() + j["NV"].sum()) <= 13.5),
        ("existen todas las graficas", all((FIGURAS / f).exists() for f in GRAFICAS)),
        ("el Excel tiene sus 5 hojas",
         len(load_workbook(TABLAS / "civimetria_tablero_municipal.xlsx", read_only=True).sheetnames) == 5),
    ]
    fallas = 0
    for nombre, ok in pruebas:
        print(f"  {'PASA ' if ok else 'FALLA'}  {nombre}")
        fallas += not ok
    print(f"\n{len(pruebas) - fallas} de {len(pruebas)} verificaciones pasan")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
