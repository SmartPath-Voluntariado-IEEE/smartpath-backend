"""
Genera el ejemplo antes/después de HU-58 para la sustentación: toma una
oferta real ya recolectada y muestra su descripción cruda junto a las
habilidades y requisitos que el sistema extrajo de ella.

Uso:
    python scripts/demo_hu58.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import get_admin_client  # noqa: E402


def main():
    client = get_admin_client()

    rows = (
        client
        .table("jobs")
        .select(
            "id,position,company,description,requirements,"
            "job_skills(priority,skills(name))"
        )
        .execute()
        .data
        or []
    )

    if not rows:
        print("No hay ofertas en la base de datos. Corre primero:")
        print("  python scripts/scrape_jobs.py")
        return

    # Se elige la oferta con mejor mezcla de exigidas y deseables, para que
    # el ejemplo muestre las dos categorías, no solo una.
    def score(row):
        skills = row.get("job_skills") or []
        required = sum(1 for s in skills if s["priority"] == 2)
        desirable = sum(1 for s in skills if s["priority"] == 1)
        return min(required, desirable) * 10 + required + desirable

    best = max(rows, key=score)

    required = [
        s["skills"]["name"]
        for s in best["job_skills"]
        if s["priority"] == 2
    ]
    desirable = [
        s["skills"]["name"]
        for s in best["job_skills"]
        if s["priority"] == 1
    ]

    print("=" * 70)
    print(f"OFERTA: {best['position']} @ {best['company']}")
    print("=" * 70)
    print()
    print("--- Descripción original (lo que hay en el aviso) ---")
    print((best["description"] or "")[:800])
    print()
    print("--- Lo que extrae el sistema (HU-58) ---")
    print(f"Tecnologías exigidas  : {', '.join(required) or '(ninguna)'}")
    print(f"Tecnologías deseables : {', '.join(desirable) or '(ninguna)'}")
    print("Requisitos no técnicos:")
    for req in best.get("requirements") or []:
        print(f"  - {req['label']}")


if __name__ == "__main__":
    main()
