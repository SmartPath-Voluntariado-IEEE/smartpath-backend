"""
Backfill del vínculo curso-habilidad sobre el catálogo ya cargado.

Los cursos ingestados antes de HU-49 se vincularon con la habilidad que se
buscó, no con las que el curso realmente cubre: un curso de React y Node
quedó colgando de una sola, y los que se cargaron sin `skill_slug` quedaron
sin ningún vínculo —invisibles para el motor de recomendaciones, que filtra
estricto por `skill_slugs`—.

Este script recorre `courses`, aplica el mismo matcher que usa la ingesta
sobre el título y crea los vínculos que falten.

Uso:

    python -m scripts.link_course_skills --dry-run
    python -m scripts.link_course_skills
    python -m scripts.link_course_skills --show-unmatched

Es seguro re-ejecutarlo: solo inserta pares (course_id, skill_id) que no
existan, así que una segunda corrida no crea filas repetidas. No borra
vínculos previos; los que quedaron mal por la query anterior se revisan
aparte con `--show-unmatched` como punto de partida.
"""

import argparse

from services.catalog_service import CatalogService
from services.course_storage_service import CourseStorageService
from services.skill_matcher import match_skills


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Vincula los cursos existentes con las habilidades que "
            "mencionan en su título."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra qué vínculos se crearían, sin escribir en la base.",
    )

    parser.add_argument(
        "--show-unmatched",
        action="store_true",
        help=(
            "Lista los cursos cuyo título no menciona ninguna habilidad "
            "del catálogo. Útil para detectar alias que faltan en `skills`."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Procesa solo los primeros N cursos (para probar).",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    skills_catalog = CatalogService.get_all_skills()

    if not skills_catalog:
        raise SystemExit("La tabla skills está vacía: no hay con qué vincular.")

    courses = CourseStorageService.get_courses_for_linking()

    if args.limit:
        courses = courses[: args.limit]

    print(
        f"{len(courses)} cursos x {len(skills_catalog)} habilidades del "
        f"catálogo"
    )
    print(f"dry_run={args.dry_run}")
    print()

    created_links = 0
    matched_courses = 0
    unmatched = []

    for course in courses:
        title = course.get("title") or ""
        matched = match_skills(title, skills_catalog)

        if not matched:
            unmatched.append(title)
            continue

        matched_courses += 1
        slugs = ", ".join(skill["slug"] for skill in matched)

        if args.dry_run:
            print(f"  {title[:60]:<60} -> {slugs}")
            continue

        new_links = CourseStorageService.link_course_skills(
            course_id=course["id"],
            skill_ids=[skill["id"] for skill in matched],
        )

        if new_links:
            created_links += new_links
            print(f"  {title[:60]:<60} -> +{new_links} ({slugs})")

    print()
    print("RESUMEN")
    print(f"  cursos procesados: {len(courses)}")
    print(f"  cursos con habilidad detectada: {matched_courses}")
    print(f"  cursos sin coincidencia: {len(unmatched)}")

    if not args.dry_run:
        print(f"  vínculos nuevos creados: {created_links}")

    if args.show_unmatched and unmatched:
        print()
        print("SIN COINCIDENCIA")
        for title in unmatched:
            print(f"  {title}")


if __name__ == "__main__":
    main()
