"""
08_graficas.py

Genera las graficas del analisis en resultados/figuras, a 300 dpi para el
documento tecnico, las fichas y la presentacion. Cada perfil tiene siempre el
mismo color.

- participacion_nacional.png: participacion por eleccion federal.
- edad_por_eleccion.png: participacion nacional por edad exacta en cada eleccion.
- eleccion_k.png: metricas para elegir el numero de perfiles.
- mapa_perfiles.png: donde cae cada grupo ciudadano segun brecha y tendencia.
- historial_perfiles.png: participacion de cada perfil en las seis elecciones.
- quien_es_cada_perfil.png: a que perfil pertenece cada grupo de sexo y edad.
- composicion_perfiles.png: edad, sexo y tamano de cada perfil.
- concentracion_municipal.png: cuantos municipios concentran los votos
  recuperables en intermedias.
- validacion_judicial.png: participacion de cada perfil en la eleccion judicial
  de 2025, que no se uso para construir los perfiles.

Uso:
    python src/08_graficas.py
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from comun import ANIOS, EDADES, FIGURAS, PERFILES, PRESIDENCIALES, PROCESADOS, SEXO, TABLAS

# Paleta validada para daltonismo entre perfiles vecinos (dataviz validate_palette, modo claro).
COLORES = {"Intermitentes": "#E34948", "Ocasionales": "#EDA100", "En descenso": "#2A78D6",
           "En ascenso": "#1BAF7A", "Constantes": "#6250D6"}
TINTA = "#222222"
FUENTE = "Fuente: INE, Conteos Censales de Participación Ciudadana 2009-2024. Elaboración propia."

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"], "font.size": 10,
    "axes.edgecolor": "#888888", "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlelocation": "left",
    "savefig.dpi": 300, "savefig.bbox": "tight",
})


def guarda(fig, nombre: str, nota: str = FUENTE, y: float = -0.02) -> None:
    fig.text(0.01, y, nota, fontsize=7.5, color="#666666", ha="left", va="top")
    fig.savefig(FIGURAS / nombre)
    plt.close(fig)


def participacion_nacional(celdas: pd.DataFrame) -> None:
    t = celdas.groupby("anio")[["SV", "NV"]].sum()
    nac = 100 * t["SV"] / (t["SV"] + t["NV"])
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.plot(nac.index, nac.values, color="#555555", lw=1.2, zorder=1)
    for a, v in nac.items():
        pres = a in PRESIDENCIALES
        ax.scatter(a, v, s=60, zorder=2, color=TINTA if pres else "white", edgecolor=TINTA, lw=1.5)
        ax.annotate(f"{v:.1f}%", (a, v), xytext=(0, 9 if pres else -16), textcoords="offset points",
                    ha="center", fontsize=9)
    ax.scatter([], [], color=TINTA, label="Presidencial")
    ax.scatter([], [], color="white", edgecolor=TINTA, label="Intermedia")
    ax.legend(frameon=False, loc="lower right")
    ax.set_xticks(ANIOS)
    ax.set_ylim(30, 72)
    ax.set_ylabel("Participación (%)")
    ax.grid(axis="y", alpha=0.3)
    caidas = {a: nac[a - 3] - nac[a] for a in ANIOS if a not in PRESIDENCIALES and a - 3 in nac.index}
    anios = " y ".join(str(a) for a in caidas)
    ax.set_title(f"En las intermedias de {anios} se votó entre {min(caidas.values()):.0f} y "
                 f"{max(caidas.values()):.0f} puntos menos que en la presidencial anterior")
    guarda(fig, "participacion_nacional.png",
           FUENTE + " Participación: registros con marca de voto entre registros con información.")


def edad_por_eleccion() -> None:
    t = pd.read_csv(PROCESADOS / "participacion_nacional_edad.csv", dtype={"sexo": str})
    t = t[t["anio"].isin(ANIOS) & t["edad"].between(18, 85)]
    t = t.groupby(["anio", "edad"])[["SV", "NV"]].sum()
    t = (100 * t["SV"] / (t["SV"] + t["NV"])).unstack("anio")
    jovenes = t.loc[18:35]
    minimos = jovenes.idxmin()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    pos = {}
    for a in t.loc[85].sort_values().index:
        cerca = [v for v in pos.values() if abs(v - t.loc[85, a]) < 2]
        pos[a] = max(cerca) + 2 if cerca else t.loc[85, a]
    for a in ANIOS:
        pres = a in PRESIDENCIALES
        color = TINTA if pres else "#999999"
        ax.plot(t.index, t[a], "-" if pres else "--", color=color, lw=1.4)
        ax.text(86, pos[a], str(a), fontsize=8, va="center", color=color)
        ax.scatter(18, t.loc[18, a], s=18, color=color, zorder=3)
    ax.axvspan(minimos.min() - 0.5, minimos.max() + 0.5, color="#F3E3C3", zorder=0)
    ax.set_xlim(17, 90)
    ax.set_xticks([18, 25, 30, 40, 50, 60, 70, 80])
    ax.set_xlabel("edad el día de la elección")
    ax.set_ylabel("Participación (%)")
    ax.grid(axis="y", alpha=0.3)
    ax.set_title(f"Se vota más a los 18 que a los 19; la participación toca fondo entre los "
                 f"{minimos.min()} y los {minimos.max()} años")
    guarda(fig, "edad_por_eleccion.png",
           "Línea continua: presidencial; punteada: intermedia. Sombreado: edad de menor participación en "
           "cada elección (entre 18 y 35 años). " + FUENTE)


def eleccion_k() -> None:
    m = pd.read_csv(TABLAS / "eleccion_k.csv")
    paneles = [("silueta", "Silueta (más alto, mejor)", (0, 0.35)),
               ("calinski_harabasz", "Calinski-Harabasz (más alto, mejor)", None),
               ("davies_bouldin", "Davies-Bouldin (más bajo, mejor)", None),
               ("estabilidad_ari_media", "Estabilidad por remuestreo (ARI)", (0, 1))]
    fig, axs = plt.subplots(1, 4, figsize=(12, 3))
    for ax, (col, titulo, lim) in zip(axs, paneles):
        ax.plot(m["k"], m[col], "o-", color="#555555")
        ax.scatter([5], m.loc[m["k"] == 5, col], s=90, color=COLORES["Intermitentes"], zorder=3)
        ax.set_title(titulo, fontsize=9.5)
        ax.set_xticks(m["k"])
        ax.set_xlabel("número de perfiles")
        ax.grid(alpha=0.3)
        if lim:
            ax.set_ylim(*lim)
    fig.suptitle("Elección del número de perfiles (en rojo, el elegido: 5)", x=0.01, ha="left",
                 fontweight="bold", fontsize=11)
    fig.tight_layout()
    guarda(fig, "eleccion_k.png")


def mapa_perfiles(grupos: pd.DataFrame) -> None:
    rng = np.random.default_rng(1)
    w = grupos["lista_nominal"].to_numpy(dtype=float)
    m = grupos.iloc[rng.choice(len(grupos), 6000, replace=False, p=w / w.sum())]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), sharex=True)
    for ax, (col, etiqueta) in zip(axs, [("brecha", "brecha: presidencial menos intermedia (puntos)"),
                                         ("tendencia", "tendencia 2009-2024 sin efecto presidencial (puntos)")]):
        for p in PERFILES:
            d = m[m["perfil"] == p]
            ax.scatter(d["nivel"], d[col], s=5, alpha=0.3, color=COLORES[p], lw=0)
            g = grupos[grupos["perfil"] == p]
            cx = np.average(g["nivel"], weights=g["lista_nominal"])
            cy = np.average(g[col], weights=g["lista_nominal"])
            ax.scatter(cx, cy, s=140, marker="X", color=COLORES[p], edgecolor="white", lw=1.2, zorder=3, label=p)
            desplazamiento = {"Ocasionales": (-62, -16), "Intermitentes": (2, 9)} if col == "tendencia" else {}
            ax.annotate(p, (cx, cy), xytext=desplazamiento.get(p, (7, 5)), textcoords="offset points",
                        fontsize=8, color=TINTA,
                        fontweight="bold", zorder=4,
                        bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.8))
        ax.axhline(0, color="#999999", lw=0.8)
        ax.set_xlabel("nivel: participación promedio (%)")
        ax.set_ylabel(etiqueta)
        ax.set_xlim(15, 95)
        ax.grid(alpha=0.25)
    axs[0].set_ylim(-8, 40)
    axs[1].set_ylim(-40, 50)
    axs[1].legend(frameon=False, fontsize=8.5, loc="upper left", markerscale=0.8)
    fig.suptitle("Las tres variables del modelo: cada punto es un grupo ciudadano (sexo y edad en un municipio)",
                 x=0.01, ha="left", fontweight="bold", fontsize=11)
    fig.tight_layout()
    guarda(fig, "mapa_perfiles.png",
           "Muestra de 6 mil grupos tomada en proporción a su tamaño. La X marca el centro de cada perfil. " + FUENTE)


def historial_perfiles(res: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for _, r in res.iterrows():
        ax.plot(ANIOS, [r[f"part_{a}"] for a in ANIOS], "o-", color=COLORES[r["perfil"]], lw=2,
                label=f"{r['perfil']} ({r['personas'] / 1e6:.1f} M)")
    for a in ANIOS:
        if a not in PRESIDENCIALES:
            ax.axvspan(a - 0.6, a + 0.6, color="#EEEEEE", zorder=0)
    ax.text(2009, 81, "intermedia", ha="center", fontsize=8, color="#666666")
    ax.set_xticks(ANIOS)
    ax.set_ylim(25, 85)
    ax.set_ylabel("Participación (%)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right", ncol=2)
    ax.set_title("Historial de participación de cada perfil")
    guarda(fig, "historial_perfiles.png", "Entre paréntesis, millones de personas. " + FUENTE)


def quien_es(reparto: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    v = reparto[PERFILES].to_numpy()
    ax.imshow(v, cmap="Greys", vmin=0, vmax=80, aspect="auto")
    ax.set_xticks(range(len(PERFILES)))
    ax.set_xticklabels(PERFILES)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(reparto)))
    ax.set_yticklabels([f"{s}, {e}" for s, e in reparto.index], fontsize=9)
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            ax.text(j, i, f"{v[i, j]:.0f}%", ha="center", va="center", fontsize=8.5,
                    color="white" if v[i, j] > 45 else TINTA)
    ax.axhline(5.5, color="white", lw=3)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("De cada 100 personas de cada sexo y edad, cuántas están en cada perfil", pad=28)
    guarda(fig, "quien_es_cada_perfil.png")


def composicion(res: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    tonos = ["#1F1F1F", "#474747", "#707070", "#999999", "#C2C2C2", "#E0E0E0"]
    y = np.arange(len(res))[::-1]
    izq = np.zeros(len(res))
    for e, t in zip(EDADES, tonos):
        val = res[f"pct_{e}"].to_numpy()
        ax.barh(y, val, left=izq, color=t, height=0.6, label=e)
        for yi, xi, vi in zip(y, izq, val):
            if vi >= 7:
                ax.text(xi + vi / 2, yi, f"{vi:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if t in tonos[:3] else TINTA)
        izq += val
    ax.set_yticks(y)
    ax.set_yticklabels([f"{p}  ({h:.0f}% hombres)" for p, h in zip(res["perfil"], res["pct_hombres"])])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% de las personas del perfil")
    ax.legend(title="edad", frameon=False, ncol=6, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    ax.set_title("Edad y sexo de cada perfil")
    guarda(fig, "composicion_perfiles.png", FUENTE + " Lista nominal más reciente de cada grupo.", y=-0.16)


def concentracion(mun: pd.DataFrame) -> None:
    v = mun["votos_recuperables_intermedia"].dropna().sort_values(ascending=False).to_numpy()
    acum = 100 * v.cumsum() / v.sum()
    n = np.arange(1, len(v) + 1)
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.plot(n, acum, color=COLORES["Intermitentes"], lw=2)
    for k in (50, 100, 200):
        ax.scatter(k, acum[k - 1], color=TINTA, zorder=3)
        ax.annotate(f"{k} municipios: {acum[k - 1]:.0f}%", (k, acum[k - 1]), xytext=(10, -14),
                    textcoords="offset points", fontsize=9)
    ax.set_xscale("log")
    marcas = [1, 10, 50, 100, 200, 500, 1000, len(v)]
    ax.set_xticks(marcas)
    ax.set_xticklabels([f"{m:,}" for m in marcas])
    ax.set_ylim(0, 102)
    ax.set_xlabel("municipios, de más a menos votos recuperables (escala logarítmica)")
    ax.set_ylabel("% acumulado")
    ax.grid(alpha=0.3)
    ax.set_title(f"{v.sum() / 1e6:.1f} millones de votos recuperables en intermedias, "
                 "concentrados en pocos municipios")
    guarda(fig, "concentracion_municipal.png",
           "Votos recuperables: personas que votan en presidenciales y no en intermedias (estimación con "
           "lista nominal y brecha de cada grupo). " + FUENTE)


def validacion_judicial() -> None:
    t = pd.read_csv(TABLAS / "validacion_judicial2025.csv").set_index("perfil").reindex(PERFILES)
    pj = pd.read_csv(PROCESADOS / "participacion_judicial2025_sexo_edad.csv")
    pj = pj[pj["anio_valido"]]
    nacional = 100 * pj["SV"].sum() / (pj["SV"].sum() + pj["NV"].sum())
    orden = t["participacion_judicial_2025"].sort_values()
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.barh(orden.index, orden.values, color=[COLORES[p] for p in orden.index], height=0.6)
    ax.axvline(nacional, color=TINTA, lw=1, ls="--", zorder=1)
    for i, v in enumerate(orden.values):
        ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=9, zorder=2,
                bbox=dict(fc="white", ec="none", pad=1))
    ax.set_ylim(-1, len(orden) - 0.5)
    ax.text(nacional + 0.2, -0.75, f"participación nacional {nacional:.1f}%", fontsize=8.5)
    ax.set_xlim(0, orden.max() * 1.2)
    ax.set_xlabel("participación en la elección judicial de 2025 (%)")
    ax.set_title("Los perfiles, hechos con 2009-2024, ordenan quién votó en la elección judicial de 2025")
    guarda(fig, "validacion_judicial.png",
           "Fuente: INE, Conteos Censales de Participación Ciudadana, Proceso Electoral Extraordinario del Poder "
           "Judicial de la Federación 2024-2025. Elaboración propia.")


def main() -> int:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    celdas = pd.read_csv(PROCESADOS / "participacion_municipio_sexo_edad.csv", dtype={"cve_muni": str, "sexo": str})
    celdas = celdas[celdas["anio_valido"]]
    grupos = pd.read_csv(PROCESADOS / "grupos_ciudadanos.csv", dtype={"cve_muni": str, "sexo": str})
    perf = pd.read_csv(PROCESADOS / "grupos_perfiles.csv", dtype={"cve_muni": str, "sexo": str})
    grupos = grupos.merge(perf[["cve_muni", "sexo", "grupo_edad", "perfil"]], on=["cve_muni", "sexo", "grupo_edad"])
    res = pd.read_csv(PROCESADOS / "perfiles_resumen.csv")
    reparto = pd.read_csv(TABLAS / "reparto_sexo_edad.csv", index_col=[0, 1])
    reparto = reparto.reindex([(s, e) for s in SEXO.values() for e in EDADES])
    mun = pd.read_csv(PROCESADOS / "municipio_focalizacion.csv", dtype={"cve_muni": str})

    participacion_nacional(celdas)
    edad_por_eleccion()
    eleccion_k()
    mapa_perfiles(grupos)
    historial_perfiles(res)
    quien_es(reparto)
    composicion(res)
    concentracion(mun)
    validacion_judicial()
    print("Graficas guardadas en", FIGURAS)
    for f in sorted(FIGURAS.glob("*.png")):
        print("  ", f.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
