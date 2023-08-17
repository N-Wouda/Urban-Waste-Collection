def f2i(val: float, scale: int = 10_000) -> int:
    """
    Translates the given float value into an integer, by multiplying it by
    scale and rounding the result.
    """
    return round(val * scale)
