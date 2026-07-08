"""Generate first-party procedural material review swatches for river environments."""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont


RECIPE_PLAN_RELATIVE_PATH = Path("unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json")
SWATCH_ROOT_RELATIVE_PATH = Path("unreal/Content/RaftSim/Rendering/MaterialSwatches")
SWATCH_MANIFEST_RELATIVE_PATH = SWATCH_ROOT_RELATIVE_PATH / "first_party_material_swatch_manifest.json"
TEXTURE_ATLAS_ROOT_RELATIVE_PATH = Path("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases")
TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH = (
    TEXTURE_ATLAS_ROOT_RELATIVE_PATH / "first_party_material_texture_atlas_manifest.json"
)

SWATCH_SIZE = (960, 720)
ATLAS_TILE_SIZE = 512
ATLAS_COLUMNS = 3
BG = (16, 18, 19)
PANEL_BG = (30, 33, 33)
TEXT = (232, 235, 229)
MUTED = (154, 164, 158)

COLOR_TOKENS: dict[str, tuple[int, int, int]] = {
    "muted_granite": (121, 126, 119),
    "dry_grass_bank": (151, 132, 78),
    "green_riparian_shadow": (42, 82, 55),
    "wet_rock_edges": (46, 58, 56),
    "red_tan_strata": (162, 100, 66),
    "pale_sandbar": (198, 174, 126),
    "dark_wet_bank_line": (48, 48, 42),
    "talus_shadow": (80, 62, 55),
    "dark_basalt_wetness": (34, 39, 38),
    "moss_green_edges": (48, 91, 50),
    "rainforest_leaf_litter": (82, 63, 34),
    "cloud_safe_low_detail_fill": (66, 87, 73),
    "gray_granite": (124, 125, 117),
    "tea_green_wetness": (67, 91, 78),
    "light_sediment": (176, 162, 129),
    "red_sandstone": (151, 83, 58),
    "tan_dust": (190, 159, 111),
    "narrow_wet_release_line": (44, 50, 51),
    "near_black_wet_rock": (25, 30, 29),
    "moss": (54, 100, 46),
    "fresh_leaf_litter": (107, 76, 40),
    "oak_green": (73, 104, 49),
    "pine_deep_green": (36, 73, 48),
    "dry_summer_grass": (181, 153, 83),
    "desert_scrub_green": (91, 112, 74),
    "cottonwood_shadow": (71, 91, 58),
    "sand_dust": (184, 152, 106),
    "broadleaf_rainforest": (30, 105, 49),
    "deep_understory": (22, 55, 34),
    "wet_root_and_vine": (57, 42, 28),
    "clear_green": (42, 113, 103),
    "white_foam_lines": (228, 232, 218),
    "wet_rock_reflection": (80, 108, 103),
    "green_brown_turbidity": (83, 104, 78),
    "long_current_slicks": (179, 195, 180),
    "subtle_boils": (132, 158, 145),
    "deep_green_shadow": (20, 74, 69),
    "bright_foam": (237, 242, 229),
    "rain_wet_edges": (65, 96, 82),
    "small_foam_tongues": (225, 232, 218),
    "warm_summer_light": (223, 189, 124),
    "light_river_haze": (176, 189, 176),
    "long_wave_foam": (220, 224, 206),
    "warm_canyon_haze": (205, 157, 116),
    "sandbar_bounce_light": (218, 187, 129),
    "rainforest_spray": (183, 211, 196),
    "waterfall_mist": (226, 236, 226),
    "diffuse_canopy_light": (100, 139, 84),
    "dark_rubber": (28, 30, 31),
    "bright_paddle_blades": (220, 75, 42),
    "metal_oar_frame": (118, 122, 122),
    "wood_or_composite_oars": (126, 80, 43),
    "wet_dark_rubber": (18, 22, 23),
    "canopy_reflections": (37, 82, 57),
}


