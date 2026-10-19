import math


class InvalidStats(ValueError):
    """The screenshot cannot support a reliable performance rating."""


def validate_rating_stats(stats):
    """Require all rating inputs; never silently score missing data as zero."""
    result = dict(stats)
    counts = {"kills", "total_matches", "first_bloods"}
    for name in ("acs", "kd_ratio", "headshot_percentage", "kills", "total_matches", "first_bloods"):
        value = stats.get(name)
        if isinstance(value, bool) or value is None:
            raise InvalidStats(f"Missing or invalid {name}.")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            raise InvalidStats(f"Missing or invalid {name}.") from None
        if not math.isfinite(number) or number < 0:
            raise InvalidStats(f"Invalid {name}.")
        if name in counts and not number.is_integer():
            raise InvalidStats(f"{name} must be a whole number.")
        result[name] = int(number) if name in counts else number
    if result["total_matches"] <= 0:
        raise InvalidStats("Total matches must be greater than zero.")
    if result["headshot_percentage"] > 100:
        raise InvalidStats("HS% must be between 0 and 100.")
    if result["first_bloods"] > result["kills"]:
        raise InvalidStats("First bloods cannot exceed kills.")
    return result


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def scaled(value, target):
    if value is None or target <= 0:
        return 0.0
    return clamp((float(value) / float(target)) * 100.0)


def calculate_rating(stats: dict):
    stats = validate_rating_stats(stats)
    acs = stats.get("acs")
    kd = stats.get("kd_ratio")
    hs = stats.get("headshot_percentage")
    kills = stats.get("kills")
    matches = stats.get("total_matches")
    first_bloods = stats.get("first_bloods")

    kills_per_match = None
    fb_per_match = None

    if matches not in (None, 0):
        if kills is not None:
            kills_per_match = float(kills) / float(matches)
        if first_bloods is not None:
            fb_per_match = float(first_bloods) / float(matches)

    score = (
        scaled(acs, 300) * 0.30
        + scaled(kd, 1.50) * 0.25
        + scaled(hs, 30) * 0.20
        + scaled(kills_per_match, 12) * 0.15
        + scaled(fb_per_match, 2.0) * 0.10
    )

    score = round(clamp(score), 1)

    if score >= 90:
        grade = "S"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 60:
        grade = "C"
    else:
        grade = "D"

    return score, grade


def rating_label(grade: str):
    return {
        "S": "ELITE",
        "A": "EXCELLENT",
        "B": "STRONG",
        "C": "DEVELOPING",
        "D": "NEEDS IMPROVEMENT",
    }.get(grade, "UNRATED")

