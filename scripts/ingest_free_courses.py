"""
Re-ingesta del catálogo de cursos priorizando la oferta gratuita.

Recorre las habilidades del catálogo y, por cada una, pide cursos a la fuente
con `freeOnly` activado y los vincula en `course_skills`.

Uso:

    python -m scripts.ingest_free_courses --dry-run
    python -m scripts.ingest_free_courses --skills python,react
    python -m scripts.ingest_free_courses --languages english,spanish

Es seguro re-ejecutarlo: el almacenamiento deduplica por URL y por par
(course_id, skill_id), así que una segunda corrida no crea filas repetidas.
"""

import argparse
import sys
import time

from services.catalog_service import CatalogService
from services.course_ingestion_service import CourseIngestionService


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Ingesta cursos gratuitos para las habilidades del catálogo."
        ),
    )

    parser.add_argument(
        "--skills",
        help=(
            "Slugs separados por coma. Por defecto, todas las habilidades "
            "del catálogo."
        ),
    )

    parser.add_argument(
        "--languages",
        default="spanish,english",
        help=(
            "Idiomas a consultar, separados por coma. La oferta gratuita "
            "universitaria está sobre todo en inglés."
        ),
    )

    parser.add_argument(
        "--max-items",
        type=int,
        default=10,
        help="Cursos a pedir por habilidad e idioma (máximo 50).",
    )

    parser.add_argument(
        "--include-paid",
        action="store_true",
        help=(
            "Desactiva freeOnly. Usar solo para completar habilidades sin "
            "oferta gratuita."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el plan y el costo en corridas, sin llamar a la fuente.",
    )

    return parser.parse_args()


def resolve_skills(requested: str | None) -> list[dict]:
    catalog = CatalogService.get_all_skills()

    if not requested:
        return catalog

    wanted = [s.strip() for s in requested.split(",") if s.strip()]
    by_slug = {s["slug"]: s for s in catalog}

    missing = [slug for slug in wanted if slug not in by_slug]

    if missing:
        raise SystemExit(
            f"Estos slugs no existen en el catálogo: {', '.join(missing)}"
        )

    return [by_slug[slug] for slug in wanted]


def main():
    args = parse_args()

    skills = resolve_skills(args.skills)
    languages = [
        lang.strip()
        for lang in args.languages.split(",")
        if lang.strip()
    ]

    total_runs = len(skills) * len(languages)

    print(
        f"{len(skills)} habilidades x {len(languages)} idiomas "
        f"= {total_runs} corridas de la fuente"
    )
    print(f"free_only={not args.include_paid} max_items={args.max_items}")
    print()

    if args.dry_run:
        for skill in skills:
            print(f"  {skill['slug']:<20} query='{skill['name']}'")
        print("\n(dry-run: no se llamó a la fuente)")
        return

    totals = {
        "collected": 0,
        "created": 0,
        "already_exists": 0,
        "linked": 0,
        "failed": 0,
    }

    for index, skill in enumerate(skills, start=1):
        for language in languages:
            label = f"[{index}/{len(skills)}] {skill['slug']} ({language})"

            try:
                result = CourseIngestionService.ingest_courses(
                    search_query=skill["name"],
                    max_items=args.max_items,
                    language=language,
                    skill_slug=skill["slug"],
                    free_only=not args.include_paid,
                )
            except Exception as error:
                totals["failed"] += 1
                print(f"{label}: ERROR {error}", file=sys.stderr)
                continue

            totals["collected"] += result["collected"]
            totals["created"] += result["created"]
            totals["already_exists"] += result["already_exists"]
            totals["linked"] += result["linked_to_skill"]

            print(
                f"{label}: {result['collected']} recolectados, "
                f"{result['created']} nuevos, "
                f"{result['linked_to_skill']} vinculados"
            )

            # La fuente es un scraper de terceros; un respiro entre corridas
            # evita saturarla.
            time.sleep(1)

    print()
    print("RESUMEN")
    for key, value in totals.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
