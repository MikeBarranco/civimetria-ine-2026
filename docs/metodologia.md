# Metodología

Este documento explica cada decisión del análisis y por qué se tomó. El código que la aplica está en `src/` y los números citados salen de la última corrida de `python src/ejecutar_todo.py`.

## 1. Pregunta y unidad de análisis

El Reto 1 pregunta qué tipos de ciudadanía existen según su comportamiento de participación, y pide segmentar con los datos de participación y después caracterizar cada grupo con edad, sexo, escolaridad, región e historial.

El CCPC no tiene datos de personas. Cada renglón es una combinación de sección electoral, sexo y edad, con cuántas personas de la lista nominal votaron, no votaron o no tienen dato. Con eso definimos la unidad del análisis:

- **Grupo ciudadano**: las personas de un mismo sexo y grupo de edad que viven en un mismo municipio, según la sección de su credencial. Ejemplo: mujeres de 25 a 29 años de Tijuana.
- Grupos de edad: 18-24, 25-29, 30-39, 40-49, 50-59 y 60 o más. Sexo: hombres y mujeres. El sexo no binario solo aparece en 2024 y con muy pocos registros; cuenta en los totales pero no forma grupos propios.
- Cada grupo pertenece a un solo municipio y a un solo perfil. Un municipio tiene hasta 12 grupos, así que puede tener personas de varios perfiles.
- **Perfil**: conjunto de grupos ciudadanos con un comportamiento de participación parecido.

Elegimos el municipio, y no la sección, porque a nivel sección los grupos son muy chicos y su porcentaje de participación cambia mucho con unos cuantos votos. Elegimos grupos de personas, y no municipios completos, porque el reto pide tipos de ciudadanía y porque dentro de un mismo municipio los jóvenes y los adultos mayores votan muy distinto.

## 2. Fuentes

| Fuente | Qué aporta | Uso |
|---|---|---|
| INE, CCPC 2009, 2012, 2015, 2018, 2021 y 2024 | Lista nominal, votos y registros sin dato por sección, sexo y edad | Base del modelo |
| INE, CCPC de la elección judicial 2024-2025 | Lo mismo para la elección de junio de 2025 | Solo validación |
| CONAPO, índice de marginación 2020 | Población sin educación básica, población en localidades de menos de 5 mil habitantes, grado de marginación | Caracterización |
| INEGI, Censo 2020, resultados por localidad (ITER) | Grado promedio de escolaridad, población en hogares indígenas, población afromexicana | Caracterización |

## 3. Cómo se mide la participación

En el CCPC cada registro de la lista nominal (LN) queda como SV (con marca de voto), NV (sin marca de voto) o NS (no especificado: cuadernillo sin marcas o no disponible para su captura). Siempre se cumple LN = SV + NV + NS.

Usamos **participación = SV / (SV + NV)**. Es la fórmula del manual de la plataforma CCPC del INE ("% Participación = Sí votaron / (Sí votaron + No votaron)"). Dividir entre LN contaría a los NS como si no hubieran votado, y los NS no se reparten parejo: hay municipios y años con entre 10% y 99% de NS. Con esta fórmula, la participación nacional de 2012, 2018 y 2024 (62.1%, 62.4% y 59.7%) es igual a la que publican los estudios de participación del INE.

Un municipio-año se deja como faltante si cumple cualquiera de estas condiciones:

1. **Cobertura menor a 50%**, donde cobertura = (SV + NV) / LN. Con menos de la mitad de los registros, lo observado ya no representa al municipio.
2. **Participación menor a 2%**. Todo el municipio aparece sin voto, señal de casillas no instaladas o no capturadas.
3. **Lista nominal incompleta**: menos del 80% del promedio de la elección anterior y la siguiente. El CCPC de 2012 trae 76.5 millones de registros, cuando la lista nominal oficial de ese año fue de unos 79.4 millones; en algunos municipios faltan secciones completas y la lista nominal se desploma ese año para recuperarse después.

Con estas reglas se marcan 321 de 14,779 municipio-año; 113 de ellos por lista nominal incompleta, casi todos de 2012.

## 4. Cruce con CONAPO e INEGI

La clave de municipio del INE no es la clave del INEGI. En 1,364 municipios la numeración es distinta; por ejemplo, en Colima la clave 06001 del INE es Colima y la del INEGI es Armería. Unir por clave pegaría los datos de un municipio a otro.

Por eso el cruce se hace por entidad y nombre normalizado (sin acentos, en mayúsculas y sin signos), más 25 equivalencias revisadas a mano para nombres que se escriben distinto en cada fuente. En los municipios de Oaxaca que se llaman igual (San Juan Mixtepec y San Pedro Mixtepec), la equivalencia se confirmó con la población. El script se detiene si una clave del INEGI se usa dos veces o si un cruce cambia de entidad.

Resultado: 2,469 de 2,477 municipios con dato censal. Los 8 restantes se crearon después del Censo 2020.

## 5. Variables de cada grupo ciudadano

Con los años válidos de cada grupo:

