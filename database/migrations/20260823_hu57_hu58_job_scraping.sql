-- ============================================
-- MIGRATION HU-57 / HU-58
-- HU-57: recolección de ofertas laborales por scraping (JobSpy).
-- HU-58: habilidades, tecnologías y requisitos extraídos de cada oferta.
--
-- La tabla `jobs` nació pensada para filas insertadas a mano por el seed:
-- no tenía forma de saber de dónde venía una fila ni de reconocer que una
-- oferta ya estaba guardada. Sin eso, cada corrida del recolector duplica
-- el catálogo. Esta migración añade procedencia, identidad externa y los
-- campos estructurados que HU-58 extrae de la descripción.
-- ============================================

-- --------------------------------------------
-- HU-57: procedencia y frescura
-- --------------------------------------------

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source VARCHAR(30);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS external_id VARCHAR(160);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS url TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS search_term VARCHAR(120);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_remote BOOLEAN;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_type VARCHAR(60);

-- Salario tal como lo publica la fuente. La columna `salary` original se
-- mantiene y guarda el valor normalizado a soles mensuales, porque
-- market_overview y job-matches ya dependen de ella.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_min INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_max INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_currency VARCHAR(10);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_interval VARCHAR(20);

-- La descripción de Indeed/LinkedIn supera con holgura los 120 caracteres
-- que aceptaban company y position en el esquema original.
ALTER TABLE jobs ALTER COLUMN company TYPE VARCHAR(200);
ALTER TABLE jobs ALTER COLUMN position TYPE VARCHAR(300);
ALTER TABLE jobs ALTER COLUMN location TYPE VARCHAR(200);
ALTER TABLE jobs ALTER COLUMN seniority TYPE VARCHAR(60);

-- Clave de deduplicación: una oferta es la misma si viene del mismo portal
-- con el mismo id externo. Es lo que permite que el recolector use upsert y
-- se pueda reejecutar sin inflar el catálogo.
--
-- El índice es un UNIQUE normal, no parcial: Postgres exige que un
-- ON CONFLICT repita el WHERE de un índice parcial para poder usarlo como
-- objetivo, y PostgREST (el upsert de Supabase) no lo añade — de ahí el
-- error "no unique or exclusion constraint matching the ON CONFLICT
-- specification". No hace falta el WHERE de todas formas: un UNIQUE normal
-- ya permite múltiples NULL en las mismas columnas, así que las filas
-- viejas sin `source` no chocan entre sí.
DROP INDEX IF EXISTS jobs_source_external_id_key;

CREATE UNIQUE INDEX jobs_source_external_id_key
    ON jobs (source, external_id);

CREATE INDEX IF NOT EXISTS jobs_scraped_at_idx ON jobs (scraped_at DESC);
CREATE INDEX IF NOT EXISTS jobs_posted_at_idx ON jobs (posted_at DESC);

-- --------------------------------------------
-- HU-58: requisitos extraídos de la descripción
-- --------------------------------------------

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS experience_years_min SMALLINT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS education_level VARCHAR(40);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS english_required BOOLEAN;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requirements JSONB DEFAULT '[]'::jsonb;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requirements_extracted_at TIMESTAMP;

-- `priority` distingue una tecnología exigida (2) de una deseable (1), que
-- es la diferencia que HU-58 pide reconocer dentro de los requisitos.
COMMENT ON COLUMN job_skills.priority IS
    '2 = requisito excluyente, 1 = deseable/mencionado';

COMMENT ON COLUMN jobs.requirements IS
    'HU-58: requisitos no técnicos detectados (educación, idioma, experiencia, contrato)';
