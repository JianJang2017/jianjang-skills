#!/usr/bin/env python3
"""Render an exact-text, 16:9 blackboard mockup as a 4K PNG."""

import argparse
import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 3840, 2160
FONT_CANDIDATES = (
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
)


def font(size):
    candidates = [os.environ.get("HEIBANBAO_FONT"), *FONT_CANDIDATES]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    raise RuntimeError("未找到支持中文的字体；请设置 HEIBANBAO_FONT 为中文 TTF/TTC 文件路径")


def color(value, default):
    value = value or default
    if not isinstance(value, str) or len(value) != 7 or value[0] != "#":
        raise ValueError(f"颜色必须是 #RRGGBB：{value}")
    try:
        return tuple(bytes.fromhex(value[1:]))
    except ValueError as exc:
        raise ValueError(f"颜色必须是 #RRGGBB：{value}") from exc


def wrapped(draw, text, chosen_font, max_width):
    lines = []
    for paragraph in str(text).splitlines():
        line = ""
        for char in paragraph:
            candidate = line + char
            if line and draw.textlength(candidate, font=chosen_font) > max_width:
                if char in "，。；：？！、）》」”" and len(line) > 1:
                    lines.append(line[:-1].rstrip())
                    line = line[-1] + char
                else:
                    lines.append(line.rstrip())
                    line = char
            else:
                line = candidate
        lines.append(line.rstrip())
    return lines or [""]


def fit_one_line(draw, value, chosen_font, max_width, label):
    if "\n" in value or draw.textlength(value, font=chosen_font) > max_width:
        raise ValueError(f"{label}过长，请缩短到一行：{value}")


def background(canvas, source):
    if not source:
        return
    with Image.open(source) as raw:
        image = raw.convert("RGB")
        scale = max(WIDTH / image.width, HEIGHT / image.height)
        size = (round(image.width * scale), round(image.height * scale))
        image = image.resize(size, Image.Resampling.LANCZOS)
        left = (image.width - WIDTH) // 2
        top = (image.height - HEIGHT) // 2
        image = image.crop((left, top, left + WIDTH, top + HEIGHT))
        canvas.paste(Image.blend(canvas, image, 0.62))


def star(draw, cx, cy, radius, fill, outline=None):
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        distance = radius if index % 2 == 0 else radius * 0.45
        points.append((cx + math.cos(angle) * distance, cy + math.sin(angle) * distance))
    draw.polygon(points, fill=fill, outline=outline)