- **Participación presidencial**: promedio de 2012, 2018 y 2024.
- **Participación intermedia**: promedio de 2009, 2015 y 2021.
- **Nivel**: promedio de las dos anteriores. Se calcula así para que un grupo al que le falta un año no salga sesgado por el tipo de elección que le falta.
- **Brecha**: participación presidencial menos intermedia. Mide qué tanto depende el grupo de que haya elección presidencial.
- **Tendencia**: cambio estimado de 2009 a 2024 sin el efecto de la elección presidencial. Se obtiene con una regresión por grupo: participación = a + b × (año − 2009) / 15 + c × presidencial. La tendencia es b. Restar 2009 de 2024 directamente confundiría "subió" con "esta vez hubo elección presidencial", porque 2009 fue intermedia y 2024 presidencial.

Entran al modelo los grupos con al menos dos elecciones presidenciales y dos intermedias válidas, y con 50 personas o más. Son 28,158 grupos con 97.8 millones de personas, el 99.5% de la lista nominal.

## 6. Segmentación

- **Variables del agrupamiento**: nivel, brecha y tendencia. Responden tres preguntas sobre cómo participa un grupo: cuánto, qué tan parejo entre tipos de elección y hacia dónde va. Solo se usa comportamiento; la edad, el sexo y el contexto se usan después para describir.
- **Preparación**: cada variable se recorta a sus percentiles 1 y 99 y se estandariza con promedio y desviación ponderados por lista nominal.
- **Método**: k-means ponderado por lista nominal (cada grupo pesa según sus personas), con 50 inicios y semilla fija.
- **Número de perfiles**: se compararon de 3 a 7 perfiles con cuatro criterios.

| Perfiles | Silueta | Calinski-Harabasz | Davies-Bouldin | Estabilidad por remuestreo (ARI) |
|---|---|---|---|---|
| 3 | 0.279 | 4,565 | 1.12 | 0.94 |
| 4 | 0.263 | 4,538 | 1.12 | 0.92 |
| **5** | **0.243** | **4,004** | **1.19** | **0.92** |
| 6 | 0.228 | 3,683 | 1.11 | 0.87 |
| 7 | 0.222 | 3,667 | 1.19 | 0.86 |

Ningún criterio elige por sí solo cinco perfiles: la silueta, Calinski-Harabasz y la estabilidad favorecen tres, y Davies-Bouldin, seis. La decisión es de interpretación. Tres perfiles quedan fuera del rango de 4 a 6 que pide el reto. Con cuatro, se juntan en un solo perfil quienes votan en presidenciales y faltan en intermedias con quienes casi no votan en ninguna; son personas distintas que piden estrategias distintas. Con cinco se separan, y la estabilidad es igual o mayor que con cuatro (su peor remuestreo es 0.81 contra 0.69). Así quedan los tres comportamientos clásicos de la literatura sobre participación (constantes, intermitentes y ocasionales) y dos que solo se ven con historial: grupos cuya participación sube y grupos cuya participación baja.

- **Nombres**: se asignan con reglas fijas, en este orden y entre los perfiles que aún no tienen nombre: el de mayor brecha es Intermitentes; el de tendencia más negativa, En descenso; el de tendencia más positiva, En ascenso; de los dos restantes, el de mayor nivel es Constantes y el de menor, Ocasionales. Si los datos cambian, los nombres se reasignan solos.
- **Claridad**: para cada grupo, 1 − (distancia a su centro / distancia al segundo centro más cercano). Cerca de 0, el grupo está en la frontera entre dos perfiles. El 11.6% de las personas está en grupos con claridad menor a 0.1.

## 7. Caracterización

Cada perfil se describe con promedios ponderados por lista nominal de:

- participación en cada elección, presidencial e intermedia;
- composición por sexo y grupo de edad;
- porcentaje en secciones urbanas (INE) y población en localidades de menos de 5 mil habitantes (CONAPO);
- grado promedio de escolaridad y población en hogares indígenas y afromexicana (INEGI), y población sin educación básica (CONAPO);
- entidades con más personas del perfil y municipios donde es mayoría.

Las variables de escolaridad, indígena y afromexicana son del municipio del grupo, no de las personas del grupo. Por eso el reto habla de "posible escolaridad".

## 8. Focalización municipal

Para decidir dónde actuar, cada municipio recibe:

- **Votos recuperables en intermedias**: suma, sobre sus grupos, de lista nominal × brecha. Estima la caída neta de participación entre presidencial e intermedia; como el CCPC no sigue a cada votante de una elección a otra, no dice cuántas personas distintas forman esa caída. La siguiente elección federal, en junio de 2027, es intermedia. En total son unos 13.0 millones; los 100 municipios con más concentran el 60%.
- **Índice de prioridad (0 a 100)**: combina el déficit de participación en intermedias (40%), el tamaño de la lista nominal (30%) y la brecha (30%). Cada componente se convierte a rango percentil para que ningún municipio extremo domine la escala. Los pesos son un criterio del equipo; la sección 9 muestra que el orden casi no cambia si se mueven. No se calcula para los 29 municipios sin historial suficiente, casi todos creados después de 2018.

