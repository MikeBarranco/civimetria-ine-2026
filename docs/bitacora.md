# Bitácora del proyecto

Diario del proyecto: qué es cada cosa, qué se hizo y por qué se tomó cada decisión.

## Qué es este proyecto

Civimetría es nuestra participación en el Hackathon INE 2026, Reto 1: Perfiles ciudadanos de participación. Con los Conteos Censales de Participación Ciudadana del INE agrupamos a la ciudadanía en cinco perfiles según cómo vota y, para cada perfil, decimos quiénes son, dónde están y qué estrategia conviene, pensando en la elección intermedia de 2027. Los entregables son un documento técnico, fichas de perfil, una presentación y este código.

## Qué es cada archivo y carpeta

- README.md: portada del proyecto, resultados en breve y cómo reproducirlo.
- src/: el análisis, del 01 al 10, más comun.py (constantes y funciones compartidas) y ejecutar_todo.py.
- docs/metodologia.md: cada decisión del método y por qué.
- docs/diccionario-de-datos.md: qué significa cada columna.
- docs/perfiles.md: los cinco perfiles con sus cifras y su dirección de estrategia.
- docs/bitacora.md: este diario.
- docs/flujo-git.md: cómo nombramos los commits y cómo trabajamos los dos en el repositorio.
- datos/crudos/: fuentes originales (no se suben; se descargan con src/01).
- datos/huellas_crudos.csv: huella SHA-256 de cada fuente.
- datos/procesados/: tablas del análisis.
- resultados/: gráficas y tablas, incluido el Excel para el INE.
- referencias/: documentos oficiales del concurso.
- entregables/: documento técnico, fichas y presentación.

## Decisiones y por qué se tomaron

- Reto 1. La rúbrica da 65 de 100 puntos al apego al reto y a la solidez del método, que es donde podemos destacar.
- Nombre del equipo: Civimetría, por cívica más medición.
- Unidad de análisis: el grupo ciudadano (personas de un mismo sexo y grupo de edad en un municipio). El reto pide tipos de ciudadanía, no tipos de municipio, y dentro de un municipio los jóvenes y los adultos mayores votan muy distinto.
- Segmentar solo con comportamiento (nivel, brecha y tendencia) y describir después con edad, sexo, escolaridad y región, como lo pide la convocatoria.
- Cinco perfiles. Con cuatro se mezclan quienes votan solo en presidenciales con quienes casi no votan, que piden estrategias distintas.
- Participación = SV / (SV + NV), la fórmula del manual de la plataforma CCPC.
- Elección judicial 2025 fuera del modelo, para usarla como validación.
- Python con versiones fijas, un solo comando para reproducir todo y verificaciones automáticas al final.
- Herramientas gratuitas: Python y GitHub con GitHub Desktop. Las fichas y la presentación se generaron desde los datos, para que cada cifra salga de las tablas del análisis. Usamos un asistente de inteligencia artificial (Claude) como apoyo para programar, buscar fuentes y revisar textos; las decisiones de método, la verificación de las cifras y la revisión final son del equipo.

## Registro por fecha

- 15 de octubre de 2026: registro del equipo Civimetría en el Reto 1.
- 20 de octubre de 2026: repositorio, estructura de carpetas, documentación inicial y entorno de Python.
- 21 de octubre de 2026: descarga de los seis CCPC federales, tabla por municipio y primer cruce con CONAPO.
- 30 de octubre de 2026, mañana: primera segmentación con municipios como unidad (4 perfiles). Una revisión crítica encontró tres errores que se corrigieron el mismo día:
  - la participación se dividía entre toda la lista nominal, incluidos los registros sin dato, que en algunos municipios llegan al 99%; se cambió a SV / (SV + NV);
  - la tendencia comparaba 2009 (intermedia) con 2024 (presidencial); se cambió por una regresión que separa el efecto presidencial;
  - la clave de municipio del INE se trataba como si fuera la del INEGI, lo que pegaba los datos de CONAPO al municipio equivocado en 1,364 casos; ahora el cruce es por entidad y nombre, con 25 equivalencias revisadas a mano.
- 30 de octubre de 2026, tarde: cambio de unidad a grupos ciudadanos y segmentación por comportamiento en cinco perfiles. Se agregaron el Censo 2020 del INEGI (escolaridad, población indígena y afromexicana) y el CCPC de la elección judicial 2025 como validación externa: los perfiles ordenan bien quién votó en ella.
- 30 de octubre de 2026, noche: auditoría de los datos de origen. El CCPC 2012 trae 3 millones de registros menos que la lista nominal oficial; se agregó una regla para descartar los municipio-año con lista nominal incompleta, y con ella mejoró la estabilidad del modelo. También se agregaron la medida de claridad de cada grupo, la curva de participación por edad exacta, las huellas SHA-256 de las fuentes y 18 verificaciones automáticas. El perfil "En retirada" se renombró "En descenso" para que no se confunda con personas jubiladas.
- 30 de octubre de 2026, noche: documento técnico (11 páginas), fichas de perfil en PDF y PNG y presentación ejecutiva de 10 diapositivas. La paleta de los perfiles se cambió por una validada para daltonismo.
- 30 de octubre de 2026, noche: hicimos dos revisiones de todo el proyecto, una auditoría técnica del código y los datos y una evaluación de la propuesta contra la rúbrica oficial. A partir de ellas:
  - el documento técnico cita trabajos previos sobre abstención en México (Lutz, 2005; Lizama Carrasco, 2012; INE, 2022);
  - se explica que ningún criterio elige por sí solo cinco perfiles y se reportan completas las cifras de la comparación con el método de Ward;
  - la validación judicial se describe como "los perfiles ordenan correctamente quién votó" y se aclara que explican un tercio de las diferencias;
  - los votos recuperables se describen como una estimación de la caída entre presidencial e intermedia;
  - la nota de uso responsable dice con precisión qué tablas tienen celdas pequeñas;
  - la descarga ahora se detiene si un archivo no coincide con su huella SHA-256.

## Qué sigue

- 31 de octubre: firmar las cartas de cesión de derechos y de decir verdad, armar el .zip con el nombre del equipo y el eje, y enviarlo a los dos correos antes de las 23:59.