def illustration(draw, kind, cx, cy, main, accent):
    """Simple chalk line drawings placed in a panel's lower half."""
    line = 12
    if kind == "book":
        draw.line([(cx - 235, cy + 65), (cx - 235, cy - 100), (cx - 30, cy - 65), (cx, cy - 35)], fill=accent, width=line, joint="curve")
        draw.line([(cx + 235, cy + 65), (cx + 235, cy - 100), (cx + 30, cy - 65), (cx, cy - 35)], fill=accent, width=line, joint="curve")
        draw.line([(cx - 235, cy + 65), (cx - 25, cy + 100), (cx, cy + 125), (cx + 25, cy + 100), (cx + 235, cy + 65)], fill=accent, width=line, joint="curve")
        draw.line((cx, cy - 35, cx, cy + 125), fill=main, width=8)
        for offset in (-140, -95, -50):
            draw.line((cx - 190, cy + offset, cx - 55, cy + offset + 25), fill=main, width=6)
            draw.line((cx + 55, cy + offset + 25, cx + 190, cy + offset), fill=main, width=6)
    elif kind == "torch":
        draw.polygon([(cx - 35, cy - 30), (cx + 35, cy - 30), (cx + 17, cy + 185), (cx - 17, cy + 185)], outline=main)
        draw.line((cx - 35, cy - 30, cx + 35, cy - 30, cx + 17, cy + 185, cx - 17, cy + 185, cx - 35, cy - 30), fill=main, width=line)
        draw.line((cx - 95, cy - 58, cx + 95, cy - 58), fill=accent, width=18)
        draw.polygon([(cx, cy - 275), (cx - 100, cy - 118), (cx - 45, cy - 78), (cx + 45, cy - 78), (cx + 100, cy - 118)], outline=accent)
        draw.line([(cx, cy - 275), (cx - 100, cy - 118), (cx - 45, cy - 78), (cx + 45, cy - 78), (cx + 100, cy - 118), (cx, cy - 275)], fill=accent, width=line, joint="curve")
        draw.line((cx, cy - 188, cx - 29, cy - 115, cx + 26, cy - 115, cx, cy - 188), fill=main, width=7)
    elif kind == "footprints":
        for dx, dy, angle in [(-125, 105, -1), (-10, -20, 1), (130, -135, -1)]:
            x, y = cx + dx, cy + dy
            draw.ellipse((x - 42, y - 53, x + 42, y + 53), outline=main, width=line)
            toe_x = x + 34 * angle
            draw.ellipse((toe_x - 27, y - 105, toe_x + 27, y - 59), outline=accent, width=9)
    elif kind == "sprout":
        draw.arc((cx - 200, cy + 102, cx + 200, cy + 230), 190, 350, fill=accent, width=line)
        draw.line((cx, cy + 154, cx, cy - 140), fill=main, width=line)
        draw.line((cx, cy + 20, cx - 110, cy - 45), fill=main, width=line)
        draw.line((cx, cy - 25, cx + 115, cy - 100), fill=main, width=line)
        draw.ellipse((cx - 235, cy - 140, cx - 80, cy - 5), outline=accent, width=line)
        draw.ellipse((cx + 75, cy - 205, cx + 230, cy - 65), outline=accent, width=line)
        draw.ellipse((cx - 14, cy - 194, cx + 14, cy - 165), fill=accent)
    elif kind == "camera":
        draw.rounded_rectangle((cx - 225, cy - 125, cx + 225, cy + 145), radius=35, outline=accent, width=line)
        draw.rounded_rectangle((cx - 145, cy - 165, cx - 20, cy - 125), radius=10, outline=main, width=9)
        draw.ellipse((cx - 92, cy - 84, cx + 92, cy + 100), outline=main, width=17)
        draw.ellipse((cx - 36, cy - 28, cx + 36, cy + 44), outline=accent, width=10)
        draw.ellipse((cx + 150, cy - 78, cx + 174, cy - 54), fill=main)
    elif kind == "microphone":
        draw.rounded_rectangle((cx - 74, cy - 202, cx + 74, cy + 42), radius=70, outline=accent, width=15)
        draw.arc((cx - 132, cy - 155, cx + 132, cy + 140), 0, 180, fill=main, width=15)
        draw.line((cx, cy + 135, cx, cy + 218), fill=accent, width=15)
        draw.line((cx - 100, cy + 218, cx + 100, cy + 218), fill=accent, width=15)
        for offset in (-65, -15, 35):
            draw.line((cx - 48, cy + offset, cx + 48, cy + offset), fill=main, width=8)
    elif kind == "pen":
        draw.polygon([(cx - 165, cy + 160), (cx - 112, cy + 188), (cx + 195, cy - 132), (cx + 143, cy - 186)], outline=accent)
        draw.line([(cx - 165, cy + 160), (cx - 112, cy + 188), (cx + 195, cy - 132), (cx + 143, cy - 186), (cx - 165, cy + 160)], fill=accent, width=line, joint="curve")
        draw.line((cx - 147, cy + 170, cx - 198, cy + 225), fill=main, width=line)
        draw.line((cx + 65, cy - 62, cx + 125, cy - 8), fill=main, width=9)
        draw.line((cx + 116, cy - 147, cx + 164, cy - 103), fill=main, width=9)
    elif kind == "newspaper":
        draw.rounded_rectangle((cx - 205, cy - 172, cx + 205, cy + 173), radius=16, outline=accent, width=line)
        draw.line((cx - 165, cy - 112, cx + 165, cy - 112), fill=main, width=18)
        draw.rectangle((cx - 165, cy - 70, cx - 25, cy + 50), outline=main, width=9)
        for yy in (-55, -18, 19, 65, 105):
            x1 = cx + 15 if yy <= 19 else cx - 165
            draw.line((x1, cy + yy, cx + 165, cy + yy), fill=accent, width=8)


