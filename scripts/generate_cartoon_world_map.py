#!/usr/bin/env python3
"""
Generate src/data/cartoonWorldMapData.ts from Wikimedia's public-domain
Simple_world_map.svg and curate exact cartoon world map coordinates for all
65 real-world BeamNG maps in src/data/modsCatalog.json.
"""

from __future__ import annotations

import json
import math
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "src" / "data" / "modsCatalog.json"
OUT_PATH = ROOT / "src" / "data" / "cartoonWorldMapData.ts"
SVG_URL = "https://upload.wikimedia.org/wikipedia/commons/4/41/Simple_world_map.svg"
VIEWBOX_W = 494.7
VIEWBOX_H = 265.7

# Regional affine calibration points measured directly on Simple_world_map.svg vertices
# (width=494.7, height=265.7) so points stay crisp and centered on their landmasses.
CALIBRATION_ANCHORS: list[tuple[float, float, float, float]] = [
    # (lon, lat, svg_x, svg_y)
    (-122.0, 41.4, 46.5, 76.5),     # Mount Shasta / N California
    (-118.4, 34.1, 48.2, 89.2),     # Los Angeles
    (-117.1, 32.5, 49.8, 92.2),     # San Diego / Estero Beach
    (-115.0, 36.2, 54.0, 86.0),     # Las Vegas / Nevada
    (-105.0, 38.8, 69.0, 81.5),     # Colorado Pikes Peak
    (-93.4, 37.9, 86.0, 83.0),      # Missouri
    (-83.5, 36.0, 100.5, 85.5),     # Appalachians
    (-80.2, 25.8, 102.5, 101.5),    # Miami Florida
    (-70.8, 44.5, 126.0, 69.0),     # Maine New England
    (-75.5, 5.1, 114.5, 136.5),     # Colombia
    (-67.8, -16.3, 126.5, 169.5),   # Bolivia
    (-64.0, -34.6, 129.0, 198.0),   # Argentina
    (-1.5, 52.5, 229.0, 56.5),      # UK
    (0.2, 48.0, 232.5, 65.5),       # France Le Mans
    (1.2, 41.1, 232.0, 77.0),       # Tarragona Spain
    (9.0, 49.0, 245.5, 64.5),       # Germany / Alps center
    (11.9, 55.2, 249.5, 54.5),      # Denmark / Sweden
    (9.1, 59.5, 247.0, 46.5),       # Norway
    (22.2, 49.5, 263.5, 65.0),      # Poland
    (25.4, 42.7, 266.0, 74.5),      # Bulgaria
    (30.1, 61.0, 273.5, 45.0),      # Priozersk
    (13.0, -19.8, 251.5, 166.5),    # Skeleton Coast Namibia
    (18.0, 14.5, 259.0, 118.0),     # Sahara Chad
    (66.5, 47.5, 326.0, 69.0),      # Kazakhstan
    (150.8, 59.6, 442.0, 46.5),     # Magadan Russia
    (139.7, 35.7, 440.5, 86.2),     # Tokyo Japan
    (135.5, 34.7, 434.2, 87.8),     # Osaka Japan
    (149.6, -33.4, 452.0, 200.0),   # Bathurst Sydney Australia
    (152.8, -27.4, 456.5, 190.0),   # Brisbane Australia
]


def extract_subpath_polygons(d: str) -> list[list[tuple[float, float]]]:
    """Parse an SVG path string into absolute coordinate closed polygon lists."""
    tokens = re.findall(r"[A-Za-z]|[-+]?\d*\.?\d+", d)
    cx = cy = sx = sy = 0.0
    cmd = ""
    current: list[tuple[float, float]] = []
    polygons: list[list[tuple[float, float]]] = []
    i = 0

    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            cmd = tok
            i += 1
            if cmd in ("Z", "z"):
                if current:
                    polygons.append(current)
                    current = []
                cx, cy = sx, sy
            continue

        if cmd in ("m", "M"):
            dx, dy = float(tokens[i]), float(tokens[i + 1])
            i += 2
            if cmd == "m":
                cx += dx
                cy += dy
                cmd = "l"
            else:
                cx, cy = dx, dy
                cmd = "L"
            sx, sy = cx, cy
            current.append((cx, cy))
        elif cmd in ("l", "L"):
            dx, dy = float(tokens[i]), float(tokens[i + 1])
            i += 2
            if cmd == "l":
                cx += dx
                cy += dy
            else:
                cx, cy = dx, dy
            current.append((cx, cy))
        elif cmd in ("h", "H"):
            dx = float(tokens[i])
            i += 1
            cx = cx + dx if cmd == "h" else dx
            current.append((cx, cy))
        elif cmd in ("v", "V"):
            dy = float(tokens[i])
            i += 1
            cy = cy + dy if cmd == "v" else dy
            current.append((cx, cy))
        else:
            i += 1

    if current:
        polygons.append(current)
    return polygons


