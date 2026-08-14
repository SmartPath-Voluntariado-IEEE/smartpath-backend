from services.analysis_service import AnalysisService
from services.course_normalizer_service import CourseNormalizerService
from services.course_pricing import is_free_course, is_free_price


def test_free_trial_no_cuenta_como_gratis():
    assert is_free_price("Free") is True
    assert is_free_price("free course") is True
    assert is_free_price("Free Trial Available") is False
    assert is_free_price("Paid Course") is False
    assert is_free_price(None) is False


def test_columna_is_free_tiene_prioridad_sobre_la_etiqueta():
    # Filas ya migradas: manda el booleano.
    assert is_free_course({"is_free": True, "price": "Paid Course"}) is True
    assert is_free_course({"is_free": False, "price": "Free"}) is False

    # Filas anteriores a la migración: cae a la etiqueta de texto.
    assert is_free_course({"price": "Free"}) is True
    assert is_free_course({"price": "Paid Course"}) is False


def test_normalizador_conserva_institucion_y_gratuidad():
    normalized = CourseNormalizerService.normalize_course({
        "provider": "edX",
        "isUniversityCourse": True,
        "title": "CS50",
        "isFree": True,
        "pricingLabel": "Paid Course",
        "courseUrl": "https://example.org/cs50",
        "effort": "10 weeks, 6 hours/week",
    })

    assert normalized["institution"] == "edX"
    assert normalized["is_free"] is True
    assert normalized["price"] == "Free"
    assert normalized["duration_hours"] == 60


def test_institucion_vacia_si_no_es_curso_universitario():
    normalized = CourseNormalizerService.normalize_course({
        "provider": "Udemy",
        "isUniversityCourse": False,
        "title": "Curso suelto",
    })

    assert normalized["institution"] is None


def test_duracion_soporta_los_formatos_de_la_fuente():
    normalize = CourseNormalizerService.normalize_duration_hours

    assert normalize("6 weeks, 4 hours/week") == 24
    assert normalize("5 hours 38 minutes") == 6
    assert normalize("3 hours") == 3
    # Un curso corto no debe quedar en 0 horas.
    assert normalize("45 minutes") == 1
    assert normalize(None) is None
    assert normalize("a tu propio ritmo") is None


def test_los_cursos_gratis_encabezan_las_recomendaciones():
    catalog = [
        {
            "title": "Curso pago con rating alto",
            "platform": "Udemy",
            "url": "https://example.org/pago",
            "price": "Paid Course",
            "rating": 5.0,
            "level": "Beginner",
            "duration_hours": 20,
            "skill_slugs": ["python"],
        },
        {
            "title": "Curso gratis sin rating",
            "platform": "edX",
            "institution": "MIT",
            "url": "https://example.org/gratis",
            "price": "Free",
            "rating": None,
            "level": None,
            "duration_hours": None,
            "skill_slugs": ["python"],
        },
    ]

    recs = AnalysisService.recommend_courses(
        skill_slug="python",
        user_level=1,
        availability=10,
        preferences=["video"],
        target_role="Backend Developer",
        courses_catalog=catalog,
        skill_name="Python",
    )

    # El gratuito va primero pese a no tener rating.
    assert recs[0]["title"] == "Curso gratis sin rating"
    assert recs[0]["is_free"] is True
    assert "Gratis en MIT." in recs[0]["why"]

    # Sin duración no se inventa una estimación de semanas.
    assert recs[0]["hours"] is None
    assert "sem a" not in recs[0]["why"]

    assert recs[1]["is_free"] is False
