import json

import google.generativeai as genai

from core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-3.6-flash")


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
    if not settings.GEMINI_API_KEY:
        raise ValueError("Falta GEMINI_API_KEY en las variables de entorno.")

    prompt = f"""
Analiza el siguiente contenido extraído de la página de un curso llamado
"{course_title}". Identifica los módulos, temas o secciones en los que
está organizado el curso.

Contenido de la página:
---
{scraped_text}
---

Responde SOLO con un array JSON, sin texto adicional, con este formato:
[
  {{"order": 1, "title": "Nombre del módulo", "content_summary": "Resumen breve de 2-3 líneas de qué cubre este módulo"}},
  ...
]

Si no puedes identificar módulos claros, infiere una estructura razonable
basándote en el contenido disponible. Genera entre 4 y 12 módulos.
"""
    response = _model.generate_content(prompt)
    return _parse_json_response(response.text)


def generate_quiz_for_module(module_title: str, content_summary: str) -> list[dict]:
    if not settings.GEMINI_API_KEY:
        raise ValueError("Falta GEMINI_API_KEY en las variables de entorno.")

    prompt = f"""
Genera exactamente 10 preguntas de opción múltiple para evaluar la
comprensión de este módulo de un curso técnico:

Título del módulo: {module_title}
Contenido: {content_summary}

Cada pregunta debe tener 4 opciones (solo una correcta), ser clara,
y evaluar comprensión real del tema, no memorización trivial.

Responde SOLO con un array JSON, sin texto adicional:
[
  {{"question": "...", "options": ["opción A", "opción B", "opción C", "opción D"], "correct_option": 0}},
  ...
]
correct_option es el índice (0 a 3) de la opción correcta dentro de "options".
"""
    response = _model.generate_content(prompt)
    questions = _parse_json_response(response.text)

    if len(questions) != 10:
        raise ValueError(
            f"La IA generó {len(questions)} preguntas en vez de 10. Reintenta."
        )

    return questions