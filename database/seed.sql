-- ============================================
-- SEED: ROLE TARGETS
-- ============================================

INSERT INTO role_targets (id, label) VALUES
('backend', 'Backend Developer'),
('frontend', 'Frontend Developer'),
('fullstack', 'Full Stack Developer'),
('data-analyst', 'Data Analyst'),
('data-engineer', 'Data Engineer'),
('ml', 'Machine Learning Engineer'),
('devops', 'DevOps Engineer')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- SEED: SKILLS
-- ============================================

INSERT INTO skills (name, slug, category, aliases) VALUES
-- Desarrollo de Software
('Python', 'python', 'language', ARRAY['python']),
('JavaScript', 'javascript', 'language', ARRAY['javascript', 'js', 'java script']),
('TypeScript', 'typescript', 'language', ARRAY['typescript', 'ts']),
('Java', 'java', 'language', ARRAY['java']),
('C#', 'csharp', 'language', ARRAY['c#', 'csharp', 'c sharp']),
('PHP', 'php', 'language', ARRAY['php']),
('React', 'react', 'framework', ARRAY['react', 'reactjs', 'react.js']),
('Next.js', 'nextjs', 'framework', ARRAY['next.js', 'nextjs', 'next']),
('Angular', 'angular', 'framework', ARRAY['angular', 'angularjs']),
('Vue.js', 'vuejs', 'framework', ARRAY['vue', 'vuejs', 'vue.js']),
('Node.js', 'nodejs', 'framework', ARRAY['node', 'nodejs', 'node.js']),
('Django', 'django', 'framework', ARRAY['django']),
('Flask', 'flask', 'framework', ARRAY['flask']),
('FastAPI', 'fastapi', 'framework', ARRAY['fastapi', 'fast api']),
('Spring Boot', 'springboot', 'framework', ARRAY['spring boot', 'spring']),
('.NET', 'dotnet', 'framework', ARRAY['dotnet', '.net', 'asp.net']),
('Git', 'git', 'tool', ARRAY['git', 'github', 'gitlab']),
('GitHub', 'github', 'tool', ARRAY['github']),
('Docker', 'docker', 'tool', ARRAY['docker']),
('SQL', 'sql', 'language', ARRAY['sql']),
('APIs REST', 'rest', 'methodology', ARRAY['api rest', 'rest api', 'restful']),
('Metodologías ágiles', 'scrum', 'methodology', ARRAY['scrum', 'kanban', 'agile', 'metodologias agiles', 'metodologías ágiles']),
('GraphQL', 'graphql', 'methodology', ARRAY['graphql']),
('Tailwind CSS', 'tailwind', 'framework', ARRAY['tailwind']),

-- Redes y Telecomunicaciones
('CCNA', 'ccna', 'tool', ARRAY['ccna', 'cisco certified network associate']),
('Routing y Switching', 'routing_switching', 'methodology', ARRAY['routing', 'switching', 'enrutamiento', 'conmutacion', 'conmutación']),
('TCP/IP', 'tcp_ip', 'methodology', ARRAY['tcp/ip', 'tcp ip']),
('Redes LAN/WAN', 'lan_wan', 'methodology', ARRAY['lan', 'wan', 'redes lan', 'redes wan']),
('Firewalls', 'firewalls', 'tool', ARRAY['firewall', 'cortafuegos']),
('VPN', 'vpn', 'tool', ARRAY['vpn']),
('VoIP', 'voip', 'tool', ARRAY['voip', 'telefonia ip', 'telefonía ip']),
('Cableado estructurado', 'structured_cabling', 'methodology', ARRAY['cableado estructurado']),
('Administración de servidores', 'sysadmin', 'methodology', ARRAY['administracion de servidores', 'administración de servidores']),
('Fibra óptica', 'fiber_optics', 'tool', ARRAY['fibra optica', 'fibra óptica']),

