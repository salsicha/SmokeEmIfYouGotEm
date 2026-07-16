"""Extract South Fork full-reach NHD flowline candidates from a source zip."""

from __future__ import annotations

import hashlib
import json
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .south_fork_a1_full_reach_acquisition import FULL_REACH_REVIEW_ENVELOPE_WGS84


SOURCE_ZIP_URL = (
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU8/Shape/"
    "NHD_H_18020129_HU8_Shape.zip"
)
SOURCE_ZIP_SHA256 = "d75ca0bf998021d71b34c5b52f36a4ce9465a110cae9c3bb4350475a9eda0473"
SOURCE_ZIP_SIZE_BYTES = 19_558_205
FULL_REACH_NHD_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_nhd_named_flowline_extract.geojson"
)
FULL_REACH_NHD_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_nhd_named_flowline_extract_manifest.json"
)


@dataclass(frozen=True)
class DbfField:
    name: str
    field_type: str
    offset: int
    length: int
    decimal_count: int


@dataclass(frozen=True)
class ShapeRecord:
    record_number: int
    shape_type: int
    bbox: tuple[float, float, float, float]
    lines: list[list[list[float]]]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _decode_dbf_header(dbf_bytes: bytes) -> tuple[int, int, list[DbfField]]:
    record_count = struct.unpack("<I", dbf_bytes[4:8])[0]
    header_length = struct.unpack("<H", dbf_bytes[8:10])[0]
    record_length = struct.unpack("<H", dbf_bytes[10:12])[0]
    fields: list[DbfField] = []
    offset = 1
    position = 32
    while dbf_bytes[position] != 0x0D:
        descriptor = dbf_bytes[position : position + 32]
        raw_name = descriptor[:11].split(b"\0", 1)[0]
        name = raw_name.decode("ascii").strip()
        length = int(descriptor[16])
        fields.append(
            DbfField(
                name=name,
                field_type=chr(descriptor[11]),
                offset=offset,
                length=length,
                decimal_count=int(descriptor[17]),
            )
        )
        offset += length
        position += 32
    return record_count, record_length, fields


def _decode_dbf_value(raw: bytes, field: DbfField) -> Any:
    text = raw.decode("latin1", errors="replace").strip()
    if text == "":
        return None
    if field.field_type in {"C", "D"}:
        return text
    if field.field_type in {"N", "F"}:
        try:
            value = float(text)
        except ValueError:
            return text
        if field.decimal_count == 0 and value.is_integer():
            return int(value)
        return value
    if field.field_type == "L":
        return text.upper() in {"Y", "T"}
    return text


def _iter_dbf_records(dbf_bytes: bytes) -> list[dict[str, Any]]:
    record_count, record_length, fields = _decode_dbf_header(dbf_bytes)
    header_length = struct.unpack("<H", dbf_bytes[8:10])[0]
    records: list[dict[str, Any]] = []
    for index in range(record_count):
        start = header_length + index * record_length
        record = dbf_bytes[start : start + record_length]
        if not record or record[0:1] == b"*":
            records.append({"_deleted": True})
            continue
        values = {"_deleted": False}
        for field in fields:
            raw = record[field.offset : field.offset + field.length]
            values[field.name] = _decode_dbf_value(raw, field)
        records.append(values)
    return records


