# HU-57 / HU-58 — Recolección de ofertas laborales

## Objetivo

**HU-57.** Extraer información relevante de las ofertas laborales mediante un
proceso de scraping definido, para disponer de datos actualizados del mercado
tecnológico.

**HU-58.** Identificar las habilidades, tecnologías y requisitos presentes en
las ofertas recolectadas, para enriquecer la información que usa SmartPath.

Ambas alimentan la pestaña **Bolsa laboral** del frontend, que recomienda
ofertas alineadas con la ruta que el usuario eligió en el onboarding.

---

## Punto de partida

Antes de esta HU, la tabla `jobs` tenía 35 filas de dos orígenes, ninguno
sostenible:

| Origen | Filas | Problema |
|---|---|---|
| `seed.sql` | 10 | Ofertas escritas a mano. Un mercado laboral inventado hace que toda recomendación calculada sobre él no signifique nada. |
| API de TheirStack | 25 | API de pago; la clave `THEIRSTACK_API_KEY` no estaba configurada, así que el recolector no podía ejecutarse. |

Además, `jobs` no tenía forma de saber de dónde venía una fila ni de
reconocer una oferta ya guardada, y el recolector hacía `insert` plano: cada
corrida duplicaba el catálogo.

---

## Fuente elegida: JobSpy

