"""
Tests de HU-57: normalización de lo que devuelve JobSpy.

Se prueba la traducción de una fila del portal a la forma de la tabla `jobs`,
que es donde se concentran las decisiones frágiles: NaN de pandas, sueldos en
periodicidades distintas y el nivel del puesto deducido del título.
"""

from services.job_scraping_service import JobScrapingService

NAN = float("nan")


def row(**overrides):
    """Fila mínima de JobSpy, con lo imprescindible para normalizar."""

    base = {
        "id": "in-abc123",
        "site": "indeed",
        "title": "Desarrollador Backend",
        "company": "Acme",
        "location": "Lima, LIM, PE",
        "job_url": "https://pe.indeed.com/viewjob?jk=abc123",
        "description": "Buscamos backend con Python.",
    }
    base.update(overrides)
    return base


# ------------------------------------------------
# Limpieza de celdas
# ------------------------------------------------

def test_clean_descarta_nan_de_pandas():
    # Es el caso que motiva la función: str(nan) da 'nan', y sin filtro esa
    # cadena se guardaría como si fuera el nombre de la empresa.
    assert JobScrapingService._clean(NAN) is None
    assert JobScrapingService._clean("nan") is None
    assert JobScrapingService._clean("   ") is None
    assert JobScrapingService._clean("  Acme  ") == "Acme"


def test_normalize_deja_company_en_none_si_viene_nan():
    result = JobScrapingService.normalize_job(row(company=NAN))

    assert result["company"] is None


# ------------------------------------------------
# Identidad externa
# ------------------------------------------------

def test_normalize_descarta_oferta_sin_id_ni_url():
    assert JobScrapingService.normalize_job(row(id=NAN, job_url=NAN)) is None


def test_normalize_descarta_oferta_sin_titulo():
    assert JobScrapingService.normalize_job(row(title=NAN)) is None


def test_normalize_usa_la_url_como_id_si_falta_el_id():
    result = JobScrapingService.normalize_job(row(id=NAN))

    assert result["external_id"] == "https://pe.indeed.com/viewjob?jk=abc123"


def test_normalize_prefiere_la_url_directa_de_la_empresa():
    result = JobScrapingService.normalize_job(
        row(job_url_direct="https://acme.com/careers/42")
    )

    assert result["url"] == "https://acme.com/careers/42"


def test_external_id_usa_la_url_directa_cuando_existe():
    # Indeed republica una misma vacante de terceros (Lever, Greenhouse...)
    # varias veces dentro de una sola búsqueda, cada vez con un `id` propio
    # distinto. Sin esto, esas repeticiones se guardan como ofertas
    # distintas: es justo el bug que se vio en producción.
    result = JobScrapingService.normalize_job(
        row(id="in-aaa111", job_url_direct="https://jobs.lever.co/acme/xyz")
    )

    assert result["external_id"] == "https://jobs.lever.co/acme/xyz"


def test_dos_avisos_republicados_colapsan_a_la_misma_identidad():
    primero = JobScrapingService.normalize_job(
        row(id="in-aaa111", job_url_direct="https://jobs.lever.co/acme/xyz")
    )
    segundo = JobScrapingService.normalize_job(
        row(id="in-bbb222", job_url_direct="https://jobs.lever.co/acme/xyz")
    )

    assert primero["external_id"] == segundo["external_id"]


# ------------------------------------------------
# Sueldo
# ------------------------------------------------

def test_salario_mensual_en_soles_es_el_promedio_del_rango():
    assert JobScrapingService._monthly_salary(1500, 2500, "monthly", "PEN") == 2000


def test_salario_anual_en_soles_se_lleva_a_mensual():
    assert JobScrapingService._monthly_salary(24000, 24000, "yearly", "PEN") == 2000


def test_salario_en_otra_moneda_no_contamina_la_columna_legacy():
    # market_overview promedia `salary` sin mirar la moneda: meter dólares
    # ahí daría un promedio de mercado sin sentido. Debe quedar en None y
    # conservarse solo en salary_min/max/currency.
    assert JobScrapingService._monthly_salary(60000, 90000, "yearly", "USD") is None


def test_sin_importes_no_hay_salario():
    assert JobScrapingService._monthly_salary(None, None, "monthly", "PEN") is None


def test_normalize_conserva_el_salario_crudo_aunque_no_sea_en_soles():
    result = JobScrapingService.normalize_job(
        row(min_amount=60000, max_amount=90000, currency="USD", interval="yearly")
    )

    assert result["salary"] is None
    assert result["salary_min"] == 60000
    assert result["salary_max"] == 90000
    assert result["salary_currency"] == "USD"
    assert result["salary_interval"] == "yearly"


# ------------------------------------------------
# Nivel del puesto
# ------------------------------------------------

def test_seniority_se_deduce_del_titulo():
    assert JobScrapingService._seniority("Practicante de Sistemas", None) == "Practicante"
    assert JobScrapingService._seniority("Full Stack Java Senior", None) == "Senior"
    assert JobScrapingService._seniority("Backend Developer Junior", None) == "Junior"


def test_semi_senior_no_se_confunde_con_senior():
    # 'Semi Senior' contiene 'senior': si el orden de las reglas fuera otro,
    # todos los semi senior quedarían clasificados como senior.
    assert JobScrapingService._seniority("Desarrollador Semi Senior", None) == "Semi Senior"


def test_seniority_es_none_cuando_el_titulo_no_lo_dice():
    assert JobScrapingService._seniority("Desarrollador Backend", None) is None


# ------------------------------------------------
# Fechas
# ------------------------------------------------

def test_fecha_invalida_no_se_inventa():
    assert JobScrapingService._to_date("no es una fecha") is None
    assert JobScrapingService._to_date(NAN) is None
    assert JobScrapingService._to_date("2026-08-22") == "2026-08-22"


# ------------------------------------------------
# Términos de búsqueda
# ------------------------------------------------

def test_terminos_por_rol_no_traen_duplicados():
    terms = JobScrapingService.build_search_terms(["backend", "backend"])

    assert terms == ["desarrollador backend", "backend developer"]


def test_sin_roles_se_buscan_todos_mas_los_extra():
    terms = JobScrapingService.build_search_terms()

    assert "practicante de sistemas" in terms
    assert "desarrollador backend" in terms
    assert len(terms) == len(set(terms))
