import httpx

from core.config import settings


class VacancyService:

    @staticmethod
    async def search_jobs():

        headers = {
            "Authorization": f"Bearer {settings.THEIRSTACK_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "job_description_pattern_or": ["analytics"],
            "limit": 25,
            "page": 0,
            "posted_at_max_age_days": 30
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.theirstack.com/v1/jobs/search",
                headers=headers,
                json=body
            )

        return response.json()
