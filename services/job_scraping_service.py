"""
HU-57: recolección de ofertas laborales reales mediante scraping.

Sustituye al recolector de TheirStack (`vacancy_service`), que dependía de
una API de pago cuya clave no está configurada, y al bloque de ofertas del
seed, que inyectaba filas escritas a mano. Aquí las ofertas se recolectan
de portales reales con JobSpy (Indeed, LinkedIn, Glassdoor…).

Dos decisiones que condicionan el resto del módulo:

- **Identidad externa.** Cada oferta se guarda con `source` + `external_id`,
  y el guardado es un upsert sobre ese par. Es lo que permite reejecutar el
  recolector todos los días sin duplicar el catálogo: una oferta ya vista se
  actualiza, no se vuelve a insertar.

- **Términos derivados de los roles.** No se busca "trabajo de programador"
  en abstracto: se busca por los roles objetivo que el onboarding ofrece
  (`role_targets`). Así el catálogo recolectado cubre las rutas que los
  usuarios realmente eligen, que es de lo que depende la recomendación.
"""

from datetime import date, datetime

from core.config import settings
from database.database import get_admin_client

# Términos de búsqueda por rol objetivo. Varios por rol porque los portales
# peruanos publican el mismo puesto con nombres muy distintos ("Desarrollador
# Backend", "Backend Developer"), y buscar solo en inglés pierde la mitad de
# la oferta local.
SEARCH_TERMS_BY_ROLE: dict[str, list[str]] = {
    "backend": ["desarrollador backend", "backend developer"],
    "frontend": ["desarrollador frontend", "frontend developer"],
    "fullstack": ["desarrollador full stack", "full stack developer"],
    "data-analyst": ["analista de datos", "data analyst"],
    "data-engineer": ["ingeniero de datos", "data engineer"],
    "ml": ["machine learning", "inteligencia artificial"],
    "devops": ["devops", "ingeniero devops"],
}

# Términos extra, sin rol asociado, que traen las prácticas y puestos junior
# que son el público de SmartPath y que las búsquedas por rol dejan fuera.
EXTRA_SEARCH_TERMS: list[str] = [
    "practicante de sistemas",
    "practicante desarrollo de software",
    "programador junior",
]

# Longitud máxima guardada de la descripción. Las descripciones completas de
# LinkedIn llegan a decenas de miles de caracteres y el análisis de HU-58
# solo necesita el cuerpo del aviso.
MAX_DESCRIPTION_CHARS = 20000


# Cuántos meses equivale cada periodicidad que reportan los portales, para
# poder llevar todos los sueldos a una cifra mensual comparable.
MONTHLY_FACTOR: dict[str, float] = {
    "yearly": 1 / 12,
    "annual": 1 / 12,
    "monthly": 1.0,
    "weekly": 52 / 12,
    "daily": 22.0,
    "hourly": 160.0,
}


