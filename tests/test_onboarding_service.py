# tests/test_onboarding_service.py
from unittest.mock import patch
from services.onboarding import ChatbotOnboarding, STEP_ASK_NAME, STEP_ASK_INTERESTS, STEP_COMPLETED


class TestGetCurrentStep:

    def test_no_profile_starts_at_name(self):
        assert ChatbotOnboarding.get_current_step(None) == STEP_ASK_NAME

    def test_complete_profile_returns_completed(self):
        profile = {
            "full_name": "Ana", "career": "Sistemas", "academic_cycle": 8,
            "interests": ["backend"], "target_role_id": "backend",
        }
        assert ChatbotOnboarding.get_current_step(profile) == STEP_COMPLETED


class TestSuggestRoles:

    def test_scores_roles_by_interest_overlap(self):
        with patch("services.onboarding.CatalogService.get_all_role_targets") as mock_roles:
            mock_roles.return_value = [
                {"id": "backend", "label": "Backend Developer", "core_skill_slugs": []},
                {"id": "fullstack", "label": "Full Stack Developer", "core_skill_slugs": []},
            ]
            # "backend" y "cloud-devops" ambos sugieren "backend" → score más alto
            suggestions = ChatbotOnboarding.suggest_roles(["backend", "cloud-devops"])
            assert suggestions[0]["id"] == "backend"
            assert suggestions[0]["match_score"] == 2

    def test_no_matches_returns_full_catalog(self):
        with patch("services.onboarding.CatalogService.get_all_role_targets") as mock_roles:
            mock_roles.return_value = [
                {"id": "ml", "label": "ML Engineer", "core_skill_slugs": []},
            ]
            suggestions = ChatbotOnboarding.suggest_roles(["invalid-interest"])
            assert len(suggestions) == 1  # cae al catálogo completo