def poly_to_svg_d(pts: list[tuple[float, float]]) -> str:
    """Serialize a polygon to compact absolute SVG path syntax."""
    if not pts:
        return ""
    coords = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for x, y in pts[1:]:
        coords.append(f"L{x:.1f} {y:.1f}")
    coords.append("Z")
    return "".join(coords)


def classify_p1_polygon(idx: int) -> str:
    """Classify each polygon of path13056 into a continent color group."""
    if idx == 2:
        return "lakes"
    if idx == 8:
        return "greenland"
    if idx in (13, 14, 15, 16):
        return "japan"
    if idx in (41, 42, 43):
        return "oceania"
    if idx in (3, 4, 5, 171, 172, 173, 174, 175) or (176 <= idx <= 192) or idx in (199, 206, 209, 210):
        return "northAmerica"
    if idx in (193, 194, 195, 196, 197, 198, 200, 201, 202, 203, 204, 205, 207, 208):
        return "southAmerica"
    if idx in (6, 7, 73, 99, 100, 101, 102) or (64 <= idx <= 71) or (75 <= idx <= 98) or (104 <= idx <= 110):
        return "europe"
    if idx in (0, 1) or (123 <= idx <= 170):
        return "africa"
    return "asia"


def lonlat_to_percent(lon: float, lat: float) -> tuple[float, float]:
    """
    Convert geographic (lon, lat) into canvas percentage (0..100, 0..100) using
    exact regional linear baseline + IDW residual blending against
    CALIBRATION_ANCHORS so every landmass matches Simple_world_map.svg closely.
    """
    # Nearest-anchor IDW residual around a simple equirectangular fit:
    base_x = 231.0 + lon * 1.485
    base_y = 143.5 - lat * 1.625

    num_rx = 0.0
    num_ry = 0.0
    den = 0.0
    for a_lon, a_lat, svg_x, svg_y in CALIBRATION_ANCHORS:
        d2 = (lon - a_lon) ** 2 + (lat - a_lat) ** 2
        if d2 < 1e-6:
            return (
                round((svg_x / VIEWBOX_W) * 100.0, 2),
                round((svg_y / VIEWBOX_H) * 100.0, 2),
            )
        w = 1.0 / (d2 + 8.0) ** 1.6
        a_base_x = 231.0 + a_lon * 1.485
        a_base_y = 143.5 - a_lat * 1.625
        num_rx += w * (svg_x - a_base_x)
        num_ry += w * (svg_y - a_base_y)
        den += w

    sx = base_x + num_rx / den
    sy = base_y + num_ry / den
    return (
        max(1.5, min(98.5, (sx / VIEWBOX_W) * 100.0)),
        max(2.0, min(97.0, (sy / VIEWBOX_H) * 100.0)),
    )


