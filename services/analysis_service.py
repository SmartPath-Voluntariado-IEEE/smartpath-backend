import re
from typing import List, Dict, Any

SKILL_TIER: Dict[str, int] = {
    "git": 1, "github": 1, "sql": 1, "linux": 1, "excel": 1, "english": 1,
    "javascript": 2, "typescript": 2, "python": 2, "java": 2, "tailwind": 2, "pandas": 2,
    "react": 3, "nodejs": 3, "springboot": 3, "rest": 3, "powerbi": 3, "django": 3, "fastapi": 3,
    "nextjs": 3, "mongodb": 3, "mysql": 3, "postgres": 3,
    "docker": 4, "redis": 4, "graphql": 4, "scrum": 4,
    "kubernetes": 5, "aws": 5, "gcp": 5, "azure": 5, "tensorflow": 5,
}

def extract_skills_from_text(text: str, skills_catalog: List[Dict[str, Any]]) -> List[str]:
    lower = " " + text.lower() + " "
    found = set()
    for s in skills_catalog:
        aliases = s.get("aliases")
        names = [s["name"]] + (aliases if aliases else [])
        for n in names:
            needle = n.lower()
            escaped = re.escape(needle)
            # Asegurar límites de palabra compatibles con caracteres como # o +
            pattern = rf"(^|[^a-z0-9\+#\.])({escaped})([^a-z0-9\+#]|$)"
            if re.search(pattern, lower, re.IGNORECASE):
                found.add(s["slug"])
                break
    return list(found)

class AnalysisService:
    @staticmethod
    def market_skill_frequency(jobs: List[Dict[str, Any]], skills_catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        counts = {}
        for j in jobs:
            text = f"{j.get('position', '')} {j.get('description', '')}"
            extracted = extract_skills_from_text(text, skills_catalog)
            for slug in extracted:
                counts[slug] = counts.get(slug, 0) + 1
                
        total = len(jobs)
        stats = []
        for slug, count in counts.items():
            s_info = next((s for s in skills_catalog if s["slug"] == slug), None)
            if s_info:
                stats.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "category": s_info["category"],
                    "count": count,
                    "frequency": count / total if total > 0 else 0.0
                })
        stats.sort(key=lambda x: x["count"], reverse=True)
        return stats

    @staticmethod
    def analyze_gap(user_skills: List[Dict[str, Any]], target_role: Dict[str, Any], market: List[Dict[str, Any]], skills_catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
        user_map = {us["skill_slug"]: us["level"] for us in user_skills}
        freq_map = {m["skill_slug"]: m["frequency"] for m in market}
        
        mastered = []
        partial = []
        missing = []
        
        core_slugs = target_role.get("core_skill_slugs", [])
        for slug in core_slugs:
            s_info = next((s for s in skills_catalog if s["slug"] == slug), None)
            if not s_info:
                continue
            lvl = user_map.get(slug)
            freq = freq_map.get(slug, 0.0)
            
            if lvl and lvl >= 4:
                mastered.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "level": lvl,
                    "marketFreq": freq
                })
            elif lvl and lvl >= 2:
                partial.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "level": lvl,
                    "marketFreq": freq
                })
            else:
                missing.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "marketFreq": freq,
                    "priority": freq * 100.0 - SKILL_TIER.get(slug, 3)
                })
                
        # Agregar habilidades top demandadas que no están en el core del rol ni tiene el usuario
        for m in market[:8]:
            slug = m["skill_slug"]
            if slug in core_slugs:
                continue
            if slug in user_map:
                continue
            s_info = next((s for s in skills_catalog if s["slug"] == slug), None)
            if s_info:
                missing.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "marketFreq": m["frequency"],
                    "priority": m["frequency"] * 60.0 - SKILL_TIER.get(slug, 3)
                })
                
        missing.sort(key=lambda x: x["priority"], reverse=True)
        
        coverage = 0.0
        if core_slugs:
            coverage = (len(mastered) + len(partial) * 0.5) / len(core_slugs)
            
        return {
            "target_role": target_role,
            "mastered": mastered,
            "partial": partial,
            "missing": missing,
            "coverage": coverage
        }

    @staticmethod
    def generate_roadmap(gap: Dict[str, Any]) -> List[Dict[str, Any]]:
        buckets = {}
        
        # Combinar missing y partial
        all_skills = []
        for m in gap["missing"]:
            all_skills.append({
                "skill_slug": m["skill_slug"],
                "name": m["name"],
                "marketFreq": m["marketFreq"]
            })
        for p in gap["partial"]:
            all_skills.append({
                "skill_slug": p["skill_slug"],
                "name": p["name"],
                "marketFreq": p["marketFreq"]
            })
            
        for m in all_skills:
            slug = m["skill_slug"]
            tier = SKILL_TIER.get(slug, 3)
            
            if tier not in buckets:
                buckets[tier] = []
                
            if not any(x["skill_slug"] == slug for x in buckets[tier]):
                # Estimar horas basándose en el tier
                hours_by_tier = [0, 10, 25, 40, 30, 45]
                est_hours = hours_by_tier[tier] if tier < len(hours_by_tier) else 30
                
                buckets[tier].append({
                    "skill_slug": slug,
                    "name": m["name"],
                    "marketFreq": m["marketFreq"],
                    "estHours": est_hours
                })
                
        labels = {
            1: "Fundamentos",
            2: "Lenguajes base",
            3: "Frameworks & datos",
            4: "Contenedores & prácticas",
            5: "Cloud & especialización",
        }
        
        roadmap = []
        for lvl in sorted(buckets.keys()):
            skills = buckets[lvl]
            skills.sort(key=lambda x: x["marketFreq"], reverse=True)
            roadmap.append({
                "level": lvl,
                "label": labels.get(lvl, f"Nivel {lvl}"),
                "skills": skills
            })
        return roadmap

    @staticmethod
    def recommend_courses(skill_slug: str, user_level: int, availability: int, preferences: List[str], target_role: str, courses_catalog: List[Dict[str, Any]], skill_name: str) -> List[Dict[str, Any]]:
        # Filtrar los cursos que contienen la skill seleccionada
        matched = [c for c in courses_catalog if skill_slug in c.get("skill_slugs", [])]
        
        user_prefs_lower = [p.lower() for p in preferences] if preferences else ["video"]
        primary_style = user_prefs_lower[0] if user_prefs_lower else "video"

        recs = []
        for c in matched:
            course_title = c.get("title", "").lower()
            course_hours = c.get("duration_hours", 10)
            
            # Determinar coincidencia de formato (HU1)
            is_matched = any(p in course_title or (p == "video" and "video" in course_title) for p in user_prefs_lower)
            format_style = primary_style if is_matched else "general"

            # Calcular semanas estimadas según la disponibilidad semanal (HU2)
            weeks_est = max(1, round(course_hours / max(availability, 1)))

            recs.append({
                "title": c["title"],
                "platform": c["platform"],
                "url": c["url"],
                "price": c["price"],
                "rating": c["rating"],
                "hours": course_hours,
                "level": c["level"],
                "style": format_style,
                "why": f"Curso recomendado en formato {format_style} (~{weeks_est} sem a {availability}h/sem) enfocado en tu meta de {target_role or 'Desarrollador'}.",
                "_matched": 1 if is_matched else 0,
            })

        # Ordenar: primero los que coinciden con la preferencia de formato (HU1), luego por rating
        recs.sort(key=lambda x: (x["_matched"], x["rating"]), reverse=True)
        
        # Remover campo auxiliar interno
        for r in recs:
            r.pop("_matched", None)

        return recs
