# Civimetría

Perfiles ciudadanos de participación construidos con los Conteos Censales de Participación Ciudadana (CCPC) del INE, 2009 a 2024.

Equipo Civimetría, Hackathon INE 2026 "Hackea la participación: datos que construyen democracia", Reto 1: Perfiles ciudadanos de participación. Título de la obra: *Perfiles que deciden: segmentación ciudadana para focalizar la inversión en participación del INE*.

## Qué responde

La pregunta del reto es qué tipos de ciudadanía existen según su comportamiento de participación. El CCPC no tiene datos de personas, pero sí de grupos: cuántas personas de cierto sexo y edad, en cada sección, votaron o no en cada elección federal. Con eso armamos la unidad del análisis, el **grupo ciudadano**: las personas de un mismo sexo y grupo de edad que viven en un mismo municipio (por ejemplo, mujeres de 25 a 29 años de Tijuana).

Agrupamos 28,158 grupos ciudadanos, que suman 97.8 millones de personas (99.5% de la lista nominal), solo por cómo han votado en seis elecciones federales. Después describimos cada perfil con edad, sexo, escolaridad, región, población indígena y afromexicana, y qué tan rural es su municipio.

## Resultados en breve

| Perfil | Personas | Participación presidencial / intermedia | Rasgo que lo define | Participación en la elección judicial 2025 |
|---|---|---|---|---|
| Intermitentes | 16.0 M | 64.8% / 42.9% | Votan en presidenciales y faltan en intermedias; 66% mujeres, sobre todo de 30 a 49 años, muy urbanos | 12.0% |
| Ocasionales | 23.3 M | 49.5% / 34.1% | Votan poco en cualquier elección; 68% hombres, la mitad menores de 30 años | 8.2% |
| En descenso | 16.1 M | 53.3% / 47.2% | Su participación baja elección tras elección; 61% hombres, Jalisco, Nuevo León, Guanajuato y Sonora | 7.8% |
| En ascenso | 17.8 M | 70.2% / 55.1% | Su participación sube desde 2009; 47% tiene 60 años o más | 20.0% |
| Constantes | 24.7 M | 70.5% / 61.7% | Votan alto y parejo; adultos de 40 años o más, mayoría mujeres | 16.4% |

Otros resultados:

- En una elección intermedia, como la de 2027, se pueden recuperar unos **13.0 millones de votos**, que es la caída estimada de participación entre presidencial e intermedia. Los 100 municipios con más votos recuperables concentran el 60%.
- La elección judicial de 2025 no se usó para construir los perfiles. Aun así, los perfiles ordenan bien quién votó en ella: el perfil explica el 32% de las diferencias entre grupos.
- En todas las elecciones se vota más a los 18 años que a los 19 (61.5% contra 53.4% en 2024). La participación toca fondo entre los 23 y los 26 años.

El detalle de cada perfil está en [docs/perfiles.md](docs/perfiles.md) y el método completo en [docs/metodologia.md](docs/metodologia.md).

## Cómo está hecho

```mermaid
flowchart LR
    A[01 Descarga INE, CONAPO e INEGI] --> B[02 Participación por municipio, sexo y edad]
    B --> C[03 Cruce con CONAPO e INEGI]
    C --> D[04 Grupos ciudadanos]
    D --> E[05 Segmentación en 5 perfiles]
    E --> F[06 Focalización municipal]
    E --> G[07 Robustez y validación]
    F --> H[08 Gráficas y 09 Excel]
    G --> H
    H --> I[10 Verificaciones]
```

Cada paso es un script de `src/` que se puede leer de principio a fin. Las constantes y funciones compartidas están en `src/comun.py`.

## Datos