@dataclass(frozen=True)
class SwatchRecord:
    river_id: str
    target_read: str
    output_path: Path
    sha256: str
    width: int
    height: int
    recipe_ids: tuple[str, ...]


@dataclass(frozen=True)
class TextureAtlasRecord:
    river_id: str
    target_read: str
    output_paths: dict[str, Path]
    sha256: dict[str, str]
    width: int
    height: int
    tile_size: int
    recipe_ids: tuple[str, ...]


def _repo_path(repo_root: Path, relative_path: Path) -> Path:
    return repo_root / relative_path


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seed_for(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16], 16)


def _color_for_token(token: str) -> tuple[int, int, int]:
    if token in COLOR_TOKENS:
        return COLOR_TOKENS[token]
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return (48 + digest[0] % 128, 48 + digest[1] % 128, 48 + digest[2] % 128)


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] * (1.0 - t) + b[i] * t) for i in range(3))


def _shade(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    target = (255, 255, 255) if amount >= 0.0 else (0, 0, 0)
    return _blend(color, target, abs(amount))


def _clamp_byte(value: float) -> int:
    return int(max(0.0, min(255.0, value)))


def _palette_for(recipe: dict, river_id: str) -> list[tuple[int, int, int]]:
    binding = recipe["river_bindings"][river_id]
    palette = [_color_for_token(token) for token in binding["material_bias"]]
    return palette or [(100, 110, 105)]


def _draw_noise_rect(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    palette: list[tuple[int, int, int]],
    rng: random.Random,
    density: int,
) -> None:
    x0, y0, x1, y1 = rect
    for _ in range(density):
        radius = rng.randint(2, 11)
        x = rng.randint(x0 + radius, max(x0 + radius, x1 - radius))
        y = rng.randint(y0 + radius, max(y0 + radius, y1 - radius))
        base = rng.choice(palette)
        color = _shade(base, rng.uniform(-0.18, 0.22))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def _hash_unit(x: int, y: int, seed: int) -> float:
    value = (x * 374761393 + y * 668265263 + seed * 1442695040888963407) & 0xFFFFFFFF
    value = (value ^ (value >> 13)) * 1274126177
    value = value ^ (value >> 16)
    return (value & 0xFFFF) / 65535.0


def _apply_material_microtexture(image: Image.Image, recipe: dict, river_id: str) -> Image.Image:
    kind = _recipe_kind(recipe["recipe_id"])
    palette = _palette_for(recipe, river_id)
    seed = _seed_for("atlas-photo-microtexture", river_id, recipe["recipe_id"])
    amplitude_by_kind = {
        "terrain": 0.22,
        "rock": 0.20,
        "foliage": 0.24,
        "water": 0.16,
        "mist": 0.10,
        "raft": 0.14,
    }
    chroma_by_kind = {
        "terrain": 0.14,
        "rock": 0.12,
        "foliage": 0.18,
        "water": 0.10,
        "mist": 0.08,
        "raft": 0.10,
    }
    amplitude = amplitude_by_kind[kind]
    chroma = chroma_by_kind[kind]
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            n0 = _hash_unit(x, y, seed)
            n1 = _hash_unit(x // 3, y // 3, seed + 17)
            n2 = _hash_unit(x // 11, y // 11, seed + 31)
            ridge = math.sin((x + seed % 97) * 0.071 + (y - seed % 53) * 0.043)
            shade = (n0 - 0.5) * amplitude + (n1 - 0.5) * amplitude * 0.55 + ridge * amplitude * 0.18
            target = palette[int(n2 * len(palette)) % len(palette)]
            r, g, b = pixels[x, y]
            r = r * (1.0 - chroma) + target[0] * chroma
            g = g * (1.0 - chroma) + target[1] * chroma
            b = b * (1.0 - chroma) + target[2] * chroma
            pixels[x, y] = (
                _clamp_byte(r + shade * 255.0),
                _clamp_byte(g + (shade * 0.86 + (n1 - 0.5) * 0.045) * 255.0),
                _clamp_byte(b + (shade * 0.72 + (n2 - 0.5) * 0.035) * 255.0),
            )
    return image


def _draw_terrain(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], palette: list[tuple[int, int, int]], rng: random.Random) -> None:
    x0, y0, x1, y1 = rect
    height = y1 - y0
    for y in range(y0, y1):
        t = (y - y0) / max(1, height - 1)
        base = _blend(palette[0], palette[min(1, len(palette) - 1)], t)
        wave = math.sin(t * math.pi * 8.0 + rng.random() * 0.02) * 0.08
        draw.line((x0, y, x1, y), fill=_shade(base, wave))
    for band in range(8):
        y = y0 + int((band + 0.45 + rng.random() * 0.25) * height / 8)
        color = _shade(palette[band % len(palette)], 0.18 if band % 2 == 0 else -0.12)
        draw.line((x0, y, x1, y + rng.randint(1, 3)), fill=color, width=rng.randint(1, 3))
    _draw_noise_rect(draw, rect, palette, rng, 90)


def _draw_rock(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], palette: list[tuple[int, int, int]], rng: random.Random) -> None:
    x0, y0, x1, y1 = rect
    draw.rectangle(rect, fill=_shade(palette[0], -0.2))
    for index in range(22):
        rx = rng.randint(10, 42)
        ry = rng.randint(6, 24)
        cx = rng.randint(x0 + rx, max(x0 + rx, x1 - rx))
        cy = rng.randint(y0 + ry, max(y0 + ry, y1 - ry))
        base = palette[index % len(palette)]
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=_shade(base, rng.uniform(-0.16, 0.20)))
        draw.arc((cx - rx, cy - ry, cx + rx, cy + ry), 190, 345, fill=_shade(base, 0.35), width=2)
    draw.rectangle((x0, y1 - 18, x1, y1), fill=_shade(palette[-1], -0.25))


