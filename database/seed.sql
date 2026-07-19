-- =======
--  SKILLS
-- =======

INSERT INTO skills (name, category, aliases) VALUES
-- Desarrollo de Software
('Python', 'Desarrollo de Software', ARRAY['python']),
('JavaScript', 'Desarrollo de Software', ARRAY['javascript', 'js', 'java script']),
('TypeScript', 'Desarrollo de Software', ARRAY['typescript', 'ts']),
('Java', 'Desarrollo de Software', ARRAY['java']),
('C#', 'Desarrollo de Software', ARRAY['c#', 'csharp', 'c sharp']),
('PHP', 'Desarrollo de Software', ARRAY['php']),
('React', 'Desarrollo de Software', ARRAY['react', 'reactjs', 'react.js']),
('Angular', 'Desarrollo de Software', ARRAY['angular', 'angularjs']),
('Vue.js', 'Desarrollo de Software', ARRAY['vue', 'vuejs', 'vue.js']),
('Node.js', 'Desarrollo de Software', ARRAY['node', 'nodejs', 'node.js']),
('Django', 'Desarrollo de Software', ARRAY['django']),
('Flask', 'Desarrollo de Software', ARRAY['flask']),
('FastAPI', 'Desarrollo de Software', ARRAY['fastapi', 'fast api']),
('Spring Boot', 'Desarrollo de Software', ARRAY['spring boot', 'spring']),
('.NET', 'Desarrollo de Software', ARRAY['dotnet', '.net', 'asp.net']),
('Git', 'Desarrollo de Software', ARRAY['git', 'github', 'gitlab']),
('SQL', 'Desarrollo de Software', ARRAY['sql']),
('APIs REST', 'Desarrollo de Software', ARRAY['api rest', 'rest api', 'restful']),
('Metodologías ágiles', 'Desarrollo de Software', ARRAY['scrum', 'kanban', 'agile', 'metodologias agiles', 'metodologías ágiles']),

-- Redes y Telecomunicaciones
('CCNA', 'Redes y Telecomunicaciones', ARRAY['ccna', 'cisco certified network associate']),
('Routing y Switching', 'Redes y Telecomunicaciones', ARRAY['routing', 'switching', 'enrutamiento', 'conmutacion', 'conmutación']),
('TCP/IP', 'Redes y Telecomunicaciones', ARRAY['tcp/ip', 'tcp ip']),
('Redes LAN/WAN', 'Redes y Telecomunicaciones', ARRAY['lan', 'wan', 'redes lan', 'redes wan']),
('Firewalls', 'Redes y Telecomunicaciones', ARRAY['firewall', 'cortafuegos']),
('VPN', 'Redes y Telecomunicaciones', ARRAY['vpn']),
('VoIP', 'Redes y Telecomunicaciones', ARRAY['voip', 'telefonia ip', 'telefonía ip']),
('Cableado estructurado', 'Redes y Telecomunicaciones', ARRAY['cableado estructurado']),
('Administración de servidores', 'Redes y Telecomunicaciones', ARRAY['administracion de servidores', 'administración de servidores']),
('Fibra óptica', 'Redes y Telecomunicaciones', ARRAY['fibra optica', 'fibra óptica']),

-- Ciberseguridad
('Seguridad de redes', 'Ciberseguridad', ARRAY['seguridad de redes', 'network security']),
('Ethical Hacking', 'Ciberseguridad', ARRAY['ethical hacking', 'hacking etico', 'hacking ético', 'pentesting', 'pruebas de penetracion', 'pruebas de penetración']),
('Análisis de vulnerabilidades', 'Ciberseguridad', ARRAY['analisis de vulnerabilidades', 'análisis de vulnerabilidades', 'vulnerability assessment']),
('SIEM', 'Ciberseguridad', ARRAY['siem']),
('Criptografía', 'Ciberseguridad', ARRAY['criptografia', 'criptografía', 'cryptography']),
('Gestión de incidentes', 'Ciberseguridad', ARRAY['gestion de incidentes', 'gestión de incidentes', 'incident response']),
('ISO 27001', 'Ciberseguridad', ARRAY['iso 27001', 'iso27001']),
('Firewalls y IDS/IPS', 'Ciberseguridad', ARRAY['ids', 'ips', 'intrusion detection', 'intrusion prevention']),

-- Ciencia de Datos / Analítica
('R', 'Ciencia de Datos / Analítica', ARRAY['r language', 'lenguaje r']),
('Pandas', 'Ciencia de Datos / Analítica', ARRAY['pandas']),
('Machine Learning', 'Ciencia de Datos / Analítica', ARRAY['machine learning', 'aprendizaje automatico', 'aprendizaje automático', 'ml']),
('Power BI', 'Ciencia de Datos / Analítica', ARRAY['power bi', 'powerbi']),
('Tableau', 'Ciencia de Datos / Analítica', ARRAY['tableau']),
('Excel avanzado', 'Ciencia de Datos / Analítica', ARRAY['excel avanzado', 'advanced excel']),
('Big Data', 'Ciencia de Datos / Analítica', ARRAY['big data']),
('Estadística', 'Ciencia de Datos / Analítica', ARRAY['estadistica', 'estadística', 'statistics']),
('Visualización de datos', 'Ciencia de Datos / Analítica', ARRAY['visualizacion de datos', 'visualización de datos', 'data visualization']),