- INE, [Conteos Censales de Participación Ciudadana](https://ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/) de las elecciones federales 2009, 2012, 2015, 2018, 2021 y 2024, y de la elección judicial 2024-2025 (esta última solo para validar).
- CONAPO, [Índice de marginación por municipio 2020](https://conapo.segob.gob.mx/work/models/CONAPO/Datos_Abiertos/Municipio/IMM_2020.xlsx).
- INEGI, Censo de Población y Vivienda 2020, principales resultados por localidad (ITER).

Todos son datos abiertos y agregados; ninguno contiene datos personales. Los archivos originales no se suben al repositorio por su tamaño (unos 420 MB); el script `01` los descarga y compara su huella SHA-256 con la registrada en [datos/huellas_crudos.csv](datos/huellas_crudos.csv).

## Cómo reproducirlo

Requisitos: Python 3.14 y conexión a internet para la primera descarga. Desde la carpeta del repositorio:

```bash
python -m venv .venv
```

En Windows se activa con `.venv\Scripts\activate`; en macOS o Linux, con `source .venv/bin/activate`. Después:

```bash
pip install -r requirements.txt
```

```bash
python src/ejecutar_todo.py
```

La corrida completa tarda unos 9 minutos y termina con 18 verificaciones automáticas (por ejemplo, que la participación nacional coincida con la que publica el INE y que cada municipio se cruce con un solo municipio del INEGI). Las semillas aleatorias están fijas, así que los resultados salen iguales en cada corrida.

## Qué produce

- `datos/procesados/`: tablas intermedias y finales en CSV.
- `resultados/figuras/`: 9 gráficas a 300 dpi.
- `resultados/tablas/`: tablas de elección del número de perfiles, robustez y validación, y `civimetria_tablero_municipal.xlsx`, un Excel con cada municipio, su índice de prioridad, sus votos recuperables y cuántas personas tiene de cada perfil, más un resumen por entidad.

El documento técnico, las fichas y la presentación de `entregables/` se armaron con scripts aparte a partir de estas tablas y gráficas, y sus cifras se cotejaron con ellas.

## Estructura del repositorio

- `src/`: el análisis, del `01` al `10`.
- `datos/procesados/`: resultados del análisis en CSV.
- `datos/crudos/`: datos originales (no se suben; se descargan con `01`).
- `resultados/`: gráficas y tablas.
- `docs/`: metodología, diccionario de datos, perfiles y bitácora.
- `referencias/`: documentos oficiales del concurso.
- `entregables/`: documento técnico, fichas y presentación.

## Límites

- Los perfiles describen grupos de personas, no a cada persona. Decir que un perfil "vota poco" es decir que sus grupos votan poco en promedio.
- Cada grupo es un rango de edad, no las mismas personas a lo largo del tiempo: quienes tenían 25 años en 2009 ya están en otro grupo en 2024.
- Los perfiles tienen un núcleo claro y bordes graduales. El 11.6% de las personas está en grupos que quedan entre dos perfiles; el archivo `grupos_perfiles.csv` indica cuál es su segundo perfil más cercano.
- El CCPC dice quién votó, no por qué. Las causas requieren otros estudios.

## Uso de los resultados

Los perfiles están pensados para la educación cívica y el fomento de la participación del INE. No usan ningún dato sobre preferencias políticas y no deben usarse con fines partidistas. Los perfiles se calculan solo con grupos de 50 personas o más; las tablas de `datos/procesados` reproducen agregados que el INE ya publica por sección.

## Cronograma

| Fecha | Qué hicimos |
|---|---|
| 15 de octubre | Registro del equipo en el Reto 1. Elegimos el enfoque: segmentar a la ciudadanía por su historial de participación y ligar cada perfil a una estrategia. |
| 20 de octubre | Repositorio, estructura de carpetas, diccionario de datos con el esquema real del CCPC y entorno de Python. |
| 21 de octubre | Descarga de los seis CCPC federales, tabla de participación por municipio de 2009 a 2024 y cruce con el índice de marginación de CONAPO. |
| 30 de octubre, mañana | Primera segmentación, con municipios como unidad. La revisión del método encontró tres errores (fórmula de participación, tendencia mezclada con el tipo de elección y cruce de claves INE-INEGI), que se corrigieron el mismo día. |
| 30 de octubre, tarde | Cambio de unidad a grupos ciudadanos y segmentación en cinco perfiles. Se agregaron el Censo 2020 y la elección judicial de 2025 como validación externa. |
| 30 de octubre, noche | Corrección de la lista nominal incompleta de 2012, huellas de las fuentes y 18 verificaciones. Documento técnico, fichas y presentación. Revisión técnica y evaluación contra la rúbrica oficial; sus observaciones se incorporaron a los entregables y al código. |
| 31 de octubre | Revisión final, firma de las cartas y envío del .zip al INE. |

El detalle de cada decisión está en [docs/bitacora.md](docs/bitacora.md).

## Equipo

- Miguel Angel Barranco Ortega (representante del equipo)
- María Isabel Ruiz Machorro

El proyecto lo hicimos entre los dos. Elegimos juntos el reto y el enfoque, propusimos y discutimos cada decisión del método, revisamos el código, los datos y las cifras, y armamos y revisamos los entregables. Los cambios se subieron al repositorio desde la cuenta de Miguel.

Usamos un asistente de inteligencia artificial (Claude) como apoyo para programar, buscar fuentes y revisar textos. Las decisiones de método, la verificación de las cifras y la revisión final son del equipo, y todo el análisis se puede comprobar corriendo el código.
