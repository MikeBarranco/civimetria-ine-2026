"""
02_construye_tabla_municipio.py

Lee los ZIP del CCPC (uno por anio) desde datos/crudos y construye cinco tablas:
- participacion_municipio_largo.csv: una fila por municipio y anio.
- participacion_municipio_sexo_edad.csv: una fila por municipio, anio, sexo y
  grupo de edad. Es la base de los grupos ciudadanos que se segmentan en 04 y 05.
- participacion_municipio.csv: una fila por municipio con su historial resumido.
- participacion_judicial2025_sexo_edad.csv: la eleccion judicial de 2025 con el
  mismo desglose. No entra al modelo; sirve para validarlo en 07.
- participacion_nacional_edad.csv: totales nacionales por eleccion, sexo y edad
  exacta (incluye 2025), para ver en que edad se gana o se pierde participacion.

Como se mide la participacion:
- En el CCPC cada registro de la lista nominal (LN) queda como SV (con marca de
  voto), NV (sin marca) o NS (no especificado: cuadernillo sin marcas o no
  disponible para su captura). LN = SV + NV + NS.
- Usamos participacion = SV / (SV + NV), es decir, solo sobre los registros con
  informacion. Es la formula del manual de la plataforma CCPC del INE
  ("% Participacion = Si votaron / (Si votaron + No votaron)"). Dividir entre LN
  contaria a los NS como si no hubieran votado, y los NS no se reparten parejo:
  hay municipios y anios con 10% a 99% de NS. Con SV / (SV + NV) la cifra
  nacional de 2012, 2018 y 2024 coincide con la que publican los estudios de
  participacion del INE.

Un municipio-anio se deja como faltante si:
- su cobertura, (SV + NV) / LN, es menor a 50%: lo observado ya no representa
  al municipio;
- su participacion es menor a 2%: todo aparece sin voto, senal de casillas no
  instaladas o no capturadas;
- su lista nominal es menor al 80% del promedio de la eleccion anterior y la
  siguiente. El CCPC 2012 trae 76.5 millones de registros frente a cerca de 79.4
  millones de la lista nominal oficial; en algunos municipios faltan secciones
  completas y la lista nominal se desploma ese anio para recuperarse despues.

Como se resume el historial (2009-2024):
- Las elecciones presidenciales (2012, 2018, 2024) siempre tienen mas
  participacion que las intermedias (2009, 2015, 2021). Para que un municipio con
  un anio faltante no salga sesgado, los promedios se calculan por separado para
  cada tipo de eleccion y luego se promedian entre si (promedio balanceado).
- La tendencia se estima con una regresion por municipio que separa el efecto de
  la eleccion presidencial del cambio en el tiempo. Asi no se confunde "subio"
  con "esta vez hubo eleccion presidencial".

Uso:
    python src/02_construye_tabla_municipio.py
"""
import io
import sys
import zipfile
import numpy as np
import pandas as pd
from comun import ANIOS, CRUDOS, EDADES, PRESIDENCIALES, PROCESADOS, tendencia_ajustada

COLS = ["EDOCVE", "EDONOM", "MPIOCVE", "MPIONOM", "TIPOSEC", "SEXO", "EDAD", "LN", "SV", "NV", "NS"]
CONTEOS = ["LN", "SV", "NV", "NS"]
CORTES_EDAD = [17, 24, 29, 39, 49, 59, 200]
COBERTURA_MINIMA = 50.0
PARTICIPACION_MINIMA = 2.0
CONTINUIDAD_MINIMA = 0.8
# Cifras publicadas, solo para validar. Las de los estudios de participacion del
# INE salen de los mismos cuadernillos; las de computos se calculan con actas e
# incluyen casillas especiales y voto en el extranjero, por eso son un poco mayores.
REF_ESTUDIOS_INE = {2012: 62.1, 2018: 62.4, 2024: 59.7}
REF_COMPUTOS = {2009: 44.8, 2021: 52.7}