def _parse_polyline_record(record_number: int, content: bytes) -> ShapeRecord | None:
    shape_type = struct.unpack("<i", content[:4])[0]
    if shape_type == 0:
        return None
    if shape_type not in {3, 13, 23}:
        raise ValueError(f"Unsupported NHDFlowline shape type: {shape_type}")
    bbox = struct.unpack("<4d", content[4:36])
    part_count = struct.unpack("<i", content[36:40])[0]
    point_count = struct.unpack("<i", content[40:44])[0]
    parts_offset = 44
    points_offset = parts_offset + part_count * 4
    parts = list(struct.unpack(f"<{part_count}i", content[parts_offset:points_offset]))
    point_values = struct.unpack(
        f"<{point_count * 2}d",
        content[points_offset : points_offset + point_count * 16],
    )
    points = [
        [round(float(point_values[index]), 7), round(float(point_values[index + 1]), 7)]
        for index in range(0, len(point_values), 2)
    ]
    lines: list[list[list[float]]] = []
    for part_index, start in enumerate(parts):
        stop = parts[part_index + 1] if part_index + 1 < len(parts) else len(points)
        lines.append(points[start:stop])
    return ShapeRecord(
        record_number=record_number,
        shape_type=shape_type,
        bbox=tuple(float(value) for value in bbox),
        lines=lines,
    )


def _iter_shape_records(shp_bytes: bytes) -> list[ShapeRecord | None]:
    records: list[ShapeRecord | None] = []
    position = 100
    while position < len(shp_bytes):
        record_number, word_count = struct.unpack(">2i", shp_bytes[position : position + 8])
        position += 8
        byte_count = word_count * 2
        content = shp_bytes[position : position + byte_count]
        position += byte_count
        records.append(_parse_polyline_record(record_number, content))
    return records


def _bbox_intersects(
    bbox: tuple[float, float, float, float],
    bounds: dict[str, float],
) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return not (
        max_lon < bounds["min_lon"]
        or min_lon > bounds["max_lon"]
        or max_lat < bounds["min_lat"]
        or min_lat > bounds["max_lat"]
    )


def _feature_geometry(shape: ShapeRecord) -> dict[str, Any]:
    if len(shape.lines) == 1:
        return {"type": "LineString", "coordinates": shape.lines[0]}
    return {"type": "MultiLineString", "coordinates": shape.lines}


def _source_feature_properties(
    source_index: int,
    shape: ShapeRecord,
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_layer": "NHDFlowline",
        "source_record_index": source_index,
        "source_record_number": shape.record_number,
        "permanent_identifier": record.get("permanent_"),
        "gnis_id": record.get("gnis_id"),
        "gnis_name": record.get("gnis_name"),
        "reachcode": record.get("reachcode"),
        "lengthkm": record.get("lengthkm"),
        "fdate": record.get("fdate"),
        "resolution": record.get("resolution"),
        "flowdir": record.get("flowdir"),
        "ftype": record.get("ftype"),
        "fcode": record.get("fcode"),
        "mainpath": record.get("mainpath"),
        "innetwork": record.get("innetwork"),
        "visibility": record.get("visibility"),
        "bbox_wgs84": [round(value, 7) for value in shape.bbox],
        "geometry_status": "named_flowline_source_candidate_not_ordered_route",
    }


