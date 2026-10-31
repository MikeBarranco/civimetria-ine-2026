"""
03_enriquece.py

Cruza la tabla de participacion por municipio con dos fuentes del Censo 2020:
- CONAPO, indice de marginacion 2020 y sus componentes (educacion, vivienda,
  ingreso y tamano de localidad).
- INEGI, principales resultados por localidad (ITER), renglon de total
  municipal: grado promedio de escolaridad, poblacion en hogares indigenas,
  poblacion que habla lengua indigena y poblacion afromexicana. Cubren la
  escolaridad y el referente indigena y afrodescendiente que menciona el reto.

Importante: la clave de municipio del INE (MPIOCVE) NO es la clave del INEGI.
En 21 estados la numeracion es distinta (por ejemplo, en Colima la clave 06001
del INE es Colima y la del INEGI es Armeria). Cruzar por clave pegaria los datos
de un municipio a otro. Por eso el cruce se hace por entidad y nombre
normalizado (sin acentos, mayusculas y sin signos), mas una tabla de
equivalencias revisada a mano para los nombres que se escriben distinto en cada
fuente. Los que aun asi no empatan son municipios creados despues del Censo
2020, que no tienen dato censal y se dejan como faltantes.

Uso:
    python src/03_enriquece.py
"""
import sys
import unicodedata
import zipfile
import pandas as pd
from comun import CRUDOS, PROCESADOS

CONAPO = CRUDOS / "CONAPO_IMM_2020.xlsx"
ITER = CRUDOS / "INEGI_ITER_2020.zip"

MAPA = {
    "POB_TOT": "poblacion_2020",
    "ANALF": "pct_analfabeta",
    "SBASC": "pct_sin_educacion_basica",
    "PL.5000": "pct_localidades_menores_5mil",
    "PO2SM": "pct_ingreso_hasta_2sm",
    "IM_2020": "indice_marginacion",
    "GM_2020": "grado_marginacion",
    "IMN_2020": "marginacion_normalizada",
}
VALOR = list(MAPA.values())

# Clave INE -> clave INEGI para municipios cuyo nombre se escribe distinto en
# cada fuente. Revisado uno por uno; en los Mixtepec de Oaxaca, que se repiten de
# nombre, se confirmo con la poblacion (lista nominal del INE frente a POB_TOT).
EQUIVALENCIAS = {
    "04006": "04006",  # Hopelchen (errata en el INE: "Hopelche}en")
    "07038": "07039",  # Huitiupan
    "10006": "10006",  # Simon Bolivar / General Simon Bolivar
    "13050": "13036",  # San Agustin Metzquititlan
    "17013": "17013",  # Jonacatepec / Jonacatepec de Leandro Valle
    "19010": "19010",  # Carmen / El Carmen
    "19014": "19014",  # Dr. Arroyo / Doctor Arroyo
    "19015": "19015",  # Dr. Coss / Doctor Coss
    "19016": "19016",  # Dr. Gonzalez / Doctor Gonzalez
    "19020": "19020",  # Gral. Bravo / General Bravo
    "19021": "19021",  # Gral. Escobedo / General Escobedo
    "19022": "19022",  # Gral. Teran / General Teran
    "19023": "19023",  # Gral. Trevino / General Trevino
    "19024": "19024",  # Gral. Zaragoza / General Zaragoza
    "19025": "19025",  # Gral. Zuazua / General Zuazua
    "20121": "20124",  # Heroica Villa de San Blas Atempa / San Blas Atempa
    "20208": "20208",  # San Juan Mixtepec, Dto. 08 (LN 6,170; poblacion 6,941)
    "20209": "20209",  # San Juan Mixtepec, Dto. 26 (LN 508; poblacion 607)
    "20316": "20318",  # San Pedro Mixtepec, Dto. 22 (LN 39,995; poblacion 49,780)
    "20317": "20319",  # San Pedro Mixtepec, Dto. 26 (LN 713; poblacion 972)
    "20332": "20334",  # Villa de Tututepec / ... de Melchor Ocampo
    "20562": "20038",  # Villa Hidalgo Yalalag / Villa Hidalgo
    "29037": "29037",  # Zitlaltepec / Ziltlaltepec de Trinidad Sanchez Santos
    "30010": "30009",  # Alto Lucero de Gutierrez Barrios
    "30047": "30045",  # Cosamaloapan / Cosamaloapan de Carpio
}


