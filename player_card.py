import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",

        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "DejaVuSerif-Bold.ttf"
        if bold
        else "DejaVuSerif.ttf",
    ]

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            pass

    return ImageFont.load_default()


def _fit_font(draw, text, max_width, start_size, min_size=18, bold=True):
    size = start_size

    while size >= min_size:
        font = _font(size, bold=bold)
        box = draw.textbbox((0, 0), text, font=font)

        if box[2] - box[0] <= max_width:
            return font

        size -= 2

    return _font(min_size, bold=bold)


def _draw_center(draw, center_x, center_y, text, font, fill):
    box = draw.textbbox((0, 0), text, font=font)

    width = box[2] - box[0]
    height = box[3] - box[1]

    x = center_x - width / 2
    y = center_y - height / 2 - box[1]

    draw.text(
        (x + 2, y + 2),
        text,
        font=font,
        fill=(0, 0, 0, 210),
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


def _format(value, digits=None, percent=False):
    if value is None:
        text = "N/A"

    elif isinstance(value, float):
        digits = 1 if digits is None else digits
        text = f"{value:.{digits}f}".rstrip("0").rstrip(".")

    else:
        text = f"{value:,}"

    if percent and text != "N/A":
        text += "%"

    return text


def _fit_photo(avatar_bytes: bytes, width: int, height: int):
    photo = Image.open(
        io.BytesIO(avatar_bytes)
    ).convert("RGBA")

    return ImageOps.fit(
        photo,
        (width, height),
        method=Image.LANCZOS,
        centering=(0.5, 0.5),
    )


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

    card = Image.open(
        Path(template_path)
    ).convert("RGBA")

    draw = ImageDraw.Draw(card)

    GOLD = (245, 220, 178, 255)
    BRIGHT_GOLD = (255, 235, 200, 255)

    # ==============================================================
    # PLAYER PHOTO
    # ==============================================================

    photo_left = 211
    photo_top = 350
    photo_right = 730
    photo_bottom = 948

    photo_width = photo_right - photo_left
    photo_height = photo_bottom - photo_top

    photo = _fit_photo(
        avatar_bytes,
        photo_width,
        photo_height,
    )

    card.alpha_composite(
        photo,
        dest=(photo_left, photo_top),
    )

    draw = ImageDraw.Draw(card)

    draw.rectangle(
        (
            photo_left,
            photo_top,
            photo_right - 1,
            photo_bottom - 1,
        ),
        outline=(212, 169, 104, 210),
        width=2,
    )

    # ==============================================================
    # PLAYER NAME
    # ==============================================================

    name = str(
        player_name or "PLAYER"
    ).upper()

    name_font = _fit_font(
        draw,
        name,
        max_width=510,
        start_size=54,
        min_size=28,
        bold=True,
    )

    _draw_center(
        draw,
        470,
        1039,
        name,
        name_font,
        BRIGHT_GOLD,
    )

    # ==============================================================
    # STAT VALUES
    # ==============================================================

    rating = _format(
        rating_score,
        digits=1,
    )

    acs_text = _format(
        acs,
        digits=1,
    )

    kd_text = _format(
        kd_ratio,
        digits=2,
    )

    hs_text = _format(
        hs_percent,
        digits=1,
        percent=True,
    )

    kills_text = _format(
        kills,
        digits=0,
    )

    matches_text = _format(
        total_matches,
        digits=0,
    )

    fb_text = _format(
        first_bloods,
        digits=0,
    )

    top_values = [
        (176, 1286, rating),
        (368, 1286, acs_text),
        (559, 1286, kd_text),
        (750, 1286, hs_text),
    ]

    for x, y, value in top_values:
        font = _fit_font(
            draw,
            value,
            max_width=135,
            start_size=46,
            min_size=28,
            bold=True,
        )

        _draw_center(
            draw,
            x,
            y,
            value,
            font,
            GOLD,
        )

    bottom_values = [
        (220, 1461, kills_text),
        (470, 1461, matches_text),
        (720, 1461, fb_text),
    ]

    for x, y, value in bottom_values:
        font = _fit_font(
            draw,
            value,
            max_width=160,
            start_size=48,
            min_size=28,
            bold=True,
        )

        _draw_center(
            draw,
            x,
            y,
            value,
            font,
            GOLD,
        )

    output = io.BytesIO()

    card.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output.getvalue()
