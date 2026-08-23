"""
Tests de HU-58: habilidades, tecnologías y requisitos extraídos del aviso.

Lo que más se prueba aquí es la distinción entre requisito excluyente y
deseable, porque es lo que evita que la bolsa laboral recomiende puestos
para los que el usuario no califica.
"""

from services.job_requirements_service import (
    PRIORITY_DESIRABLE,
    PRIORITY_REQUIRED,
    JobRequirementsService,
)


CATALOG = [
    {"id": 1, "name": "Python", "aliases": ["python"]},
    {"id": 2, "name": "React", "aliases": ["react", "reactjs"]},
    {"id": 3, "name": "TypeScript", "aliases": ["typescript", "ts"]},
    {"id": 4, "name": "Docker", "aliases": ["docker"]},
    {"id": 5, "name": "PostgreSQL", "aliases": ["postgres", "postgresql"]},
    {"id": 6, "name": "Kubernetes", "aliases": ["kubernetes", "k8s"]},
    {"id": 7, "name": "Java", "aliases": ["java"]},
    {"id": 8, "name": "JavaScript", "aliases": ["javascript", "js"]},
]

BY_ID = {skill["id"]: skill["name"] for skill in CATALOG}


def names(result, priority):
    return sorted(BY_ID[i] for i, p in result.items() if p == priority)


AVISO = """
Requisitos:
- Dominio de React y TypeScript
- Manejo de PostgreSQL

Deseable:
- Conocimientos de Docker
- Kubernetes
"""


# ------------------------------------------------
# Exigido vs. deseable
# ------------------------------------------------

def test_las_secciones_separan_exigido_de_deseable():
    result = JobRequirementsService.extract_skills(AVISO, CATALOG)

    assert names(result, PRIORITY_REQUIRED) == ["PostgreSQL", "React", "TypeScript"]
    assert names(result, PRIORITY_DESIRABLE) == ["Docker", "Kubernetes"]


def test_una_marca_en_la_linea_pesa_mas_que_la_seccion():
    aviso = """
    Requisitos:
    - Python
    - Docker (deseable)
    """

    result = JobRequirementsService.extract_skills(aviso, CATALOG)

    assert result[1] == PRIORITY_REQUIRED   # Python
    assert result[4] == PRIORITY_DESIRABLE  # Docker


def test_excluyente_dentro_de_una_seccion_de_deseables_sube_la_prioridad():
    aviso = """
    Deseable:
    - Kubernetes
    - Python (excluyente)
    """

    result = JobRequirementsService.extract_skills(aviso, CATALOG)

    assert result[1] == PRIORITY_REQUIRED
    assert result[6] == PRIORITY_DESIRABLE


def test_una_tecnologia_repetida_se_queda_con_la_exigencia_mas_alta():
    aviso = """
    Deseable:
    - Docker

    Requisitos:
    - Docker
    """

    result = JobRequirementsService.extract_skills(aviso, CATALOG)

    assert result[4] == PRIORITY_REQUIRED


def test_sin_secciones_todo_queda_como_deseable():
    # Un aviso en prosa no afirma que nada sea excluyente; asumir lo
    # contrario haría que casi todo pareciera un requisito duro.
    aviso = "Trabajamos con Python y Docker en un equipo pequeño."

    result = JobRequirementsService.extract_skills(aviso, CATALOG)

    assert names(result, PRIORITY_DESIRABLE) == ["Docker", "Python"]
    assert names(result, PRIORITY_REQUIRED) == []


def test_una_frase_larga_que_menciona_requisitos_no_abre_seccion():
    aviso = (
        "Antes de postular revisa que cumples todos los requisitos del "
        "puesto porque el proceso de seleccion es exigente y largo.\n"
        "Usamos Python a diario.\n"
    )

    result = JobRequirementsService.extract_skills(aviso, CATALOG)

    assert result[1] == PRIORITY_DESIRABLE


def test_java_no_coincide_dentro_de_javascript():
    result = JobRequirementsService.extract_skills("Stack: JavaScript.", CATALOG)

    assert names(result, PRIORITY_DESIRABLE) == ["JavaScript"]


def test_descripcion_vacia_no_devuelve_habilidades():
    assert JobRequirementsService.extract_skills("", CATALOG) == {}


# ------------------------------------------------
# Años de experiencia
# ------------------------------------------------

def test_experiencia_reconoce_las_formas_habituales():
    extract = JobRequirementsService.extract_experience_years

    assert extract("2 anos de experiencia en backend") == 2
    assert extract("experiencia minima de 3 anos") == 3
    assert extract("3+ years of experience") == 3


def test_experiencia_se_queda_con_el_minimo():
    # El aviso pide 2 años para entrar; quedarse con el 5 excluiría al
    # usuario de una oferta a la que sí puede postular.
    texto = "2 anos de experiencia en backend y 5 anos liderando equipos"

    assert JobRequirementsService.extract_experience_years(texto) == 2


def test_experiencia_ignora_cifras_absurdas():
    assert JobRequirementsService.extract_experience_years("50 anos de experiencia") is None


def test_sin_experiencia_declarada_devuelve_none():
    assert JobRequirementsService.extract_experience_years("Buscamos backend") is None


# ------------------------------------------------
# Requisitos no técnicos
# ------------------------------------------------

def test_extract_requirements_arma_los_chips():
    aviso = """
    Egresado de Ingenieria de Sistemas.
    Experiencia minima de 2 anos.
    Ingles intermedio.
    Modalidad hibrido, tiempo completo.
    """

    result = JobRequirementsService.extract_requirements(aviso)

    assert result["experience_years_min"] == 2
    assert result["education_level"] == "Egresado"
    assert result["english_required"] is True

    tipos = {item["type"]: item["value"] for item in result["requirements"]}
    assert tipos["idioma"] == "Intermedio"
    assert tipos["modalidad"] == "Híbrido"
    assert tipos["contrato"] == "Tiempo completo"


def test_practicante_se_detecta_como_contrato_de_practicas():
    result = JobRequirementsService.extract_requirements(
        "Buscamos practicante para el area de TI",
        "Practicante de Sistemas",
    )

    tipos = {item["type"]: item["value"] for item in result["requirements"]}
    assert tipos["contrato"] == "Prácticas"


def test_aviso_sin_requisitos_no_inventa_ninguno():
    result = JobRequirementsService.extract_requirements("Unete a nuestro equipo.")

    assert result["requirements"] == []
    assert result["experience_years_min"] is None
    assert result["education_level"] is None
    assert result["english_required"] is False


def test_singular_y_plural_en_la_etiqueta_de_experiencia():
    uno = JobRequirementsService.extract_requirements("1 ano de experiencia")
    dos = JobRequirementsService.extract_requirements("2 anos de experiencia")

    assert uno["requirements"][0]["label"] == "1 año de experiencia"
    assert dos["requirements"][0]["label"] == "2 años de experiencia"