## 9. Robustez y validación

| Prueba | Resultado |
|---|---|
| Remuestreo (30 veces) | 29 de 30 recuperan la misma segmentación; ARI mediano 0.93 |
| Estabilidad por perfil (Jaccard mediano; 0.75 se considera estable y 0.85 muy estable) | Intermitentes 0.87, Ocasionales 0.92, En descenso 0.93, En ascenso 0.96, Constantes 0.95 |
| Semillas distintas | ARI mínimo 0.98 |
| Otro método (agrupamiento jerárquico de Ward) | Coincide en 90% con En ascenso, 81% con Ocasionales, 74% con Intermitentes, 59% con Constantes y 57% con En descenso |
| Grupos de 200 personas o más en vez de 50 | 99.4% de las personas queda en el mismo perfil |
| Sin recortar valores extremos | 99.4% queda en el mismo perfil |
| Participación presidencial e intermedia en vez de nivel y brecha | 67.2% queda en el mismo perfil |
| Pesos del índice de prioridad movidos 0.1 | Correlación de rangos de 0.98 o más; se conservan al menos 86 de los 100 municipios prioritarios |
| Validación temporal: variables con 2009-2018 contra lo observado en 2021 | Correlación de 0.85 para el nivel y de 0.41 para la brecha frente a la caída de 2018 a 2021 |
| Validación externa: elección judicial 2025, que no entra al modelo | En ascenso 20.0%, Constantes 16.4%, Intermitentes 12.0%, Ocasionales 8.2%, En descenso 7.8% (nacional 13.0%); el perfil explica el 32% de las diferencias entre grupos |

Dos lecturas de esta tabla. La segmentación es estable frente a cambios menores, pero depende de cómo se define "comportamiento": con presidencial e intermedia, el nivel pesa el doble y la intermitencia pierde peso. Elegimos nivel, brecha y tendencia porque dan el mismo peso a las tres preguntas. Y otros métodos de agrupamiento cortan distinto los perfiles con bordes graduales (Constantes y En descenso), lo que confirma que la participación cambia de forma continua: los perfiles resumen esa variación, no son categorías naturales con fronteras nítidas.

## 10. Otros análisis

- **Edad exacta**: con los totales nacionales por edad, en todas las elecciones se vota más a los 18 años que a los 19 (61.5% contra 53.4% en 2024), y la participación toca fondo entre los 23 y los 26 años. La caída ocurre justo después del primer voto.
- **Probado y descartado**: agrupar por la trayectoria completa de seis elecciones ordena a los grupos casi solo por su nivel y pierde la intermitencia y la tendencia (coincide en 27% con el modelo). También probamos si el tipo de la primera elección de una persona (presidencial o intermedia) cambia cómo vota después, como sugiere la literatura reciente; el efecto en estos datos es de 0.6 puntos y no es concluyente.

## 11. Supuestos y limitaciones

- **Datos agregados.** Los perfiles describen grupos, no personas. Afirmar algo de una persona a partir del promedio de su grupo sería una falacia ecológica.
- **Grupos de edad, no cohortes.** El grupo de 25 a 29 años de 2009 no son las mismas personas que el de 2024. El historial de un grupo es el de esa franja de edad en ese municipio.
- **Fuente de la participación.** El CCPC se basa en los cuadernillos de la lista nominal: no incluye casillas especiales ni voto en el extranjero, y ubica a las personas por el domicilio de su credencial. Por eso difiere un poco de los cómputos distritales (por ejemplo, 51.8% contra 52.7% en 2021).
- **Contexto de 2020.** Escolaridad, marginación y población indígena y afromexicana son del Censo 2020 y del municipio, no del grupo.
- **Bordes graduales.** El 11.6% de las personas está en grupos de frontera entre dos perfiles.
- **Causas.** El CCPC dice quién votó, no por qué. Las estrategias para el perfil En descenso parten de un diagnóstico, no de una causa supuesta.

## 12. Uso responsable

Solo usamos datos públicos y agregados. Los perfiles se calculan con grupos de 50 personas o más. Las tablas intermedias de `datos/procesados` reproducen agregados que el INE ya publica con más detalle, por sección; en municipios pequeños algunas de sus celdas tienen muy pocas personas. El análisis no usa datos sobre preferencias políticas. Los perfiles están pensados para la educación cívica y el fomento de la participación, no para fines partidistas.

## 13. Reproducibilidad

- Un solo comando, `python src/ejecutar_todo.py`, corre todo en unos 9 minutos.
- Versiones de librerías fijas en `requirements.txt`; Python 3.14.
- Semillas aleatorias fijas.
- Huella SHA-256 de cada archivo de origen en `datos/huellas_crudos.csv`; si una fuente publica una versión distinta, el script lo avisa.
- `src/10_verificaciones.py` revisa 18 condiciones al final de cada corrida y termina con error si alguna falla.