[`python-jobspy`](https://github.com/cullenwatson/JobSpy) raspa Indeed,
LinkedIn, Glassdoor, ZipRecruiter y Bayt con una sola interfaz.

Por qué se eligió:

- **Cobertura local real.** Indeed con `country_indeed="peru"` devuelve
  ofertas peruanas con la descripción completa en español, que es lo que
  HU-58 necesita analizar.
- **Sin API de pago ni claves.** No hay costo por corrida ni credencial que
  gestionar, a diferencia de TheirStack.
- **Un solo formato de salida.** Todos los portales devuelven las mismas
  columnas, así que añadir LinkedIn no obliga a escribir otro normalizador.

### Configuración por defecto

Solo se consulta **Indeed**. LinkedIn se deja fuera por defecto porque limita
por IP muy rápido y una corrida bloqueada deja el lote entero vacío; se
activa con `JOBSPY_SITES=indeed,linkedin` cuando haya proxies configurados.

Variables de entorno (todas opcionales, con valor por defecto en
`core/config.py`):

| Variable | Por defecto | Qué controla |
|---|---|---|
| `JOBSPY_SITES` | `indeed` | Portales a consultar, separados por coma |
| `JOBSPY_COUNTRY` | `peru` | País de Indeed |
| `JOBSPY_LOCATION` | `Peru` | Ubicación buscada |
| `JOBSPY_RESULTS_PER_TERM` | `25` | Ofertas por término y portal |
| `JOBSPY_HOURS_OLD` | `720` | Antigüedad máxima (30 días) |
| `JOBSPY_DELAY_SECONDS` | `3` | Pausa entre términos, contra el rate limit |
| `JOBSPY_PROXIES` | vacío | Proxies, separados por coma |

### Instalación

`python-jobspy` **no se instala desde `requirements.txt`**: fija
`numpy==1.26.3`, que no publica wheels para Python 3.13+ y hace que pip
intente compilar numpy desde fuente. Se instala aparte, y `setup.ps1` ya lo
hace:

```
pip install python-jobspy==1.1.82 --no-deps
```

Sus dependencias reales (pandas, numpy, markdownify, regex, requests,
tls-client) sí están en `requirements.txt`.

---

## HU-57: el proceso de recolección

`services/job_scraping_service.py`.

### Términos de búsqueda

No se busca "trabajo de programador" en abstracto: los términos derivan de
los **roles objetivo** que ofrece el onboarding (`role_targets`), para que el
catálogo recolectado cubra las rutas que los usuarios realmente eligen.

Cada rol tiene términos en español y en inglés, porque los portales peruanos
publican el mismo puesto de las dos formas. A eso se suman términos extra
(`practicante de sistemas`, `programador junior`) que traen los puestos de
entrada que son el público de SmartPath.

### Normalización

Cada fila de JobSpy se traduce a la forma de `jobs`. Los puntos que no son
obvios:

- **NaN de pandas.** JobSpy devuelve un DataFrame: las celdas ausentes llegan
  como `NaN`, y `str(nan)` da la cadena `'nan'`. Sin filtro, una empresa sin
  nombre se guardaría literalmente como `"nan"`.
- **Seniority deducido del título.** Indeed Perú casi nunca rellena
  `job_level`, pero el nivel viene en el título ("Practicante de Sistemas").
  Sin esta deducción, los rangos salariales por nivel de `market_overview`
  quedarían todos bajo "Sin especificar".
- **Salario.** `salary_min/max/currency/interval` guardan lo que publica el
  portal. La columna legacy `salary` guarda el equivalente **mensual en
  soles**, y solo cuando el importe ya viene en soles: `market_overview`
  promedia esa columna sin mirar la moneda, y mezclar un sueldo anual en
  dólares con uno mensual en soles daría un promedio sin significado.

### Deduplicación

Cada oferta se guarda con `source` + `external_id`, con un índice único sobre
ese par, y el guardado es un **upsert**. Eso permite correr el recolector a
diario sin inflar el catálogo: una oferta ya vista se actualiza.

El lote se deduplica también en memoria antes de enviarlo, porque Postgres
rechaza un `ON CONFLICT` que afecte dos veces a la misma fila en una misma
sentencia, y un término puede devolver la misma oferta en dos páginas.

### Tolerancia a fallos

Un término que falle (rate limit, portal caído) no aborta la corrida: se
registra en `errors` y el resto continúa.

---

## HU-58: habilidades, tecnologías y requisitos

`services/job_requirements_service.py`.

### Tecnologías

Se reutiliza `skill_matcher`, el mismo criterio que ya usan cursos y
vacantes, para que "React" signifique lo mismo en todo el backend.

**Exigido vs. deseable** es el punto fino. Un aviso que pide "React
(excluyente)" y menciona "deseable Docker" no está pidiendo lo mismo en ambos
casos, y una recomendación que los trate igual manda al usuario a postular a
puestos para los que no califica.

El análisis es **por línea**: se detecta la sección activa (`Requisitos:` /
`Deseable:`) y cada tecnología hereda la exigencia de la línea donde se la
nombró. Una marca dentro de la propia línea pesa más que la sección. Si una
tecnología aparece dos veces, manda la exigencia más alta.

Se guarda en `job_skills.priority`: **2 = excluyente, 1 = deseable**.

### Requisitos no técnicos

Se extraen a `jobs.requirements` (JSONB) como lista de objetos
`{type, label, value}`, lista para pintarse como chips sin volver a parsear:

| Tipo | Ejemplo | Columna dedicada |
|---|---|---|
| `experiencia` | "2 años de experiencia" | `experience_years_min` |
| `educacion` | "Titulado" | `education_level` |
| `idioma` | "Inglés intermedio" | `english_required` |
| `contrato` | "Prácticas" | — |
| `modalidad` | "Híbrido" | — |

En años de experiencia se toma el **mínimo** encontrado, no el primero: un
aviso que dice "2 años en backend" y "5 años liderando" pide 2 años para
entrar, y quedarse con el 5 excluiría al usuario de una oferta a la que sí
puede postular.

---

## Bolsa laboral: recomendación por ruta

`services/job_recommendation_service.py`, endpoint
`GET /users/job-recommendations`.

`GET /users/job-matches` (HU-62) ya existía y contesta otra cosa: qué
porcentaje de lo que pide una oferta ya sabe el usuario hoy. Eso deja arriba
las ofertas fáciles aunque no tengan que ver con la ruta — una oferta que
pide solo Excel da 100% para casi cualquiera.

El puntaje nuevo combina dos señales y **las devuelve por separado**, para
que la interfaz explique el porqué en vez de mostrar un número opaco:

- **Alineación** (60%): cuánto tiene que ver la oferta con la ruta elegida.
  Es el promedio de "qué parte de la oferta es de mi ruta" y "qué parte de mi
  ruta cubre la oferta". Las dos lecturas se corrigen entre sí: la primera
  sola premiaría a un aviso que pide una única tecnología de la ruta; la
  segunda sola premiaría a los avisos que enumeran veinte tecnologías.
- **Preparación** (40%): cuánto de lo que la oferta **exige** ya domina el
  usuario. Se mide contra los requisitos excluyentes cuando el aviso los
  distingue.
- **Bonus de nivel** (+8 puntos): si el nivel del puesto encaja con la
  experiencia declarada. Es pequeño a propósito: ordena entre ofertas
  parecidas, no debe rescatar una oferta irrelevante.

La respuesta incluye `missing_from_route`: lo que le falta al usuario y su
ruta **sí enseña**. Es el puente con el roadmap, y la razón por la que esta
pestaña vive dentro de SmartPath y no es un portal de empleo más.

---

## Cómo ejecutarlo

### 1. Aplicar la migración

`database/migrations/20260823_hu57_hu58_job_scraping.sql` añade procedencia,
identidad externa y los campos de HU-58. Es idempotente.

```
python database/run_migrations.py
```

o pegar el archivo en el SQL Editor de Supabase.

### 2. Retirar las ofertas antiguas (destructivo)

```
python scripts/scrape_jobs.py --purge-seed
```

Borra las filas con `source` vacío: las 10 sembradas a mano y las 25 de
TheirStack. Pide confirmación escrita.

### 3. Recolectar

```
# Todo el catálogo (17 términos; tarda varios minutos)
python scripts/scrape_jobs.py

# Prueba rápida
python scripts/scrape_jobs.py --roles backend,frontend --results 10

# Reanalizar habilidades y requisitos de lo ya guardado
python scripts/scrape_jobs.py --only-requirements
```

El script es la vía pensada para una tarea programada diaria: una
recolección completa no entra en el ciclo de una petición HTTP.

---

## Endpoints

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/jobs/search?search_term=…` | Previsualiza lo que devuelve un portal, sin guardar |
| `POST` | `/jobs/collect` | Recolecta y guarda (HU-57 + HU-58) |
| `POST` | `/jobs/extract-requirements` | Reanaliza habilidades y requisitos (HU-58) |
| `GET` | `/users/job-recommendations` | Bolsa laboral: ofertas alineadas con la ruta |

---

## Limitaciones conocidas

- **Términos amplios traen ruido.** "practicante de sistemas" devuelve también
  prácticas de contabilidad. No se filtran al recolectar: sin tecnologías
  detectadas, HU-58 les da alineación 0 y quedan al fondo de la bolsa.
- **Indeed rara vez publica salario.** La mayoría de ofertas peruanas llegan
  sin importe, así que los rangos salariales de `market_overview` se apoyan en
  una fracción del catálogo.
- **LinkedIn necesita proxies** para una recolección sostenida.
