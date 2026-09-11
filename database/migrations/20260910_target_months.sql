BEGIN;

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS target_months INTEGER DEFAULT 6;

COMMENT ON COLUMN public.users.target_months IS
'Plazo objetivo en meses para completar la ruta de aprendizaje';

NOTIFY pgrst, 'reload schema';

COMMIT;