# Curated (lat, lon, regionLabel) per map id for all 65 real-world maps.
# Clustered regions (Japan, California, Appalachians, Germany, UK, Switzerland,
# France, Australia) are automatically fanned slightly around their cluster center.
REAL_MAP_COORDS: dict[str, tuple[float, float, str]] = {
    # Japan (15 maps)
    "2k-ashinoko-zip-53bf51": (35.20, 139.02, "Japón"),
    "2k-irohazaka-performance-build-v3-6-2024-by-t-e84e14": (36.73, 139.49, "Japón"),
    "2k-momiji-modland-zip-064af7": (36.85, 139.72, "Japón"),
    "2k-nagao-reworked-release-v39-2024-by-beamfix-f3a132": (35.26, 138.98, "Japón"),
    "2k-sadamine-zip-93044b": (36.04, 139.18, "Japón"),
    "2k-tsuchisaka-zip-2f198b": (36.14, 139.04, "Japón"),
    "2k-turnpike-ultimate-build-v2-6-2025-by-beamu-1d4c44": (35.19, 139.06, "Japón"),
    "2k-yabitsu-optimized-patch-v3-3-2025-by-beamu-2f07fd": (35.42, 139.22, "Japón"),
    "happogahara-zip-bf58dc": (36.87, 139.84, "Japón"),
    "kamurocho-judgment-am5-zip-cbce63": (35.69, 139.70, "Japón"),
    "nanamagari-zip-c580ac": (35.23, 139.08, "Japón"),
    "osaka-zip-7d36bb": (34.67, 135.50, "Japón"),
    "tokyo-zip-229530": (35.68, 139.77, "Japón"),
    "twinringbyjosh-modland-zip-ad3ace": (36.53, 140.22, "Japón"),
    "yokohama-zip-31f55f": (35.44, 139.63, "Japón"),
    "dousojintouge-zip-0b9e5e": (36.28, 140.16, "Japón"),
    "otarumi-touge-v1-zip-ab6702": (35.63, 139.24, "Japón"),

    # North America (14 maps)
    "caney-ridge-16k-zip-431678": (37.05, -82.40, "EE. UU."),
    "dealsgap-zip-ba0768": (35.47, -83.92, "EE. UU."),
    "the-gap-zip-3a1006": (36.60, -83.67, "EE. UU."),
    "tbd-newport-speedway-rally-zip-d74e15": (35.98, -83.17, "EE. UU."),
    "miami-city-real-world-remastered-tuning-versi-95ba49": (25.76, -80.19, "EE. UU."),
    "nevada-interstate-openbeta-zip-5e0d04": (39.50, -117.00, "EE. UU."),
    "dardslasvegasspeedway-offroad-zip-ceb592": (36.27, -115.01, "EE. UU."),
    "pikespeak-zip-06acce": (38.84, -105.04, "EE. UU."),
    "dardslucasoilspeedway-zip-177169": (37.94, -93.39, "EE. UU."),
    "nefr-0391-zip-95fc3f": (44.47, -70.79, "EE. UU."),
    "veincalif10-zip-d0f63c": (36.27, -121.81, "EE. UU."),
    "dardsglenhelenraceway-zip-3308c6": (34.20, -117.39, "EE. UU."),
    "dardslakeelsinoremotorsportspark-zip-886e68": (33.66, -117.31, "EE. UU."),
    "mulholland-v092b-hotfix-zip-0bdca5": (34.12, -118.41, "EE. UU."),
    "shasta-deploy-260713-zip-42c363": (41.41, -122.19, "EE. UU."),
    "dardsesterobeachshortcourse-zip-b9fcd2": (31.76, -116.61, "México"),

    # South America (3 maps)
    "beamng-11987-zip-652bd2": (5.07, -75.52, "Colombia"),
    "bolivianroadsbydino12507-zip-bc87b8": (-16.28, -67.80, "Bolivia"),
    "rutas2-zip-f49f4f": (-34.60, -64.00, "Argentina"),

    # Europe (18 maps)
    "60s-lemans1point1-zip-f2ce73": (47.95, 0.21, "Francia"),
    "lemans26-tunim-zip-74a32e": (48.00, 0.20, "Francia"),
    "monaco-tunim-zip-655d79": (43.73, 7.42, "Mónaco"),
    "xwtarragona-zip-9c6f17": (41.12, 1.24, "España"),
    "cadwell1point2-zip-21df6b": (53.31, -0.06, "Reino Unido"),
    "myherin-main-zip-1b00cb": (52.40, -3.77, "Reino Unido"),
    "somerset1-9-zip-f9848e": (51.10, -2.92, "Reino Unido"),
    "ks-nord-v20231124-v2-zip-2753f3": (50.34, 6.95, "Alemania"),
    "grille-autobahn-loop-zip-b13e59": (51.16, 10.45, "Alemania"),
    "schneeweg-grille-zip-2d7064": (50.59, 12.64, "Alemania"),
    "sgh1-5-zip-212021": (51.47, 11.30, "Alemania"),
    "three-passes-v093-small-modland-zip-439678": (46.57, 8.39, "Suiza"),
    "mbwr-alps-zip-eb8c31": (46.80, 8.23, "Suiza"),
    "passostelvio-zip-ac852a": (46.53, 10.45, "Italia"),
    "fakotor-trojica-modland-zip-e1eb93": (42.41, 18.77, "Montenegro"),
    "buzludzha-modfan-zip-1a8d35": (42.74, 25.39, "Bulgaria"),
    "sanok-repo-zip-eb1e8c": (49.55, 22.21, "Polonia"),
    "nissering-zip-695d81": (55.22, 11.90, "Dinamarca"),
    "sexdrega-sweden-map-modland-zip-9792b6": (57.58, 13.12, "Suecia"),
    "norwegian-backroads-152-reshjemheia-zip-9b2c15": (59.45, 9.06, "Noruega"),
    "priozersk-tg-koeno102rp-zip-f758a2": (61.04, 30.13, "Rusia"),

    # Africa (2 maps)
    "skeleton-coast-zip-351f86": (-19.80, 13.00, "Namibia"),
    "south-east-sahara-map-offroad-modland-zip-f351d7": (14.50, 18.00, "Chad"),

    # Asia & Eurasia (2 maps)
    "kasach-desert-zip-20fa27": (47.50, 66.50, "Kazajistán"),
    "magadan-modland-zip-83bfa0": (59.56, 150.80, "Rusia (Magadán)"),

    # Oceania (4 maps)
    "mount-glorious-zip-0f9c4a": (-27.33, 152.76, "Australia"),
    "mount-coottha-zip-c37462": (-27.48, 152.96, "Australia"),
    "mountpanorama12htunim-zip-ea3cac": (-33.44, 149.55, "Australia"),
    "rydal-039-fix-zip-40a057": (-33.47, 150.04, "Australia"),
}


