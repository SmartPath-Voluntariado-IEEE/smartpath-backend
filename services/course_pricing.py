"""
Criterio único de gratuidad de un curso.

La fuente entrega la gratuidad como booleano (`isFree`), pero durante la
normalización se aplanaba a la etiqueta de texto `price`. Mientras la columna
`is_free` no exista en todas las filas, este módulo concentra la regla para
que el resto del backend no la reimplemente de formas distintas.
"""


# "Free Trial Available" NO cuenta como gratis: el curso se paga después de
# la prueba, y ofrecerlo como gratuito rompería la promesa de la plataforma.
FREE_PRICE_LABELS = {
    "free",
    "free course",
    "free online course",
}


def is_free_price(price: str | None) -> bool:
    if not price:
        return False

    return price.strip().lower() in FREE_PRICE_LABELS


def is_free_course(course: dict) -> bool:
    """
    Prefiere la columna booleana `is_free` cuando está disponible y cae a la
    etiqueta `price` para las filas anteriores a la migración.
    """

    stored = course.get("is_free")

    if stored is not None:
        return bool(stored)

    return is_free_price(course.get("price"))
