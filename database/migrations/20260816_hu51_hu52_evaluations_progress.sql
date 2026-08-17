BEGIN;

-- ============================================
-- HU-51: PREGUNTAS DE EVALUACION POR MODULO
-- Cada skill del roadmap funciona como modulo.
-- ============================================

CREATE TABLE IF NOT EXISTS public.evaluation_questions (
    id SERIAL PRIMARY KEY,
    skill_slug VARCHAR(50) NOT NULL
        REFERENCES public.skills(slug)
        ON DELETE CASCADE,
    question TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_option SMALLINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- HU-52: RESULTADOS DE EVALUACIONES
-- ============================================

CREATE TABLE IF NOT EXISTS public.evaluation_attempts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL
        REFERENCES public.users(id)
        ON DELETE CASCADE,
    skill_slug VARCHAR(50) NOT NULL
        REFERENCES public.skills(slug)
        ON DELETE CASCADE,
    score NUMERIC(5,2) NOT NULL
        CHECK (score >= 0 AND score <= 100),
    correct_answers INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- HU-52: PROGRESO ACTUAL DEL MODULO
-- ============================================

CREATE TABLE IF NOT EXISTS public.user_module_progress (
    user_id UUID NOT NULL
        REFERENCES public.users(id)
        ON DELETE CASCADE,
    skill_slug VARCHAR(50) NOT NULL
        REFERENCES public.skills(slug)
        ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started'
        CHECK (
            status IN (
                'not_started',
                'in_progress',
                'completed'
            )
        ),
    best_score NUMERIC(5,2)
        CHECK (
            best_score IS NULL
            OR (best_score >= 0 AND best_score <= 100)
        ),
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, skill_slug)
);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE public.evaluation_questions
ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.evaluation_attempts
ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.user_module_progress
ENABLE ROW LEVEL SECURITY;


-- Cada usuario solo puede leer sus intentos.
CREATE POLICY "Users can read own evaluation attempts"
ON public.evaluation_attempts
FOR SELECT
TO authenticated
USING (
    (SELECT auth.uid()) = user_id
);

-- Cada usuario solo puede crear intentos para si mismo.
CREATE POLICY "Users can create own evaluation attempts"
ON public.evaluation_attempts
FOR INSERT
TO authenticated
WITH CHECK (
    (SELECT auth.uid()) = user_id
);

-- Cada usuario solo puede leer su propio progreso.
CREATE POLICY "Users can read own module progress"
ON public.user_module_progress
FOR SELECT
TO authenticated
USING (
    (SELECT auth.uid()) = user_id
);

-- Cada usuario solo puede crear su propio progreso.
CREATE POLICY "Users can create own module progress"
ON public.user_module_progress
FOR INSERT
TO authenticated
WITH CHECK (
    (SELECT auth.uid()) = user_id
);

-- Cada usuario solo puede actualizar su propio progreso.
CREATE POLICY "Users can update own module progress"
ON public.user_module_progress
FOR UPDATE
TO authenticated
USING (
    (SELECT auth.uid()) = user_id
)
WITH CHECK (
    (SELECT auth.uid()) = user_id
);

NOTIFY pgrst, 'reload schema';

COMMIT;