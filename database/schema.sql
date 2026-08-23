-- ============================================
-- ROLE TARGETS
-- ============================================

CREATE TABLE role_targets (
    id VARCHAR(30) PRIMARY KEY,
    label VARCHAR(100) NOT NULL
);

-- ============================================
-- USERS
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id TEXT UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    career VARCHAR(120),
    university VARCHAR(150),
    academic_cycle SMALLINT,
    english_level VARCHAR(30),
    experience_level VARCHAR(50),
    role_experience TEXT,
    weekly_hours INTEGER,
    professional_goal VARCHAR(100),
    target_role_id VARCHAR(30) REFERENCES role_targets(id),
    interests TEXT[],
    learning_preferences TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SKILLS
-- ============================================

CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(60),
    description TEXT,
    difficulty SMALLINT DEFAULT 1,
    aliases TEXT[]
);

-- ============================================
-- ROLE TARGET SKILLS (relación roles <-> skills core)
-- ============================================

CREATE TABLE role_target_skills (
    role_id VARCHAR(30) REFERENCES role_targets(id) ON DELETE CASCADE,
    skill_slug VARCHAR(50) REFERENCES skills(slug) ON DELETE CASCADE,
    PRIMARY KEY(role_id, skill_slug)
);

-- ============================================
-- USER SKILLS
-- ============================================

CREATE TABLE user_skills (
    user_id UUID,
    skill_id INTEGER,
    level SMALLINT DEFAULT 1,
    PRIMARY KEY(user_id, skill_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ============================================
-- KNOWLEDGE GRAPH
-- Skill prerequisites
-- ============================================

CREATE TABLE skill_prerequisites (
    skill_id INTEGER,
    prerequisite_skill_id INTEGER,
    PRIMARY KEY(skill_id, prerequisite_skill_id),
    FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    FOREIGN KEY(prerequisite_skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ============================================
-- JOB OFFERS
-- ============================================

CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    company VARCHAR(120),
    position VARCHAR(120),
    salary INTEGER,
    seniority VARCHAR(40),
    description TEXT,
    location VARCHAR(100),
    posted_at DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- JOB SKILLS
-- ============================================

CREATE TABLE job_skills (
    job_id INTEGER,
    skill_id INTEGER,
    priority SMALLINT DEFAULT 1,
    PRIMARY KEY(job_id, skill_id),
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ============================================
-- COURSES
-- ============================================

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(80),
    title VARCHAR(200),
    instructor VARCHAR(120),
    duration_hours INTEGER,
    language VARCHAR(40),
    price VARCHAR(50), -- Cambiado de NUMERIC a VARCHAR para almacenar textos como "Suscripción" o "S/ 39"
    rating NUMERIC(3,2),
    level VARCHAR(20), -- Añadida columna level ("Básico", "Intermedio", "Avanzado")
    certificate BOOLEAN DEFAULT FALSE,
    url TEXT
);

-- ============================================
-- COURSE SKILLS
-- ============================================

CREATE TABLE course_skills (
    course_id INTEGER,
    skill_id INTEGER,
    PRIMARY KEY(course_id, skill_id),
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ============================================
-- EVALUATION QUESTIONS
-- ============================================

CREATE TABLE evaluation_questions (
    id SERIAL PRIMARY KEY,
    skill_slug VARCHAR(50) NOT NULL
        REFERENCES skills(slug)
        ON DELETE CASCADE,
    question TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_option SMALLINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EVALUATION ATTEMPTS
-- ============================================

CREATE TABLE evaluation_attempts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,
    skill_slug VARCHAR(50) NOT NULL
        REFERENCES skills(slug)
        ON DELETE CASCADE,
    score NUMERIC(5,2) NOT NULL
        CHECK (score >= 0 AND score <= 100),
    correct_answers INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- USER MODULE PROGRESS
-- ============================================

CREATE TABLE user_module_progress (
    user_id UUID NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,
    skill_slug VARCHAR(50) NOT NULL
        REFERENCES skills(slug)
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

ALTER TABLE evaluation_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_module_progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own evaluation attempts"
ON evaluation_attempts
FOR SELECT
TO authenticated
USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own evaluation attempts"
ON evaluation_attempts
FOR INSERT
TO authenticated
WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can read own module progress"
ON user_module_progress
FOR SELECT
TO authenticated
USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own module progress"
ON user_module_progress
FOR INSERT
TO authenticated
WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own module progress"
ON user_module_progress
FOR UPDATE
TO authenticated
USING ((SELECT auth.uid()) = user_id)
WITH CHECK ((SELECT auth.uid()) = user_id);

-- ============================================
-- ACHIEVEMENTS (GAMIFICACIÓN)
-- ============================================

CREATE TABLE achievements (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    icon_name VARCHAR(50) NOT NULL,
    badge_color VARCHAR(30) DEFAULT 'purple',
    criteria_type VARCHAR(50) NOT NULL,
    criteria_value INTEGER DEFAULT 1,
    xp_points INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_achievements (
    user_id UUID,
    achievement_id VARCHAR(50),
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY(user_id, achievement_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);