-- Ciberseguridad
('Seguridad de redes', 'network_security', 'methodology', ARRAY['seguridad de redes', 'network security']),
('Ethical Hacking', 'ethical_hacking', 'methodology', ARRAY['ethical hacking', 'hacking etico', 'hacking ético', 'pentesting', 'pruebas de penetracion', 'pruebas de penetración']),
('Análisis de vulnerabilidades', 'vulnerability_analysis', 'methodology', ARRAY['analisis de vulnerabilidades', 'análisis de vulnerabilidades', 'vulnerability assessment']),
('SIEM', 'siem', 'tool', ARRAY['siem']),
('Criptografía', 'cryptography', 'methodology', ARRAY['criptografia', 'criptografía', 'cryptography']),
('Gestión de incidentes', 'incident_management', 'methodology', ARRAY['gestion de incidentes', 'gestión de incidentes', 'incident response']),
('ISO 27001', 'iso_27_001', 'methodology', ARRAY['iso 27001', 'iso27001']),
('Firewalls y IDS/IPS', 'ids_ips', 'tool', ARRAY['ids', 'ips', 'intrusion detection', 'intrusion prevention']),

-- Ciencia de Datos / Analítica
('R', 'r', 'language', ARRAY['r language', 'lenguaje r']),
('Pandas', 'pandas', 'framework', ARRAY['pandas']),
('Machine Learning', 'machine_learning', 'methodology', ARRAY['machine learning', 'aprendizaje automatico', 'aprendizaje automático', 'ml']),
('Power BI', 'powerbi', 'tool', ARRAY['powerbi', 'power bi']),
('Tableau', 'tableau', 'tool', ARRAY['tableau']),
('Excel avanzado', 'excel', 'tool', ARRAY['excel avanzado', 'advanced excel']),
('Big Data', 'big_data', 'methodology', ARRAY['big data']),
('Estadística', 'statistics', 'methodology', ARRAY['estadistica', 'estadística', 'statistics']),
('Visualización de datos', 'data_visualization', 'methodology', ARRAY['visualizacion de datos', 'visualización de datos', 'data visualization']),
('TensorFlow', 'tensorflow', 'framework', ARRAY['tensorflow']),
('PostgreSQL', 'postgres', 'database', ARRAY['postgresql', 'postgres']),
('MongoDB', 'mongodb', 'database', ARRAY['mongo', 'mongodb']),
('MySQL', 'mysql', 'database', ARRAY['mysql']),
('Redis', 'redis', 'database', ARRAY['redis']),

-- Soporte TI / Infraestructura
('Mantenimiento de hardware', 'hardware_maintenance', 'tool', ARRAY['mantenimiento de hardware', 'hardware']),
('Soporte técnico', 'tech_support', 'tool', ARRAY['soporte tecnico', 'soporte técnico', 'help desk', 'mesa de ayuda']),
('Sistemas operativos', 'os', 'tool', ARRAY['windows server', 'linux', 'sistemas operativos']),
('Active Directory', 'active_directory', 'tool', ARRAY['active directory']),
('Virtualización', 'virtualization', 'methodology', ARRAY['virtualizacion', 'virtualización', 'vmware', 'hyper-v']),
('Resolución de incidencias', 'troubleshooting', 'methodology', ARRAY['resolucion de incidencias', 'resolución de incidencias', 'troubleshooting']),
('ITIL', 'itil', 'methodology', ARRAY['itil']),
('Gestión de inventario TI', 'it_inventory', 'methodology', ARRAY['gestion de inventario', 'gestión de inventario']),
('Linux', 'linux', 'tool', ARRAY['linux']),
('Inglés', 'english', 'soft', ARRAY['ingles', 'english']),
('Kubernetes', 'kubernetes', 'tool', ARRAY['kubernetes', 'k8s']),
('AWS', 'aws', 'cloud', ARRAY['aws']),
('Azure', 'azure', 'cloud', ARRAY['azure']),
('GCP', 'gcp', 'cloud', ARRAY['gcp', 'google cloud'])
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- SEED: ROLE TARGET SKILLS
-- ============================================

