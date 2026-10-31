"""
09_tablero_municipal.py

Arma un Excel listo para usar en el INE, sin programar: cada municipio con su
indice de prioridad, sus votos recuperables en intermedias y cuantas personas
tiene de cada perfil; un resumen por entidad para cada Junta Local; los perfiles
y el reparto por sexo y edad.

Salida: resultados/tablas/civimetria_tablero_municipal.xlsx

Uso:
    python src/09_tablero_municipal.py
"""
import sys
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from comun import PERFILES, PROCESADOS, TABLAS

SALIDA = TABLAS / "civimetria_tablero_municipal.xlsx"

COLUMNAS = {
    "rank_prioridad": "Lugar nacional de prioridad",
    "entidad": "Entidad",
    "municipio": "Municipio",
    "cve_muni": "Clave INE",
    "cve_inegi": "Clave INEGI",
    "prioridad": "Índice de prioridad (0-100)",
    "lista_nominal": "Lista nominal",
    "votos_recuperables_intermedia": "Votos recuperables en intermedias (estimado)",
    "no_votarian_intermedia": "No votarían en una intermedia (estimado)",
    "perfil_mayoritario": "Perfil mayoritario",
    **{f"pct_{p}": f"% {p}" for p in PERFILES},
    "part_presidencial": "Participación presidencial promedio (%)",
    "part_intermedia": "Participación intermedia promedio (%)",
    "brecha_pres_inter": "Brecha presidencial - intermedia (pts)",
    "tendencia": "Tendencia 2009-2024 (pts)",
    "part_2021": "Participación 2021 (%)",
    "part_2024": "Participación 2024 (%)",
    "part_jovenes": "Participación 18-29 años (%)",
    "part_mujeres": "Participación mujeres (%)",
    "part_hombres": "Participación hombres (%)",
    "grado_promedio_escolaridad": "Grado promedio de escolaridad (INEGI 2020)",
    "pct_poblacion_indigena": "% población en hogares indígenas (INEGI 2020)",
    "pct_afromexicana": "% población afromexicana (INEGI 2020)",
    "grado_marginacion": "Grado de marginación (CONAPO 2020)",
    "historial_suficiente": "Historial suficiente",
}

LEEME = [
    ("Civimetría. Perfiles ciudadanos de participación y focalización municipal", ""),
    ("", ""),
    ("Qué es", "Para cada municipio: qué tan prioritario es para una elección intermedia, cuántos votos se "
               "podrían recuperar y cuántas personas tiene de cada perfil ciudadano."),
    ("Cómo usarlo", "En la hoja Municipios, filtre por Entidad o por Perfil mayoritario con las flechas del "
                    "encabezado. Ya está ordenada de mayor a menor prioridad. La hoja Por entidad resume cada estado."),
    ("", ""),
    ("Perfiles", "Se agruparon 28 mil grupos ciudadanos (personas de un mismo sexo y grupo de edad en un "
                 "municipio) según cómo votaron de 2009 a 2024. La hoja Perfiles describe los cinco."),
    ("Participación", "Registros con marca de voto entre registros con información en los cuadernillos "
                      "(SV / (SV + NV)), según los Conteos Censales de Participación Ciudadana (CCPC) del INE."),
    ("Presidencial / intermedia", "Promedio de 2012, 2018 y 2024 / promedio de 2009, 2015 y 2021."),
    ("Votos recuperables", "Suma, sobre los grupos del municipio, de su lista nominal por su brecha "
                           "presidencial - intermedia: personas que votan en presidenciales y no en intermedias. "
                           "Es una estimación con datos agregados, no un conteo de personas."),
    ("Índice de prioridad", "0 a 100. Déficit de participación en intermedias (40%), tamaño de la lista nominal "
                            "(30%) y brecha presidencial - intermedia (30%), cada uno en rango percentil. Si los "
                            "pesos se mueven 0.1, el orden casi no cambia."),
    ("Tendencia", "Cambio estimado de 2009 a 2024 sin el efecto de la elección presidencial."),
    ("Historial suficiente", "Al menos dos elecciones presidenciales y dos intermedias con información. Sin "
                             "historial suficiente (casi todos son municipios creados después de 2018) no hay "
                             "índice de prioridad."),
    ("", ""),
    ("Fuentes", "INE, Conteos Censales de Participación Ciudadana 2009-2024. CONAPO, Índice de marginación por "
                "municipio 2020. INEGI, Censo de Población y Vivienda 2020, principales resultados por localidad."),
    ("Límites", "Los datos son agregados: describen grupos y municipios, no a cada persona. Un municipio puede "
                "tener secciones muy distintas a su promedio."),
    ("Código", "Todo se reproduce con python src/ejecutar_todo.py en el repositorio del proyecto."),
]


def formatea(ws, anchos: dict) -> None:
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="3B3B3B")
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 48
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for i, col in enumerate(ws.iter_cols(1, ws.max_column), start=1):
        ws.column_dimensions[get_column_letter(i)].width = anchos.get(i, 15)
        for celda in col[1:]:
            if isinstance(celda.value, float):
                celda.number_format = "0.0"
            elif isinstance(celda.value, int):
                celda.number_format = "#,##0"


