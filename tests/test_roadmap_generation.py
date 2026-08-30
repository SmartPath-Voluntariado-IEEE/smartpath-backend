from services.analysis_service import (
    MIN_SKILL_HOURS,
    AnalysisService,
)


def build_gap(missing=None, partial=None, mastered=None):
    return {
        "target_role": {"id": "backend", "label": "Backend"},
        "mastered": mastered or [],
        "partial": partial or [],
        "missing": missing or [],
        "coverage": 0.0,
    }


def course(slug, hours=None, free=True, language="English"):
    return {
        "title": f"Curso de {slug}",
        "platform": "freeCodeCamp",
        "url": f"https://example.org/{slug}-{hours}-{free}",
        "price": "Free" if free else "Paid Course",
        "is_free": free,
        "language": language,
        "rating": None,
        "level": None,
        "duration_hours": hours,
        "skill_slugs": [slug],
    }


def test_est_hours_sale_de_los_cursos_reales_y_no_del_tier():
    gap = build_gap(missing=[
        {"skill_slug": "docker", "name": "Docker", "marketFreq": 0.2},
    ])

    catalog = [
        course("docker", hours=10),
        course("docker", hours=20),
        course("docker", hours=30),
    ]

    roadmap = AnalysisService.generate_roadmap(
        gap,
        courses_catalog=catalog,
    )

    skill = roadmap[0]["skills"][0]

    # Mediana 20h de contenido x2 de práctica.
    assert skill["estHours"] == 40
    assert skill["freeCourseCount"] == 3


def test_est_hours_cae_al_tier_sin_datos_de_duracion():
    gap = build_gap(missing=[
        {"skill_slug": "docker", "name": "Docker", "marketFreq": 0.2},
    ])

    roadmap = AnalysisService.generate_roadmap(gap, courses_catalog=[])

    # Tier 4 de la tabla de respaldo.
    assert roadmap[0]["skills"][0]["estHours"] == 30


def test_una_habilidad_no_puede_estimarse_en_una_hora():
    gap = build_gap(missing=[
        {"skill_slug": "git", "name": "Git", "marketFreq": 0.2},
    ])

    roadmap = AnalysisService.generate_roadmap(
        gap,
        courses_catalog=[course("git", hours=1)],
    )

    assert roadmap[0]["skills"][0]["estHours"] == MIN_SKILL_HOURS


def test_una_habilidad_sin_cursos_pierde_prioridad():
    gap = build_gap(missing=[
        {"skill_slug": "docker", "name": "Docker", "marketFreq": 0.2},
        {"skill_slug": "redis", "name": "Redis", "marketFreq": 0.2},
    ])

    # Mismo tier (4) y misma demanda: solo los diferencia la oferta de cursos.
    roadmap = AnalysisService.generate_roadmap(
        gap,
        courses_catalog=[course("docker", hours=10)],
    )

    skills = roadmap[0]["skills"]

    assert skills[0]["skill_slug"] == "docker"
    assert skills[0]["priority"] > skills[1]["priority"]
    assert skills[1]["freeCourseCount"] == 0


def test_una_habilidad_ausente_urge_mas_que_una_a_medias():
    gap = build_gap(
        missing=[{"skill_slug": "docker", "name": "Docker", "marketFreq": 0.2}],
        partial=[{"skill_slug": "redis", "name": "Redis", "marketFreq": 0.2}],
    )

    roadmap = AnalysisService.generate_roadmap(gap)
    skills = roadmap[0]["skills"]

    assert skills[0]["skill_slug"] == "docker"


def test_los_intereses_del_usuario_desempatan():
    gap = build_gap(missing=[
        {"skill_slug": "docker", "name": "Docker", "marketFreq": 0.2},
        {"skill_slug": "redis", "name": "Redis", "marketFreq": 0.2},
    ])

    roadmap = AnalysisService.generate_roadmap(
        gap,
        profile={"interests": ["database"]},
        skills_catalog=[
            {"slug": "redis", "category": "database"},
            {"slug": "docker", "category": "tool"},
        ],
    )

    assert roadmap[0]["skills"][0]["skill_slug"] == "redis"


def test_el_roadmap_informa_el_plazo_pero_no_recorta():
    gap = build_gap(missing=[
        {"skill_slug": "git", "name": "Git", "marketFreq": 0.5},
        {"skill_slug": "aws", "name": "AWS", "marketFreq": 0.5},
    ])

    # 2h/semana durante 1 mes = 8.66h de presupuesto: no alcanza para todo.
    roadmap = AnalysisService.generate_roadmap(
        gap,
        profile={"weekly_hours": 2, "target_months": 1},
    )

    # Ningún nivel se elimina.
    assert [lvl["level"] for lvl in roadmap] == [1, 5]

    assert roadmap[0]["withinTarget"] is False
    assert roadmap[-1]["withinTarget"] is False
    assert roadmap[-1]["cumulativeHours"] > roadmap[0]["cumulativeHours"]


def test_habilidades_dominadas_permanecen_en_el_roadmap():
    # HU-69: Habilidad dominada debe mantenerse en el nivel correspondiente
    gap = build_gap(
        missing=[{"skill_slug": "docker", "name": "Docker", "marketFreq": 0.3}],
        mastered=[{"skill_slug": "git", "name": "Git", "marketFreq": 0.5, "level": 5}],
    )

    roadmap = AnalysisService.generate_roadmap(gap)

    levels = {lvl["level"]: lvl for lvl in roadmap}
    assert 1 in levels
    assert 4 in levels

    git_skill = next((s for s in levels[1]["skills"] if s["skill_slug"] == "git"), None)
    assert git_skill is not None
    assert git_skill["isMastered"] is True


def test_habilidades_dominadas_no_inflan_horas_pendientes():
    # Las horas acumuladas solo deben contar el esfuerzo restante
    gap = build_gap(
        missing=[{"skill_slug": "docker", "name": "Docker", "marketFreq": 0.3}],
        mastered=[{"skill_slug": "git", "name": "Git", "marketFreq": 0.5, "level": 5}],
    )

    roadmap = AnalysisService.generate_roadmap(
        gap,
        courses_catalog=[
            course("git", hours=10),
            course("docker", hours=10),
        ],
        profile={"weekly_hours": 10, "target_months": 3},
    )

    levels = {lvl["level"]: lvl for lvl in roadmap}
    # Nivel 1 tiene git (dominada), cumulativeHours debe ser 0
    assert levels[1]["cumulativeHours"] == 0
    # Nivel 4 tiene docker (pendiente 20h), cumulativeHours debe ser 20
    assert levels[4]["cumulativeHours"] == 20


def test_ingles_bajo_prioriza_cursos_en_espanol():
    catalog = [
        course("python", hours=10, language="English"),
        course("python", hours=10, language="Spanish"),
    ]

    recs = AnalysisService.recommend_courses(
        skill_slug="python",
        user_level=1,
        availability=10,
        preferences=["video"],
        target_role="Backend",
        courses_catalog=catalog,
        skill_name="Python",
        english_level="basico",
    )

    assert recs[0]["language"] == "Spanish"


def test_sin_dato_de_ingles_no_se_penaliza_ningun_idioma():
    catalog = [
        course("python", hours=10, language="English"),
        course("python", hours=10, language="Spanish"),
    ]

    recs = AnalysisService.recommend_courses(
        skill_slug="python",
        user_level=1,
        availability=10,
        preferences=["video"],
        target_role="Backend",
        courses_catalog=catalog,
        skill_name="Python",
        english_level=None,
    )

    # Ambos siguen presentes y el idioma no altera el orden.
    assert len(recs) == 2

