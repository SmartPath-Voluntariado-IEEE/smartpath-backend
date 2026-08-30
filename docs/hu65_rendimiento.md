# HU-65 — Rendimiento de las secciones de cursos y perfil

> *Como usuario, quiero que las secciones de cursos y perfil carguen más
> rápido, para tener una experiencia fluida al usar la plataforma.*

## Diagnóstico

Ambas pantallas eran lentas por la misma razón: **cada petición volvía a
pedirle a Supabase datos que casi nunca cambian**, y el frontend esperaba a
que *todo* terminara antes de pintar algo.

| Causa | Detalle |
|---|---|
| Catálogo sin caché | `skills`, `role_targets`, `courses` y `jobs` se consultaban por red en cada request. Medido: **4.6 s** en traer el catálogo completo una vez. |
| Un cliente Supabase por consulta | `get_db_client(token)` llamaba a `create_client()` en cada uso → handshake TLS nuevo. Medido: **~370 ms** por cliente, y se creaban 2+ por request autenticado. |
| Perfil en dos viajes | `UserService.get_profile()` consultaba `users` y luego `user_skills` por separado. |
| Perfil leído dos veces | `/users/roadmap` pedía el perfil, y además llamaba al endpoint de gap-analysis, que lo volvía a pedir. |
| Frontend bloqueante | `/cursos` esperaba `getRoadmap` (el endpoint más caro) solo para saber qué pestañas mostrar; `/perfil` mostraba un spinner de pantalla completa hasta que llegaban los catálogos. |

## Cambios

### Backend

- **`core/cache.py` (nuevo)** — caché en memoria con TTL, thread-safe, agrupada
  por *namespace* e invalidable. La función se ejecuta fuera del lock para que
  una consulta lenta no bloquee las lecturas de otras peticiones.
- **`services/catalog_service.py`** — `get_all_skills`, `get_all_role_targets`,
  `get_all_courses`, `get_all_jobs`, `get_role_skills` y `get_market_overview`
  quedan cacheadas 10 min. Se agregó `CatalogService.invalidate_cache()`.
- **`api/routes.py`** — `/jobs/collect`, `/jobs/extract-requirements` y
  `/courses/ingest` invalidan la caché al terminar, para que lo recién escrito
  se vea de inmediato. Se extrajo `_build_gap_analysis(profile)` para que
  `/users/roadmap` y `/dashboard/course-progress` reutilicen el perfil ya
  cargado en vez de volver a pedirlo.
- **`database/database.py`** — los clientes autenticados se reutilizan por token
  (LRU de 128), conservando el aislamiento de RLS. `clear_token_clients()` para
  pruebas.
- **`services/user_service.py`** — el perfil y sus habilidades se traen en una
  sola consulta anidada, con retorno al camino de dos consultas si PostgREST no
  resuelve la relación.
- **`main.py`** — `GZipMiddleware` (el catálogo de cursos son cientos de KB).

### Frontend

- **`lib/request-cache.ts` (nuevo)** — caché de peticiones por sesión de
  navegación que además **deduplica**: guarda la promesa, no el resultado, así
  dos llamadas simultáneas comparten una sola petición. Los errores no se
  cachean.
- **`services/api.ts`** — cachea `getCatalogSkills`, `getCatalogRoles`,
  `getCatalogCourses` (por habilidad/página) y `getRoadmap` (por token).
  `upsertBackendProfile`, `selectCourseForSkill` y `unlinkCourseFromSkill`
  invalidan el roadmap cacheado.
- **`app/cursos/page.tsx`** — carga en tres pasos: (1) pestañas de habilidad con
  el perfil local, que ya está en localStorage; (2) el roadmap las refina en
  segundo plano; (3) el progreso de cursos llega aparte y solo cambia el estado
  de los botones. La grilla tiene su propio *skeleton* en vez de bloquear la
  pantalla.
- **`app/perfil/page.tsx`** — el formulario se pinta con los datos locales al
  instante; el selector de roles y la lista de habilidades muestran su propia
  carga.

## Mediciones (contra la base de datos real)

Catálogo, primera llamada vs. cacheada:

| Consulta | Sin caché | Cacheada | Filas |
|---|---:|---:|---:|
| `get_all_skills` | 1895 ms | ~0 ms | 70 |
| `get_all_role_targets` | 561 ms | ~0 ms | 7 |
| `get_all_courses` | 670 ms | ~0 ms | 1000 |
| `get_all_jobs` | 1539 ms | ~0 ms | 233 |
| `get_market_overview` | (deriva de jobs) | ~0 ms | — |
| **Total** | **4665 ms** | **~0 ms** | |

Consultas de catálogo que hace `/users/roadmap`: **2566 ms → ~0 ms** a partir de
la segunda visita.

Creación de clientes Supabase: **1853 ms → 386 ms** por 5 llamadas con el mismo
token (solo la primera crea el cliente).

> Las cifras se tomaron en una corrida local contra Supabase; el valor absoluto
> depende de la latencia de red, pero la relación entre columnas se mantiene.

## Verificación

- Backend: `pytest` → **87 pruebas pasan** (80 previas + 7 nuevas en
  `tests/test_cache.py`, que cubren TTL, separación por argumentos, expiración,
  invalidación por namespace y reutilización de clientes).
- `conftest.py` limpia caché y clientes entre pruebas para que ninguna vea el
  estado de otra.
- Frontend: `tsc --noEmit` y `next build` correctos; `eslint` sin errores nuevos.

## Cómo probarlo

1. Levantar el backend (`./run.ps1`) y el frontend (`npm run dev`).
2. Abrir `/cursos`: las pestañas de habilidad aparecen de inmediato y la grilla
   muestra el *skeleton* mientras cargan los cursos.
3. Cambiar de pestaña y volver: la respuesta es instantánea (caché de cliente).
4. Abrir `/perfil`: el formulario se ve al instante; el selector de roles se
   completa en cuanto llega el catálogo.
5. Tras correr `/courses/ingest` o `/jobs/collect`, la siguiente lectura ya
   muestra los datos nuevos (la caché se invalida sola).

## Riesgo conocido

El catálogo puede quedar hasta 10 minutos desactualizado si alguien escribe en
esas tablas **directamente en Supabase**, sin pasar por el backend. Las
escrituras hechas desde la API invalidan la caché al instante. Si hace falta un
TTL distinto, se ajusta en `CATALOG_TTL_SECONDS` (`services/catalog_service.py`).
