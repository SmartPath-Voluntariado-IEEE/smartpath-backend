# Protocolo de Validación y Pruebas - SmartPath

Este documento detalla los casos de prueba y verificaciones necesarias para comprobar que la migración del procesamiento del frontend al backend FastAPI con Supabase PostgreSQL se ha realizado correctamente.

---

## 📋 Checklist de Verificación Técnica

### 1. Inicialización de Base de Datos

- [X] Ejecutar el reset y carga completa:
  ```powershell
  cd backend
  .venv\Scripts\python.exe database\run_migrations.py --reset
  ```
- [X] Verificar que las tablas fueron recreadas y pobladas correctamente sin errores de FK.

### 2. Comprobación de Servidor Backend

- [X] El servidor backend FastAPI debe levantar en `http://localhost:8000`:
  ```powershell
  .venv\Scripts\python.exe -m uvicorn main:app --reload
  ```
- [X] Revisar que la consola reporte `Application startup complete.` sin excepciones de conexión.

---

## 🛠️ Casos de Prueba: APIs del Backend (Técnicos)

### CP-T1: Catálogos Públicos

Verificar que los catálogos de base de datos responden correctamente en formato JSON.

1. **Catálogo de Habilidades (Skills):**

   ```bash
   curl http://localhost:8000/catalog/skills
   ```

   *Criterio de aceptación:* Retorna un array JSON con skills (ej. python, react) incluyendo campo `slug`.
2. **Catálogo de Ofertas de Trabajo (Jobs):**

   ```bash
   curl http://localhost:8000/catalog/jobs
   ```

   *Criterio de aceptación:* Retorna un array JSON con 10 ofertas de trabajo seeded, incluyendo `location` y `posted_at`.
3. **Catálogo de Cursos:**

   ```bash
   curl http://localhost:8000/catalog/courses
   ```

   *Criterio de aceptación:* Retorna un array JSON de cursos conteniendo el campo `price` como texto y la relación `skill_slugs`.
4. **Catálogo de Roles Objetivos:**

   ```bash
   curl http://localhost:8000/catalog/roles
   ```

   *Criterio de aceptación:* Retorna un array JSON con los 7 perfiles (backend, frontend, etc.) y sus skills core.

---

### CP-T2: Endpoints Protegidos de Perfil y Análisis

*(Nota: Para estas pruebas necesitarás un token JWT válido de Supabase, reemplaza `TU_JWT_TOKEN` en las cabeceras).*

1. **Obtener Perfil Completo:**

   ```bash
   curl -H "Authorization: Bearer TU_JWT_TOKEN" http://localhost:8000/users/profile
   ```

   *Criterio de aceptación:* Retorna el perfil del usuario conteniendo los nuevos campos (`target_role_id`, `interests`, `learning_preferences`) y el array `skills` con sus niveles.
2. **Calcular Brecha de Habilidades (Gap Analysis):**

   ```bash
   curl -H "Authorization: Bearer TU_JWT_TOKEN" http://localhost:8000/users/gap-analysis
   ```

   *Criterio de aceptación:* Retorna un análisis de brecha conteniendo skills agrupadas en `mastered`, `partial` y `missing`, además del porcentaje `coverage`.
3. **Generar Roadmap Personalizado:**

   ```bash
   curl -H "Authorization: Bearer TU_JWT_TOKEN" http://localhost:8000/users/roadmap
   ```

   *Criterio de aceptación:* Retorna el roadmap estructurado por niveles (ej. Fundamentos, Lenguajes base) con estimación de horas.
4. **Obtener Recomendaciones de Cursos para Skill:**

   ```bash
   curl -H "Authorization: Bearer TU_JWT_TOKEN" "http://localhost:8000/users/course-recommendations?skill=react"
   ```

   *Criterio de aceptación:* Retorna las recomendaciones personalizadas de cursos de React filtradas por el nivel y preferencias del usuario.

---

## 👥 Casos de Prueba de Flujo de Usuario (Frontend)

### CP-U1: Redirección por Rutas Protegidas (Acceso no autenticado)

1. Cierra sesión en el frontend o limpia el almacenamiento local.
2. Intenta ingresar directamente a `http://localhost:3000/dashboard` o `http://localhost:3000/roadmap`.
3. *Criterio de aceptación:* La app debe interceptar el acceso y redirigirte automáticamente a `/login`.

### CP-U2: Flujo Completo de Onboarding a Dashboard

1. Inicia sesión en `http://localhost:3000/login` con tus credenciales.
2. Serás redirigido al chat de onboarding `/onboarding`.
3. Responde a las preguntas de SmartBot:
   - Nombre, carrera, ciclo actual.
   - Selecciona áreas de interés (ej. Desarrollo Backend, Cloud).
   - Selecciona tu Rol objetivo (ej. Backend Developer).
   - Califica tus habilidades (da nivel a lenguajes/frameworks).
   - Selecciona experiencia y preferencias de aprendizaje.
   - Define tus horas y metas semanales.
4. Presiona **Confirmar**.
5. *Criterio de aceptación:* El sistema debe reportar "Perfil sincronizado con el backend", redirigir al Dashboard, y mostrar:
   - Tu conexión segura activa.
   - Las métricas calculadas por el backend (cobertura del rol, horas estimadas).
   - Tus estadísticas de preparación dinámicas.

### CP-U3: Visualización de Roadmap y Cursos Recomendados

1. Desde el Dashboard, haz clic en **Ver Roadmap** (o ve a `/roadmap`).
2. *Criterio de aceptación:* Verás el mapa estructurado en niveles cargado desde el backend. Las horas estimadas y cantidad de cursos deben corresponder a la base de datos de PostgreSQL.
3. Haz clic en **Ver cursos** para cualquier habilidad.
4. *Criterio de aceptación:* Irás a la pantalla de cursos y verás las sugerencias personalizadas extraídas de forma dinámica según tu perfil.
