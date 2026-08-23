import json
import google.generativeai as genai
from core.config import settings

if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        print(f"⚠️ [GEMINI CONFIG] Error configurando API key: {e}")

_model = genai.GenerativeModel("gemini-flash-latest") if settings.GEMINI_API_KEY else None


def _parse_json_response(raw_text: str):
    cleaned = (
        raw_text.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    return json.loads(cleaned)


def extract_modules_from_content(course_title: str, scraped_text: str) -> list[dict]:
    if _model and settings.GEMINI_API_KEY:
        try:
            content_block = scraped_text if scraped_text else f"Contenido del curso sobre {course_title}."
            prompt = f"""
Analiza el siguiente contenido del curso titulado "{course_title}".
Identifica los módulos o secciones en los que está organizado.

Contenido:
---
{content_block}
---

Responde SOLO con un array JSON, sin texto adicional, con este formato:
[
  {{"order": 1, "title": "Nombre del módulo", "content_summary": "Resumen breve de 2-3 líneas de qué cubre este módulo"}},
  ...
]

Genera entre 3 y 6 módulos secuenciales claros.
"""
            response = _model.generate_content(prompt)
            data = _parse_json_response(response.text)
            if isinstance(data, list) and len(data) > 0:
                return data
        except Exception as err:
            print(f"⚠️ [GEMINI EXTRACT] Extracción falló ({err}), usando módulos estructurados de respaldo.")

    # Módulos por defecto si no hay API key o falló la extracción
    return [
        {
            "order": 1,
            "title": f"1. Fundamentos e Instalación de {course_title}",
            "content_summary": f"Conceptos iniciales, arquitectura base y preparación del entorno de trabajo para dominar {course_title}."
        },
        {
            "order": 2,
            "title": f"2. Desarrollo Práctico y Casos de Uso",
            "content_summary": f"Implementación de funcionalidades, buenas prácticas y desarrollo de ejercicios prácticos con {course_title}."
        },
        {
            "order": 3,
            "title": f"3. Optimización, Pruebas y Despliegue",
            "content_summary": f"Estrategias avanzadas, testing automatizado, resolución de errores y preparación para entornos de producción."
        }
    ]


def generate_quiz_for_module(module_title: str, content_summary: str) -> list[dict]:
    if _model and settings.GEMINI_API_KEY:
        try:
            prompt = f"""
Genera exactamente 10 preguntas de opción múltiple para evaluar la comprensión de este módulo técnico:

Título del módulo: {module_title}
Contenido: {content_summary}

Cada pregunta debe tener 4 opciones (solo una correcta), ser clara y evaluar conceptos esenciales.

Responde SOLO con un array JSON:
[
  {{"question": "...", "options": ["opción 1", "opción 2", "opción 3", "opción 4"], "correct_option": 0}},
  ...
]
correct_option es el índice (0 a 3) de la opción correcta.
"""
            response = _model.generate_content(prompt)
            questions = _parse_json_response(response.text)
            if isinstance(questions, list) and len(questions) == 10:
                return questions
        except Exception as err:
            print(f"⚠️ [GEMINI QUIZ] Generación falló ({err}), usando banco de preguntas pedagógicas.")

    # Banco pedagógico de 10 preguntas por defecto
    return [
        {
            "question": f"¿Cuál es el objetivo principal al estudiar {module_title}?",
            "options": [
                "Dominar los conceptos clave y aplicarlos siguiendo estándares de la industria.",
                "Evitar el uso de herramientas de control de versiones.",
                "Escribir código sin pruebas ni validaciones.",
                "Depender exclusivamente de configuraciones manuales."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Qué buena práctica es esencial al estructurar un proyecto?",
            "options": [
                "Modularizar el código y mantener responsabilidades separadas.",
                "Colocar todo el código en un único archivo.",
                "Ignorar los tipos de datos y validaciones de entrada.",
                "Subir contraseñas y claves privadas al repositorio."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Por qué es importante implementar pruebas automatizadas?",
            "options": [
                "Para garantizar la calidad y evitar regresiones en producción.",
                "Para hacer que el proyecto sea más lento de ejecutar.",
                "Para aumentar el costo de mantenimiento sin beneficios.",
                "Porque reemplazan la necesidad de escribir documentación."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Qué patrón o enfoque favorece la escalabilidad del software?",
            "options": [
                "El desacoplamiento de componentes y la arquitectura limpia.",
                "El acoplamiento rígido entre capas.",
                "El uso de variables globales en toda la aplicación.",
                "La eliminación de capas de abstracción."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Cómo se asegura la integridad de los datos en una aplicación moderna?",
            "options": [
                "Validando esquemas de datos tanto en frontend como en backend.",
                "Confiando ciegamente en los datos enviados por el cliente.",
                "Omitiendo restricciones de clave foránea en base de datos.",
                "Desactivando el tipado estático."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Qué beneficio ofrece el manejo explícito de errores y excepciones?",
            "options": [
                "Proveer feedback claro al usuario y registrar fallos para diagnóstico.",
                "Ocultar los errores para que nadie sepa que ocurrieron.",
                "Hacer que la aplicación se cierre de forma inesperada.",
                "Aumentar el uso de memoria RAM."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Cuál es la ventaja de utilizar herramientas de observabilidad y logging?",
            "options": [
                "Monitorear el estado del sistema y facilitar la depuración.",
                "Reducir la seguridad de la información.",
                "Evitar que el equipo técnico analice métricas.",
                "Bloquear las conexiones de los usuarios."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Qué aspecto es fundamental para la optimización del rendimiento?",
            "options": [
                "Medir cuellos de botella y aplicar caché y consultas eficientes.",
                "Optimizar prematuramente antes de medir el problema real.",
                "Cargar todos los datos de la base de datos en memoria sin paginar.",
                "Deshabilitar la compresión de respuestas HTTP."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Por qué es recomendable seguir principios de diseño como SOLID y DRY?",
            "options": [
                "Mejora la legibilidad, mantenimiento y evolución del código a largo plazo.",
                "Garantiza que el código no requiera refactorización futura.",
                "Obliga a escribir menos líneas de código sin importar la claridad.",
                "Hace que el software solo funcione en un sistema operativo específico."
            ],
            "correct_option": 0
        },
        {
            "question": "¿Qué criterio define que una tarea o módulo está listo para completarse con éxito?",
            "options": [
                "Cumple con todos los criterios de aceptación y supera las evaluaciones.",
                "Se ejecuta localmente sin verificar los casos de prueba.",
                "Se aprueba sin haber completado las preguntas del examen.",
                "Se descartan los requerimientos no implementados."
            ],
            "correct_option": 0
        }
    ]
