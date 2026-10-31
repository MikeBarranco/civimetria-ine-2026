"""
ejecutar_todo.py

Corre todo el analisis en orden, de la descarga de datos al tablero municipal.
Si un paso falla, se detiene y dice cual.

Uso:
    python src/ejecutar_todo.py
"""
from pathlib import Path
import subprocess
import sys
import time

SRC = Path(__file__).resolve().parent
PASOS = [
    "01_descarga_datos.py",
    "02_construye_tabla_municipio.py",
    "03_enriquece.py",
    "04_grupos_ciudadanos.py",
    "05_segmentacion.py",
    "06_focalizacion_municipal.py",
    "07_robustez.py",
    "08_graficas.py",
    "09_tablero_municipal.py",
    "10_verificaciones.py",
]


def main() -> int:
    inicio = time.time()
    for paso in PASOS:
        print(f"\n######## {paso} ########", flush=True)
        t = time.time()
        r = subprocess.run([sys.executable, str(SRC / paso)])
        if r.returncode != 0:
            print(f"\nFallo en {paso}. Se detiene la ejecucion.")
            return r.returncode
        print(f"({paso} tardo {time.time() - t:.0f} s)")
    print(f"\nListo. Tiempo total: {(time.time() - inicio) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