class JobScrapingService:

    # ------------------------------------------------
    # Normalización de una fila de JobSpy
    # ------------------------------------------------

    @staticmethod
    def _clean(value) -> str | None:
        """Convierte a texto no vacío, o None.

        JobSpy devuelve un DataFrame de pandas: las celdas ausentes llegan
        como NaN, no como None, y `str(nan)` produce la cadena 'nan'. Sin
        este filtro, empresas sin nombre se guardarían literalmente como
        "nan" en la base de datos.
        """

        if value is None:
            return None

        # NaN es el único valor que no es igual a sí mismo.
        if value != value:
            return None

        text = str(value).strip()

        if not text or text.lower() in {"nan", "none", "null"}:
            return None

        return text

    @staticmethod
    def _to_int(value) -> int | None:
        text = JobScrapingService._clean(value)

        if text is None:
            return None

        try:
            return int(float(text))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_date(value) -> str | None:
        if isinstance(value, (datetime, date)):
            return value.strftime("%Y-%m-%d")

        text = JobScrapingService._clean(value)

        if text is None:
            return None

        # JobSpy entrega fechas ISO; si el portal manda otra cosa, se
        # descarta antes que guardar una fecha inventada.
        try:
            return datetime.fromisoformat(text[:10]).strftime("%Y-%m-%d")
        except ValueError:
            return None

    @staticmethod
    def _to_bool(value) -> bool | None:
        if isinstance(value, bool):
            return value

        text = JobScrapingService._clean(value)

        if text is None:
            return None

        return text.lower() in {"true", "1", "yes", "si", "sí"}

    @staticmethod
    def _monthly_salary(
        salary_min: int | None,
        salary_max: int | None,
        interval: str | None,
        currency: str | None,
    ) -> int | None:
        """
        Sueldo mensual en soles, o None.

        La columna `salary` es la que consumen `market_overview` y el cálculo
        de compatibilidad desde antes de esta HU, y ambos promedian sus
        valores directamente. Por eso solo se llena cuando el importe ya está
        en soles: mezclar un sueldo anual en dólares con uno mensual en soles
        daría un promedio de mercado sin ningún significado. Los importes en
        otras monedas siguen disponibles en salary_min/max/currency.
        """

        amounts = [value for value in (salary_min, salary_max) if value]

        if not amounts:
            return None

        normalized_currency = (currency or "PEN").upper()

        if normalized_currency not in {"PEN", "S/", "SOL", "SOLES"}:
            return None

        factor = MONTHLY_FACTOR.get((interval or "monthly").lower())

        if factor is None:
            return None

        average = sum(amounts) / len(amounts)

        return round(average * factor)

    @staticmethod
    def _seniority(title: str | None, job_level: str | None) -> str | None:
        """
        Nivel del puesto, deducido del título cuando el portal no lo informa.

        Indeed Perú casi nunca rellena `job_level`, pero el nivel viene en el
        propio título del aviso ("Practicante de Sistemas", "Full Stack Java
        Senior"). Sin esta deducción, los rangos salariales por seniority de
        `market_overview` quedarían todos bajo "Sin especificar".

        El orden importa: 'semi senior' debe evaluarse antes que 'senior',
        porque el título que dice "Semi Senior" contiene también "senior".
        """

        text = f"{title or ''} {job_level or ''}".lower()

        rules = [
            (
                ("practicante", "prácticas", "practicas", "intern", "trainee"),
                "Practicante",
            ),
            (("semi senior", "semi-senior", "semisenior", "ssr"), "Semi Senior"),
            (("junior", "jr."), "Junior"),
            (
                ("lead", "líder", "lider", "jefe", "manager", "principal"),
                "Lead",
            ),
            (("senior", "sr."), "Senior"),
        ]

        for keywords, label in rules:
            if any(keyword in text for keyword in keywords):
                return label

        return None

    @staticmethod
    def normalize_job(row: dict, search_term: str | None = None) -> dict | None:
        """
        Traduce una fila de JobSpy a la forma de la tabla `jobs`.

        Devuelve None si la oferta no tiene identidad externa o no tiene
        puesto: sin `external_id` no se puede deduplicar, y una oferta sin
        título no sirve ni para mostrar ni para analizar.
        """

        clean = JobScrapingService._clean

        # La URL de destino real (job_url_direct) es la identidad estable
        # cuando existe: Indeed republica una misma vacante de terceros
        # (Lever, Greenhouse, Gupy...) varias veces dentro de una sola
        # búsqueda, cada vez con un `id` propio distinto — usar ese id como
        # clave deja pasar duplicados exactos. La URL de Indeed (job_url)
        # solo se usa como último recurso, para avisos publicados nativos
        # que no tienen redirección a otro portal.
        external_id = (
            clean(row.get("job_url_direct"))
            or clean(row.get("id"))
            or clean(row.get("job_url"))
        )
        position = clean(row.get("title"))

        if not external_id or not position:
            return None

        description = clean(row.get("description")) or ""

        salary_min = JobScrapingService._to_int(row.get("min_amount"))
        salary_max = JobScrapingService._to_int(row.get("max_amount"))
        interval = clean(row.get("interval"))
        currency = clean(row.get("currency"))

        return {
            "source": clean(row.get("site")) or "jobspy",
            "external_id": external_id[:160],
            "url": clean(row.get("job_url_direct")) or clean(row.get("job_url")),
            "company": (clean(row.get("company")) or "")[:200] or None,
            "position": position[:300],
            "location": (clean(row.get("location")) or "")[:200] or None,
            "description": description[:MAX_DESCRIPTION_CHARS] or None,
            "posted_at": JobScrapingService._to_date(row.get("date_posted")),
            "is_remote": JobScrapingService._to_bool(row.get("is_remote")),
            "job_type": (clean(row.get("job_type")) or "")[:60] or None,
            "seniority": JobScrapingService._seniority(
                position,
                clean(row.get("job_level")),
            ),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": currency,
            "salary_interval": interval,
            "salary": JobScrapingService._monthly_salary(
                salary_min,
                salary_max,
                interval,
                currency,
            ),
            "search_term": (search_term or "")[:120] or None,
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
        }

    # ------------------------------------------------
    # Recolección
    # ------------------------------------------------

    @staticmethod
    def build_search_terms(role_ids: list[str] | None = None) -> list[str]:
        """Términos a buscar, sin repetidos y en orden estable."""

        if role_ids:
            selected = [
                term
                for role_id in role_ids
                for term in SEARCH_TERMS_BY_ROLE.get(role_id, [])
            ]
        else:
            selected = [
                term
                for terms in SEARCH_TERMS_BY_ROLE.values()
                for term in terms
            ] + EXTRA_SEARCH_TERMS

        return list(dict.fromkeys(selected))

    @staticmethod
    def scrape_term(
        search_term: str,
        sites: list[str] | None = None,
        results_wanted: int | None = None,
        hours_old: int | None = None,
        location: str | None = None,
    ) -> list[dict]:
        """
        Ejecuta JobSpy para un término y devuelve ofertas ya normalizadas.

        La importación es diferida a propósito: JobSpy arrastra pandas y
        tls_client, y no hace falta pagar ese import cada vez que arranca la
        API — solo cuando de verdad se recolecta.
        """

        from jobspy import scrape_jobs

        frame = scrape_jobs(
            site_name=sites or settings.JOBSPY_SITES,
            search_term=search_term,
            location=location or settings.JOBSPY_LOCATION,
            country_indeed=settings.JOBSPY_COUNTRY,
            results_wanted=(
                results_wanted
                if results_wanted is not None
                else settings.JOBSPY_RESULTS_PER_TERM
            ),
            hours_old=(
                hours_old
                if hours_old is not None
                else settings.JOBSPY_HOURS_OLD
            ),
            description_format="markdown",
            verbose=0,
            proxies=settings.JOBSPY_PROXIES or None,
        )

        if frame is None or len(frame) == 0:
            return []

        jobs = []

        for row in frame.to_dict(orient="records"):
            normalized = JobScrapingService.normalize_job(row, search_term)

            if normalized:
                jobs.append(normalized)

        return jobs

    @staticmethod
    def save_jobs(jobs: list[dict]) -> list[dict]:
        """
        Guarda las ofertas deduplicando por (source, external_id).

        El upsert necesita que el lote no traiga la misma clave dos veces:
        Postgres rechaza un ON CONFLICT que afecte dos veces a la misma fila
        en la misma sentencia, y un término de búsqueda puede devolver la
        misma oferta en dos páginas o en dos portales.
        """

        if not jobs:
            return []

        unique: dict[tuple, dict] = {}

        for job in jobs:
            unique[(job["source"], job["external_id"])] = job

        response = (
            get_admin_client()
            .table("jobs")
            .upsert(
                list(unique.values()),
                on_conflict="source,external_id",
            )
            .execute()
        )

        return response.data or []

    @staticmethod
    def collect_and_save_jobs(
        role_ids: list[str] | None = None,
        sites: list[str] | None = None,
        results_wanted: int | None = None,
        hours_old: int | None = None,
        extract_requirements: bool = True,
    ) -> dict:
        """
        Corre el ciclo completo de HU-57: buscar, normalizar y guardar.

        Un término que falle (rate limit, portal caído) no aborta la corrida:
        se registra en `errors` y el resto de términos continúa. Media hora de
        scraping no debería perderse porque un portal respondió 429.
        """

        import time

        terms = JobScrapingService.build_search_terms(role_ids)

        collected: list[dict] = []
        errors: list[dict] = []

        for index, term in enumerate(terms):
            try:
                collected.extend(
                    JobScrapingService.scrape_term(
                        term,
                        sites=sites,
                        results_wanted=results_wanted,
                        hours_old=hours_old,
                    )
                )
            except Exception as error:
                errors.append({"search_term": term, "error": str(error)})

            # Pausa entre términos, salvo después del último.
            if index < len(terms) - 1 and settings.JOBSPY_DELAY_SECONDS > 0:
                time.sleep(settings.JOBSPY_DELAY_SECONDS)

        saved = JobScrapingService.save_jobs(collected)

        result = {
            "message": (
                "Ofertas recolectadas y guardadas correctamente."
                if saved
                else "No se guardaron ofertas nuevas."
            ),
            "search_terms": terms,
            "sites": sites or settings.JOBSPY_SITES,
            "collected": len(collected),
            "saved": len(saved),
            "errors": errors,
        }

        # HU-58 se ejecuta sobre lo recién recolectado: una oferta guardada
        # sin sus habilidades no aparece en ninguna recomendación, así que
        # dejarlo para una llamada aparte solo abre la puerta a olvidarlo.
        if extract_requirements and saved:
            from services.job_requirements_service import (
                JobRequirementsService,
            )

            result["requirements"] = JobRequirementsService.extract_and_save(
                job_ids=[job["id"] for job in saved if job.get("id")],
            )

        return result

    # ------------------------------------------------
    # Mantenimiento
    # ------------------------------------------------

    @staticmethod
    def purge_non_scraped_jobs() -> dict:
        """
        Borra las ofertas que no vinieron de scraping (las del seed antiguo).

        Es destructivo y por eso no se ejecuta solo: lo dispara el script
        `scripts/scrape_jobs.py --purge-seed` de forma explícita.
        """

        response = (
            get_admin_client()
            .table("jobs")
            .delete()
            .is_("source", "null")
            .execute()
        )

        return {
            "deleted": len(response.data or []),
            "message": "Ofertas sin origen de scraping eliminadas.",
        }
