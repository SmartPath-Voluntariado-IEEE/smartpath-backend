-- 001 — Metadatos de gratuidad e institución en `courses`
--
-- Contexto: SmartPath prioriza cursos gratuitos. Hasta ahora la gratuidad solo
-- existía como la etiqueta de texto `price` ('Free' / 'Paid Course' /
-- 'Free Trial Available'), y la institución que dicta el curso (Harvard, MIT,
-- freeCodeCamp…) se descartaba durante la normalización.
--
-- Ejecutar en: Supabase → SQL Editor. Es idempotente.

alter table public.courses
    add column if not exists institution text,
    add column if not exists is_free boolean;

-- Backfill de las 582 filas existentes a partir de la etiqueta `price`.
-- 'Free Trial Available' queda en false a propósito: el curso se paga al
-- terminar la prueba.
update public.courses
set is_free = (lower(trim(price)) in ('free', 'free course', 'free online course'))
where is_free is null;

alter table public.courses
    alter column is_free set default false;

-- El ranking y el catálogo filtran y ordenan por gratuidad en cada request.
create index if not exists courses_is_free_idx
    on public.courses (is_free);