def leer_estado(raw: bytes) -> pd.DataFrame:
    """Lee un CSV de estado probando codificacion y normaliza tipos."""
    df = None
    for enc in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str, usecols=COLS)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise ValueError("No se pudo leer el CSV")
    for c in CONTEOS + ["EDAD"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # clave INE de 5 digitos: estado(2) + municipio(3). No es la clave del INEGI (ver 03_enriquece.py)
    df["cve_muni"] = df["EDOCVE"].str.zfill(2) + df["MPIOCVE"].str.zfill(3)
    df["grupo_edad"] = pd.cut(df["EDAD"], CORTES_EDAD, labels=EDADES)
    return df


def tasa(sv, nv):
    """Participacion en porcentaje sobre registros con informacion."""
    den = sv + nv
    return np.where(den > 0, 100 * sv / den.where(den > 0, 1), np.nan)


def lee_zip(archivo: str, anio: int) -> dict:
    """Resume un ZIP del CCPC: celdas municipio-sexo-edad, LN por tipo de seccion,
    nombres de municipio y conteo nacional por sexo y edad exacta."""
    partes = {"celdas": [], "tipos": [], "nombres": [], "edades": []}
    with zipfile.ZipFile(CRUDOS / archivo) as z:
        for n in z.namelist():
            if not n.lower().endswith(".csv"):
                continue
            df = leer_estado(z.read(n))
            partes["celdas"].append(df.groupby(["cve_muni", "SEXO", "grupo_edad"], observed=True)[CONTEOS]
                                    .sum().reset_index())
            partes["tipos"].append(df.groupby(["cve_muni", "TIPOSEC"])["LN"].sum().reset_index())
            partes["nombres"].append(df.groupby("cve_muni")[["EDONOM", "MPIONOM"]].first().reset_index())
            partes["edades"].append(df.groupby(["SEXO", "EDAD"])[CONTEOS].sum().reset_index())
    salida = {}
    for clave, lista in partes.items():
        salida[clave] = pd.concat(lista, ignore_index=True)
        salida[clave]["anio"] = anio
    salida["edades"] = salida["edades"].groupby(["anio", "SEXO", "EDAD"], as_index=False)[CONTEOS].sum()
    return salida


def valida_judicial(celdas: pd.DataFrame) -> pd.DataFrame:
    """Eleccion judicial 2025 por municipio, sexo y grupo de edad. Solo se usa para validar."""
    mun = celdas.groupby("cve_muni")[CONTEOS].sum()
    valido = (100 * (mun["SV"] + mun["NV"]) / mun["LN"] >= COBERTURA_MINIMA) & (mun["SV"] > 0)
    celdas = celdas.assign(anio_valido=celdas["cve_muni"].map(valido))
    return celdas.rename(columns={"SEXO": "sexo"})


def construye_largo(celdas: pd.DataFrame, tipos: pd.DataFrame, nombres: pd.DataFrame) -> pd.DataFrame:
    """Una fila por municipio y anio, con participacion total y por grupo."""
    clave = ["cve_muni", "anio"]
    tot = celdas.groupby(clave)[CONTEOS].sum()
    tot["cobertura"] = 100 * (tot["SV"] + tot["NV"]) / tot["LN"]
    tot["participacion"] = tasa(tot["SV"], tot["NV"])
    ln = tot["LN"].unstack("anio")
    tot["continuidad_ln"] = (ln / ((ln.shift(1, axis=1) + ln.shift(-1, axis=1)) / 2)).stack()
    tot["anio_valido"] = ((tot["cobertura"] >= COBERTURA_MINIMA)
                          & (tot["participacion"] >= PARTICIPACION_MINIMA)
                          & ~(tot["continuidad_ln"] < CONTINUIDAD_MINIMA))

    def sub(mask, nombre):
        g = celdas[mask].groupby(clave)[["SV", "NV"]].sum()
        return pd.Series(tasa(g["SV"], g["NV"]), index=g.index, name=nombre)

    edad = celdas["grupo_edad"].astype(str)
    partes = [
        sub(edad.isin(["18-24", "25-29"]), "part_jovenes"),
        sub(celdas["SEXO"] == "1", "part_mujeres"),
        sub(celdas["SEXO"] == "0", "part_hombres"),
    ]
    largo = tot.join(partes)
    # los grupos solo valen si el anio del municipio es valido
    for c in ["participacion", "part_jovenes", "part_mujeres", "part_hombres"]:
        largo[c + "_valida"] = largo[c].where(largo["anio_valido"])

    t = tipos.pivot_table(index=clave, columns="TIPOSEC", values="LN", aggfunc="sum", fill_value=0)
    largo["pct_urbano"] = 100 * t.get("U", 0) / t.sum(axis=1)
    largo = largo.join(nombres.set_index(clave).rename(columns={"EDONOM": "entidad", "MPIONOM": "municipio"}))
    return largo.reset_index()


def promedio_balanceado(largo: pd.DataFrame, col: str) -> pd.Series:
    """Promedio de presidenciales y de intermedias de una columna, y luego el promedio de ambos."""
    d = largo[["cve_muni", "anio", col]].dropna()
    m = d.pivot_table(index="cve_muni", columns=d["anio"].isin(PRESIDENCIALES), values=col, aggfunc="mean")
    return (m.get(True) + m.get(False)) / 2


def construye_ancho(largo: pd.DataFrame) -> pd.DataFrame:
    part = largo.pivot_table(index="cve_muni", columns="anio", values="participacion_valida")
    part.columns = [f"part_{a}" for a in part.columns]
    part = part.reindex(index=sorted(largo["cve_muni"].unique()),
                        columns=[f"part_{a}" for a in ANIOS])

    # nombres, tamano y composicion del anio mas reciente valido
    validos = largo[largo["anio_valido"]].sort_values("anio")
    ultimo = validos.groupby("cve_muni").tail(1).set_index("cve_muni")
    ultimo_cualquiera = largo.sort_values("anio").groupby("cve_muni").tail(1).set_index("cve_muni")
    base = ultimo.reindex(part.index)
    faltan = base["entidad"].isna()
    base.loc[faltan] = ultimo_cualquiera.reindex(part.index)[faltan]
    tabla = base[["entidad", "municipio", "LN", "pct_urbano"]].rename(
        columns={"LN": "lista_nominal"}).join(part)

    cols_p = [f"part_{a}" for a in ANIOS if a in PRESIDENCIALES]
    cols_i = [f"part_{a}" for a in ANIOS if a not in PRESIDENCIALES]
    tabla["anios_con_dato"] = tabla[[f"part_{a}" for a in ANIOS]].notna().sum(axis=1)
    tabla["n_presidenciales"] = tabla[cols_p].notna().sum(axis=1)
    tabla["n_intermedias"] = tabla[cols_i].notna().sum(axis=1)
    # historial suficiente: al menos dos elecciones de cada tipo
    tabla["historial_suficiente"] = (tabla["n_presidenciales"] >= 2) & (tabla["n_intermedias"] >= 2)

    tabla["part_presidencial"] = tabla[cols_p].mean(axis=1)
    tabla["part_intermedia"] = tabla[cols_i].mean(axis=1)
    tabla["part_promedio"] = (tabla["part_presidencial"] + tabla["part_intermedia"]) / 2
    tabla["brecha_pres_inter"] = tabla["part_presidencial"] - tabla["part_intermedia"]
    tabla["tendencia"] = tendencia_ajustada(tabla[[f"part_{a}" for a in ANIOS]])

    for nombre in ["part_jovenes", "part_mujeres", "part_hombres"]:
        tabla[nombre] = promedio_balanceado(largo, nombre + "_valida")
    tabla.index.name = "cve_muni"
    return tabla.reset_index()


def main() -> int:
    PROCESADOS.mkdir(parents=True, exist_ok=True)
    print("Construyendo tablas por municipio...")
    archivos = {anio: f"CCPC{anio}.zip" for anio in ANIOS} | {2025: "CCPC_PJ2025.zip"}
    leidos = {}
    for anio, archivo in archivos.items():
        if not (CRUDOS / archivo).exists():
            raise SystemExit(f"Falta {archivo}. Corre primero 01_descarga_datos.py")
        print(f"  Procesando {archivo}...", flush=True)
        leidos[anio] = lee_zip(archivo, anio)
    celdas, tipos, nombres = (pd.concat([leidos[a][clave] for a in ANIOS], ignore_index=True)
                              for clave in ("celdas", "tipos", "nombres"))
    pd.concat([d["edades"] for d in leidos.values()]).rename(columns={"SEXO": "sexo", "EDAD": "edad"}).to_csv(
        PROCESADOS / "participacion_nacional_edad.csv", index=False, encoding="utf-8")

    largo = construye_largo(celdas, tipos, nombres)
    cols_largo = ["cve_muni", "anio", "entidad", "municipio", "LN", "SV", "NV", "NS", "cobertura",
                  "continuidad_ln", "anio_valido", "participacion_valida", "part_jovenes_valida",
                  "part_mujeres_valida", "part_hombres_valida", "pct_urbano"]
    largo[cols_largo].rename(columns={"LN": "lista_nominal", "participacion_valida": "participacion"}) \
        .to_csv(PROCESADOS / "participacion_municipio_largo.csv", index=False, encoding="utf-8")

    celdas = celdas.merge(largo[["cve_muni", "anio", "anio_valido"]], on=["cve_muni", "anio"])
    celdas.rename(columns={"SEXO": "sexo"}).to_csv(
        PROCESADOS / "participacion_municipio_sexo_edad.csv", index=False, encoding="utf-8")

    ancho = construye_ancho(largo)
    ancho.to_csv(PROCESADOS / "participacion_municipio.csv", index=False, encoding="utf-8")

    judicial = valida_judicial(leidos[2025]["celdas"].drop(columns="anio"))
    judicial.to_csv(PROCESADOS / "participacion_judicial2025_sexo_edad.csv", index=False, encoding="utf-8")

    # Validacion
    print("\n== VALIDACION ==")
    print("municipios en la tabla:", ancho["cve_muni"].nunique())
    nac = largo.groupby("anio")[["SV", "NV", "LN", "NS"]].sum()
    print("participacion nacional SV/(SV+NV) frente a cifras publicadas:")
    for a, f in nac.iterrows():
        p = 100 * f["SV"] / (f["SV"] + f["NV"])
        ref = "sin cifra de referencia"
        if a in REF_ESTUDIOS_INE:
            ref = f"estudio INE {REF_ESTUDIOS_INE[a]:.1f}%"
        elif a in REF_COMPUTOS:
            ref = f"computos {REF_COMPUTOS[a]:.1f}%"
        print(f"  {a}: {p:.1f}%  ({ref}; NS {100 * f['NS'] / f['LN']:.1f}% de la LN)")
    inval = largo[~largo["anio_valido"]]
    print(f"municipio-anio marcados como faltantes: {len(inval)} de {len(largo)}; por anio:",
          inval.groupby("anio").size().to_dict())
    print(f"  de ellos, por lista nominal incompleta: {int((largo['continuidad_ln'] < CONTINUIDAD_MINIMA).sum())}")
    print("lista nominal del CCPC por anio (millones):", (nac["LN"] / 1e6).round(2).to_dict())
    print("municipios con los 6 anios validos:", int((ancho["anios_con_dato"] == len(ANIOS)).sum()))
    print("municipios con historial suficiente (>=2 presidenciales y >=2 intermedias):",
          int(ancho["historial_suficiente"].sum()))
    j = judicial[judicial["anio_valido"]]
    print(f"eleccion judicial 2025: participacion {100 * j['SV'].sum() / (j['SV'].sum() + j['NV'].sum()):.1f}% "
          f"en {j['cve_muni'].nunique()} municipios validos")
    print("guardado en:", PROCESADOS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
