"""
Recolector de ofertas laborales por línea de comandos (HU-57 / HU-58).

Es la vía pensada para correr de forma programada (tarea diaria), porque una
recolección completa tarda varios minutos y no encaja en el ciclo de una
petición HTTP. El endpoint POST /jobs/collect hace lo mismo y sirve para
disparos manuales desde el frontend o Swagger.

Uso:

    # Recolectar para todos los roles y extraer requisitos
    python scripts/scrape_jobs.py

    # Solo un par de rutas, con menos resultados (prueba rápida)
    python scripts/scrape_jobs.py --roles backend,frontend --results 10

    # Incluir LinkedIn además de Indeed
    python scripts/scrape_jobs.py --sites indeed,linkedin

    # Reanalizar habilidades y requisitos de lo ya guardado, sin scrapear
    python scripts/scrape_jobs.py --only-requirements

    # Borrar las ofertas antiguas que no vinieron de scraping (destructivo)
    python scripts/scrape_jobs.py --purge-seed
"""

import argparse
import os
import sys

# Permite ejecutar el script directamente (python scripts/scrape_jobs.py)
# sin haber instalado el proyecto como paquete.
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

from services.job_requirements_service import JobRequirementsService
from services.job_scraping_service import JobScrapingService


def parse_args():
    parser = argparse.ArgumentParser(
        description="Recolecta ofertas laborales reales y extrae sus requisitos.",
    )

    parser.add_argument(
        "--roles",
        help=(
            "Roles objetivo separados por coma "
            "(backend, frontend, fullstack, data-analyst, data-engineer, "
            "ml, devops). Por defecto, todos."
        ),
    )
    parser.add_argument(
        "--sites",
        help="Portales separados por coma (indeed, linkedin, glassdoor).",
    )
    parser.add_argument(
        "--results",
        type=int,
        help="Ofertas por término de búsqueda y portal.",
    )
    parser.add_argument(
        "--hours-old",
        type=int,
        help="Antigüedad máxima de las ofertas, en horas.",
    )
    parser.add_argument(
        "--skip-requirements",
        action="store_true",
        help="No extraer habilidades ni requisitos tras recolectar.",
    )
    parser.add_argument(
        "--only-requirements",
        action="store_true",
        help="Solo reanalizar las ofertas ya guardadas, sin scrapear.",
    )
    parser.add_argument(
        "--purge-seed",
        action="store_true",
        help=(
            "DESTRUCTIVO: borra las ofertas sin origen de scraping "
            "(las sembradas a mano y las importadas de TheirStack)."
        ),
    )

    return parser.parse_args()


def split_list(value: str | None) -> list[str] | None:
    if not value:
        return None

    return [item.strip() for item in value.split(",") if item.strip()]


def main():
    args = parse_args()

    if args.purge_seed:
        # Se pide confirmación explícita porque borra filas de producción y
        # no hay forma de recuperarlas: las ofertas sembradas no existen en
        # ningún portal del que se puedan volver a traer.
        print(
            "Se borrarán TODAS las ofertas cuyo campo `source` esté vacío "
            "(las que no vinieron de scraping)."
        )
        answer = input("Escribe 'BORRAR' para confirmar: ").strip()

        if answer != "BORRAR":
            print("Cancelado. No se borró nada.")
            return

        result = JobScrapingService.purge_non_scraped_jobs()
        print(f"Ofertas eliminadas: {result['deleted']}")
        return

    if args.only_requirements:
        print("Reanalizando habilidades y requisitos del catálogo...")
        result = JobRequirementsService.extract_and_save()
        print(f"  Ofertas analizadas:   {result['jobs_analyzed']}")
        print(f"  Relaciones creadas:   {result['relations_created']}")
        return

    print("Recolectando ofertas laborales...")

    result = JobScrapingService.collect_and_save_jobs(
        role_ids=split_list(args.roles),
        sites=split_list(args.sites),
        results_wanted=args.results,
        hours_old=args.hours_old,
        extract_requirements=not args.skip_requirements,
    )

    print(f"\nPortales:   {', '.join(result['sites'])}")
    print(f"Términos:   {len(result['search_terms'])}")
    print(f"Recolectadas: {result['collected']}")
    print(f"Guardadas:    {result['saved']}")

    if result.get("requirements"):
        requirements = result["requirements"]
        print(f"Analizadas (HU-58): {requirements.get('jobs_analyzed', 0)}")
        print(f"Relaciones skill:   {requirements.get('relations_created', 0)}")

    if result["errors"]:
        print(f"\nTérminos con error ({len(result['errors'])}):")
        for error in result["errors"]:
            print(f"  - {error['search_term']}: {error['error'][:120]}")


if __name__ == "__main__":
    main()
