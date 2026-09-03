from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "renders" / "listing"
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONT_REGULAR = Path(r"C:\Windows\Fonts\arial.ttf")

CARDS = [
    (
        "listing_01_hero_raw.png",
        "listing_01_hero_mockup.png",
        "ANIME-INSPIRED COSPLAY PROP",
        "Matte PLA body  •  cloth-wrapped grip  •  display and roleplay use",
    ),
    (
        "listing_02_dimensions_raw.png",
        "listing_02_dimensions_mockup.png",
        "FULL-SIZE DISPLAY PROP",
        "Approx. 280 mm long  •  45 mm wide  •  25 mm deep",
    ),
    (
        "listing_03_grip_raw.png",
        "listing_03_grip_mockup.png",
        "HAND-FINISHED GRIP",
        "Textured white cloth wrap  •  rounded finger ring",
    ),
    (
        "listing_04_blade_raw.png",
        "listing_04_blade_mockup.png",
        "FACETED PLA CONSTRUCTION",
        "Blunt rounded tip  •  nonfunctional costume accessory",
    ),
    (
        "listing_05_packaging_raw.png",
        "listing_05_packaging_mockup.png",
        "MADE-TO-ORDER PACKAGING CONCEPT",
        "Protective kraft mailer  •  presentation shown as a digital mockup",
    ),
]


def fit_font(text: str, max_width: int, start_size: int, font_path: Path) -> ImageFont.FreeTypeFont:
    size = start_size
    while size > 16:
        font = ImageFont.truetype(str(font_path), size)
        if font.getlength(text) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(str(font_path), size)


for source_name, output_name, title, subtitle in CARDS:
    image = Image.open(OUT / source_name).convert("RGBA")
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    band_height = max(105, int(height * 0.17))
    draw.rectangle((0, height - band_height, width, height), fill=(13, 16, 18, 224))

    margin = max(28, int(width * 0.025))
    title_font = fit_font(title, width - 2 * margin, max(30, int(height * 0.045)), FONT_BOLD)
    subtitle_font = fit_font(subtitle, width - 2 * margin, max(22, int(height * 0.026)), FONT_REGULAR)
    draw.text((margin, height - band_height + 20), title, font=title_font, fill=(248, 247, 242, 255))
    draw.text((margin, height - band_height + 28 + title_font.size), subtitle, font=subtitle_font, fill=(205, 211, 213, 255))

    badge = "DIGITAL MOCKUP — NOT A PRODUCT PHOTO"
    badge_font = fit_font(badge, int(width * 0.44), max(18, int(height * 0.019)), FONT_BOLD)
    badge_padding_x, badge_padding_y = 16, 10
    badge_w = int(badge_font.getlength(badge)) + badge_padding_x * 2
    badge_h = badge_font.size + badge_padding_y * 2
    badge_x, badge_y = width - badge_w - margin, margin
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=badge_h // 3,
        fill=(16, 19, 21, 220),
        outline=(235, 236, 232, 180),
        width=2,
    )
    draw.text(
        (badge_x + badge_padding_x, badge_y + badge_padding_y - 1),
        badge,
        font=badge_font,
        fill=(248, 247, 242, 255),
    )

    Image.alpha_composite(image, overlay).convert("RGB").save(OUT / output_name, quality=96)
    print(f"Wrote {OUT / output_name}")
