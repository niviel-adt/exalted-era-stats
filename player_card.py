import io
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def _font(size: int, bold: bool = False):
    candidates = [
        "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue

    return ImageFont.load_default()


def _fit_font(draw, text, max_width, start_size, min_size=18, bold=False):
    size = start_size
    while size >= min_size:
        font = _font(size, bold=bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 2
    return _font(min_size, bold=bold)


def _draw_centered(draw, center_xy, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = center_xy[0] - (bbox[2] - bbox[0]) / 2
    y = center_xy[1] - (bbox[3] - bbox[1]) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _format_number(value, digits=None, percent=False):
    if value is None:
        return "N/A"

    if isinstance(value, float):
        digits = 2 if digits is None else digits
        text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:,}"

    if percent:
        return f"{text}%"
    return text


def _avatar_image(avatar_bytes, size):
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = ImageOps.fit(avatar, (size, size), method=Image.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(avatar, (0, 0), mask)
    return out


def render_player_card(
    *,
    template_path: str,
    player_name: str,
    rating_grade: str,
    acs,
    kd_ratio,
    hs_percent,
    kills,
    total_matches,
    first_bloods,
    avatar_bytes: bytes,
) -> bytes:
    base = Image.open(Path(template_path)).convert("RGBA")
    draw = ImageDraw.Draw(base)

    width, height = base.size

    # Relative layout tuned for the supplied template.
    gold = (242, 224, 194, 255)
    bright = (255, 244, 225, 255)
    subtle = (225, 205, 170, 255)

    # Player photo slot
    photo_box = (
        int(width * 0.299),
        int(height * 0.159),
        int(width * 0.703),
        int(height * 0.464),
    )
    photo_w = photo_box[2] - photo_box[0]
    photo_h = photo_box[3] - photo_box[1]
    avatar_size = min(photo_w, photo_h) - int(width * 0.03)
    avatar = _avatar_image(avatar_bytes, avatar_size)
    avatar_x = photo_box[0] + (photo_w - avatar_size) // 2
    avatar_y = photo_box[1] + int((photo_h - avatar_size) * 0.42)
    base.alpha_composite(avatar, dest=(avatar_x, avatar_y))

    # Soft glow ring around avatar
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    margin = int(width * 0.012)
    ring_box = (
        avatar_x - margin,
        avatar_y - margin,
        avatar_x + avatar_size + margin,
        avatar_y + avatar_size + margin,
    )
    glow_draw.ellipse(ring_box, outline=(255, 228, 170, 150), width=max(3, width // 256))
    base = Image.alpha_composite(base, glow)
    draw = ImageDraw.Draw(base)

    # Player name
    max_name_width = int(width * 0.50)
    name_font = _fit_font(draw, player_name.upper(), max_name_width, start_size=max(26, width // 17), min_size=18, bold=False)
    _draw_centered(draw, (width * 0.53, height * 0.552), player_name.upper(), name_font, bright)

    # Primary 3 stats row
    title_font = _font(max(18, width // 38), bold=False)
    value_font_large = _font(max(28, width // 24), bold=True)
    value_font_medium = _font(max(24, width // 27), bold=True)

    # The template already has labels, so we only place values.
    stats_top_y = height * 0.70
    second_row_y = height * 0.812

    centers_top = [
        (width * 0.245, stats_top_y),
        (width * 0.500, stats_top_y),
        (width * 0.754, stats_top_y),
    ]
    top_values = [
        rating_grade,
        _format_number(acs, digits=1),
        _format_number(kd_ratio, digits=2),
    ]

    for center, value in zip(centers_top, top_values):
        _draw_centered(draw, (center[0], center[1]), value, value_font_large, gold)

    centers_bottom = [
        (width * 0.198, second_row_y),
        (width * 0.398, second_row_y),
        (width * 0.600, second_row_y),
        (width * 0.800, second_row_y),
    ]
    bottom_values = [
        _format_number(hs_percent, digits=1, percent=True),
        _format_number(kills, digits=0),
        _format_number(total_matches, digits=0),
        _format_number(first_bloods, digits=0),
    ]

    for center, value in zip(centers_bottom, bottom_values):
        font = _fit_font(draw, value, int(width * 0.15), start_size=max(20, width // 27), min_size=16, bold=True)
        _draw_centered(draw, (center[0], center[1]), value, font, gold)

    # Tiny subtitle under portrait: Discord player card style
    small_font = _font(max(14, width // 52), bold=False)
    _draw_centered(draw, (width * 0.50, height * 0.448), "EXALTED ERA PLAYER", small_font, subtle)

    output = io.BytesIO()
    base.save(output, format="PNG")
    return output.getvalue()
