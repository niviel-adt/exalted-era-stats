def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def scaled(value, target):
    if value is None or target <= 0:
        return 0.0
    return clamp((float(value) / float(target)) * 100.0)


def calculate_rating(stats: dict):
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
