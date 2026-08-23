-- ============================================
-- MIGRATION: ACHIEVEMENTS & GAMIFICATION
-- ============================================

CREATE TABLE IF NOT EXISTS achievements (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general', -- 'modules', 'quizzes', 'courses', 'roadmap', 'streak'
    icon_name VARCHAR(50) NOT NULL,
    badge_color VARCHAR(30) DEFAULT 'purple',
    criteria_type VARCHAR(50) NOT NULL,
    criteria_value INTEGER DEFAULT 1,
    xp_points INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_achievements (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(50) REFERENCES achievements(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (user_id, achievement_id)
);

-- ============================================
-- SEED INITIAL ACHIEVEMENTS
-- ============================================

INSERT INTO achievements (id, title, description, category, icon_name, badge_color, criteria_type, criteria_value, xp_points)
VALUES
    ('first-module-passed', 'Primer Paso', 'Aprueba tu primera evaluación de módulo con éxito.', 'modules', 'Target', 'purple', 'passed_modules_count', 1, 50),
    ('perfect-score', 'Puntaje Perfecto', 'Obtén una calificación perfecta del 100% en cualquier test.', 'quizzes', 'Award', 'emerald', 'perfect_score', 1, 100),
    ('three-modules-passed', 'Explorador Imparable', 'Completa 3 módulos evaluados satisfactoriamente.', 'modules', 'Zap', 'indigo', 'passed_modules_count', 3, 150),
    ('course-completed', 'Curso Conquistado', 'Aprueba todos los módulos de un curso activo.', 'courses', 'BookOpen', 'amber', 'completed_course', 1, 200),
    ('level-1-mastered', 'Fundamentos Dominados', 'Domina todas las habilidades clave del Nivel 1 en tu Roadmap.', 'roadmap', 'Trophy', 'orange', 'level_completed', 1, 300),
    ('streak-active', 'Hábito de Hierro', 'Mantén una racha de estudio activa en la plataforma.', 'streak', 'Flame', 'orange', 'streak_days', 3, 100)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    icon_name = EXCLUDED.icon_name,
    badge_color = EXCLUDED.badge_color,
    criteria_type = EXCLUDED.criteria_type,
    criteria_value = EXCLUDED.criteria_value,
    xp_points = EXCLUDED.xp_points;