def spread_clustered_pins(
    raw_points: dict[str, tuple[float, float, str]]
) -> dict[str, dict[str, object]]:
    """
    Separate pins that land closer than a threshold percentage so densely
    packed regions (Kanto Japan, Germany, Alps, California, Brisbane/Bathurst)
    are all independently visible & clickable on the world map.
    """
    items = [
        {"id": k, "x": xy[0], "y": xy[1], "region": region}
        for k, (xy, region) in raw_points.items()
    ]
    min_dist = 0.85
    for _ in range(36):
        moved = False
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                dx = items[j]["x"] - items[i]["x"]
                dy = (items[j]["y"] - items[i]["y"]) * 0.62
                dist = math.hypot(dx, dy)
                if dist < min_dist:
                    if dist < 1e-4:
                        angle = (i * 2.399963 + j * 1.1) % (2 * math.pi)
                        dx, dy = math.cos(angle), math.sin(angle)
                        dist = 1.0
                    push = (min_dist - dist) * 0.48
                    nx = (dx / dist) * push
                    ny = (dy / dist) * push / 0.62
                    items[i]["x"] = round(max(1.5, min(98.5, items[i]["x"] - nx)), 2)
                    items[i]["y"] = round(max(2.0, min(97.0, items[i]["y"] - ny)), 2)
                    items[j]["x"] = round(max(1.5, min(98.5, items[j]["x"] + nx)), 2)
                    items[j]["y"] = round(max(2.0, min(97.0, items[j]["y"] + ny)), 2)
                    moved = True
        if not moved:
            break

    return {
        row["id"]: {
            "x": round(float(row["x"]), 2),
            "y": round(float(row["y"]), 2),
            "region": row["region"],
        }
        for row in items
    }


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    real_maps = [m for m in catalog["maps"] if m.get("isRealWorld")]

    missing = [m["id"] for m in real_maps if m["id"] not in REAL_MAP_COORDS]
    if missing:
        raise RuntimeError(f"Missing real-world coordinates for IDs: {missing}")

    req = urllib.request.Request(
        SVG_URL, headers={"User-Agent": "BeamNGModsGallery/1.0"}
    )
    svg_text = urllib.request.urlopen(req, timeout=20).read().decode("utf-8")
    root = ET.fromstring(svg_text)

    p1_el = root.find('.//{http://www.w3.org/2000/svg}path[@id="path13056"]')
    p2_el = root.find('.//{http://www.w3.org/2000/svg}path[@id="path13058"]')
    if p1_el is None or p2_el is None:
        raise RuntimeError("Could not find world map SVG paths in Simple_world_map.svg")

    p1_polys = extract_subpath_polygons(p1_el.attrib["d"])
    p2_polys = extract_subpath_polygons(p2_el.attrib["d"])

    groups: dict[str, list[str]] = {
        "northAmerica": [],
        "greenland": [],
        "southAmerica": [],
        "europe": [],
        "africa": [],
        "asia": [],
        "japan": [],
        "oceania": [],
        "lakes": [],
    }

    for idx, poly in enumerate(p1_polys):
        if len(poly) < 3:
            continue
        group = classify_p1_polygon(idx)
        groups[group].append(poly_to_svg_d(poly))

    for poly in p2_polys:
        if len(poly) >= 3:
            groups["oceania"].append(poly_to_svg_d(poly))

    continent_specs = [
        {
            "id": "northAmerica",
            "label": "AMÉRICA DEL NORTE",
            "labelX": 88,
            "labelY": 81,
            "fill": "#FFBE0B",
            "highlight": "#FDE047",
            "paths": groups["northAmerica"],
        },
        {
            "id": "greenland",
            "label": "ÁRTICO",
            "labelX": 188,
            "labelY": 28,
            "fill": "#E0F2FE",
            "highlight": "#FFFFFF",
            "paths": groups["greenland"],
        },
        {
            "id": "southAmerica",
            "label": "AMÉRICA DEL SUR",
            "labelX": 139,
            "labelY": 168,
            "fill": "#4ADE80",
            "highlight": "#86EFAC",
            "paths": groups["southAmerica"],
        },
        {
            "id": "europe",
            "label": "EUROPA",
            "labelX": 250,
            "labelY": 61,
            "fill": "#A78BFA",
            "highlight": "#C4B5FD",
            "paths": groups["europe"],
        },
        {
            "id": "africa",
            "label": "ÁFRICA",
            "labelX": 258,
            "labelY": 124,
            "fill": "#FF9F1C",
            "highlight": "#FDBA74",
            "paths": groups["africa"],
        },
        {
            "id": "asia",
            "label": "ASIA",
            "labelX": 356,
            "labelY": 72,
            "fill": "#FB7185",
            "highlight": "#FDA4AF",
            "paths": groups["asia"],
        },
        {
            "id": "japan",
            "label": "JAPÓN",
            "labelX": 452,
            "labelY": 92,
            "fill": "#F43F5E",
            "highlight": "#FFE4E6",
            "paths": groups["japan"],
        },
        {
            "id": "oceania",
            "label": "OCEANÍA",
            "labelX": 432,
            "labelY": 195,
            "fill": "#2DD4BF",
            "highlight": "#5EEAD4",
            "paths": groups["oceania"],
        },
    ]

    raw_points = {
        map_id: (lonlat_to_percent(lon, lat), region)
        for map_id, (lat, lon, region) in REAL_MAP_COORDS.items()
    }
    spread_points = spread_clustered_pins(raw_points)

    all_land_path = "".join(
        d for spec in continent_specs for d in spec["paths"]
    )
    great_lakes_path = "".join(groups["lakes"])

    payload = {
        "viewBox": {"width": VIEWBOX_W, "height": VIEWBOX_H},
        "allLandPath": all_land_path,
        "greatLakesPath": great_lakes_path,
        "continents": continent_specs,
        "defaultRealMapPins": spread_points,
    }

    ts_content = (
        "// Auto-generated by scripts/generate_cartoon_world_map.py\n"
        "// Simplified world landmass polygons + curated coordinates for 65 real-world BeamNG maps.\n\n"
        "export interface CartoonContinent {\n"
        "  id: string;\n"
        "  label: string;\n"
        "  labelX: number;\n"
        "  labelY: number;\n"
        "  fill: string;\n"
        "  highlight: string;\n"
        "  paths: string[];\n"
        "}\n\n"
        "export interface DefaultWorldPin {\n"
        "  x: number;\n"
        "  y: number;\n"
        "  region: string;\n"
        "}\n\n"
        f"export const WORLD_MAP_VIEWBOX = {json.dumps(payload['viewBox'])};\n\n"
        f"export const WORLD_ALL_LAND_PATH = {json.dumps(payload['allLandPath'])};\n\n"
        f"export const WORLD_GREAT_LAKES_PATH = {json.dumps(payload['greatLakesPath'])};\n\n"
        f"export const CARTOON_CONTINENTS: CartoonContinent[] = {json.dumps(payload['continents'], ensure_ascii=False, indent=2)};\n\n"
        f"export const DEFAULT_REAL_MAP_PINS: Record<string, DefaultWorldPin> = {json.dumps(payload['defaultRealMapPins'], ensure_ascii=False, indent=2)};\n"
    )

    OUT_PATH.write_text(ts_content, encoding="utf-8")
    print(f"Generated {OUT_PATH} with {len(spread_points)} real map pins and {sum(len(c['paths']) for c in continent_specs)} polygons.")


if __name__ == "__main__":
    main()
