# HU-38 — Selección de fuentes de cursos

## Objetivo

Definir las plataformas educativas que SmartPath utilizará como fuentes para recolectar información de cursos de forma parcial y automatizada.

La selección debe priorizar fuentes que:

- Ofrezcan información útil para SmartPath.
- Permitan obtener datos de manera automatizada.
- Tengan una fuente oficial o estable.
- Entreguen metadatos como título, nivel, duración, URL y temática.
- No requieran técnicas frágiles o difíciles de mantener.

## Campos requeridos por SmartPath

La tabla `courses` utiliza los siguientes campos:

- `platform`
- `title`
- `instructor`
- `duration_hours`
- `language`
- `price`
- `rating`
- `level`
- `certificate`
- `url`

No es obligatorio que una fuente entregue todos los campos. Los campos faltantes podrán ser completados o normalizados posteriormente en HU-40.

## Fuentes evaluadas

| Plataforma | Método de acceso | Automatizable | Observación inicial |
|---|---|---:|---|
| Microsoft Learn | API REST oficial con Microsoft Entra | Sí | Fuente sólida, pero requiere autenticación y configuración previa en Azure. |
| Open edX | API REST | Parcial | La API está documentada, pero la instancia `courses.edx.org` presentó timeout durante la prueba, por lo que no se selecciona aún para el MVP. |
| Udemy | Affiliate API | Limitado | El acceso directo a la Affiliate API fue discontinuado y requiere acceso mediante su programa de afiliados. |

## Fuente seleccionada para el MVP

### Class Central Scraper mediante Apify

Se selecciona como fuente principal para la recolección automatizada de cursos.

La integración permite realizar búsquedas desde un único punto de acceso y obtener cursos provenientes de múltiples proveedores educativos, entre ellos Coursera, Udacity, freeCodeCamp, Simplilearn y otros.

Durante la prueba con la consulta `machine learning` se obtuvieron correctamente cursos de diferentes proveedores con información estructurada como:

- título
- proveedor
- institución
- rating
- nivel
- idioma
- disponibilidad gratuita
- URL del curso

Esta estrategia evita implementar una integración independiente para cada plataforma educativa.

### Fuente alternativa

freeCodeCamp puede mantenerse como una fuente secundaria mediante su repositorio oficial y GitHub API, en caso de requerir una fuente directa adicional.

## Política de gratuidad

SmartPath prioriza que el usuario pueda cerrar su brecha sin pagar. Por eso la recolección usa el parámetro `freeOnly` del actor en `true` por defecto, lo que habilita la oferta gratuita que Class Central ya indexa:

- **edX** — cursos abiertos de Harvard, MIT y otras universidades.
- **freeCodeCamp**
- **YouTube**
- **Coursera** — modalidad de auditoría gratuita.

`freeOnly` queda expuesto como query param en `/courses/collect` y `/courses/ingest`. Se desactiva solo para completar habilidades que no tengan oferta gratuita disponible.

### Criterio de "gratis"

`Free Trial Available` **no** cuenta como gratuito: el curso se cobra al terminar la prueba. El criterio único vive en `services/course_pricing.py`.

La gratuidad se persiste como el booleano `courses.is_free`, no como la etiqueta de texto `price`. Para las filas anteriores a la migración, el criterio cae automáticamente a `price`.

### Campos agregados

`institution` se conserva durante la normalización, porque el prestigio de la institución (Harvard, MIT, freeCodeCamp) es parte del valor de un curso gratuito.

Ambas columnas se crean con `docs/migrations/001_courses_free_metadata.sql`.

### Efecto en las recomendaciones

El orden de `/users/course-recommendations` es: **gratuidad → coincidencia con el formato preferido → rating**. El catálogo (`/catalog/courses`) también devuelve los gratuitos primero.