def lee_iter() -> pd.DataFrame:
    """Totales municipales del ITER 2020 (renglones con LOC = 0000 y MUN distinto de 000)."""
    cols = ["ENTIDAD", "MUN", "LOC", "POBTOT", "P_3YMAS", "P3YM_HLI", "PHOG_IND", "POB_AFRO", "GRAPROES"]
    with zipfile.ZipFile(ITER) as z:
        nombre = next(n for n in z.namelist() if "conjunto_de_datos" in n and n.lower().endswith(".csv"))
        df = pd.read_csv(z.open(nombre), dtype=str, usecols=cols)
    df = df[(df["LOC"] == "0000") & (df["MUN"] != "000")].copy()
    num = {c: pd.to_numeric(df[c], errors="coerce") for c in cols[3:]}
    return pd.DataFrame({
        "cve_inegi": df["ENTIDAD"] + df["MUN"],
        "grado_promedio_escolaridad": num["GRAPROES"],
        "pct_poblacion_indigena": 100 * num["PHOG_IND"] / num["POBTOT"],
        "pct_habla_lengua_indigena": 100 * num["P3YM_HLI"] / num["P_3YMAS"],
        "pct_afromexicana": 100 * num["POB_AFRO"] / num["POBTOT"],
    })


def normaliza(texto: str) -> str:
    """Quita acentos, pasa a mayusculas y deja solo letras y numeros."""
    if not isinstance(texto, str):
        return ""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return "".join(c for c in t.upper() if c.isalnum())


def main() -> int:
    part = pd.read_csv(PROCESADOS / "participacion_municipio.csv", dtype={"cve_muni": str})
    part["cve_muni"] = part["cve_muni"].str.zfill(5)
    part["cve_ent"] = part["cve_muni"].str[:2]
    part["nom_norm"] = part["municipio"].map(normaliza)

    con = pd.read_excel(CONAPO, sheet_name="IMM_2020", dtype={"CVE_MUN": str, "CVE_ENT": str})
    con["cve_inegi"] = con["CVE_MUN"].str.zfill(5)
    con["cve_ent"] = con["CVE_ENT"].str.zfill(2)
    con["nom_norm"] = con["NOM_MUN"].map(normaliza)
    for col in ["POB_TOT", "ANALF", "SBASC", "PL.5000", "PO2SM", "IM_2020", "IMN_2020"]:
        con[col] = pd.to_numeric(con[col], errors="coerce")
    con = con.rename(columns=MAPA)

    # 1) equivalencias revisadas a mano
    part["cve_inegi"] = part["cve_muni"].map(EQUIVALENCIAS)
    n_manual = int(part["cve_inegi"].notna().sum())

    # 2) entidad + nombre normalizado, solo cuando el nombre es unico en el estado
    unicos = ~part.duplicated(["cve_ent", "nom_norm"], keep=False)
    por_nombre = con[["cve_ent", "nom_norm", "cve_inegi"]].rename(columns={"cve_inegi": "cve_nombre"})
    part = part.merge(por_nombre, on=["cve_ent", "nom_norm"], how="left")
    usar = part["cve_inegi"].isna() & unicos & part["cve_nombre"].notna()
    part.loc[usar, "cve_inegi"] = part.loc[usar, "cve_nombre"]
    n_nombre = int(usar.sum())

    # Controles: cada clave INEGI se usa una sola vez y la entidad coincide
    asignadas = part["cve_inegi"].dropna()
    if asignadas.duplicated().any():
        raise SystemExit(f"Clave INEGI repetida: {asignadas[asignadas.duplicated()].tolist()}")
    if (asignadas.str[:2] != part.loc[asignadas.index, "cve_ent"]).any():
        raise SystemExit("Hay un cruce entre estados distintos")

    enr = part.merge(con[["cve_inegi", "NOM_MUN"] + VALOR], on="cve_inegi", how="left")
    enr = enr.rename(columns={"NOM_MUN": "municipio_conapo"})
    enr = enr.merge(lee_iter(), on="cve_inegi", how="left")

    # Validacion
    total = len(enr)
    con_dato = int(enr[VALOR[0]].notna().sum())
    sin_dato = enr[enr[VALOR[0]].isna()]
    distinta = int((enr["cve_inegi"].notna() & (enr["cve_inegi"] != enr["cve_muni"])).sum())
    print("== CRUCE CON CONAPO ==")
    print(f"municipios en la tabla: {total}")
    print(f"por nombre exacto (entidad + nombre): {n_nombre}")
    print(f"por equivalencia revisada a mano: {n_manual}")
    print(f"con dato de CONAPO: {con_dato} ({100 * con_dato / total:.1f}%)")
    print(f"con dato del INEGI (ITER): {int(enr['grado_promedio_escolaridad'].notna().sum())}")
    print(f"municipios cuya clave INE difiere de la del INEGI: {distinta}")
    print(f"sin dato (municipios creados despues del Censo 2020): {len(sin_dato)}")
    if len(sin_dato):
        print(sin_dato[["cve_muni", "entidad", "municipio"]].to_string(index=False))

    enr = enr.drop(columns=["cve_ent", "nom_norm", "cve_nombre"])
    salida = PROCESADOS / "municipio_enriquecido.csv"
    enr.to_csv(salida, index=False, encoding="utf-8")
    print("guardado en:", salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
