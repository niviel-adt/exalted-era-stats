import io
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


def _fit_font(draw, text, max_width, start_size, min_size=14, bold=True):
    size = start_size
    while size >= min_size:
        font = _font(size, bold=bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 2
    return _font(min_size, bold=bold)


def _center(draw, xy, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = xy[0] - (bbox[2] - bbox[0]) / 2
    y = xy[1] - (bbox[3] - bbox[1]) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _fmt(value, digits=None, percent=False):
    if value is None:
        text = "N/A"
    elif isinstance(value, float):
        digits = 1 if digits is None else digits
        text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:,}"
    return f"{text}%" if percent and text != "N/A" else text


def _rounded_photo(avatar_bytes, size_xy, radius=24):
    image = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    image = ImageOps.fit(image, size_xy, method=Image.LANCZOS)

    mask = Image.new("L", size_xy, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, size_xy[0], size_xy[1]), radius=radius, fill=255)

    out = Image.new("RGBA", size_xy, (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def render_player_card(
    *,
    template_path: str,
    player_name: str,
    rating_score,
    rating_grade,
    acs,
    kd_ratio,
    hs_percent,
    kills,
    total_matches,
    first_bloods,
    avatar_bytes: bytes,
) -> bytes:
    base = Image.open(Path(template_path)).convert("RGBA")
    w, h = base.size
    draw = ImageDraw.Draw(base)

    dark_fill = (3, 3, 5, 245)
    gold = (244, 223, 186, 255)
    bright = (255, 240, 215, 255)
    subtle = (220, 196, 160, 255)

    def rr(box, fill, radius=16, outline=None, width=0):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

    # --- PHOTO AREA ---
    photo_frame = (
        int(w * 0.252),
        int(h * 0.226),
        int(w * 0.747),
        int(h * 0.602),
    )
    inner_pad_x = int(w * 0.018)
    inner_pad_y = int(h * 0.014)
    photo_inner = (
        photo_frame[0] + inner_pad_x,
        photo_frame[1] + inner_pad_y,
        photo_frame[2] - inner_pad_x,
        photo_frame[3] - inner_pad_y,
    )

    rr(photo_inner, dark_fill, radius=28)
    photo_size = (photo_inner[2] - photo_inner[0], photo_inner[3] - photo_inner[1])
    photo = _rounded_photo(avatar_bytes, photo_size, radius=28)
    base.alpha_composite(photo, dest=(photo_inner[0], photo_inner[1]))

    # subtle dark gradient band under portrait so text reads clearly
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle(
        (
            photo_inner[0],
            int(h * 0.53),
            photo_inner[2],
            photo_inner[3],
        ),
        fill=(0, 0, 0, 70),
    )
    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    # --- NAME AREA ---
    # cover the old placeholder cleanly, then draw the real name
    name_box = (
        int(w * 0.150),
        int(h * 0.628),
        int(w * 0.852),
        int(h * 0.697),
    )
    rr(name_box, (2, 2, 4, 235), radius=12)

    name_text = str(player_name or "PLAYER").upper()
    name_font = _fit_font(draw, name_text, int(w * 0.56), start_size=max(28, w // 14), min_size=20, bold=True)
    _center(draw, (w * 0.50, h * 0.664), name_text, name_font, bright)

    # small grade subtitle
    grade_text = f"GRADE {rating_grade}" if rating_grade else "EXALTED ERA"
    grade_font = _fit_font(draw, grade_text, int(w * 0.28), start_size=max(12, w // 55), min_size=10, bold=False)
    _center(draw, (w * 0.50, h * 0.690), grade_text, grade_font, subtle)

    # --- VALUE MASKS ---
    def mask_value(cx, cy, bw, bh):
        rr(
            (
                int(cx - bw / 2),
                int(cy - bh / 2),
                int(cx + bw / 2),
                int(cy + bh / 2),
            ),
            (2, 2, 4, 228),
            radius=10,
        )

    # mask the old sample numbers only, preserving labels/icons
    top_y = h * 0.808
    bottom_y = h * 0.918

    for cx in [w * 0.163, w * 0.398, w * 0.616, w * 0.842]:
        mask_value(cx, top_y, w * 0.125, h * 0.052)

    for cx in [w * 0.220, w * 0.500, w * 0.780]:
        mask_value(cx, bottom_y, w * 0.155, h * 0.058)

    # --- VALUES ---
    rating_display = _fmt(rating_score, digits=1)
    acs_display = _fmt(acs, digits=0)
    kd_display = _fmt(kd_ratio, digits=2)
    hs_display = _fmt(hs_percent, digits=1, percent=True)
    kills_display = _fmt(kills, digits=0)
    matches_display = _fmt(total_matches, digits=0)
    fb_display = _fmt(first_bloods, digits=0)

    top_centers = [
        (w * 0.163, top_y),
        (w * 0.398, top_y),
        (w * 0.616, top_y),
        (w * 0.842, top_y),
    ]
    top_text = [
        rating_display,
        acs_display,
        kd_display,
        hs_display,
    ]

    for (cx, cy), value in zip(top_centers, top_text):
        font = _fit_font(draw, value, int(w * 0.12), start_size=max(28, w // 18), min_size=20, bold=True)
        _center(draw, (cx, cy), value, font, gold)

    bottom_centers = [
        (w * 0.220, bottom_y),
        (w * 0.500, bottom_y),
        (w * 0.780, bottom_y),
    ]
    bottom_text = [
        kills_display,
        matches_display,
        fb_display,
    ]

    for (cx, cy), value in zip(bottom_centers, bottom_text):
        font = _fit_font(draw, value, int(w * 0.15), start_size=max(28, w // 18), min_size=20, bold=True)
        _center(draw, (cx, cy), value, font, gold)

    # subtle player caption beneath photo
    caption = "PLAYER CARD"
    caption_font = _fit_font(draw, caption, int(w * 0.22), start_size=max(12, w // 60), min_size=10, bold=False)
    _center(draw, (w * 0.50, h * 0.590), caption, caption_font, subtle)

    out = io.BytesIO()
    base.save(out, format="PNG")
    return out.getvalue()