def build_full_reach_nhd_named_flowline_extract(
    *,
    source_zip: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build GeoJSON and manifest for the full-reach named-flowline candidate pool."""

    source_zip = source_zip.resolve()
    repo_root = repo_root.resolve()
    source_sha = _sha256(source_zip)
    if source_sha != SOURCE_ZIP_SHA256:
        raise ValueError(
            f"Unexpected NHD source zip hash {source_sha}; expected {SOURCE_ZIP_SHA256}"
        )

    with zipfile.ZipFile(source_zip) as archive:
        dbf_records = _iter_dbf_records(archive.read("Shape/NHDFlowline.dbf"))
        shape_records = _iter_shape_records(archive.read("Shape/NHDFlowline.shp"))

    if len(dbf_records) != len(shape_records):
        raise ValueError("NHDFlowline DBF and SHP record counts do not match")

    bounds = FULL_REACH_REVIEW_ENVELOPE_WGS84
    named_record_count = 0
    selected_length_km = 0.0
    features: list[dict[str, Any]] = []
    for index, (record, shape) in enumerate(zip(dbf_records, shape_records, strict=True)):
        if record.get("_deleted") or shape is None:
            continue
        if record.get("gnis_name") != "South Fork American River":
            continue
        named_record_count += 1
        if not _bbox_intersects(shape.bbox, bounds):
            continue
        selected_length_km += float(record.get("lengthkm") or 0.0)
        features.append(
            {
                "type": "Feature",
                "geometry": _feature_geometry(shape),
                "properties": _source_feature_properties(index, shape, record),
            }
        )

    selected_bounds = _combined_bbox(features)
    geojson = {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_full_reach_nhd_named_flowline_extract.geojson.v1",
        "name": "south_fork_american_full_reach_nhd_named_flowline_extract",
        "generated_on": "2026-07-16",
        "status": "review_gated_named_flowline_pool_not_ordered_route",
        "source": {
            "url": SOURCE_ZIP_URL,
            "sha256": source_sha,
            "source_archive_committed": False,
            "source_archive_size_bytes": source_zip.stat().st_size,
            "source_crs": "EPSG:4269 NAD83 geographic degrees",
            "layer": "NHDFlowline",
        },
        "selection": {
            "gnis_name": "South Fork American River",
            "review_envelope_wgs84": bounds,
            "named_record_count_in_hu8": named_record_count,
            "selected_record_count": len(features),
            "selected_length_km_source_sum": round(selected_length_km, 6),
            "selected_bounds_wgs84": selected_bounds,
        },
        "promotion_gate": (
            "This is a named-flowline candidate pool. Build a directed route graph, "
            "clip to reviewed Chili Bar/Folsom anchors, and pass Coloma station "
            "checkpoint review before replacing editor or solver geometry."
        ),
        "features": features,
    }
    manifest = {
        "schema": "raftsim.south_fork.a1_full_reach_nhd_named_flowline_extract.manifest.v1",
        "generated_on": "2026-07-16",
        "status": "official_nhd_hu8_named_flowlines_extracted_review_gated_not_route",
        "source_archive": {
            "url": SOURCE_ZIP_URL,
            "sha256": source_sha,
            "expected_sha256": SOURCE_ZIP_SHA256,
            "size_bytes": source_zip.stat().st_size,
            "expected_size_bytes": SOURCE_ZIP_SIZE_BYTES,
            "committed_to_repo": False,
        },
        "outputs": {
            "geojson": FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
        },
        "selection": geojson["selection"],
        "review_gates": [
            "Resolve directed route order through the 198 selected NHD records.",
            "Clip to reviewed Chili Bar put-in and Folsom Reservoir take-out anchors.",
            "Validate the Coloma station checkpoint before projecting Gorge rapids.",
            "Inspect reservoirs, side channels, braided fragments, and duplicate paths before promotion.",
            "Do not bind editor markers or solver windows to this candidate pool directly.",
        ],
    }
    return geojson, manifest


def _combined_bbox(features: list[dict[str, Any]]) -> dict[str, float] | None:
    if not features:
        return None
    boxes = [feature["properties"]["bbox_wgs84"] for feature in features]
    return {
        "min_lon": min(box[0] for box in boxes),
        "min_lat": min(box[1] for box in boxes),
        "max_lon": max(box[2] for box in boxes),
        "max_lat": max(box[3] for box in boxes),
    }


def write_full_reach_nhd_named_flowline_extract(
    *,
    source_zip: Path,
    repo_root: Path,
) -> tuple[Path, Path]:
    geojson, manifest = build_full_reach_nhd_named_flowline_extract(
        source_zip=source_zip,
        repo_root=repo_root,
    )
    geojson_path = repo_root / FULL_REACH_NHD_GEOJSON_RELATIVE_PATH
    manifest_path = repo_root / FULL_REACH_NHD_MANIFEST_RELATIVE_PATH
    geojson_path.parent.mkdir(parents=True, exist_ok=True)
    geojson_path.write_text(
        json.dumps(geojson, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return geojson_path, manifest_path
