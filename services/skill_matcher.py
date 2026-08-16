"""
Detección de habilidades del catálogo dentro de un texto libre.

La regla es una sola para todo el backend: un texto menciona una habilidad si
contiene su nombre o alguno de sus alias como palabra completa, ignorando
mayúsculas y tildes.

Se usa desde dos lados:

- `vacancy_service`, sobre la descripción de una vacante (job_skills).
- `course_ingestion_service`, sobre el título de un curso (course_skills).

Antes vivía dentro de `VacancyService`; se extrajo aquí para que el vínculo
curso-habilidad no reimplemente el criterio de otra forma.
"""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Convierte el texto a minúsculas y elimina tildes.

    Ejemplo: 'Visualización' -> 'visualizacion'.
    """

    normalized = unicodedata.normalize("NFD", text.lower())

    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )


def contains_term(text: str, term: str) -> bool:
    """
    Busca un término como palabra o expresión completa.

    Evita encontrar, por ejemplo, 'java' dentro de 'javascript'.

    El borde izquierdo también bloquea un punto pegado a la palabra, porque
    varias tecnologías lo llevan en el nombre: sin eso, el alias 'js' coincide
    dentro de 'node.js' y 'vue.js', y el curso termina etiquetado como
    JavaScript por accidente. El borde derecho sí acepta el punto, para no
    perder los términos al final de una frase ('...experiencia en Python.').
    """

    normalized_term = normalize_text(term.strip())

    if not normalized_term:
        return False

    pattern = rf"(?<![\w.]){re.escape(normalized_term)}(?!\w)"

    return re.search(pattern, normalize_text(text)) is not None


def search_terms_for(skill: dict) -> list[str]:
    """Nombre de la habilidad más sus alias, sin vacíos."""

    aliases = skill.get("aliases") or []

    return [term for term in [skill.get("name", ""), *aliases] if term]


def mentions_skill(text: str, skill: dict) -> bool:
    """True si el texto menciona la habilidad por nombre o por alias."""

    if not text:
        return False

    return any(
        contains_term(text, term)
        for term in search_terms_for(skill)
    )


def match_skills(text: str, skills: list[dict]) -> list[dict]:
    """
    Devuelve las habilidades del catálogo mencionadas en el texto.

    Un mismo texto puede mencionar varias ('React y Node.js desde cero'
    coincide con ambas), y esa es justamente la razón de existir de la
    función: el vínculo curso-habilidad no es uno a uno.
    """

    if not text:
        return []

    return [skill for skill in skills if mentions_skill(text, skill)]