-- Soporte TI / Infraestructura
('Mantenimiento de hardware', 'Soporte TI / Infraestructura', ARRAY['mantenimiento de hardware', 'hardware']),
('Soporte técnico', 'Soporte TI / Infraestructura', ARRAY['soporte tecnico', 'soporte técnico', 'help desk', 'mesa de ayuda']),
('Sistemas operativos', 'Soporte TI / Infraestructura', ARRAY['windows server', 'linux', 'sistemas operativos']),
('Active Directory', 'Soporte TI / Infraestructura', ARRAY['active directory']),
('Virtualización', 'Soporte TI / Infraestructura', ARRAY['virtualizacion', 'virtualización', 'vmware', 'hyper-v']),
('Resolución de incidencias', 'Soporte TI / Infraestructura', ARRAY['resolucion de incidencias', 'resolución de incidencias', 'troubleshooting']),
('ITIL', 'Soporte TI / Infraestructura', ARRAY['itil']),
('Gestión de inventario TI', 'Soporte TI / Infraestructura', ARRAY['gestion de inventario', 'gestión de inventario'])
ON CONFLICT (name) DO NOTHING;

-- =======
--  JOBS
-- =======
INSERT INTO jobs (company, position, salary, seniority, description) VALUES
('Rappi Perú', 'Practicante Backend Developer', 1800, 'Practicante', 'Buscamos practicante de Backend con conocimientos en Java, Spring Boot, REST APIs, Git, Docker y PostgreSQL. Deseable AWS y Scrum.'),
('BCP', 'Practicante Data Analyst', 1600, 'Practicante', 'Practicante de Data Analyst con SQL, Excel, Power BI y Python (Pandas). Inglés intermedio deseable.'),
('Culqi', 'Full Stack Developer Jr', 3500, 'Junior', 'Desarrollador Full Stack con React, TypeScript, Node.js, Tailwind, PostgreSQL, Git y GitHub. Docker y AWS son un plus.'),
('Interbank', 'Practicante Data Engineer', 2000, 'Practicante', 'Python, SQL, PostgreSQL, Airflow, Docker, GCP. Conocimientos en Pandas y Linux valorados.'),
('Yape', 'Frontend Developer Trainee', 2200, 'Practicante', 'React, Next.js, TypeScript, Tailwind CSS, Git. Conocimientos de REST APIs y buenas prácticas.'),
('NTT Data', 'Practicante Machine Learning', 2000, 'Practicante', 'Python, Pandas, TensorFlow, SQL. Deseable AWS, Docker e inglés intermedio.'),
('Belcorp', 'Backend Java Semi Senior', NULL, 'Semi Senior', 'Java, Spring Boot, REST APIs, Kubernetes, Docker, AWS, PostgreSQL, Git. Scrum.'),
('Fintech Startup', 'Full Stack Node + React', NULL, 'Junior', 'Node.js, JavaScript, TypeScript, React, MongoDB, REST APIs, Git, GitHub. Docker deseable.'),
('Globant', 'Practicante DevOps', NULL, 'Practicante', 'Linux, Docker, Kubernetes, AWS, Git, GitHub. Python es un plus.'),
('Alicorp', 'Data Analyst Junior', NULL, 'Junior', 'SQL, Power BI, Excel, Python, MySQL. Inglés intermedio.');

-- =======
--  COURSES
-- =======
INSERT INTO courses (platform, title, duration_hours, price, rating, url) VALUES
('Platzi', 'Git & GitHub desde cero', 8, 0.00, 4.80, '#'),
('Coursera', 'SQL para Análisis de Datos', 20, 0.00, 4.70, '#'),
('Udemy', 'Java + Spring Boot Master', 45, 39.00, 4.60, '#'),
('Udemy', 'React + TypeScript Pro', 30, 39.00, 4.70, '#'),
('Platzi', 'Docker y Kubernetes práctico', 25, 0.00, 4.50, '#'),
('AWS Skill Builder', 'AWS Cloud Practitioner', 15, 0.00, 4.60, '#'),
('DataCamp', 'Python para Data Science', 40, 0.00, 4.80, '#'),
('Udemy', 'Power BI de 0 a experto', 18, 39.00, 4.50, '#'),
('Udemy', 'Next.js 15 Full Stack', 28, 39.00, 4.70, '#'),
('Platzi', 'Node.js API REST profesional', 22, 0.00, 4.60, '#'),
('British Council', 'Inglés técnico para devs', 60, 199.00, 4.40, '#'),
('Coursera', 'TensorFlow Developer', 60, 149.00, 4.70, '#'),
('Udemy', 'PostgreSQL Avanzado', 15, 39.00, 4.50, '#'),
('Platzi', 'Linux para Desarrolladores', 12, 0.00, 4.60, '#'),
('Udemy', 'Tailwind CSS moderno', 10, 29.00, 4.60, '#');