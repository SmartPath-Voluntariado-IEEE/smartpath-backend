
# Crear la BD local

psql -U postgres -d roadmap_learning -f database/schema.sql

# Cargar datos de prueba

psql -U postgres -d roadmap_learning -f database/seed.sql
