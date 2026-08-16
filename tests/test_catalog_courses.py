from fastapi.testclient import TestClient

from api.routes import CatalogService
from main import app

client = TestClient(app)


def test_catalog_courses_exposes_course_detail_fields(monkeypatch):
    catalog_course = {
        "id": 1,
        "platform": "Coursera",
        "institution": None,
        "title": "Python para análisis de datos",
        "instructor": "Ada Lovelace",
        "duration_hours": 18,
        "language": "Español",
        "price": "Gratis",
        "is_free": False,
        "rating": 4.8,
        "level": "Básico",
        "certificate": True,
        "url": "https://example.com/course",
        "skill_slugs": ["python"],
    }
    monkeypatch.setattr(
        CatalogService,
        "get_all_courses",
        staticmethod(lambda skill_slug=None, limit=None, offset=0: [catalog_course]),
    )

    response = client.get("/catalog/courses")

    assert response.status_code == 200
    assert response.json() == [catalog_course]
