-- Borrar todas las tablas existentes en orden de dependencia para reiniciar limpiamente
DROP TABLE IF EXISTS course_skills CASCADE;
DROP TABLE IF EXISTS job_skills CASCADE;
DROP TABLE IF EXISTS skill_prerequisites CASCADE;
DROP TABLE IF EXISTS user_skills CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS role_target_skills CASCADE;
DROP TABLE IF EXISTS role_targets CASCADE;
DROP TABLE IF EXISTS users CASCADE;
