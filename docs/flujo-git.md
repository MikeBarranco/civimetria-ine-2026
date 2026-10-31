# Flujo de trabajo en git

Cómo manejamos el repositorio durante el concurso.

## Cómo trabajamos

Trabajamos directo en la rama main, con GitHub Desktop. Los dos revisamos el código, los resultados y los documentos y propusimos cambios; los acordábamos y se subían desde la cuenta de Miguel. No usamos ramas porque nunca editamos los mismos archivos al mismo tiempo.

Antes de cada commit corrimos `python src/ejecutar_todo.py` cuando el cambio tocaba el análisis, para que las 18 verificaciones automáticas pasaran con el código nuevo.

## Convención de commits

Cada commit empieza con un tipo, dos puntos y una descripción corta en minúscula (Conventional Commits):

`tipo: descripción corta de lo que se hizo`

Tipos que usamos:
- docs: documentación (README, metodología, diccionario, entregables).
- feat: una parte nueva del análisis.
- fix: corrección de un error.

La descripción dice qué cambió, en una línea. Si hace falta más detalle, va en la descripción larga del commit.

## Cómo subir cambios con GitHub Desktop

1. Del lado izquierdo, en Changes, aparecen los archivos modificados.
2. En Summary se escribe el título del commit con la convención de arriba.
3. En Description (opcional) se ponen los detalles.
4. Clic en Commit to main.
5. Clic en Push origin para subirlo a GitHub.
