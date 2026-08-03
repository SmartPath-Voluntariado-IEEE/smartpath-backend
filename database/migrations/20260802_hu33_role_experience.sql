BEGIN;

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS role_experience TEXT;

COMMENT ON COLUMN public.users.role_experience IS
'Descripción de la experiencia previa del usuario relacionada con su rol objetivo';

NOTIFY pgrst, 'reload schema';

COMMIT;