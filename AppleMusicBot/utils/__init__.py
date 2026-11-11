
from .formatters import get_readable_time, seconds_to_min, time_to_seconds
from .extraction import extract_user


async def int_to_alpha(num: int) -> str:
    """Convert an integer into a stable lowercase alphabetic key."""
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    num = int(num)

    if num < 0:
        raise ValueError("Number must be non-negative")

    result = ""

    while True:
        num, remainder = divmod(num, 26)
        result = alphabet[remainder] + result

        if num == 0:
            break

        num -= 1

    return result


__all__ = [
    "get_readable_time",
    "seconds_to_min",
    "time_to_seconds",
    "extract_user",
    "int_to_alpha",
]