def main() -> int:
    mun = pd.read_csv(PROCESADOS / "municipio_focalizacion.csv", dtype={"cve_muni": str, "cve_inegi": str})
    hoja_mun = mun[list(COLUMNAS)].rename(columns=COLUMNAS)
    hoja_mun["Historial suficiente"] = hoja_mun["Historial suficiente"].map({True: "Sí", False: "No"})
    for c in ["Lugar nacional de prioridad", "Votos recuperables en intermedias (estimado)",
              "No votarían en una intermedia (estimado)"]:
        hoja_mun[c] = hoja_mun[c].astype("Int64")

    res = pd.read_csv(PROCESADOS / "perfiles_resumen.csv")
    hoja_perf = res[["perfil", "personas", "pct_personas", "part_presidencial", "part_intermedia",
                     "tendencia", "pct_hombres", "pct_18-24", "pct_25-29", "pct_60+",
                     "pct_urbano", "pct_localidades_menores_5mil", "pct_sin_educacion_basica",
                     "grado_promedio_escolaridad", "pct_poblacion_indigena", "pct_afromexicana",
                     "votos_recuperables_intermedia", "municipios_donde_es_mayoria",
                     "entidades_principales"]].rename(columns={
        "perfil": "Perfil", "personas": "Personas", "pct_personas": "% de la lista nominal",
        "part_presidencial": "Participación presidencial (%)", "part_intermedia": "Participación intermedia (%)",
        "tendencia": "Tendencia 2009-2024 (pts)", "pct_hombres": "% hombres", "pct_18-24": "% 18-24 años",
        "pct_25-29": "% 25-29 años", "pct_60+": "% 60 años o más",
        "pct_urbano": "% en secciones urbanas (municipio, INE)",
        "pct_localidades_menores_5mil": "% en localidades de menos de 5 mil hab.",
        "pct_sin_educacion_basica": "% sin educación básica (municipio)",
        "grado_promedio_escolaridad": "Grado promedio de escolaridad (municipio)",
        "pct_poblacion_indigena": "% en hogares indígenas (municipio)",
        "pct_afromexicana": "% afromexicana (municipio)",
        "votos_recuperables_intermedia": "Votos recuperables en intermedias",
        "municipios_donde_es_mayoria": "Municipios donde es mayoría",
        "entidades_principales": "Entidades con más personas del perfil"})

    con = mun[mun["prioridad"].notna()]
    ent = con.groupby("entidad").agg(municipios=("cve_muni", "count"), lista_nominal=("lista_nominal", "sum"),
                                     votos=("votos_recuperables_intermedia", "sum"))
    personas = con.groupby("entidad")[[f"personas_{p}" for p in PERFILES]].sum()
    for p in PERFILES:
        ent[f"% {p}"] = 100 * personas[f"personas_{p}"] / personas.sum(axis=1)
    ent["3 municipios con más prioridad"] = (con.sort_values("rank_prioridad").groupby("entidad").head(3)
                                             .groupby("entidad")["municipio"].agg(", ".join))
    ent = ent.sort_values("votos", ascending=False).reset_index().rename(columns={
        "entidad": "Entidad", "municipios": "Municipios", "lista_nominal": "Lista nominal",
        "votos": "Votos recuperables en intermedias"})
    ent[["Municipios", "Lista nominal", "Votos recuperables en intermedias"]] = \
        ent[["Municipios", "Lista nominal", "Votos recuperables en intermedias"]].astype(int)

    reparto = pd.read_csv(TABLAS / "reparto_sexo_edad.csv").rename(
        columns={"sexo": "Sexo", "grupo_edad": "Edad"})

    with pd.ExcelWriter(SALIDA, engine="openpyxl") as xw:
        pd.DataFrame(LEEME).to_excel(xw, sheet_name="Léeme", index=False, header=False)
        hoja_mun.to_excel(xw, sheet_name="Municipios", index=False)
        hoja_perf.to_excel(xw, sheet_name="Perfiles", index=False)
        reparto.to_excel(xw, sheet_name="Sexo y edad", index=False)
        ent.to_excel(xw, sheet_name="Por entidad", index=False)

    wb = load_workbook(SALIDA)
    ws = wb["Léeme"]
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 110
    ws["A1"].font = Font(bold=True, size=14)
    for fila in ws.iter_rows(min_row=3):
        fila[0].font = Font(bold=True)
        fila[1].alignment = Alignment(wrap_text=True, vertical="top")
    formatea(wb["Municipios"], {1: 11, 2: 20, 3: 30, 4: 9, 5: 9, 10: 16})
    formatea(wb["Perfiles"], {1: 16, 19: 60})
    formatea(wb["Sexo y edad"], {1: 12, 2: 10})
    formatea(wb["Por entidad"], {1: 22, ent.shape[1]: 60})
    wb.save(SALIDA)
    print("guardado:", SALIDA)
    print(f"  municipios: {len(hoja_mun)}; entidades: {len(ent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
