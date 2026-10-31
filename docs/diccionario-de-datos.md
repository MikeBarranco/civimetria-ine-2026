# Diccionario de datos

Qué significa cada columna de las fuentes y de los archivos que produce el análisis. Las participaciones están en porcentaje (0 a 100) y las brechas y tendencias en puntos porcentuales.

## Fuentes originales (datos/crudos, no se suben)

### INE, Conteos Censales de Participación Ciudadana

Un ZIP por elección (`CCPC2009.zip` a `CCPC2024.zip` y `CCPC_PJ2025.zip`), con un CSV por entidad. Cada renglón es una combinación de sección, sexo y edad.

- AELEC: año de la elección.
- EDOCVE, EDONOM: clave INE y nombre de la entidad.
- MPIOCVE, MPIONOM: clave INE y nombre del municipio. La clave INE no es la del INEGI.
- SECCION: sección electoral en el año correspondiente.
- TIPOSEC: tipo de sección (U urbana, M mixta, R rural).
- DEF, DEL: distrito federal y local (en 2025, también CJ y DEJ: circuito y distrito judicial).
- SEXO: 0 hombres, 1 mujeres, 2 no binario (solo 2024).
- EDAD: años cumplidos el día de la elección.
- LN: lista nominal de los cuadernillos.
- SV: registros con marca de voto.
- NV: registros sin marca de voto.
- NS: registros no especificados (cuadernillo sin marcas o no disponible). LN = SV + NV + NS.

### CONAPO, índice de marginación por municipio 2020 (`CONAPO_IMM_2020.xlsx`)

Se usan POB_TOT (población), ANALF (porcentaje analfabeta), SBASC (porcentaje sin educación básica, 15 años o más), PL.5000 (porcentaje en localidades de menos de 5 mil habitantes), PO2SM (porcentaje de ocupados con ingreso de hasta 2 salarios mínimos), IM_2020 (índice de marginación; en esta edición un valor más alto significa menos marginación), GM_2020 (grado de marginación) e IMN_2020 (índice normalizado).

### INEGI, Censo 2020, principales resultados por localidad (`INEGI_ITER_2020.zip`)

Se usa el renglón de total municipal (LOC = 0000): POBTOT (población total), P_3YMAS y P3YM_HLI (población de 3 años o más y la que habla lengua indígena), PHOG_IND (población en hogares censales indígenas), POB_AFRO (población afromexicana o afrodescendiente) y GRAPROES (grado promedio de escolaridad).

## Archivos del análisis (datos/procesados)

Las tablas por municipio, sexo y edad agregan los datos públicos del CCPC, que el INE publica por sección. En municipios pequeños algunas celdas tienen muy pocas personas (79 tienen una sola), igual que en la fuente. Los perfiles solo usan grupos de 50 personas o más. En participacion_nacional_edad.csv las edades muy altas (hasta 140 años) vienen así del CCPC; las gráficas llegan a 85 años.

### participacion_municipio_sexo_edad.csv

Una fila por municipio, sexo, grupo de edad y elección. Base de los grupos ciudadanos.

- cve_muni: clave INE del municipio (5 dígitos).
- sexo: 0 hombres, 1 mujeres, 2 no binario.
- grupo_edad: 18-24, 25-29, 30-39, 40-49, 50-59 o 60+.
- LN, SV, NV, NS: conteos del CCPC.
- anio: año de la elección.
- anio_valido: si ese municipio-año pasa las reglas de calidad (ver metodología, sección 3).

### participacion_municipio_largo.csv

Una fila por municipio y elección.

- lista_nominal, SV, NV, NS: conteos totales.
- cobertura: (SV + NV) / LN, en porcentaje.
- continuidad_ln: lista nominal entre el promedio de la elección anterior y la siguiente.
- anio_valido: si pasa las reglas de calidad.
- participacion: SV / (SV + NV), vacía si el año no es válido.
- part_jovenes_valida, part_mujeres_valida, part_hombres_valida: participación de 18 a 29 años, de mujeres y de hombres.
- pct_urbano: porcentaje de la lista nominal en secciones urbanas.

### participacion_municipio.csv

Una fila por municipio con su historial.

