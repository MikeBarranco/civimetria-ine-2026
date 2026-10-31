"""
01_descarga_datos.py

Descarga a datos/crudos todas las fuentes del analisis. Si un archivo ya existe,
no lo vuelve a bajar.

- INE, Conteos Censales de Participacion Ciudadana (CCPC): un ZIP por eleccion
  federal (2009 a 2024) y el de la eleccion judicial de 2025, que se usa solo para
  validar los perfiles con una eleccion que el modelo no vio.
- CONAPO, indice de marginacion por municipio 2020 (incluye el porcentaje sin
  educacion basica y el de poblacion en localidades de menos de 5 mil habitantes).
- INEGI, Censo de Poblacion y Vivienda 2020, principales resultados por localidad
  (ITER): grado promedio de escolaridad, poblacion indigena y afromexicana.

Los datos crudos no se suben al repositorio (ver .gitignore); este script permite
volver a descargarlos para reproducir el analisis.

Integridad: de cada archivo se calcula su huella SHA-256 y se compara con la que
quedo registrada en datos/huellas_crudos.csv (que si se sube). Si un archivo no
coincide, el script se detiene con error: la fuente lo cambio o la descarga quedo
incompleta, y los resultados ya no serian los del repositorio. Para aceptar a
proposito una version nueva (por ejemplo, al agregar los conteos de 2027), se
borra su renglon de huellas_crudos.csv y se vuelve a correr.

Uso:
    python src/01_descarga_datos.py
"""
import csv
import hashlib
import sys
import requests
from comun import CRUDOS, RAIZ

HUELLAS = RAIZ / "datos" / "huellas_crudos.csv"

INE = "https://ine.mx/wp-content/uploads"
FUENTES = {
    "CCPC2009.zip": f"{INE}/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2009.zip",
    "CCPC2012.zip": f"{INE}/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2012.zip",
    "CCPC2015.zip": f"{INE}/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2015.zip",
    "CCPC2018.zip": f"{INE}/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2018.zip",
    "CCPC2021.zip": f"{INE}/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2021.zip",
    "CCPC2024.zip": f"{INE}/2025/08/DatosAbiertos_DECEyEC_ConteosCensales2024.zip",
    "CCPC_PJ2025.zip": f"{INE}/2026/09/DatosAbiertos_DECEyEC_ConteosCensalesPJ2025.zip",
    "CONAPO_IMM_2020.xlsx": "https://conapo.segob.gob.mx/work/models/CONAPO/Datos_Abiertos/Municipio/IMM_2020.xlsx",
    "INEGI_ITER_2020.zip": ("https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/"
                            "iter_00_cpv2020_csv.zip"),
}
CABECERAS = {"User-Agent": "Mozilla/5.0 (proyecto academico Hackathon INE 2026)"}


def descargar(nombre: str, url: str) -> None:
    salida = CRUDOS / nombre
    if salida.exists() and salida.stat().st_size > 0:
        print(f"  {nombre}: ya existe ({salida.stat().st_size / 1e6:.1f} MB), se omite")
        return
    print(f"  {nombre}: descargando...", flush=True)
    resp = requests.get(url, timeout=900, headers=CABECERAS)
    resp.raise_for_status()
    # se escribe aparte y se renombra al final, para que un corte no deje un archivo a medias
    parcial = salida.with_name(salida.name + ".parcial")
    parcial.write_bytes(resp.content)
    parcial.replace(salida)
    print(f"  {nombre}: listo ({len(resp.content) / 1e6:.1f} MB)")


def huella(ruta) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> int:
    CRUDOS.mkdir(parents=True, exist_ok=True)
    print("Descargando fuentes a", CRUDOS)
    for nombre, url in FUENTES.items():
        descargar(nombre, url)

    registradas = {}
    if HUELLAS.exists():
        with open(HUELLAS, encoding="utf-8") as f:
            registradas = {r["archivo"]: r["sha256"] for r in csv.DictReader(f)}
    actuales = {nombre: huella(CRUDOS / nombre) for nombre in FUENTES}
    distintas = [n for n, h in actuales.items() if n in registradas and registradas[n] != h]
    if distintas:
        for n in distintas:
            print(f"  ERROR: {n} no coincide con su huella en {HUELLAS.name}")
        print("La fuente cambio el archivo o la descarga quedo incompleta. Si el cambio es"
              " esperado, borra su renglon de huellas_crudos.csv y vuelve a correr.")
        return 1
    nuevas = [n for n in actuales if n not in registradas]
    if nuevas:
        with open(HUELLAS, "w", encoding="utf-8", newline="") as f:
            escritor = csv.writer(f)
            escritor.writerow(["archivo", "sha256", "url"])
            for n, h in actuales.items():
                escritor.writerow([n, h, FUENTES[n]])
        print(f"  huellas registradas por primera vez: {', '.join(nuevas)}")
    print("  huellas SHA-256 verificadas.")
    print("Descarga completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
