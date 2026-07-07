"""Generate first-party procedural material review swatches for river environments."""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


RECIPE_PLAN_RELATIVE_PATH = Path("unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json")
SWATCH_ROOT_RELATIVE_PATH = Path("unreal/Content/RaftSim/Rendering/MaterialSwatches")
SWATCH_MANIFEST_RELATIVE_PATH = SWATCH_ROOT_RELATIVE_PATH / "first_party_material_swatch_manifest.json"

SWATCH_SIZE = (960, 720)
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


if __name__ == "__main__":
    generate_first_party_material_swatches(Path(__file__).resolve().parents[3])
