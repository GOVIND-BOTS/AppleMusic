def time_to_seconds(time: str) -> int:
    stringt = str(time)
    if not stringt or stringt == "None":
        return 0
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


def seconds_to_min(seconds: int) -> str:
    if seconds is None:
        return "0:00"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def get_readable_time(seconds: int) -> str:
    return seconds_to_min(seconds)