INSERT INTO role_target_skills (role_id, skill_slug) VALUES
('backend', 'java'), ('backend', 'springboot'), ('backend', 'rest'), ('backend', 'sql'), ('backend', 'postgres'), ('backend', 'docker'), ('backend', 'git'), ('backend', 'aws'),
('frontend', 'javascript'), ('frontend', 'typescript'), ('frontend', 'react'), ('frontend', 'nextjs'), ('frontend', 'tailwind'), ('frontend', 'git'), ('frontend', 'rest'),
('fullstack', 'typescript'), ('fullstack', 'react'), ('fullstack', 'nodejs'), ('fullstack', 'postgres'), ('fullstack', 'git'), ('fullstack', 'rest'), ('fullstack', 'docker'),
('data-analyst', 'sql'), ('data-analyst', 'excel'), ('data-analyst', 'powerbi'), ('data-analyst', 'python'), ('data-analyst', 'pandas'), ('data-analyst', 'english'),
('data-engineer', 'python'), ('data-engineer', 'sql'), ('data-engineer', 'postgres'), ('data-engineer', 'docker'), ('data-engineer', 'linux'), ('data-engineer', 'gcp'), ('data-engineer', 'aws'),
('ml', 'python'), ('ml', 'pandas'), ('ml', 'tensorflow'), ('ml', 'sql'), ('ml', 'docker'), ('ml', 'aws'), ('ml', 'english'),
('devops', 'linux'), ('devops', 'docker'), ('devops', 'kubernetes'), ('devops', 'aws'), ('devops', 'git'), ('devops', 'python')
ON CONFLICT (role_id, skill_slug) DO NOTHING;

-- ============================================
-- SEED: JOBS
-- ============================================

INSERT INTO jobs (company, position, salary, seniority, description, location, posted_at) VALUES
('Rappi Perú', 'Practicante Backend Developer', 1800, 'Practicante', 'Buscamos practicante de Backend con conocimientos en Java, Spring Boot, REST APIs, Git, Docker y PostgreSQL. Deseable AWS y Scrum.', 'Lima, Remoto', '2026-07-10'),
('BCP', 'Practicante Data Analyst', 1600, 'Practicante', 'Practicante de Data Analyst con SQL, Excel, Power BI y Python (Pandas). Inglés intermedio deseable.', 'Lima, Perú', '2026-07-12'),
('Culqi', 'Full Stack Developer Jr', 3500, 'Junior', 'Desarrollador Full Stack con React, TypeScript, Node.js, Tailwind, PostgreSQL, Git y GitHub. Docker y AWS son un plus.', 'Remoto', '2026-07-14'),
('Interbank', 'Practicante Data Engineer', 2000, 'Practicante', 'Python, SQL, PostgreSQL, Airflow, Docker, GCP. Conocimientos en Pandas y Linux valorados.', 'Lima, Perú', '2026-07-08'),
('Yape', 'Frontend Developer Trainee', 2200, 'Practicante', 'React, Next.js, TypeScript, Tailwind CSS, Git. Conocimientos de REST APIs y buenas prácticas.', 'Lima, Híbrido', '2026-07-15'),
('NTT Data', 'Practicante Machine Learning', 2000, 'Practicante', 'Python, Pandas, TensorFlow, SQL. Deseable AWS, Docker e inglés intermedio.', 'Lima, Perú', '2026-07-11'),
('Belcorp', 'Backend Java Semi Senior', NULL, 'Semi Senior', 'Java, Spring Boot, REST APIs, Kubernetes, Docker, AWS, PostgreSQL, Git. Scrum.', 'Remoto', '2026-07-09'),
('Fintech Startup', 'Full Stack Node + React', NULL, 'Junior', 'Node.js, JavaScript, TypeScript, React, MongoDB, REST APIs, Git, GitHub. Docker deseable.', 'Remoto', '2026-07-13'),
('Globant', 'Practicante DevOps', NULL, 'Practicante', 'Linux, Docker, Kubernetes, AWS, Git, GitHub. Python es un plus.', 'Lima, Remoto', '2026-07-07'),
('Alicorp', 'Data Analyst Junior', NULL, 'Junior', 'SQL, Power BI, Excel, Python, MySQL. Inglés intermedio.', 'Lima, Perú', '2026-07-12');