def _draw_foliage(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], palette: list[tuple[int, int, int]], rng: random.Random) -> None:
    x0, y0, x1, y1 = rect
    draw.rectangle(rect, fill=_shade(palette[0], -0.33))
    for _ in range(90):
        length = rng.randint(12, 34)
        cx = rng.randint(x0 + length, max(x0 + length, x1 - length))
        cy = rng.randint(y0 + length // 3, max(y0 + length // 3, y1 - length // 3))
        color = _shade(rng.choice(palette), rng.uniform(-0.08, 0.18))
        draw.ellipse((cx - length, cy - length // 3, cx + length, cy + length // 3), fill=color)
        if rng.random() < 0.3:
            draw.line((cx, cy, cx + rng.randint(-8, 8), min(y1, cy + rng.randint(12, 36))), fill=_shade(color, -0.45), width=2)


def _draw_water(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], palette: list[tuple[int, int, int]], rng: random.Random) -> None:
    x0, y0, x1, y1 = rect
    height = y1 - y0
    for y in range(y0, y1):
        t = (y - y0) / max(1, height - 1)
        color = _blend(palette[0], palette[min(1, len(palette) - 1)], t)
        draw.line((x0, y, x1, y), fill=_shade(color, math.sin(t * math.pi * 3.0) * 0.08))
    foam = palette[-1]
    for _ in range(30):
        length = rng.randint(80, 260)
        y = rng.randint(y0 + 18, y1 - 18)
        x = rng.randint(x0, max(x0, x1 - length))
        draw.arc((x, y - 16, x + length, y + 18), 8, 170, fill=_shade(foam, rng.uniform(-0.05, 0.1)), width=rng.randint(1, 3))


def _draw_mist(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], palette: list[tuple[int, int, int]], rng: random.Random) -> None:
    x0, y0, x1, y1 = rect
    draw.rectangle(rect, fill=_shade(palette[0], -0.18))
    for _ in range(42):
        rx = rng.randint(20, 90)
        ry = rng.randint(8, 24)
        cx = rng.randint(x0 + rx, max(x0 + rx, x1 - rx))
        cy = rng.randint(y0 + ry, max(y0 + ry, y1 - ry))
        color = _shade(rng.choice(palette), rng.uniform(0.05, 0.28))
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=color)
    for _ in range(44):
        x = rng.randint(x0, x1)
        y = rng.randint(y0, y1)
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=_shade(palette[-1], 0.22))


