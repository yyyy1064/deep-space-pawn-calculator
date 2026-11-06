"""生成应用图标 assets/app.ico。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


SIZE = 1024
CENTER = SIZE // 2


def _lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def _gradient_background() -> Image.Image:
    image = Image.new("RGB", (SIZE, SIZE), "#070a10")
    pixels = image.load()
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = (
            _lerp(18, 7, t),
            _lerp(28, 10, t),
            _lerp(44, 16, t),
        )
        for x in range(SIZE):
            pixels[x, y] = color
    return image


def build_icon() -> Image.Image:
    image = _gradient_background()
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (26, 26, SIZE - 26, SIZE - 26), radius=190, fill=255
    )

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(image, (0, 0), mask)
    draw = ImageDraw.Draw(canvas, "RGBA")

    # 外框
    draw.rounded_rectangle(
        (30, 30, SIZE - 30, SIZE - 30),
        radius=186,
        outline=(208, 158, 84, 230),
        width=7,
    )

    # 轨道环
    draw.ellipse(
        (CENTER - 300, CENTER - 300, CENTER + 300, CENTER + 300),
        outline=(224, 183, 111, 95),
        width=6,
    )
    draw.ellipse(
        (CENTER - 252, CENTER - 252, CENTER + 252, CENTER + 252),
        outline=(112, 188, 188, 55),
        width=3,
    )

    # 中央菱形徽记
    outer = [
        (CENTER, 214),
        (CENTER + 268, CENTER),
        (CENTER, SIZE - 214),
        (CENTER - 268, CENTER),
    ]
    draw.polygon(outer, fill=(231, 185, 108, 255))

    inner = [
        (CENTER, 330),
        (CENTER + 152, CENTER),
        (CENTER, SIZE - 330),
        (CENTER - 152, CENTER),
    ]
    draw.polygon(inner, fill=(13, 20, 32, 255))

    # 内芯
    core = [
        (CENTER, 424),
        (CENTER + 74, CENTER),
        (CENTER, SIZE - 424),
        (CENTER - 74, CENTER),
    ]
    draw.polygon(core, fill=(112, 211, 201, 220))

    # 星点
    stars = [
        (210, 300, 9, (235, 202, 143, 220)),
        (820, 690, 7, (143, 216, 211, 210)),
        (760, 226, 5, (231, 238, 255, 190)),
        (270, 760, 5, (231, 238, 255, 160)),
        (860, 420, 4, (235, 202, 143, 170)),
        (170, 540, 4, (143, 216, 211, 160)),
    ]
    for x, y, radius, color in stars:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    return canvas.resize((512, 512), Image.Resampling.LANCZOS)


def main() -> None:
    output = Path(__file__).resolve().parent.parent / "assets" / "app.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    icon = build_icon()
    icon.save(
        output,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    icon.save(output.with_suffix(".png"), format="PNG")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