-- ============================================
-- SEED: COURSES
-- ============================================

INSERT INTO courses (platform, title, duration_hours, price, rating, level, url) VALUES
('Platzi', 'Git & GitHub desde cero', 8, 'Suscripción', 4.80, 'Básico', '#'),
('Coursera', 'SQL para Análisis de Datos', 20, 'Gratis', 4.70, 'Básico', '#'),
('Udemy', 'Java + Spring Boot Master', 45, 'S/ 39', 4.60, 'Intermedio', '#'),
('Udemy', 'React + TypeScript Pro', 30, 'S/ 39', 4.70, 'Intermedio', '#'),
('Platzi', 'Docker y Kubernetes práctico', 25, 'Suscripción', 4.50, 'Intermedio', '#'),
('AWS Skill Builder', 'AWS Cloud Practitioner', 15, 'Gratis', 4.60, 'Básico', '#'),
('DataCamp', 'Python para Data Science', 40, 'Suscripción', 4.80, 'Básico', '#'),
('Udemy', 'Power BI de 0 a experto', 18, 'S/ 39', 4.50, 'Básico', '#'),
('Udemy', 'Next.js 15 Full Stack', 28, 'S/ 39', 4.70, 'Intermedio', '#'),
('Platzi', 'Node.js API REST profesional', 22, 'Suscripción', 4.60, 'Intermedio', '#'),
('British Council', 'Inglés técnico para devs', 60, 'S/ 199', 4.40, 'Intermedio', '#'),
('Coursera', 'TensorFlow Developer', 60, 'S/ 149', 4.70, 'Avanzado', '#'),
('Udemy', 'PostgreSQL Avanzado', 15, 'S/ 39', 4.50, 'Intermedio', '#'),
('Platzi', 'Linux para Desarrolladores', 12, 'Suscripción', 4.60, 'Básico', '#'),
('Udemy', 'Tailwind CSS moderno', 10, 'S/ 29', 4.60, 'Básico', '#');

-- ============================================
-- SEED: COURSE SKILLS MAPPING
-- ============================================

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Git & GitHub desde cero' AND s.slug IN ('git', 'github');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'SQL para Análisis de Datos' AND s.slug = 'sql';

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Java + Spring Boot Master' AND s.slug IN ('java', 'springboot', 'rest');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'React + TypeScript Pro' AND s.slug IN ('react', 'typescript');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Docker y Kubernetes práctico' AND s.slug IN ('docker', 'kubernetes');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'AWS Cloud Practitioner' AND s.slug = 'aws';

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Python para Data Science' AND s.slug IN ('python', 'pandas');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Power BI de 0 a experto' AND s.slug = 'powerbi';

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Next.js 15 Full Stack' AND s.slug IN ('nextjs', 'react');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Node.js API REST profesional' AND s.slug IN ('nodejs', 'rest');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Inglés técnico para devs' AND s.slug = 'english';

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'TensorFlow Developer' AND s.slug IN ('tensorflow', 'python');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'PostgreSQL Avanzado' AND s.slug IN ('postgres', 'sql');

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Linux para Desarrolladores' AND s.slug = 'linux';

INSERT INTO course_skills (course_id, skill_id)
SELECT c.id, s.id FROM courses c, skills s WHERE c.title = 'Tailwind CSS moderno' AND s.slug = 'tailwind';

-- ============================================
-- SEED: EVALUATION QUESTIONS
-- HU-51 / HU-52
-- ============================================

-- PYTHON

INSERT INTO public.evaluation_questions
(skill_slug, question, options, correct_option)
SELECT
    'python',
    '¿Qué palabra clave se utiliza para definir una función en Python?',
    '["func", "def", "function", "lambda"]'::jsonb,
    1
