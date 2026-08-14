from services.course_ingestion_service import CourseIngestionService
from services.skill_matcher import contains_term, match_skills, mentions_skill

CATALOG = [
    {"id": 1, "slug": "python", "name": "Python", "aliases": ["python"]},
    {
        "id": 2,
        "slug": "javascript",
        "name": "JavaScript",
        "aliases": ["javascript", "js", "java script"],
    },
    {"id": 3, "slug": "java", "name": "Java", "aliases": ["java"]},
    {
        "id": 4,
        "slug": "react",
        "name": "React",
        "aliases": ["react", "reactjs", "react.js"],
    },
    {
        "id": 5,
        "slug": "nodejs",
        "name": "Node.js",
        "aliases": ["node", "nodejs", "node.js"],
    },
    {
        "id": 6,
        "slug": "scrum",
        "name": "Metodologías ágiles",
        "aliases": ["scrum", "metodologias agiles", "metodologías ágiles"],
    },
]


def slugs_for(title: str) -> set[str]:
    return {skill["slug"] for skill in match_skills(title, CATALOG)}


def test_java_no_coincide_dentro_de_javascript():
    assert slugs_for("Curso completo de JavaScript") == {"javascript"}
    assert slugs_for("Programación en Java desde cero") == {"java"}


def test_el_matcher_ignora_tildes_y_mayusculas():
    assert contains_term("Metodologías Ágiles en la práctica", "metodologias agiles")
    assert slugs_for("Introducción a las METODOLOGÍAS ÁGILES") == {"scrum"}


def test_un_curso_puede_cubrir_varias_habilidades():
    # La razón de ser de HU-49: el vínculo no es uno a uno.
    assert slugs_for("Full Stack con React y Node.js") == {"react", "nodejs"}


def test_el_alias_js_no_dispara_dentro_de_node_js():
    # El punto del nombre hacía que 'js' coincidiera al final de 'node.js',
    # etiquetando como JavaScript cursos que no lo son.
    assert slugs_for("Node.js para principiantes") == {"nodejs"}
    assert slugs_for("Aprende JS moderno") == {"javascript"}
    # Pero un punto de fin de frase no debe impedir la coincidencia.
    assert contains_term("Todo sobre Python.", "python")


def test_titulo_sin_habilidades_no_inventa_coincidencias():
    assert slugs_for("CS50: Introduction to Computer Science") == set()
    assert slugs_for("") == set()


def test_mentions_skill_tolera_alias_ausentes():
    skill = {"id": 9, "slug": "sql", "name": "SQL"}

    assert mentions_skill("Bases de datos con SQL", skill) is True
    assert mentions_skill("Bases de datos", skill) is False


def test_el_contenido_manda_sobre_la_query_de_busqueda():
    # Se buscó 'python' pero la fuente devolvió un curso de React: antes
    # quedaba colgando de python y el recomendador lo ofrecía como tal.
    skill_ids, used_fallback = CourseIngestionService.resolve_course_skills(
        title="React - The Complete Guide",
        skills_catalog=CATALOG,
        fallback_skill_id=1,
    )

    assert skill_ids == [4]
    assert used_fallback is False


def test_la_query_es_el_respaldo_cuando_el_titulo_no_dice_nada():
    skill_ids, used_fallback = CourseIngestionService.resolve_course_skills(
        title="Bootcamp Full Stack desde cero",
        skills_catalog=CATALOG,
        fallback_skill_id=1,
    )

    assert skill_ids == [1]
    assert used_fallback is True


def test_sin_titulo_reconocible_ni_query_el_curso_queda_sin_vinculo():
    skill_ids, used_fallback = CourseIngestionService.resolve_course_skills(
        title="Bootcamp Full Stack desde cero",
        skills_catalog=CATALOG,
        fallback_skill_id=None,
    )

    assert skill_ids == []
    assert used_fallback is False