def _draw_raft(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], palette: list[tuple[int, int, int]], rng: random.Random) -> None:
    x0, y0, x1, y1 = rect
    draw.rectangle(rect, fill=(34, 38, 39))
    rubber = palette[0]
    accent = palette[min(1, len(palette) - 1)]
    tube = (x0 + 48, y0 + 35, x1 - 48, y1 - 20)
    draw.rounded_rectangle(tube, radius=32, fill=_shade(rubber, 0.05), outline=_shade(rubber, 0.28), width=5)
    draw.rounded_rectangle((x0 + 110, y0 + 58, x1 - 110, y1 - 43), radius=22, fill=_shade(rubber, -0.18))
    for offset in (-42, 42):
        y = (y0 + y1) // 2 + offset
        draw.line((x0 + 70, y, x1 - 70, y + rng.randint(-5, 5)), fill=accent, width=5)
        draw.ellipse((x1 - 84, y - 14, x1 - 30, y + 16), fill=_shade(accent, 0.16))


def _recipe_kind(recipe_id: str) -> str:
    if "terrain" in recipe_id:
        return "terrain"
    if "boulder" in recipe_id:
        return "rock"
    if "foliage" in recipe_id:
        return "foliage"
    if "water_surface" in recipe_id:
        return "water"
    if "foam_spray" in recipe_id:
        return "mist"
    return "raft"