WHERE NOT EXISTS (
    SELECT 1
    FROM public.evaluation_questions
    WHERE skill_slug = 'python'
      AND question = '¿Qué palabra clave se utiliza para definir una función en Python?'
);

INSERT INTO public.evaluation_questions
(skill_slug, question, options, correct_option)
SELECT
    'python',
    '¿Qué devuelve len([1, 2, 3])?',
    '["2", "3", "4", "Error"]'::jsonb,
    1
WHERE NOT EXISTS (
    SELECT 1
    FROM public.evaluation_questions
    WHERE skill_slug = 'python'
      AND question = '¿Qué devuelve len([1, 2, 3])?'
);

INSERT INTO public.evaluation_questions
(skill_slug, question, options, correct_option)
SELECT
    'python',
    '¿Cuál de estas estructuras es mutable en Python?',
    '["tuple", "str", "list", "int"]'::jsonb,
    2
WHERE NOT EXISTS (
    SELECT 1
    FROM public.evaluation_questions
    WHERE skill_slug = 'python'
      AND question = '¿Cuál de estas estructuras es mutable en Python?'
);


-- SQL

INSERT INTO public.evaluation_questions
(skill_slug, question, options, correct_option)
SELECT
    'sql',
    '¿Qué comando se utiliza para consultar datos de una tabla?',
    '["SELECT", "UPDATE", "DELETE", "DROP"]'::jsonb,
    0
WHERE NOT EXISTS (
    SELECT 1
    FROM public.evaluation_questions
    WHERE skill_slug = 'sql'
      AND question = '¿Qué comando se utiliza para consultar datos de una tabla?'
);

INSERT INTO public.evaluation_questions
(skill_slug, question, options, correct_option)
SELECT
    'sql',
    '¿Qué cláusula permite filtrar filas en SQL?',
    '["ORDER BY", "WHERE", "GROUP BY", "JOIN"]'::jsonb,
    1
WHERE NOT EXISTS (
    SELECT 1
    FROM public.evaluation_questions
    WHERE skill_slug = 'sql'
      AND question = '¿Qué cláusula permite filtrar filas en SQL?'
);

INSERT INTO public.evaluation_questions
(skill_slug, question, options, correct_option)
SELECT
    'sql',
    '¿Qué comando agrega una nueva fila a una tabla?',
    '["ALTER", "SELECT", "INSERT", "CREATE"]'::jsonb,
    2
WHERE NOT EXISTS (
    SELECT 1
    FROM public.evaluation_questions
    WHERE skill_slug = 'sql'
      AND question = '¿Qué comando agrega una nueva fila a una tabla?'
);

-- ============================================
-- ACHIEVEMENTS SEED
-- ============================================

INSERT INTO achievements (id, title, description, category, icon_name, badge_color, criteria_type, criteria_value, xp_points)
VALUES
    ('first-module-passed', 'Primer Paso', 'Aprueba tu primera evaluación de módulo con éxito.', 'modules', 'Target', 'purple', 'passed_modules_count', 1, 50),
    ('perfect-score', 'Puntaje Perfecto', 'Obtén una calificación perfecta del 100% en cualquier test.', 'quizzes', 'Award', 'emerald', 'perfect_score', 1, 100),
    ('three-modules-passed', 'Explorador Imparable', 'Completa 3 módulos evaluados satisfactoriamente.', 'modules', 'Zap', 'indigo', 'passed_modules_count', 3, 150),
    ('course-completed', 'Curso Conquistado', 'Aprueba todos los módulos de un curso activo.', 'courses', 'BookOpen', 'amber', 'completed_course', 1, 200),
    ('level-1-mastered', 'Fundamentos Dominados', 'Domina todas las habilidades clave del Nivel 1 en tu Roadmap.', 'roadmap', 'Trophy', 'orange', 'level_completed', 1, 300),
    ('streak-active', 'Hábito de Hierro', 'Mantén una racha de estudio activa en la plataforma.', 'streak', 'Flame', 'orange', 'streak_days', 3, 100)
ON CONFLICT (id) DO NOTHING;