"""
Tests del puntaje de la bolsa laboral.

El puntaje es lo que decide qué ve el usuario arriba de la lista, así que lo
que se prueba aquí no es la aritmética sino las decisiones de producto que
la aritmética codifica: que la ruta pese más que la facilidad, que la
preparación se mida contra lo exigido y no contra todo lo mencionado, y que
un puesto acorde al momento del usuario suba un poco.
"""

from services.job_recommendation_service import JobRecommendationService


def job(required=None, desirable=None, seniority=None):
    required = required or []
    desirable = desirable or []

    return {
        "required_skills": required,
        "desirable_skills": desirable,
        "skill_slugs": required + desirable,
        "seniority": seniority,
    }


def score(job_dict, route, user, experience_level=None):
    return JobRecommendationService._score(
        job_dict,
        set(route),
        set(user),
        experience_level,
    )


RUTA_FULLSTACK = ["typescript", "react", "nodejs", "postgres", "git", "rest", "docker"]


# ------------------------------------------------
# Alineación con la ruta
# ------------------------------------------------

def test_oferta_de_la_ruta_puntua_mas_que_una_ajena():
    de_la_ruta = score(
        job(required=["react", "typescript", "nodejs"]),
        RUTA_FULLSTACK,
        [],
    )
    ajena = score(
        job(required=["excel", "sap", "contabilidad"]),
        RUTA_FULLSTACK,
        [],
    )

    assert de_la_ruta["match_percentage"] > ajena["match_percentage"]
    assert ajena["alignment_percentage"] == 0


def test_una_oferta_facil_pero_ajena_no_gana_a_una_alineada():
    # Es el defecto que tenía ordenar solo por habilidades cumplidas: una
    # oferta que pide una sola cosa que el usuario sabe daba 100%.
    facil_ajena = score(job(required=["excel"]), RUTA_FULLSTACK, ["excel"])
    alineada = score(
        job(required=["react", "typescript", "nodejs", "postgres"]),
        RUTA_FULLSTACK,
        ["react"],
    )

    assert alineada["match_percentage"] > facil_ajena["match_percentage"]


def test_alineacion_pondera_cobertura_de_la_ruta_y_foco_de_la_oferta():
    # Cubrir media ruta con puras tecnologías de la ruta alinea más que
    # nombrar una sola de ellas entre muchas ajenas.
    amplia = score(
        job(required=["react", "typescript", "nodejs", "postgres"]),
        RUTA_FULLSTACK,
        [],
    )
    anecdotica = score(
        job(required=["react", "cobol", "sap", "excel"]),
        RUTA_FULLSTACK,
        [],
    )

    assert amplia["alignment_percentage"] > anecdotica["alignment_percentage"]


# ------------------------------------------------
# Preparación
# ------------------------------------------------

def test_preparacion_se_mide_contra_lo_exigido_no_contra_los_deseables():
    # El usuario cumple los 2 requisitos duros; los 6 deseables no deberían
    # hundir su preparación al 25%.
    result = score(
        job(
            required=["react", "typescript"],
            desirable=["docker", "kubernetes", "aws", "gcp", "redis", "kafka"],
        ),
        RUTA_FULLSTACK,
        ["react", "typescript"],
    )

    assert result["readiness_percentage"] == 100


def test_sin_requisitos_duros_la_preparacion_usa_todas_las_tecnologias():
    result = score(
        job(desirable=["react", "typescript", "nodejs", "postgres"]),
        RUTA_FULLSTACK,
        ["react", "typescript"],
    )

    assert result["readiness_percentage"] == 50


def test_oferta_sin_tecnologias_no_rompe_el_calculo():
    result = score(job(), RUTA_FULLSTACK, ["react"])

    assert result["match_percentage"] == 0
    assert result["readiness_percentage"] == 0
    assert result["alignment_percentage"] == 0


# ------------------------------------------------
# Puente con el roadmap
# ------------------------------------------------

def test_missing_from_route_separa_lo_que_la_ruta_si_ensena():
    result = score(
        job(required=["react", "docker", "cobol"]),
        RUTA_FULLSTACK,
        ["react"],
    )

    assert result["matched_skills"] == ["react"]
    assert result["missing_from_route"] == ["docker"]
    assert "cobol" in result["missing_skills"]
    assert "cobol" not in result["missing_from_route"]


# ------------------------------------------------
# Nivel del puesto
# ------------------------------------------------

def test_practicante_sube_para_quien_no_tiene_experiencia():
    oferta = job(required=["react", "typescript"], seniority="Practicante")

    con_bonus = score(oferta, RUTA_FULLSTACK, [], "ninguna")
    sin_bonus = score(
        job(required=["react", "typescript"], seniority="Senior"),
        RUTA_FULLSTACK,
        [],
        "ninguna",
    )

    assert con_bonus["seniority_fit"] is True
    assert sin_bonus["seniority_fit"] is False
    assert con_bonus["match_percentage"] > sin_bonus["match_percentage"]


def test_sin_experiencia_declarada_se_asume_publico_estudiante():
    result = score(
        job(required=["react"], seniority="Practicante"),
        RUTA_FULLSTACK,
        [],
        None,
    )

    assert result["seniority_fit"] is True


def test_el_bonus_de_nivel_no_rescata_una_oferta_ajena():
    # El ajuste es pequeño a propósito: ordena entre ofertas parecidas, no
    # debe empujar algo irrelevante por encima de algo alineado.
    ajena_practicante = score(
        job(required=["excel", "sap"], seniority="Practicante"),
        RUTA_FULLSTACK,
        [],
        "ninguna",
    )
    alineada_senior = score(
        job(required=["react", "typescript", "nodejs"], seniority="Senior"),
        RUTA_FULLSTACK,
        [],
        "ninguna",
    )

    assert alineada_senior["match_percentage"] > ajena_practicante["match_percentage"]


def test_el_puntaje_nunca_se_pasa_de_cien():
    result = score(
        job(required=RUTA_FULLSTACK, seniority="Practicante"),
        RUTA_FULLSTACK,
        RUTA_FULLSTACK,
        "ninguna",
    )

    assert result["match_percentage"] <= 100
