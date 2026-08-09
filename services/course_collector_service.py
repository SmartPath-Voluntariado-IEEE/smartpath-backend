import httpx

from core.config import settings


class CourseCollectorService:

    BASE_URL = (
        "https://api.apify.com/v2/acts/"
        f"{settings.APIFY_ACTOR_ID}/"
        "run-sync-get-dataset-items"
    )

    @staticmethod
    def collect_courses(
        search_query: str,
        max_items: int = 10,
    ):
        if not settings.APIFY_API_TOKEN:
            raise ValueError(
                "Falta APIFY_API_TOKEN en las variables de entorno."
            )

        payload = {
            "mode": "search",
            "searchQuery": search_query,
            "freeOnly": False,
            "certificateOnly": False,
            "careerCertificateOnly": False,
            "universityOnly": False,
            "sortBy": "relevancy",
            "maxItems": max_items,
        }

        headers = {
            "Authorization": (
                f"Bearer {settings.APIFY_API_TOKEN}"
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = httpx.post(
                CourseCollectorService.BASE_URL,
                json=payload,
                headers=headers,
                timeout=120,
            )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as error:
            raise RuntimeError(
                "Apify tardó demasiado en responder."
            ) from error

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                f"Apify respondió con código "
                f"{error.response.status_code}: "
                f"{error.response.text}"
            ) from error

        except httpx.RequestError as error:
            raise RuntimeError(
                f"No se pudo conectar con Apify: {error}"
            ) from error