def draw_story(draw, sections):
    """Asymmetric science feature: one large hero, two notes, one full-width task strip."""
    if len(sections) != 4:
        raise ValueError("长卷布局需要四段内容：主画面、科学、文化、观察任务")

    def text_panel(section, box, fill, max_lines, font_size=53):
        x1, y1, x2, y2 = box
        draw.rounded_rectangle((x1 + 12, y1 + 15, x2 + 12, y2 + 15), radius=36, fill="#184d5c")
        draw.rounded_rectangle(box, radius=35, fill=fill, outline="#b9e8ec", width=8)
        draw.rounded_rectangle((x1 + 20, y1 + 20, x2 - 20, y2 - 20), radius=23, outline="#ffdf90", width=3)
        draw.text((x1 + 66, y1 + 48), section["title"], font=font(75), fill="#ffe6a7")
        draw.line((x1 + 65, y1 + 156, x2 - 65, y1 + 156), fill="#a7e4e9", width=5)
        body_font = font(font_size)
        lines = wrapped(draw, section["body"], body_font, x2 - x1 - 130)
        if len(lines) > max_lines:
            raise ValueError(f"板块「{section['title']}」正文 {len(lines)} 行，最多 {max_lines} 行")
        for index, line in enumerate(lines):
            draw.text((x1 + 65, y1 + 195 + index * (font_size + 23)), line, font=body_font, fill="#f7fbf5")

    hero = (120, 390, 1810, 1780)
    note_top = (1875, 390, 3710, 1040)
    note_bottom = (1875, 1090, 3710, 1780)
    text_panel(sections[0], hero, "#2b6571", max_lines=5, font_size=56)
    text_panel(sections[1], note_top, "#2c6875", max_lines=5, font_size=53)
    text_panel(sections[2], note_bottom, "#306a70", max_lines=5, font_size=53)

    # Winter sun, hills and a tilted Earth: deliberately schematic, not to scale.
    hx, hy = 120, 390
    sun_x, sun_y, sun_r = hx + 470, hy + 1010, 155
    draw.ellipse((sun_x - sun_r - 32, sun_y - sun_r - 32, sun_x + sun_r + 32, sun_y + sun_r + 32), outline="#fff0b9", width=7)
    draw.ellipse((sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r), fill="#ffd47b", outline="#fff0b9", width=12)
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        r1, r2 = 215, 270
        draw.line((sun_x + math.cos(rad) * r1, sun_y + math.sin(rad) * r1,
                   sun_x + math.cos(rad) * r2, sun_y + math.sin(rad) * r2), fill="#ffe2a0", width=9)
    draw.polygon([(hx + 70, hy + 1310), (hx + 430, hy + 1090), (hx + 650, hy + 1240),
                  (hx + 950, hy + 1030), (hx + 1330, hy + 1310)], fill="#83c6d1")
    draw.polygon([(hx + 120, hy + 1330), (hx + 710, hy + 1170), (hx + 1050, hy + 1310),
                  (hx + 1570, hy + 1080), (hx + 1650, hy + 1330)], fill="#a7d9dc")
    draw.line((hx + 85, hy + 1310, hx + 1600, hy + 1310), fill="#eaf8ef", width=12)
    earth_x, earth_y, earth_r = hx + 1210, hy + 1015, 184
    draw.ellipse((earth_x - earth_r, earth_y - earth_r, earth_x + earth_r, earth_y + earth_r), fill="#358d9b", outline="#c2eced", width=12)
    draw.arc((earth_x - 110, earth_y - 132, earth_x + 120, earth_y + 145), 48, 280, fill="#c5e5cf", width=16)
    draw.arc((earth_x - 155, earth_y - 35, earth_x + 155, earth_y + 65), 2, 178, fill="#c5e5cf", width=10)
    draw.line((earth_x - 105, earth_y + 246, earth_x + 105, earth_y - 246), fill="#ffe4a2", width=12)
    draw.text((hx + 840, hy + 555), "昼短夜长 · 白昼渐长", font=font(53), fill="#ffdf90")

    # A compact sun-and-axis sketch under the science explanation.
    sx, sy = 1875 + 1250, 390 + 510
    draw.ellipse((sx - 62, sy - 62, sx + 62, sy + 62), fill="#ffd47b", outline="#fff0bd", width=7)
    for offset in (-1, 0, 1):
        draw.line((sx - 390, sy + offset * 52, sx - 135, sy + offset * 52), fill="#ffdf90", width=7)
    draw.ellipse((sx + 185, sy - 106, sx + 385, sy + 94), outline="#b7e9ea", width=10)
    draw.line((sx + 238, sy + 143, sx + 335, sy - 153), fill="#ffdf90", width=9)

    # Cultural illustration: a warm bowl with three rice balls and a dumpling.
    bx, by = 1875 + 1380, 1090 + 535
    draw.arc((bx - 230, by - 40, bx + 230, by + 170), 0, 180, fill="#ffe4a7", width=15)
    draw.arc((bx - 230, by + 30, bx + 230, by + 235), 0, 180, fill="#ffe4a7", width=15)
    for xx, yy in [(bx - 105, by - 40), (bx + 15, by - 75), (bx + 125, by - 30)]:
        draw.ellipse((xx - 45, yy - 45, xx + 45, yy + 45), fill="#fff1d2", outline="#ffc681", width=6)
    draw.arc((bx - 490, by - 85, bx - 250, by + 165), 185, 355, fill="#ffd99a", width=15)
    draw.line((bx - 470, by + 38, bx - 275, by + 38), fill="#ffd99a", width=10)

    # A single full-width observation strip closes the visual story.
    strip = (120, 1830, 3710, 2050)
    draw.rounded_rectangle(strip, radius=40, fill="#e7f2e7", outline="#ffd788", width=12)
    draw.text((195, 1870), sections[3]["title"], font=font(64), fill="#1b5c69")
    task_font = font(49)
    task_lines = wrapped(draw, sections[3]["body"], task_font, 3710 - 1040)
    if len(task_lines) > 2:
        raise ValueError("观察任务过长，请精简到两行")
    for index, line in enumerate(task_lines):
        draw.text((1050, 1855 + index * 74), line, font=task_font, fill="#235968")
    draw.ellipse((260, 1960, 310, 2010), fill="#ffd788")
    draw.line((335, 1985, 850, 1985), fill="#7dbbc5", width=10)


