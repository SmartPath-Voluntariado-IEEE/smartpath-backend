# Base de datos

## Crear la BD local

    psql -U postgres -d roadmap_learning -f database/schema.sql

## Cargar datos de prueba

    psql -U postgres -d roadmap_learning -f database/seed.sql

El seed carga roles, habilidades, cursos y preguntas de evaluación. **No**
carga ofertas laborales: desde HU-57 se recolectan de portales reales con
`python scripts/scrape_jobs.py`. Ver `docs/job_sources.md`.

## Migraciones

`database/migrations/` contiene las migraciones incrementales, con fecha como
prefijo para que el orden alfabético sea el cronológico. Son idempotentes
(`IF NOT EXISTS`), así que reejecutarlas sobre una base ya migrada no rompe
nada.

    python database/run_migrations.py

Ese comando aplica `schema.sql`, `seed.sql` y luego todas las migraciones en
orden. Con `--reset` limpia la base antes (destructivo).

Si no hay acceso directo a Postgres, pegar el archivo de la migración en el
SQL Editor de Supabase.