def _draw_albedo_tile(recipe: dict, river_id: str, tile_size: int) -> Image.Image:
    rng = random.Random(_seed_for("atlas-albedo", river_id, recipe["recipe_id"]))
    palette = _palette_for(recipe, river_id)
    image = Image.new("RGB", (tile_size, tile_size), _shade(palette[0], -0.08))
    draw = ImageDraw.Draw(image)
    rect = (0, 0, tile_size, tile_size)
    kind = _recipe_kind(recipe["recipe_id"])
    if kind == "terrain":
        _draw_terrain(draw, rect, palette, rng)
        for _ in range(34):
            y = rng.randint(0, tile_size - 1)
            x_offset = rng.randint(-40, 40)
            color = _shade(rng.choice(palette), rng.uniform(-0.18, 0.18))
            draw.line((x_offset, y, tile_size + x_offset, y + rng.randint(-28, 28)), fill=color, width=rng.randint(1, 4))
    elif kind == "rock":
        _draw_rock(draw, rect, palette, rng)
        for _ in range(70):
            x = rng.randint(0, tile_size)
            y = rng.randint(0, tile_size)
            length = rng.randint(24, 110)
            color = _shade(rng.choice(palette), rng.uniform(-0.28, 0.24))
            draw.line((x, y, x + rng.randint(-length, length), y + rng.randint(-length // 2, length // 2)), fill=color, width=1)
    elif kind == "foliage":
        _draw_foliage(draw, rect, palette, rng)
        for _ in range(180):
            x = rng.randint(0, tile_size)
            y = rng.randint(0, tile_size)
            color = _shade(rng.choice(palette), rng.uniform(-0.20, 0.18))
            draw.line((x, y, x + rng.randint(-16, 16), y + rng.randint(10, 34)), fill=color, width=1)
    elif kind == "water":
        _draw_water(draw, rect, palette, rng)
        for _ in range(52):
            y = rng.randint(0, tile_size - 1)
            length = rng.randint(tile_size // 3, tile_size)
            x = rng.randint(-tile_size // 5, tile_size // 2)
            color = _shade(rng.choice(palette), rng.uniform(-0.14, 0.22))
            draw.arc((x, y - 18, x + length, y + 22), 4, 176, fill=color, width=rng.randint(1, 3))
    elif kind == "mist":
        _draw_mist(draw, rect, palette, rng)
    else:
        _draw_raft(draw, rect, palette, rng)
        for _ in range(18):
            y = rng.randint(40, tile_size - 40)
            draw.line((0, y, tile_size, y + rng.randint(-8, 8)), fill=_shade(palette[0], rng.uniform(-0.16, 0.16)), width=2)
    return _apply_material_microtexture(image.filter(ImageFilter.GaussianBlur(radius=0.22)), recipe, river_id)


def _height_tile(recipe: dict, river_id: str, tile_size: int) -> Image.Image:
    rng = random.Random(_seed_for("atlas-height", river_id, recipe["recipe_id"]))
    kind = _recipe_kind(recipe["recipe_id"])
    image = Image.new("L", (tile_size, tile_size), 128)
    draw = ImageDraw.Draw(image)
    if kind == "terrain":
        for y in range(tile_size):
            base = 110 + math.sin(y / 23.0) * 20 + math.sin(y / 7.0) * 6
            draw.line((0, y, tile_size, y), fill=_clamp_byte(base))
        for _ in range(44):
            y = rng.randint(0, tile_size - 1)
            draw.line((rng.randint(-80, 80), y, tile_size + rng.randint(-80, 80), y + rng.randint(-26, 26)), fill=rng.randint(116, 184), width=rng.randint(1, 6))
    elif kind == "rock":
        image.paste(96, (0, 0, tile_size, tile_size))
        for _ in range(56):
            rx = rng.randint(24, 92)
            ry = rng.randint(12, 62)
            cx = rng.randint(-rx, tile_size + rx)
            cy = rng.randint(-ry, tile_size + ry)
            shade = rng.randint(112, 208)
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=shade)
            draw.arc((cx - rx, cy - ry, cx + rx, cy + ry), 190, 342, fill=min(255, shade + 30), width=2)
    elif kind == "foliage":
        image.paste(74, (0, 0, tile_size, tile_size))
        for _ in range(220):
            rx = rng.randint(8, 28)
            ry = rng.randint(3, 12)
            cx = rng.randint(0, tile_size)
            cy = rng.randint(0, tile_size)
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rng.randint(124, 220))
    elif kind == "water":
        for y in range(tile_size):
            base = 126 + math.sin(y / 18.0) * 12 + math.sin(y / 5.5) * 3
            draw.line((0, y, tile_size, y), fill=_clamp_byte(base))
        for _ in range(38):
            y = rng.randint(0, tile_size)
            draw.arc((rng.randint(-120, 120), y - 18, tile_size + rng.randint(-80, 120), y + 18), 3, 177, fill=rng.randint(134, 176), width=rng.randint(1, 3))
    elif kind == "mist":
        image.paste(118, (0, 0, tile_size, tile_size))
        for _ in range(80):
            rx = rng.randint(20, 110)
            ry = rng.randint(8, 34)
            cx = rng.randint(-rx, tile_size + rx)
            cy = rng.randint(-ry, tile_size + ry)
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rng.randint(130, 190))
    else:
        image.paste(104, (0, 0, tile_size, tile_size))
        for y in range(24, tile_size, 56):
            draw.line((0, y + rng.randint(-4, 4), tile_size, y + rng.randint(-4, 4)), fill=rng.randint(130, 180), width=5)
        for _ in range(38):
            x = rng.randint(0, tile_size)
            draw.line((x, 0, x + rng.randint(-30, 30), tile_size), fill=rng.randint(80, 150), width=1)
    return image.filter(ImageFilter.GaussianBlur(radius=1.2))


def _normal_map_from_height(height: Image.Image, strength: float = 7.0) -> Image.Image:
    width, height_px = height.size
    source = height.load()
    normal = Image.new("RGB", height.size, (128, 128, 255))
    target = normal.load()
    for y in range(height_px):
        y0 = max(0, y - 1)
        y1 = min(height_px - 1, y + 1)
        for x in range(width):
            x0 = max(0, x - 1)
            x1 = min(width - 1, x + 1)
            dx = (float(source[x1, y]) - float(source[x0, y])) / 255.0
            dy = (float(source[x, y1]) - float(source[x, y0])) / 255.0
            nx = -dx * strength
            ny = -dy * strength
            nz = 1.0
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            target[x, y] = (
                _clamp_byte((nx / length) * 127.5 + 127.5),
                _clamp_byte((ny / length) * 127.5 + 127.5),
                _clamp_byte((nz / length) * 127.5 + 127.5),
            )
    return normal


def _packed_ao_roughness_height_tile(recipe: dict, river_id: str, height: Image.Image) -> Image.Image:
    kind = _recipe_kind(recipe["recipe_id"])
    roughness_by_kind = {
        "terrain": 214,
        "rock": 188,
        "foliage": 226,
        "water": 74,
        "mist": 242,
        "raft": 172,
    }
    rng = random.Random(_seed_for("atlas-orm", river_id, recipe["recipe_id"]))
    width, height_px = height.size
    source = height.load()
    packed = Image.new("RGB", height.size, (220, roughness_by_kind[kind], 128))
    target = packed.load()
    for y in range(height_px):
        for x in range(width):
            h = int(source[x, y])
            local_noise = rng.randint(-5, 5)
            ao = _clamp_byte(172 + h * 0.34 + local_noise)
            roughness = _clamp_byte(roughness_by_kind[kind] + (128 - h) * (0.10 if kind != "water" else 0.04))
            target[x, y] = (ao, roughness, h)
    return packed


def _atlas_tile_layout(recipes: list[dict], tile_size: int) -> list[dict]:
    layout = []
    for index, recipe in enumerate(recipes):
        column = index % ATLAS_COLUMNS
        row = index // ATLAS_COLUMNS
        layout.append(
            {
                "recipe_id": recipe["recipe_id"],
                "x": column * tile_size,
                "y": row * tile_size,
                "width": tile_size,
                "height": tile_size,
            }
        )
    return layout


def _draw_texture_atlases(material_plan: dict, river_profile: dict, output_root: Path) -> TextureAtlasRecord:
    river_id = river_profile["river_id"]
    recipes = material_plan["material_recipes"]
    rows = math.ceil(len(recipes) / ATLAS_COLUMNS)
    atlas_size = (ATLAS_COLUMNS * ATLAS_TILE_SIZE, rows * ATLAS_TILE_SIZE)
    atlases = {
        "albedo": Image.new("RGB", atlas_size, (0, 0, 0)),
        "normal": Image.new("RGB", atlas_size, (128, 128, 255)),
        "ao_roughness_height": Image.new("RGB", atlas_size, (220, 190, 128)),
    }
    for index, recipe in enumerate(recipes):
        column = index % ATLAS_COLUMNS
        row = index // ATLAS_COLUMNS
        offset = (column * ATLAS_TILE_SIZE, row * ATLAS_TILE_SIZE)
        height = _height_tile(recipe, river_id, ATLAS_TILE_SIZE)
        atlases["albedo"].paste(_draw_albedo_tile(recipe, river_id, ATLAS_TILE_SIZE), offset)
        atlases["normal"].paste(_normal_map_from_height(height), offset)
        atlases["ao_roughness_height"].paste(_packed_ao_roughness_height_tile(recipe, river_id, height), offset)

    output_root.mkdir(parents=True, exist_ok=True)
    output_paths = {
        kind: output_root / f"{river_id}_first_party_material_texture_atlas_{kind}.png"
        for kind in atlases
    }
    for kind, image in atlases.items():
        image.save(output_paths[kind])

    return TextureAtlasRecord(
        river_id=river_id,
        target_read=river_profile["target_read"],
        output_paths=output_paths,
        sha256={kind: _hash_file(path) for kind, path in output_paths.items()},
        width=atlas_size[0],
        height=atlas_size[1],
        tile_size=ATLAS_TILE_SIZE,
        recipe_ids=tuple(recipe["recipe_id"] for recipe in recipes),
    )


def _draw_recipe_panel(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    recipe: dict,
    river_id: str,
    font: ImageFont.ImageFont,
) -> None:
    x0, y0, x1, y1 = rect
    rng = random.Random(_seed_for(river_id, recipe["recipe_id"]))
    palette = _palette_for(recipe, river_id)
    draw.rounded_rectangle(rect, radius=8, fill=PANEL_BG)
    sample_rect = (x0 + 14, y0 + 26, x1 - 14, y1 - 18)
    if "terrain" in recipe["recipe_id"]:
        _draw_terrain(draw, sample_rect, palette, rng)
    elif "boulder" in recipe["recipe_id"]:
        _draw_rock(draw, sample_rect, palette, rng)
    elif "foliage" in recipe["recipe_id"]:
        _draw_foliage(draw, sample_rect, palette, rng)
    elif "water_surface" in recipe["recipe_id"]:
        _draw_water(draw, sample_rect, palette, rng)
    elif "foam_spray" in recipe["recipe_id"]:
        _draw_mist(draw, sample_rect, palette, rng)
    else:
        _draw_raft(draw, sample_rect, palette, rng)
    draw.rectangle((x0 + 14, y0 + 14, x1 - 14, y0 + 38), fill=(18, 20, 20))
    draw.text((x0 + 22, y0 + 18), recipe["recipe_id"], fill=TEXT, font=font)


def _draw_swatch(material_plan: dict, river_profile: dict, output_path: Path) -> SwatchRecord:
    river_id = river_profile["river_id"]
    image = Image.new("RGB", SWATCH_SIZE, BG)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.text((28, 22), f"{river_id} first-party material swatch", fill=TEXT, font=font)
    target_read = river_profile["target_read"]
    if len(target_read) > 118:
        target_read = target_read[:115].rstrip() + "..."
    draw.text((28, 42), target_read, fill=MUTED, font=font)
    draw.text((28, 58), "review-only procedural texture target; not photoreal approval evidence", fill=(202, 176, 111), font=font)

    recipes = material_plan["material_recipes"]
    margin_x = 24
    top = 88
    gap = 14
    panel_height = (SWATCH_SIZE[1] - top - 26 - gap * 2) // 3
    panel_width = (SWATCH_SIZE[0] - margin_x * 2 - gap) // 2
    for index, recipe in enumerate(recipes):
        col = index % 2
        row = index // 2
        x0 = margin_x + col * (panel_width + gap)
        y0 = top + row * (panel_height + gap)
        _draw_recipe_panel(draw, (x0, y0, x0 + panel_width, y0 + panel_height), recipe, river_id, font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return SwatchRecord(
        river_id=river_id,
        target_read=river_profile["target_read"],
        output_path=output_path,
        sha256=_hash_file(output_path),
        width=SWATCH_SIZE[0],
        height=SWATCH_SIZE[1],
        recipe_ids=tuple(recipe["recipe_id"] for recipe in recipes),
    )


def _records_to_manifest(repo_root: Path, records: Iterable[SwatchRecord], material_plan: dict) -> dict:
    swatches = []
    for record in records:
        swatches.append(
            {
                "river_id": record.river_id,
                "target_read": record.target_read,
                "path": str(record.output_path.relative_to(repo_root)),
                "sha256": record.sha256,
                "width": record.width,
                "height": record.height,
                "recipe_ids": list(record.recipe_ids),
                "status": "review_only_first_party_procedural_material_swatch_not_lifelike_capture",
            }
        )
    return {
        "schema": "raftsim.unreal.first_party_material_swatch_manifest.v1",
        "generated_on": "2026-07-06",
        "status": "review_only_first_party_procedural_material_swatches_generated_not_lifelike_capture",
        "material_recipe_plan": str(RECIPE_PLAN_RELATIVE_PATH),
        "policy": material_plan["policy"],
        "swatches": swatches,
        "current_decision": "Use these deterministic PNG contact sheets for material direction review and Unreal import experiments only. They are first-party procedural artifacts, not production texture sets and not lifelike in-engine screenshot evidence.",
    }


def _texture_records_to_manifest(repo_root: Path, records: Iterable[TextureAtlasRecord], material_plan: dict) -> dict:
    records = list(records)
    atlases = []
    for record in records:
        atlases.append(
            {
                "river_id": record.river_id,
                "target_read": record.target_read,
                "status": "importable_first_party_procedural_texture_atlas_review_only_not_lifelike_capture",
                "maps": {
                    kind: {
                        "path": str(path.relative_to(repo_root)),
                        "sha256": record.sha256[kind],
                    }
                    for kind, path in record.output_paths.items()
                },
                "width": record.width,
                "height": record.height,
                "tile_size": record.tile_size,
                "recipe_ids": list(record.recipe_ids),
            }
        )
    return {
        "schema": "raftsim.unreal.first_party_material_texture_atlas_manifest.v1",
        "generated_on": "2026-07-07",
        "status": "importable_first_party_procedural_texture_atlases_generated_review_only_not_lifelike_capture",
        "material_recipe_plan": str(RECIPE_PLAN_RELATIVE_PATH),
        "material_swatch_manifest": str(SWATCH_MANIFEST_RELATIVE_PATH),
        "policy": material_plan["policy"]
        | {
            "third_party_photo_texture_inputs_used": False,
            "social_media_or_footage_texture_inputs_used": False,
            "atlas_outputs_are_first_party_procedural": True,
            "atlas_import_does_not_mark_any_river_lifelike": True,
        },
        "map_semantics": {
            "albedo": "Base color atlas with one deterministic tile per material recipe.",
            "normal": "Tangent-space normal approximation derived from first-party procedural height tiles.",
            "ao_roughness_height": "Packed RGB map: R=ambient occlusion, G=roughness, B=height/displacement candidate.",
        },
        "recipe_tile_layout": _atlas_tile_layout(material_plan["material_recipes"], ATLAS_TILE_SIZE),
        "atlases": atlases,
        "promotion_gate": "These atlases may be imported into Unreal material instances as first-party texture candidates, but lifelike approval still requires in-engine material application, guide/geospatial review, hazard readability review, screenshots, and desktop/VR performance evidence.",
        "current_decision": "Use these deterministic PNG atlases as the first importable first-party material texture pack for terrain, rock, foliage, water, mist, and raft material iteration. They are not source imagery, not social-media-derived, and not lifelike screenshot evidence.",
    }


def generate_first_party_material_swatches(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    material_plan = json.loads(_repo_path(repo_root, RECIPE_PLAN_RELATIVE_PATH).read_text(encoding="utf-8"))
    output_root = _repo_path(repo_root, SWATCH_ROOT_RELATIVE_PATH)
    records = []
    for river_profile in material_plan["river_profiles"]:
        output_path = output_root / f"{river_profile['river_id']}_first_party_material_swatch.png"
        records.append(_draw_swatch(material_plan, river_profile, output_path))

    manifest = _records_to_manifest(repo_root, records, material_plan)
    manifest_path = _repo_path(repo_root, SWATCH_MANIFEST_RELATIVE_PATH)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def generate_first_party_material_texture_atlases(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    material_plan = json.loads(_repo_path(repo_root, RECIPE_PLAN_RELATIVE_PATH).read_text(encoding="utf-8"))
    output_root = _repo_path(repo_root, TEXTURE_ATLAS_ROOT_RELATIVE_PATH)
    records = []
    for river_profile in material_plan["river_profiles"]:
        records.append(_draw_texture_atlases(material_plan, river_profile, output_root))

    manifest = _texture_records_to_manifest(repo_root, records, material_plan)
    manifest_path = _repo_path(repo_root, TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    generate_first_party_material_swatches(root)
    generate_first_party_material_texture_atlases(root)