def render(data, source_dir, output):
    title = data.get("title")
    sections = data.get("sections")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("需要主标题 title")
    if not isinstance(sections, list) or not 2 <= len(sections) <= 6:
        raise ValueError("需要 2 至 6 个板块")
    for section in sections:
        if not isinstance(section, dict) or not section.get("title") or not section.get("body"):
            raise ValueError("每个板块都需要 title 和 body")

    palette = data.get("colors") or {}
    main = color(palette.get("main"), "#86d7ee")
    accent = color(palette.get("accent"), "#ffd878")
    ink = color(palette.get("text"), "#f4f1e8")
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#347e6b")
    base_draw = ImageDraw.Draw(canvas)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        shade = (round(57 - ratio * 17), round(133 - ratio * 29), round(113 - ratio * 19))
        base_draw.line((0, y, WIDTH, y), fill=shade)
    background_file = data.get("backgroundImage")
    if background_file:
        path = Path(background_file)
        background(canvas, path if path.is_absolute() else source_dir / path)
    draw = ImageDraw.Draw(canvas)

    # A bright framed classroom board with ample contrast for chalk lettering.
    draw.rounded_rectangle((24, 24, WIDTH - 24, HEIGHT - 24), radius=24, outline="#e8b56c", width=28)
    draw.rounded_rectangle((55, 55, WIDTH - 55, HEIGHT - 55), radius=20, outline="#a4dcc6", width=5)
    for x in range(80, WIDTH - 80, 113):
        for y in range(82, HEIGHT - 82, 97):
            draw.ellipse((x, y, x + 3, y + 3), fill=(105, 177, 145))
    if not background_file:
        draw.arc((120, 80, 650, 290), 185, 345, fill=accent, width=10)
        draw.arc((WIDTH - 650, 80, WIDTH - 120, 290), 195, 355, fill=accent, width=10)
        for x, y, size in [(220, 136, 45), (350, 227, 22), (WIDTH - 220, 136, 45), (WIDTH - 350, 227, 22)]:
            star(draw, x, y, size, accent)

    header_color = "#2d7890" if data.get("layout") == "story" else "#c84f4c"
    draw.rounded_rectangle((575, 61, WIDTH - 575, 337), radius=72, fill=header_color, outline=accent, width=12)
    draw.rounded_rectangle((604, 82, WIDTH - 604, 316), radius=58, outline="#f7e4b1", width=4)

    title_font = font(128)
    subtitle_font = font(54)
    fit_one_line(draw, title, title_font, WIDTH - 720, "主标题")
    draw.text((WIDTH // 2, 94), title, font=title_font, fill="#fff8e8", anchor="mt", stroke_width=1)
    subtitle = data.get("subtitle")
    if subtitle:
        fit_one_line(draw, subtitle, subtitle_font, WIDTH - 720, "副标题")
        draw.text((WIDTH // 2, 263), subtitle, font=subtitle_font, fill="#fff1c3", anchor="mt")

    if data.get("layout") == "story":
        draw_story(draw, sections)
        draw.text((WIDTH // 2, 2078), data.get("style") or "节气长卷", font=font(31), fill="#fff1c3", anchor="mt")
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, format="PNG", optimize=True)
        return

    count = len(sections)
    cols = 2 if count <= 4 else 3
    rows = (count + cols - 1) // cols
    margin_x, gap_x, gap_y = 135, 58, 54
    top, bottom = 390, 136
    panel_w = (WIDTH - 2 * margin_x - gap_x * (cols - 1)) // cols
    panel_h = (HEIGHT - top - bottom - gap_y * (rows - 1)) // rows
    heading_font = font(72 if cols == 2 else 62)
    body_font = font(54 if cols == 2 else 47)
    line_height = 78 if cols == 2 else 69

    for index, section in enumerate(sections):
        col, row = index % cols, index // cols
        x = margin_x + col * (panel_w + gap_x)
        y = top + row * (panel_h + gap_y)
        box = (x, y, x + panel_w, y + panel_h)
        draw.rounded_rectangle((x + 13, y + 15, x + panel_w + 13, y + panel_h + 15), radius=36, fill="#245a4e")
        draw.rounded_rectangle(box, radius=34, fill="#2d7060", outline="#f7dc9c", width=8)
        draw.rounded_rectangle((x + 18, y + 18, x + panel_w - 18, y + panel_h - 18), radius=22, outline=main, width=3)
        draw.rounded_rectangle((x + 38, y + 29, x + panel_w - 38, y + 136), radius=22, fill="#a93f40")
        star(draw, x + 87, y + 82, 27, accent)
        heading = str(section["title"])
        fit_one_line(draw, heading, heading_font, panel_w - 170, "板块标题")
        draw.text((x + 135, y + 40), heading, font=heading_font, fill="#fff6df")
        draw.line((x + 55, y + 155, x + panel_w - 55, y + 155), fill=accent, width=5)
        lines = wrapped(draw, section["body"], body_font, panel_w - 110)
        max_lines = (panel_h - 227) // line_height + 1
        if len(lines) > max_lines:
            raise ValueError(f"板块「{heading}」正文 {len(lines)} 行，当前最多 {max_lines} 行；请精简正文或减少板块数")
        for line_index, line in enumerate(lines):
            draw.text((x + 55, y + 187 + line_index * line_height), line, font=body_font, fill=ink)
        if section.get("illustration") and len(lines) <= 4 and panel_h >= 650:
            cx, cy = x + panel_w // 2, y + panel_h - 180
            draw.ellipse((cx - 168, cy - 168, cx + 168, cy + 168), fill="#39856f", outline="#b7e0bc", width=7)
            for sx, sy in [(cx - 220, cy - 72), (cx + 220, cy - 72), (cx - 215, cy + 100), (cx + 215, cy + 100)]:
                star(draw, sx, sy, 15, accent)
            icon = Image.new("RGBA", (560, 560), (0, 0, 0, 0))
            illustration(ImageDraw.Draw(icon), section["illustration"], 280, 280, "#ff9980", "#ffe29a")
            icon = icon.resize((336, 336), Image.Resampling.LANCZOS)
            canvas.paste(icon, (cx - 168, cy - 168), icon)

    footer = f"{data.get('style') or '手绘粉笔风'} · 黑板排版示意"
    draw.text((WIDTH // 2, HEIGHT - 101), footer, font=font(36), fill="#fff1c3", anchor="mt")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="layout.json")
    parser.add_argument("--output", required=True, type=Path, help="输出 PNG 路径")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".png":
        parser.error("--output 必须为 .png 文件")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    render(data, args.input.resolve().parent, args.output)
    print(args.output)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
