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
    weekly_hours INTEGER,
    professional_goal VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SKILLS
-- ============================================

CREATE TABLE skills (

    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(60),
    description TEXT,
    difficulty SMALLINT DEFAULT 1,
    aliases TEXT[]
);

-- ============================================
-- USER SKILLS
-- ============================================

CREATE TABLE user_skills (
    user_id UUID,
    skill_id INTEGER,
    level SMALLINT DEFAULT 1,
    PRIMARY KEY(user_id,skill_id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(skill_id) REFERENCES skills(id)

);

-- ============================================
-- KNOWLEDGE GRAPH
-- Skill prerequisites
-- ============================================

CREATE TABLE skill_prerequisites (

    skill_id INTEGER,
    prerequisite_skill_id INTEGER,
    PRIMARY KEY(skill_id,prerequisite_skill_id),
    FOREIGN KEY(skill_id) REFERENCES skills(id),
    FOREIGN KEY(prerequisite_skill_id) REFERENCES skills(id)

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

-- ============================================
-- JOB SKILLS
-- ============================================

CREATE TABLE job_skills (
    job_id INTEGER,
    skill_id INTEGER,
    priority SMALLINT DEFAULT 1,
    PRIMARY KEY(job_id,skill_id),
    FOREIGN KEY(job_id) REFERENCES jobs(id),
    FOREIGN KEY(skill_id) REFERENCES skills(id)

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
    price NUMERIC(8,2),
    rating NUMERIC(3,2),
    certificate BOOLEAN DEFAULT FALSE,
    url TEXT

);

-- ============================================
-- COURSE SKILLS
-- ============================================

CREATE TABLE course_skills (

    course_id INTEGER,
    skill_id INTEGER,
    PRIMARY KEY(course_id,skill_id),
    FOREIGN KEY(course_id) REFERENCES courses(id),
    FOREIGN KEY(skill_id) REFERENCES skills(id)

);