- entidad, municipio, lista_nominal (del año válido más reciente), pct_urbano.
- part_2009 a part_2024: participación de cada elección.
- anios_con_dato, n_presidenciales, n_intermedias: cuántas elecciones válidas tiene.
- historial_suficiente: al menos dos presidenciales y dos intermedias válidas.
- part_presidencial, part_intermedia: promedios por tipo de elección.
- part_promedio: promedio de los dos anteriores.
- brecha_pres_inter: presidencial menos intermedia.
- tendencia: cambio de 2009 a 2024 sin el efecto presidencial.
- part_jovenes, part_mujeres, part_hombres: promedio balanceado entre tipos de elección.

### municipio_enriquecido.csv

Lo anterior más el cruce censal.

- cve_inegi: clave INEGI del municipio. municipio_conapo: nombre en CONAPO, para revisar el cruce.
- poblacion_2020, pct_analfabeta, pct_sin_educacion_basica, pct_localidades_menores_5mil, pct_ingreso_hasta_2sm, indice_marginacion, grado_marginacion, marginacion_normalizada: de CONAPO.
- grado_promedio_escolaridad, pct_poblacion_indigena (hogares indígenas entre población total), pct_habla_lengua_indigena, pct_afromexicana: del INEGI.

### grupos_ciudadanos.csv

Una fila por grupo ciudadano (municipio, sexo y grupo de edad).

- part_2009 a part_2024: participación del grupo en cada elección válida.
- lista_nominal: tamaño del grupo en su elección válida más reciente.
- part_presidencial, part_intermedia, nivel, brecha, tendencia: variables del modelo (ver metodología, sección 5).
- en_modelo: si entra a la segmentación (historial suficiente y 50 personas o más).
- entidad, municipio y variables de contexto de su municipio: pct_urbano, pct_localidades_menores_5mil, pct_sin_educacion_basica, grado_promedio_escolaridad, pct_poblacion_indigena, pct_afromexicana, grado_marginacion.

### grupos_perfiles.csv

Una fila por grupo del modelo.

- perfil: Intermitentes, Ocasionales, En descenso, En ascenso o Constantes.
- perfil_cercano: el segundo perfil más cercano.
- claridad: 1 menos la razón entre la distancia a su perfil y al segundo más cercano. Cerca de 0, el grupo está en la frontera.

### perfiles_resumen.csv

Una fila por perfil, con promedios ponderados por lista nominal.

- personas, pct_personas, grupos, municipios_presentes.
- nivel, brecha, tendencia, part_presidencial, part_intermedia, part_2009 a part_2024.
- pct_hombres y pct_18-24 a pct_60+: composición por sexo y edad.
- pct_urbano, pct_localidades_menores_5mil, pct_sin_educacion_basica, grado_promedio_escolaridad, pct_poblacion_indigena, pct_afromexicana: contexto.
- votos_recuperables_intermedia: suma de lista nominal × brecha.
- no_votarian_intermedia: personas que no votarían en una intermedia con su participación intermedia promedio.
- entidades_principales: las cuatro entidades con más personas del perfil.
- municipios_donde_es_mayoria.

### municipio_focalizacion.csv

Lo de municipio_enriquecido más:

- personas_{perfil} y pct_{perfil}: personas de cada perfil en el municipio.
- perfil_mayoritario.
- votos_recuperables_intermedia: suma sobre sus grupos de lista nominal × brecha.
- no_votarian_intermedia: lista nominal × (100 menos participación intermedia).
- prioridad: índice de 0 a 100 (ver metodología, sección 8). rank_prioridad: lugar nacional.

### participacion_judicial2025_sexo_edad.csv

Igual que participacion_municipio_sexo_edad para la elección judicial de 2025. Solo se usa para validar.

### participacion_nacional_edad.csv

Totales nacionales por elección (incluida 2025), sexo y edad exacta: LN, SV, NV, NS.

## Tablas de resultados (resultados/tablas)

- eleccion_k.csv: silueta, Calinski-Harabasz, Davies-Bouldin y estabilidad por remuestreo para 3 a 7 perfiles.
- reparto_sexo_edad.csv: de cada sexo y grupo de edad, qué porcentaje de sus personas está en cada perfil.
- robustez_perfiles.csv: estabilidad por perfil (Jaccard mediano y porcentaje de remuestreos estables) y coincidencia con el método de Ward.
- robustez_decisiones.csv: cuánto cambia la segmentación con otras decisiones del análisis.
- robustez_pesos.csv: efecto de cada combinación de pesos sobre el índice de prioridad.
- validacion_temporal.csv y validacion_judicial2025.csv: validaciones.
- civimetria_tablero_municipal.xlsx: Excel para uso del INE, con hojas Léeme, Municipios, Perfiles, Sexo y edad, y Por entidad.
