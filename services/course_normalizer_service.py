import re


class CourseNormalizerService:

    @staticmethod
    def normalize_duration_hours(effort: str | None) -> int | None:
        """
        La fuente expresa el esfuerzo en varios formatos, así que se prueban
        en orden de especificidad. Devuelve None si no reconoce ninguno, para
        no inventar una duración.
        """

        if not effort:
            return None

        text = effort.lower()

        # "6 weeks, 4 hours/week" -> semanas por horas semanales
        weekly = re.search(
            r"(\d+(?:\.\d+)?)\s*weeks?.*?(\d+(?:\.\d+)?)\s*hours?/week",
            text,
        )

        if weekly:
            return round(
                float(weekly.group(1)) * float(weekly.group(2))
            )

        # "5 hours 38 minutes" / "3 hours" / "45 minutes"
        hours_match = re.search(r"(\d+(?:\.\d+)?)\s*hours?", text)
        minutes_match = re.search(r"(\d+(?:\.\d+)?)\s*min", text)

        if hours_match or minutes_match:
            total = 0.0

            if hours_match:
                total += float(hours_match.group(1))

            if minutes_match:
                total += float(minutes_match.group(1)) / 60

            # Un curso de 38 minutos no debe quedar en 0 horas.
            return max(1, round(total))

        return None

    @staticmethod
    def normalize_course(course: dict) -> dict:

        is_free = course.get("isFree") is True

        if is_free:
            price = "Free"
        else:
            price = course.get("pricingLabel")

        level = course.get("level")

        if level:
            level = level.capitalize()

        # El modo `search` del actor no expone la institución que dicta el
        # curso (Harvard, MIT…), solo el proveedor. Cuando marca el curso como
        # universitario se guarda el proveedor como mejor aproximación
        # disponible; si no, la columna queda vacía.
        institution = None

        if course.get("isUniversityCourse"):
            institution = course.get("provider")

        return {
            "platform": course.get("provider"),
            "institution": institution,
            "title": course.get("title"),
            "instructor": course.get("instructor"),
            "duration_hours":
                CourseNormalizerService.normalize_duration_hours(
                    course.get("effort")
                ),
            "language": course.get("language"),
            "price": price,
            "is_free": is_free,
            "rating": course.get("rating"),
            "level": level,
            "certificate": course.get(
                "hasCertificate",
                False,
            ),
            "url": course.get("courseUrl"),
        }