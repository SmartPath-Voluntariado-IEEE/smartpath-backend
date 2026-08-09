import re


class CourseNormalizerService:

    @staticmethod
    def normalize_duration_hours(effort: str | None) -> int | None:
        if not effort:
            return None

        pattern = r"(\d+(?:\.\d+)?)\s*weeks?.*?(\d+(?:\.\d+)?)\s*hours?/week"

        match = re.search(
            pattern,
            effort.lower(),
        )

        if not match:
            return None

        weeks = float(match.group(1))
        hours_per_week = float(match.group(2))

        return round(weeks * hours_per_week)

    @staticmethod
    def normalize_course(course: dict) -> dict:

        is_free = course.get("isFree")

        if is_free is True:
            price = "Free"
        else:
            price = course.get("pricingLabel")

        level = course.get("level")

        if level:
            level = level.capitalize()

        return {
            "platform": course.get("provider"),
            "title": course.get("title"),
            "instructor": None,
            "duration_hours":
                CourseNormalizerService.normalize_duration_hours(
                    course.get("effort")
                ),
            "language": course.get("language"),
            "price": price,
            "rating": course.get("rating"),
            "level": level,
            "certificate": course.get(
                "hasCertificate",
                False,
            ),
            "url": course.get("courseUrl"),
        }