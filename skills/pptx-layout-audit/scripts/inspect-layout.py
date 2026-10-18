#!/usr/bin/env python3
"""Read-only, deterministic PPTX inventory and explicit layout contracts (stdlib).

CLI: inspect-layout.py deck.pptx [--contracts contracts.json] [--output layout.json]
Output defaults to stdout; --output - also means stdout. Exit codes: 0 = inventory
completed / all requested rules passed, 1 = native structure or contract defect,
2 = invalid input or I/O error, 3 = requested rules remain unverified without a
proven violation.
An empty/absent rule list never produces a contract PASS.

JSON schema_version 1: artifact + SHA-256, slide_count, slide_size_pt, slides in
presentation relationship order, recursive shapes in XML drawing order,
limitations, structure {status, counts, defects}, and contracts {status, counts,
rules}. File inspection records source_integrity with hashes before and after
inspection; artifact_sha256 always identifies the exact inspected byte snapshot.
Structure always checks slide-wide p:cNvPr ID uniqueness and at most one
direct a:pPr per a:p, including table cells and nested groups. Identical repeated
pPr elements still violate the grammar. These are two focused checks, not full
OOXML schema validation. Overall status is fail/unverified/pass/inspected; a
successful inventory without contracts is inspected, never a layout PASS.
Every rule contains measured
checks with pass/fail/unverified status. Failure takes precedence over unverified.
Native IDs, not shape enumeration, select top-level objects. Coordinates, insets,
font sizes and contract distances are points (12700 EMU/pt); raw XML properties
retain their named native units. No timestamps or environment-dependent rendering.

Contract semantics:
* alignment compares outer bbox left/right/top/bottom/center_x/center_y;
  gap measures second.start - first.end on x/y, including negative overlaps.
* text_alignment checks every paragraph's explicit pPr/@algn and the explicit
  bodyPr/@anchor (tcPr/@anchor in table cells). Missing/inherited values are
  unverified, even if a specification default would match the request.
* containment padding is minimum clearance from the parent's outer rectangle,
  in top/right/bottom/left order. Intersect this padded box with the native content
  box: use max(padding, explicit inset), NEVER add the same clearance twice.
  Omitted body insets are null; schema defaults are informational, not evidence.
* directed_edge ports are midpoints of named bbox sides. The first segment must
  depart outward and the final segment must arrive inward through those sides.
  Euclidean endpoint/join gaps use maximum_endpoint_gap_pt plus tolerance_pt.
  Line headEnd decorates the native start; tailEnd decorates the native end.
  Flips change native endpoints. A head arrow reverses traversal. Ordered
  connectors are source-to-target; only the last may have an arrow. Unmarked
  intermediate segments can be traversed either way; ambiguous joins are
  unverified. Native stCxn/endCxn IDs are checked when present; connection-site
  indices are recorded, not interpreted as port numbers or drag-editability.

Only straight native line/straightConnector1 geometry is routed. Axis-aligned
group scale/translation/reflection is normalized for inventory; nested IDs are
not contract targets, and group scale is NEVER automatically applied to physical
text insets. Nested text content rectangles remain unverified. Rotations,
unknown transforms, custom/bent/curved routes,
inherited defaults and compatibility alternatives remain visible limitations.
Custom-path objects are inventory-only contract targets. The textNoShape preset
is an explicit no-warp case; other text warps are not resolved. Tables preserve
their frame, raw grid dimensions and separate grid-slot rectangles; differing
frame/grid extents are never rescaled into agreement. Each axis permits only
integer-EMU discrepancies consistent with independently rounding N component
dimensions and their frame to nearest EMU: floor((N + 1) / 2) EMU. Each rounding
contributes at most 0.5 EMU; the observed discrepancy is integral. The output's
frame_grid_rounding records this assumption, counts, allowance and signed
residual. This bounds possible rounding error, not proof of authoring intent.
Merged cells and nested
table transforms remain unverified. Negative content widths/heights are retained
and marked invalid, never normalized into positive rectangles. Empty text and
table overflow/autofit can affect their visual significance; inspect the render.
Stored bounding rectangles exclude strokes/effects. This does not measure glyph
fit, optical alignment, aesthetics, application rendering or intended semantics.
"""

import argparse
import hashlib
import io
import json
import math
import posixpath
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET


NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
STRICT_NS = {
    "http://purl.oclc.org/ooxml/presentationml/main": NS["p"],
    "http://purl.oclc.org/ooxml/drawingml/main": NS["a"],
    "http://purl.oclc.org/ooxml/officeDocument/relationships": NS["r"],
}
EMU_PER_PT = 12700
EPS_PT = 1e-9
SIDES = ("top", "right", "bottom", "left")
INSET_ATTRS = ("tIns", "rIns", "bIns", "lIns")
MARGIN_ATTRS = ("marT", "marR", "marB", "marL")
# Informational ordinary-shape bodyPr defaults, never table-cell margins.
DEFAULT_INSETS_PT = dict(zip(SIDES, (3.6, 7.2, 3.6, 7.2)))
HORIZONTAL = {
    "l": "left", "ctr": "center", "r": "right", "just": "justify",
    "justLow": "justify_low", "dist": "distributed", "thaiDist": "thai_distributed",
}
VERTICAL = {"t": "top", "ctr": "center", "b": "bottom",
            "just": "justify", "dist": "distributed"}
SHAPE_TYPES = {"sp", "cxnSp", "pic", "graphicFrame", "grpSp", "contentPart"}
ARROWS = {"triangle", "stealth", "arrow"}
IDENTITY = (1.0, 1.0, 0.0, 0.0)  # sx, sy, tx, ty, in points


class InputError(ValueError):
    """An invalid package or contract, rather than a layout finding."""


def local(tag):
    return tag.rsplit("}", 1)[-1]


def attrs(element):
    return dict(element.attrib) if element is not None else {}


def integer(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise InputError("Invalid XML integer: {!r}".format(value)) from exc


def points(value):
    value = integer(value)
    return None if value is None else value / EMU_PER_PT


def boolean(value, default=False):
    if value is None:
        return default
    if value not in ("0", "1", "true", "false"):
        raise InputError("Invalid XML boolean: {!r}".format(value))
    return value in ("1", "true")


def xml_part(archive, name):
    try:
        root = ET.fromstring(archive.read(name))
    except (KeyError, ET.ParseError) as exc:
        raise InputError("Cannot read XML part {}: {}".format(name, exc)) from exc
    # Strict and Transitional use the same properties needed by this inspector.
    for element in root.iter():
        for old, new in STRICT_NS.items():
            element.tag = element.tag.replace("{" + old + "}", "{" + new + "}")
        element.attrib = {
            next((key.replace("{" + old + "}", "{" + new + "}")
                  for old, new in STRICT_NS.items() if key.startswith("{" + old + "}")),
                 key): value for key, value in element.attrib.items()
        }
    return root


def relationship_target(part, target):
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise InputError("Unsupported internal relationship target: " + target)
    decoded = unquote(parsed.path)
    name = posixpath.normpath(posixpath.join(posixpath.dirname(part), decoded)
                             if not decoded.startswith("/") else decoded.lstrip("/"))
    if name in ("", ".", "..") or name.startswith("../") or "\\" in name:
        raise InputError("Invalid package relationship target: " + target)
    return name


def relationships(archive, part):
    name = posixpath.join(posixpath.dirname(part), "_rels",
                         posixpath.basename(part) + ".rels") if part else "_rels/.rels"
    result = {}
    for element in xml_part(archive, name):
        if local(element.tag) != "Relationship":
            continue
        item = attrs(element)
        rid = item.get("Id")
        if not rid or rid in result:
            raise InputError("Missing/duplicate relationship ID in " + name)
        result[rid] = item
    return result


def require_internal_target(part, relation, kind):
    if relation is None or not relation.get("Type", "").endswith("/" + kind):
        raise InputError("Missing {} relationship in {}".format(kind, part or "/"))
    if relation.get("TargetMode", "Internal") != "Internal":
        raise InputError("External {} relationship is unsupported".format(kind))
    return relationship_target(part, relation.get("Target", ""))


def bbox(x, y, width, height):
    return {"x": x, "y": y, "width": width, "height": height}


def map_point(matrix, point):
    sx, sy, tx, ty = matrix
    return [sx * point[0] + tx, sy * point[1] + ty]


def map_box(matrix, box):
    if box["width"] < 0 or box["height"] < 0:
        raise InputError("Cannot normalize a rectangle with negative width or height.")
    first = map_point(matrix, (box["x"], box["y"]))
    last = map_point(matrix, (box["x"] + box["width"], box["y"] + box["height"]))
    return bbox(min(first[0], last[0]), min(first[1], last[1]),
                abs(last[0] - first[0]), abs(last[1] - first[1]))


def inset_box(box, insets):
    return bbox(box["x"] + insets["left"], box["y"] + insets["top"],
                box["width"] - insets["left"] - insets["right"],
                box["height"] - insets["top"] - insets["bottom"])


def transform(element):
    data = attrs(element)
    for name in ("off", "ext", "chOff", "chExt"):
        child = element.find("a:" + name, NS) if element is not None else None
        data[name] = {key: integer(value) for key, value in attrs(child).items()}
    rotation = integer(data.get("rot", "0"))
    box = None
    if {"x", "y"} <= data["off"].keys() and {"cx", "cy"} <= data["ext"].keys():
        box = bbox(*(data["off"][key] / EMU_PER_PT for key in ("x", "y")),
                   *(data["ext"][key] / EMU_PER_PT for key in ("cx", "cy")))
    issues = []
    if box is None:
        issues.append("Missing/inherited transform offset or extent.")
    elif box["width"] < 0 or box["height"] < 0:
        issues.append("Negative transform extent.")
    if rotation % 21600000:
        issues.append("Rotated geometry is not normalized.")
    return {
        "raw": data, "rotation_deg": rotation / 60000,
        "flip_h": boolean(data.get("flipH")), "flip_v": boolean(data.get("flipV")),
        "local_bbox_pt": box, "issues": issues,
    }


def group_matrix(info, parent):
    """Compose axis-aligned child-coordinate scaling, reflection and translation."""
    box, raw = info["local_bbox_pt"], info["raw"]
    if info["issues"] or parent is None:
        return None
    if not ({"x", "y"} <= raw["chOff"].keys()
            and {"cx", "cy"} <= raw["chExt"].keys()):
        return None
    cw, ch = (raw["chExt"][key] / EMU_PER_PT for key in ("cx", "cy"))
    if cw <= 0 or ch <= 0:
        return None
    sx = box["width"] / cw * (-1 if info["flip_h"] else 1)
    sy = box["height"] / ch * (-1 if info["flip_v"] else 1)
    tx = box["x"] + (box["width"] if info["flip_h"] else 0) - sx * raw["chOff"]["x"] / EMU_PER_PT
    ty = box["y"] + (box["height"] if info["flip_v"] else 0) - sy * raw["chOff"]["y"] / EMU_PER_PT
    psx, psy, ptx, pty = parent
    return psx * sx, psy * sy, psx * tx + ptx, psy * ty + pty


def font_properties(element):
    raw = attrs(element)
    result = {"raw": raw, "size_pt": None, "typefaces": {}}
    for key, output in (("sz", "size_pt"), ("kern", "kerning_pt"), ("spc", "spacing_pt")):
        if key in raw:
            result[output] = integer(raw[key]) / 100
    for key, output in (("b", "bold"), ("i", "italic")):
        result[output] = boolean(raw.get(key), default=None)
    if element is not None:
        result["typefaces"] = {local(child.tag): attrs(child) for child in element
                               if local(child.tag) in ("latin", "ea", "cs", "sym")}
        fill = element.find("a:solidFill", NS)
        result["color"] = [xml_summary(child) for child in fill] if fill is not None else None
    return result


def xml_summary(element):
    return {"type": local(element.tag), "attributes": attrs(element),
            "children": [xml_summary(child) for child in element]}


def text_body(element, cell_properties=None, is_cell=False):
    body = element.find("a:bodyPr", NS)
    raw = attrs(body)
    insets = {side: points(raw.get(key)) for side, key in zip(SIDES, INSET_ATTRS)}
    anchor_raw = attrs(cell_properties).get("anchor") if is_cell else raw.get("anchor")
    result = {
        "body_properties": raw, "insets_pt": insets,
        "schema_default_insets_pt": None if is_cell else DEFAULT_INSETS_PT.copy(),
        "insets_source": "explicit_bodyPr_not_table_cell_margins" if is_cell else
            "explicit_bodyPr_physical_units_not_group_scaled",
        "rendered_fit_status": "unverified",
        "rendered_fit_reason": "Stored properties do not establish glyph fit, clipping or optical placement.",
        "vertical_alignment": VERTICAL.get(anchor_raw),
        "vertical_alignment_raw": anchor_raw,
        "vertical_alignment_source": "tcPr" if is_cell else "bodyPr",
        "paragraphs": [], "limitations": [],
        "autofit": [xml_summary(child) for child in body
                    if local(child.tag) in ("noAutofit", "normAutofit", "spAutoFit")]
                   if body is not None else [],
    }
    if not is_cell and None in insets.values():
        result["limitations"].append("Omitted body insets may be inherited; defaults are not certified.")
    if anchor_raw is None:
        result["limitations"].append("Vertical text alignment is omitted/inherited.")
    orientation = attrs(cell_properties) if is_cell else raw
    warp = body.find("a:prstTxWarp", NS) if body is not None else None
    no_warp = warp is None or (
        warp.get("prst") == "textNoShape" and not warp.findall("a:avLst/a:gd", NS)
    )
    result["orientation_supported"] = (
        integer(raw.get("rot", "0")) % 21600000 == 0
        and raw.get("vert", "horz") == "horz"
        and orientation.get("vert", "horz") == "horz"
        and no_warp
    )
    if not result["orientation_supported"]:
        result["limitations"].append("Rotated, vertical or warped text is not normalized.")
    for number, paragraph in enumerate(element.findall("a:p", NS), 1):
        property_nodes = paragraph.findall("a:pPr", NS)
        properties = property_nodes[0] if property_nodes else None
        prop = attrs(properties)
        ambiguous = len(property_nodes) > 1
        variants = []
        for node in property_nodes:
            value = xml_summary(node)
            if value not in variants:
                variants.append(value)
        item = {
            "paragraph": number, "properties": prop,
            "paragraph_properties_count": len(property_nodes), "paragraph_property_variants": variants,
            "properties_source": "first_pPr_invalid_duplicate_grammar" if ambiguous else "explicit_pPr",
            "horizontal_alignment": None if ambiguous else HORIZONTAL.get(prop.get("algn")),
            "horizontal_alignment_raw": None if ambiguous else prop.get("algn"),
            "horizontal_alignment_source": "invalid_multiple_pPr" if ambiguous else
                ("explicit_pPr" if "algn" in prop else "inherited_unresolved"),
            "margins_pt": {key: points(prop.get(key)) for key in ("marL", "marR", "indent")},
            "default_font": font_properties(properties.find("a:defRPr", NS) if properties is not None else None),
            "end_font": font_properties(paragraph.find("a:endParaRPr", NS)),
            "spacing": {}, "bullets": [], "runs": [],
        }
        if properties is not None:
            for child in properties:
                name = local(child.tag)
                if name in ("lnSpc", "spcBef", "spcAft"):
                    item["spacing"][name] = [
                        {"unit": "pt" if local(value.tag) == "spcPts" else "percent",
                         "value": integer(value.get("val")) / (100 if local(value.tag) == "spcPts" else 1000)}
                        for value in child
                    ]
                elif name.startswith("bu"):
                    item["bullets"].append(xml_summary(child))
        for child in paragraph:
            kind = local(child.tag)
            if kind in ("r", "fld", "br"):
                item["runs"].append({
                    "type": kind, "text": "\n" if kind == "br" else child.findtext("a:t", "", NS),
                    "font": font_properties(child.find("a:rPr", NS)),
                })
        item["text"] = "".join(run["text"] for run in item["runs"])
        result["paragraphs"].append(item)
    if any(p["paragraph_properties_count"] > 1 for p in result["paragraphs"]):
        result["limitations"].append("Duplicate pPr elements make paragraph formatting ambiguous; see structure defects.")
    if any(p["horizontal_alignment_raw"] is None for p in result["paragraphs"]):
        result["limitations"].append("Paragraph text alignment is omitted/inherited.")
    style = element.find("a:lstStyle", NS)
    result["local_list_style"] = xml_summary(style) if style is not None else None
    result["text"] = "\n".join(p["text"] for p in result["paragraphs"])
    return result


def line_properties(shape, info, parent, preset):
    line = shape.find("p:spPr/a:ln", NS)
    style = shape.find("p:style/a:lnRef", NS)
    inherited = line is None or (style is not None and style.get("idx") != "0")
    result = {"width_pt": points(attrs(line).get("w")), "raw": attrs(line),
              "geometry": preset, "endpoints_pt": None, "direction": "unverified",
              "attachments": {}, "limitations": []}
    for name in ("headEnd", "tailEnd"):
        end = line.find("a:" + name, NS) if line is not None else None
        raw = attrs(end)
        result[name] = {
            "type": raw.get("type", "none" if end is not None or not inherited else None),
            "raw": raw, "source": "explicit" if "type" in raw else
            ("inherited_unresolved" if inherited and end is None else "schema_default"),
        }
    for xml_name, key in (("stCxn", "start"), ("endCxn", "end")):
        connection = shape.find("p:nvCxnSpPr/p:cNvCxnSpPr/a:" + xml_name, NS)
        result["attachments"][key] = (
            {"shape_id": integer(connection.get("id")), "site_index": integer(connection.get("idx"))}
            if connection is not None else None
        )
    if preset not in ("line", "straightConnector1"):
        result["limitations"].append("Only straight line/straightConnector1 routes are normalized.")
    elif info["issues"] or parent is None:
        result["limitations"].append("Line transform cannot be normalized.")
    else:
        box = info["local_bbox_pt"]
        start = [box["x"] + (box["width"] if info["flip_h"] else 0),
                 box["y"] + (box["height"] if info["flip_v"] else 0)]
        end = [box["x"] + (0 if info["flip_h"] else box["width"]),
               box["y"] + (0 if info["flip_v"] else box["height"])]
        result["endpoints_pt"] = {"start": map_point(parent, start), "end": map_point(parent, end)}
    head, tail = result["headEnd"]["type"], result["tailEnd"]["type"]
    if head is None or tail is None:
        result["limitations"].append("Line-end decorations are inherited/unresolved.")
    elif head in ARROWS and tail == "none":
        result["direction"] = "end_to_start"
    elif tail in ARROWS and head == "none":
        result["direction"] = "start_to_end"
    elif head in ARROWS and tail in ARROWS:
        result["direction"] = "bidirectional"
    elif head == tail == "none":
        result["direction"] = "undirected"
    else:
        result["direction"] = "non_directional_or_mixed_decorations"
    result["geometry_status"] = "normalized" if result["endpoints_pt"] is not None else "unsupported"
    return result


def table_inventory(table, box, frame_size_emu=None):
    # Compare native integers, not rounded point values or a general layout
    # tolerance. The caller supplies the original extents only for supported
    # top-level frames; unsupported transforms retain unverified cell bboxes.
    column_emu = [integer(e.get("w")) for e in table.findall("a:tblGrid/a:gridCol", NS)]
    rows = table.findall("a:tr", NS)
    row_emu = [integer(e.get("h")) for e in rows]
    columns = [points(value) for value in column_emu]
    heights = [points(value) for value in row_emu]
    known = bool(columns) and bool(rows) and None not in columns + heights
    nonnegative = known and all(v >= 0 for v in columns + heights)
    regular = all(len(row.findall("a:tc", NS)) == len(columns) for row in rows)
    grid_emu = {"width": sum(column_emu), "height": sum(row_emu)} if known else None
    grid_size = {key: points(value) for key, value in grid_emu.items()} if known else None
    counts = {"width": len(columns), "height": len(rows)}
    allowance_emu = {key: (count + 1) // 2 for key, count in counts.items()}
    frame_known = frame_size_emu is not None and all(
        type(frame_size_emu.get(key)) is int for key in ("width", "height"))
    residual_emu = {key: frame_size_emu[key] - grid_emu[key] for key in ("width", "height")} \
        if frame_known and known else None
    can_place_grid = nonnegative and regular and box is not None
    can_map = (can_place_grid and residual_emu is not None
               and all(abs(residual_emu[key]) <= allowance_emu[key] for key in ("width", "height")))
    result = {
        "column_widths_pt": columns, "row_heights_pt": heights,
        "frame_bbox_pt": box, "grid_size_pt": grid_size,
        "grid_bbox_pt": bbox(box["x"], box["y"], **grid_size) if can_place_grid else None,
        "frame_minus_grid_pt": {key: points(value) for key, value in residual_emu.items()}
            if box is not None and residual_emu is not None else None,
        "frame_grid_status": "pass" if can_map else "unverified",
        "frame_grid_rounding": {
            "assumption": "Independent nearest-integer-EMU rounding of each component dimension and the frame; at most 0.5 EMU per value.",
            "allowance_formula": "floor((component_count + 1) / 2)",
            "component_count": counts, "allowance_emu": allowance_emu,
            "allowance_pt": {key: points(value) for key, value in allowance_emu.items()},
            "frame_size_emu": frame_size_emu, "grid_size_emu": grid_emu,
            "frame_minus_grid_emu": residual_emu,
            "status": ("exact" if all(value == 0 for value in residual_emu.values())
                       else "within_integer_rounding_allowance") if can_map else "unverified",
            "rescaled": False,
        },
        "cells": [], "limitations": [],
    }
    if not can_map:
        result["limitations"].append(
            "Table frame/grid agreement is unsupported or exceeds the accumulated integer-EMU rounding allowance; cell bboxes unverified.")
    if known and not nonnegative:
        result["limitations"].append("Negative stored table grid dimensions are invalid; they are not normalized.")
    if box is None:
        result["limitations"].append("Table slide coordinates require a supported top-level frame transform.")
    if not regular:
        result["limitations"].append("Row cell counts differ from the grid; slot assignment is unverified.")
    y = box["y"] if box else 0
    for row_number, row in enumerate(rows, 1):
        x = box["x"] if box else 0
        for col_number, cell in enumerate(row.findall("a:tc", NS), 1):
            properties = cell.find("a:tcPr", NS)
            raw = attrs(properties)
            margins = {side: points(raw.get(key)) for side, key in zip(SIDES, MARGIN_ATTRS)}
            merge = {key: cell.get(key) for key in ("gridSpan", "rowSpan", "hMerge", "vMerge")}
            merged = (any(integer(merge[key] or "1") != 1 for key in ("gridSpan", "rowSpan"))
                      or any(boolean(merge[key]) for key in ("hMerge", "vMerge")))
            slot_box = (bbox(x, y, columns[col_number - 1], heights[row_number - 1])
                        if can_place_grid and col_number <= len(columns) else None)
            cell_box = slot_box if can_map and not merged else None
            structural_box = slot_box if not merged else None
            body = cell.find("a:txBody", NS)
            text = text_body(body, properties, is_cell=True) if body is not None else None
            orientation_supported = text is None or text["orientation_supported"]
            structural_content = (inset_box(structural_box, margins)
                if structural_box is not None and None not in margins.values() and orientation_supported else None)
            content = structural_content if cell_box is not None else None
            content_invalid = structural_content is not None and (
                structural_content["width"] < 0 or structural_content["height"] < 0)
            item = {
                "row": row_number, "column": col_number, "properties": raw, "merge": merge,
                "bbox_pt": cell_box, "grid_slot_bbox_pt": slot_box,
                "structural_bbox_pt": structural_box, "margins_pt": margins,
                "margins_source": "explicit_tcPr_only_no_bodyPr_defaults_added",
                "content_bbox_pt": content, "structural_content_bbox_pt": structural_content,
                "content_bbox_status": "invalid" if content_invalid else ("valid" if content is not None else "unverified"),
                "text": text,
                "border_widths_pt": {name: points(attrs(properties.find("a:" + name, NS)
                    if properties is not None else None).get("w"))
                    for name in ("lnL", "lnR", "lnT", "lnB")},
                "limitations": [],
            }
            if merged:
                item["limitations"].append("Merged-cell geometry is not normalized.")
            if None in margins.values():
                item["limitations"].append("Omitted table margins are not certified as explicit values.")
            if not orientation_supported:
                item["limitations"].append("Cell content under rotated/vertical/warped text is unverified.")
            if content_invalid:
                item["limitations"].append("Negative stored cell content width or height; values are retained, not normalized.")
            result["cells"].append(item)
            if nonnegative and col_number <= len(columns):
                x += columns[col_number - 1]
        if nonnegative:
            y += heights[row_number - 1]
    return result


def shape_inventory(element, parent=IDENTITY, ancestors=(), drawing_order=1):
    kind = local(element.tag)
    native = next((child.find("p:cNvPr", NS) for child in element
                   if local(child.tag).startswith("nv")), None)
    native_props = attrs(native)
    transform_path = {"grpSp": "p:grpSpPr/a:xfrm", "graphicFrame": "p:xfrm"}.get(kind, "p:spPr/a:xfrm")
    info = transform(element.find(transform_path, NS))
    issues = list(info["issues"])
    if parent is None:
        issues.append("An ancestor transform/compatibility alternative cannot be normalized.")
    sp_properties = element.find("p:spPr", NS)
    if sp_properties is not None and any(local(child.tag) in ("scene3d", "sp3d") for child in sp_properties):
        issues.append("3D shape transforms are unsupported.")
    child_matrix = group_matrix(info, parent) if kind == "grpSp" else None
    if kind == "grpSp" and child_matrix is None:
        issues.append("Group child coordinates are missing, degenerate or unsupported.")
    if kind not in SHAPE_TYPES:
        issues.append("Unsupported native object or markup compatibility alternative: " + kind)
    box = map_box(parent, info["local_bbox_pt"]) if not issues else None
    preset_element = element.find("p:spPr/a:prstGeom", NS)
    preset = preset_element.get("prst") if preset_element is not None else None
    custom = element.find("p:spPr/a:custGeom", NS)
    shape = {
        "id": integer(native_props.get("id")), "name": native_props.get("name"),
        "type": kind, "native_properties": native_props, "drawing_order": drawing_order,
        "ancestor_ids": list(ancestors), "top_level": not ancestors,
        "transform": info, "geometry_status": "unsupported" if issues else "normalized",
        "geometry": {"preset": preset, "custom": custom is not None},
        "bbox_pt": box, "content_bbox_pt": box, "content_insets_pt": dict.fromkeys(SIDES, 0.0),
        "content_bbox_status": "valid" if box is not None else "unverified",
        "content_limitations": [], "text": None, "table": None, "line": None,
        "limitations": list(issues), "children": [],
    }
    placeholder = next((child.find("p:nvPr/p:ph", NS) for child in element
                        if local(child.tag).startswith("nv")), None)
    shape["placeholder"] = attrs(placeholder) if placeholder is not None else None
    shape["stroke_width_pt"] = points(attrs(element.find("p:spPr/a:ln", NS)).get("w"))
    body = element.find("p:txBody", NS)
    if body is not None:
        shape["text"] = text_body(body)
        shape["content_insets_pt"] = shape["text"]["insets_pt"].copy()
        if None in shape["content_insets_pt"].values():
            shape["content_limitations"].append("Content box requires explicit body insets.")
        if preset != "rect":
            shape["content_limitations"].append("Preset/custom text rectangles other than rect are not normalized.")
        if ancestors:
            shape["content_limitations"].append(
                "Nested text inset model is unresolved; group geometry scale is not applied to physical insets.")
        if (not shape["text"]["orientation_supported"] or info["flip_h"] or info["flip_v"]
                or (parent is not None and (parent[0] < 0 or parent[1] < 0))):
            shape["content_limitations"].append("Text content under reflection/rotation/warping is unverified.")
        if box is None or shape["content_limitations"]:
            shape["content_bbox_pt"] = None
            shape["content_bbox_status"] = "unverified"
        else:
            shape["content_bbox_pt"] = inset_box(box, shape["content_insets_pt"])
            if shape["content_bbox_pt"]["width"] < 0 or shape["content_bbox_pt"]["height"] < 0:
                shape["content_bbox_status"] = "invalid"
                shape["limitations"].append(
                    "Negative stored text content width or height; values are retained, not normalized.")
        shape["limitations"].extend(shape["text"]["limitations"])
        shape["limitations"].extend(shape["content_limitations"])
        if shape["text"]["text"] and (
                shape["content_bbox_status"] == "invalid" or
                (box is not None and (box["width"] == 0 or box["height"] == 0))):
            shape["limitations"].append(
                "Structural risk: a nonpositive stored text envelope does not prove clipping; "
                "overflow/no-wrap and rendered glyph fit remain unverified.")
    elif kind == "sp" and preset != "rect":
        shape["content_bbox_pt"] = None
        shape["content_bbox_status"] = "unverified"
        shape["content_limitations"].append(
            "A nonrectangular or inherited preset bbox is only an envelope, not a verified content region.")
        shape["limitations"].extend(shape["content_limitations"])
    table = element.find("a:graphic/a:graphicData/a:tbl", NS)
    if table is not None:
        table_box = box if (not info["flip_h"] and not info["flip_v"]
                           and not ancestors and parent == IDENTITY) else None
        frame_size_emu = {key: info["raw"]["ext"][attr]
                          for key, attr in (("width", "cx"), ("height", "cy"))} if table_box is not None else None
        shape["table"] = table_inventory(table, table_box, frame_size_emu)
        shape["limitations"].extend(shape["table"]["limitations"])
        # A table has separate content boxes per cell, not one text body.
        shape["content_bbox_pt"] = None
        shape["content_bbox_status"] = "unverified"
        shape["content_limitations"].append("Tables have per-cell content boxes.")
    if kind == "cxnSp" or preset in ("line", "straightConnector1") or (
            preset is not None and preset.startswith(("bentConnector", "curvedConnector"))):
        line_info = dict(info, issues=issues)
        shape["line"] = line_properties(element, line_info, parent, preset)
        shape["limitations"].extend(shape["line"]["limitations"])
    if kind == "graphicFrame" and table is None:
        shape["limitations"].append("Non-table graphic contents are not inspected.")
    if custom is not None:
        shape["limitations"].append("Custom paths are inventoried by outer bbox; their route geometry is unsupported.")
        if body is None:
            shape["content_bbox_pt"] = None
            shape["content_bbox_status"] = "unverified"
            shape["content_limitations"].append("Custom geometry content area is not normalized.")
    if kind == "grpSp" or kind not in SHAPE_TYPES:
        children = [child for child in element if local(child.tag) not in
                    ("nvGrpSpPr", "grpSpPr", "extLst")]
        shape["children"] = [
            shape_inventory(child, child_matrix, ancestors + (shape["id"],), order)
            for order, child in enumerate(children, 1)
        ]
    shape["limitations"] = list(dict.fromkeys(shape["limitations"]))
    return shape


def iter_shapes(shapes):
    for shape in shapes:
        yield shape
        yield from iter_shapes(shape["children"])


def structure_defects(tree, slide, part):
    """Check raw native identities/cardinality before any first-match extraction."""
    identities, defects = {}, []
    paragraph_count = 0

    def visit(element, path, owner=None, alternatives=()):
        nonlocal paragraph_count
        if element.tag in {"{" + NS["p"] + "}" + kind for kind in SHAPE_TYPES}:
            native = next((child.find("p:cNvPr", NS) for child in element
                           if local(child.tag).startswith("nv")), None)
            owner = {"id": integer(attrs(native).get("id")), "name": attrs(native).get("name"),
                     "type": local(element.tag)}
        if element.tag == "{" + NS["p"] + "}cNvPr":
            shape_id = integer(element.get("id"))
            if shape_id is not None:
                identities.setdefault(shape_id, []).append({
                    "name": element.get("name"), "shape_type": owner["type"] if owner else "spTree",
                    "path": path, "alternatives": list(alternatives),
                })
        if element.tag == "{" + NS["a"] + "}p":
            paragraph_count += 1
            properties = element.findall("a:pPr", NS)
            if len(properties) > 1:
                variants = [xml_summary(node) for node in properties]
                defects.append({
                    "code": "multiple_paragraph_properties", "status": "fail", "slide": slide,
                    "part": part, "object": owner["id"] if owner else None, "owner": owner,
                    "path": path, "paragraph_xml_index": paragraph_count, "pPr_count": len(properties),
                    "identical_properties": all(value == variants[0] for value in variants[1:]),
                    "detail": "a:p permits at most one direct a:pPr, even when duplicates are identical.",
                })
        positions = {}
        for child in element:
            name = next((prefix + ":" + local(child.tag) for prefix, uri in NS.items()
                         if child.tag.startswith("{" + uri + "}")), local(child.tag))
            positions[name] = positions.get(name, 0) + 1
            child_path = "{}/{}[{}]".format(path, name, positions[name])
            branch = alternatives + (child_path,) if local(child.tag) in ("Choice", "Fallback") else alternatives
            visit(child, child_path, owner, branch)

    visit(tree, "p:spTree[1]")
    for shape_id, occurrences in identities.items():
        if len(occurrences) > 1:
            # Markup-compatibility alternatives may be mutually exclusive; do not
            # call them a proven duplicate in the processed drawing.
            ambiguous = any(item["alternatives"] for item in occurrences)
            defects.append({
                "code": "duplicate_native_shape_id", "status": "unverified" if ambiguous else "fail",
                "slide": slide, "part": part, "object": shape_id, "occurrences": occurrences,
                "detail": "Identity across compatibility alternatives is unverified." if ambiguous else
                    "p:cNvPr IDs must be unique across the slide shape tree, including tables and groups.",
            })
    return defects


def structure_summary(defects):
    return {
        "status": status_of(defects, empty="pass"),
        "checks": ["unique_native_shape_ids", "single_paragraph_properties"],
        "counts": {
            "duplicate_native_shape_ids": sum(d["code"] == "duplicate_native_shape_id" and d["status"] == "fail" for d in defects),
            "paragraphs_with_multiple_pPr": sum(d["code"] == "multiple_paragraph_properties" for d in defects),
            "extra_pPr_elements": sum(d.get("pPr_count", 1) - 1 for d in defects),
            "unverified": sum(d["status"] == "unverified" for d in defects),
        },
        "defect_count": sum(d["status"] == "fail" for d in defects),
        "defects": defects,
    }


def inspect_bytes(data, artifact="<memory>", contracts=None):
    """Inspect bytes once so that the inventory and hash describe the same revision."""
    report = {
        "schema_version": 1, "role": "native-layout-inventory", "artifact": artifact,
        "artifact_sha256": hashlib.sha256(data).hexdigest(), "artifact_size_bytes": len(data),
        "units": "pt", "slide_count": 0, "slide_size_pt": None,
        "slides": [], "coverage": [], "findings": [], "exceptions": [],
        "limitations": [
            {"code": "scope", "detail": "Stored OOXML geometry only; no glyph-fit, optical/aesthetic or application-rendering verification. Bboxes exclude strokes and effects."},
            {"code": "inheritance", "detail": "Master/layout/theme text defaults, effective fonts and font substitution are not resolved; only explicit native properties are evidence."},
            {"code": "native_scope", "detail": "Inventory covers slide shape trees, not master/layout artwork or embedded graphic content. Nested IDs are not contract targets."},
            {"code": "attachment_scope", "detail": "Connection IDs/site indices are stored metadata; port-site equivalence and attachment while dragging are not verified."},
        ],
    }
    defects = []
    with ZipFile(io.BytesIO(data)) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise InputError("Duplicate ZIP part names make package interpretation ambiguous.")
        roots = [r for r in relationships(archive, "").values()
                 if r.get("Type", "").endswith("/officeDocument")]
        if len(roots) != 1:
            raise InputError("Expected one package officeDocument relationship.")
        presentation_part = require_internal_target("", roots[0], "officeDocument")
        presentation = xml_part(archive, presentation_part)
        if presentation.tag != "{" + NS["p"] + "}presentation":
            raise InputError("The officeDocument part is not a presentation.")
        size = presentation.find("p:sldSz", NS)
        width, height = points(attrs(size).get("cx")), points(attrs(size).get("cy"))
        if width is None or height is None or width <= 0 or height <= 0:
            raise InputError("Missing/invalid presentation slide size.")
        report["slide_size_pt"] = {"width": width, "height": height}
        rels = relationships(archive, presentation_part)
        for number, slide_id in enumerate(presentation.findall("p:sldIdLst/p:sldId", NS), 1):
            rid = slide_id.get("{" + NS["r"] + "}id")
            part = require_internal_target(presentation_part, rels.get(rid), "slide")
            slide_xml = xml_part(archive, part)
            tree = slide_xml.find("p:cSld/p:spTree", NS)
            if tree is None:
                raise InputError("Slide has no native shape tree: " + part)
            slide_defects = structure_defects(tree, number, part)
            defects.extend(slide_defects)
            root_transform = tree.find("p:grpSpPr/a:xfrm", NS)
            matrix = IDENTITY
            if root_transform is not None:
                root_info = transform(root_transform)
                raw = root_info["raw"]
                neutral = (not root_info["flip_h"] and not root_info["flip_v"]
                           and root_info["rotation_deg"] % 360 == 0
                           and raw["off"] == raw["chOff"]
                           and raw["ext"] == raw["chExt"])
                if not neutral:
                    matrix = None
                    report["limitations"].append({"slide": number, "code": "root_transform",
                        "detail": "Non-neutral slide shape-tree transform is unsupported."})
            children = [e for e in tree if local(e.tag) not in ("nvGrpSpPr", "grpSpPr", "extLst")]
            shapes = [shape_inventory(e, matrix, drawing_order=order)
                      for order, e in enumerate(children, 1)]
            slide = {
                "slide": number, "native_slide_id": integer(slide_id.get("id")),
                "relationship_id": rid, "part": part, "hidden": not boolean(slide_xml.get("show"), True),
                "shape_count": len(shapes), "recursive_shape_count": sum(1 for _ in iter_shapes(shapes)),
                "shapes": shapes, "structure": {key: value for key, value in structure_summary(slide_defects).items()
                                                if key != "defects"},
            }
            report["slides"].append(slide)
            report["coverage"].append({"slide": number, "checks": ["native_inventory", "unique_native_shape_ids",
                                      "single_paragraph_properties"], "status": "reviewed"})
            for shape in iter_shapes(shapes):
                for detail in shape["limitations"]:
                    report["limitations"].append({"slide": number, "object": shape["id"],
                        "ancestor_ids": shape["ancestor_ids"], "code": "shape_limitation", "detail": detail})
                if shape["table"]:
                    for cell in shape["table"]["cells"]:
                        details = cell["limitations"] + (cell["text"]["limitations"] if cell["text"] else [])
                        for detail in details:
                            report["limitations"].append({"slide": number, "object": shape["id"],
                                "cell": [cell["row"], cell["column"]], "code": "cell_limitation", "detail": detail})
        report["slide_count"] = len(report["slides"])
    report["structure"] = structure_summary(defects)
    for defect in defects:
        report["findings"].append({
            "id": "native-structure-{}".format(len(report["findings"]) + 1),
            "slide": defect["slide"], "object": defect["object"], "severity": "major",
            "evidence": defect, "status": "open" if defect["status"] == "fail" else "unverified",
            "recommendation": "Assign a unique p:cNvPr ID per slide object." if defect["code"] == "duplicate_native_shape_id"
                else "Serialize zero or one a:pPr per paragraph; normalize properties in the source serializer.",
        })
    report["contracts"] = evaluate_contracts(report, contracts)
    report["status"] = status_of([report["structure"], report["contracts"]])
    if report["structure"]["status"] == "pass" and report["contracts"]["status"] == "not_requested":
        report["status"] = "inspected"
    for rule in report["contracts"]["rules"]:
        for check in rule["checks"]:
            if check["status"] in ("fail", "unverified"):
                report["findings"].append({
                    "id": "contract-{}-{}".format(rule["rule_index"], len(report["findings"]) + 1),
                    "slide": rule["slide"], "object": check.get("object"),
                    "severity": "major" if check["status"] == "fail" else "observation",
                    "evidence": check, "status": "open" if check["status"] == "fail" else "unverified",
                    "recommendation": "Review the explicit contract and native properties.",
                })
    return report


def inspect_pptx(path, contracts=None):
    path = Path(path).expanduser().resolve()
    data = path.read_bytes()
    report = inspect_bytes(data, str(path), contracts)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    unchanged = report["artifact_sha256"] == after
    report["source_integrity"] = {
        "status": "pass" if unchanged else "fail", "unchanged": unchanged,
        "sha256_before": report["artifact_sha256"], "sha256_after": after,
    }
    if not unchanged:
        report["status"] = "fail"
        report["findings"].append({
            "id": "source-changed-during-inspection", "severity": "major", "status": "open",
            "evidence": "The source bytes changed during inspection; the inventory describes only sha256_before.",
            "recommendation": "Inspect an immutable copy or retry after the other writer has finished.",
        })
    return report


def finite_number(value, label, nonnegative=True):
    if type(value) not in (int, float) or not math.isfinite(value) or (nonnegative and value < 0):
        raise InputError("{} must be a finite {}number.".format(label, "nonnegative " if nonnegative else ""))
    return value


def validate_contracts(document):
    if not isinstance(document, dict) or set(document) - {"tolerance_pt", "rules"}:
        raise InputError("Contracts must be an object with rules and optional tolerance_pt.")
    tolerance = finite_number(document.get("tolerance_pt", 0.75), "tolerance_pt")
    rules = document.get("rules")
    if not isinstance(rules, list):
        raise InputError("Contracts.rules must be an array.")
    fields = {
        "alignment": ({"objects", "edge"}, set()),
        "text_alignment": ({"objects"}, {"horizontal", "vertical"}),
        "containment": ({"parent", "children"}, {"padding_pt"}),
        "gap": ({"first", "second", "axis", "minimum_pt"}, set()),
        "directed_edge": ({"source", "target", "source_port", "target_port"},
                          {"connector", "connectors", "maximum_endpoint_gap_pt"}),
    }
    for number, rule in enumerate(rules, 1):
        if not isinstance(rule, dict) or not isinstance(rule.get("type"), str) or rule["type"] not in fields:
            raise InputError("Rule {} has an unknown/missing type.".format(number))
        required, optional = fields[rule["type"]]
        keys = set(rule)
        if not (required | {"type", "slide"}) <= keys or keys - required - optional - {"type", "slide", "id", "tolerance_pt"}:
            raise InputError("Rule {} has missing or unknown fields.".format(number))
        if type(rule["slide"]) is not int or rule["slide"] < 1:
            raise InputError("Rule slide must be a positive integer.")
        if "id" in rule and not isinstance(rule["id"], str):
            raise InputError("Optional rule id must be a string.")
        finite_number(rule.get("tolerance_pt", tolerance), "Rule tolerance_pt")
        for key in ("objects", "children", "connectors"):
            if key in rule:
                ids = rule[key]
                if not isinstance(ids, list) or not ids or any(type(i) is not int or i < 1 for i in ids):
                    raise InputError("{} must be a nonempty array of native shape IDs.".format(key))
                if len(ids) != len(set(ids)):
                    raise InputError("Duplicate IDs in " + key)
        for key in ("parent", "first", "second", "source", "target", "connector"):
            if key in rule and (type(rule[key]) is not int or rule[key] < 1):
                raise InputError("{} must be a positive native shape ID.".format(key))
        kind = rule["type"]
        if kind == "alignment":
            if len(rule["objects"]) < 2 or rule["edge"] not in ("left", "right", "top", "bottom", "center_x", "center_y"):
                raise InputError("alignment needs at least two objects and a supported bbox edge.")
        elif kind == "text_alignment":
            if not {"horizontal", "vertical"} & keys:
                raise InputError("text_alignment needs horizontal and/or vertical.")
            if "horizontal" in rule and rule["horizontal"] not in HORIZONTAL.values():
                raise InputError("Unsupported horizontal text alignment.")
            if "vertical" in rule and rule["vertical"] not in tuple(VERTICAL.values()) + ("middle",):
                raise InputError("Unsupported vertical text alignment.")
        elif kind == "containment":
            padding = rule.get("padding_pt", [0, 0, 0, 0])
            if not isinstance(padding, list) or len(padding) != 4:
                raise InputError("padding_pt must contain top/right/bottom/left.")
            for value in padding:
                finite_number(value, "padding_pt")
            if rule["parent"] in rule["children"]:
                raise InputError("A containment parent cannot contain itself.")
        elif kind == "gap":
            if rule["axis"] not in ("x", "y") or rule["first"] == rule["second"]:
                raise InputError("gap needs distinct shapes and axis x/y.")
            finite_number(rule["minimum_pt"], "minimum_pt")
        else:
            if ("connector" in keys) == ("connectors" in keys):
                raise InputError("directed_edge needs exactly one of connector or connectors.")
            if any(rule[key] not in SIDES for key in ("source_port", "target_port")):
                raise InputError("Ports must be top/right/bottom/left.")
            finite_number(rule.get("maximum_endpoint_gap_pt", 2), "maximum_endpoint_gap_pt")
            connectors = rule.get("connectors", [rule.get("connector")])
            if rule["source"] == rule["target"] or {rule["source"], rule["target"]} & set(connectors):
                raise InputError("Directed edge nodes and connectors must be distinct.")
    return tolerance, rules


def status_of(checks, empty="not_requested"):
    statuses = {check["status"] for check in checks}
    return next((status for status in ("fail", "unverified", "pass") if status in statuses), empty)


def check(result, name, passed=None, **evidence):
    result["checks"].append({
        "check": name, "status": "unverified" if passed is None else ("pass" if passed else "fail"),
        **evidence,
    })


def select_shape(slide, shape_id, result, geometry=True):
    matching = [shape for shape in iter_shapes(slide["shapes"]) if shape["id"] == shape_id]
    if not matching:
        check(result, "shape_exists", False, object=shape_id, detail="Native shape ID is absent from this slide.")
        return None
    if len(matching) != 1:
        check(result, "shape_identity", object=shape_id, detail="Native shape ID is ambiguous.")
        return None
    shape = matching[0]
    if not shape["top_level"]:
        check(result, "top_level_shape", object=shape_id, detail="Nested group/compatibility objects are inventory-only.")
        return None
    local_box = shape["transform"]["local_bbox_pt"]
    if geometry and local_box is not None and (local_box["width"] < 0 or local_box["height"] < 0):
        check(result, "nonnegative_native_extent", False, object=shape_id, bbox_pt=local_box,
              detail="Negative native extent is invalid and cannot be normalized.")
        return None
    if geometry and shape["geometry"]["custom"]:
        check(result, "custom_geometry", object=shape_id,
              detail="Only the stored transform bbox is known; custom-path geometry is not verified.")
        return None
    if geometry and shape["geometry_status"] != "normalized":
        check(result, "normalized_geometry", object=shape_id, detail=shape["limitations"])
        return None
    return shape


def box_edge(box, edge):
    return {
        "left": box["x"], "right": box["x"] + box["width"],
        "top": box["y"], "bottom": box["y"] + box["height"],
        "center_x": box["x"] + box["width"] / 2, "center_y": box["y"] + box["height"] / 2,
    }[edge]


def check_text_alignment(shape, rule, result):
    bodies = [("shape", shape["text"])] if shape["text"] else []
    if shape["table"]:
        bodies.extend(("cell {},{}".format(cell["row"], cell["column"]), cell["text"])
                      for cell in shape["table"]["cells"] if cell["text"])
    if not bodies:
        check(result, "text_body", object=shape["id"], detail="No inspectable native text body.")
    for location, body in bodies:
        if not body["orientation_supported"] or shape["transform"]["flip_h"] or shape["transform"]["flip_v"]:
            check(result, "text_orientation", object=shape["id"], location=location,
                  detail="Text orientation cannot be normalized.")
            continue
        if "vertical" in rule:
            expected = "center" if rule["vertical"] == "middle" else rule["vertical"]
            actual = body["vertical_alignment"]
            check(result, "vertical_text_alignment", None if actual is None else actual == expected,
                  object=shape["id"], location=location, expected=expected, actual=actual,
                  source=body["vertical_alignment_source"])
        if "horizontal" in rule:
            if not body["paragraphs"]:
                check(result, "paragraph_alignment", object=shape["id"], detail="No paragraphs.")
            for paragraph in body["paragraphs"]:
                actual = paragraph["horizontal_alignment"]
                check(result, "horizontal_text_alignment", None if actual is None else actual == rule["horizontal"],
                      object=shape["id"], location=location, paragraph=paragraph["paragraph"],
                      expected=rule["horizontal"], actual=actual, source=paragraph["horizontal_alignment_source"])


def check_containment(parent, children, rule, result, tolerance):
    padding = dict(zip(SIDES, rule.get("padding_pt", [0, 0, 0, 0])))
    # Unknown text rectangles/orientations do not justify invented side clearances.
    insets = parent["content_insets_pt"]
    if any(detail != "Content box requires explicit body insets." for detail in parent["content_limitations"]):
        insets = dict.fromkeys(SIDES, 0.0)
    if parent["content_limitations"]:
        check(result, "native_content_box", object=parent["id"], detail=parent["content_limitations"])
    effective = {side: max(padding[side], insets[side] if insets[side] is not None else 0) for side in SIDES}
    inner = inset_box(parent["bbox_pt"], effective)
    if inner["width"] < 0 or inner["height"] < 0:
        check(result, "content_box_nonnegative", False, object=parent["id"], available_bbox_pt=inner)
    for child in children:
        actual = child["bbox_pt"]
        excess = {
            "left": inner["x"] - actual["x"], "top": inner["y"] - actual["y"],
            "right": actual["x"] + actual["width"] - inner["x"] - inner["width"],
            "bottom": actual["y"] + actual["height"] - inner["y"] - inner["height"],
        }
        check(result, "containment", max(excess.values()) <= tolerance + EPS_PT,
              object=child["id"], parent=parent["id"], excess_pt=excess,
              required_insets_pt=effective, tolerance_pt=tolerance)


def port_point(box, side):
    x, y, width, height = (box[key] for key in ("x", "y", "width", "height"))
    return {"left": [x, y + height / 2], "right": [x + width, y + height / 2],
            "top": [x + width / 2, y], "bottom": [x + width / 2, y + height]}[side]


def distance(first, second):
    return math.hypot(first[0] - second[0], first[1] - second[1])


def check_port(result, node, side, start, end, is_target, limit):
    if node is None:
        return
    point = end if is_target else start
    expected = port_point(node["bbox_pt"], side)
    gap = distance(point, expected)
    prefix = "target" if is_target else "source"
    check(result, prefix + "_endpoint", gap <= limit + EPS_PT, object=node["id"],
          port=side, endpoint_pt=point, expected_pt=expected, gap_pt=gap, allowed_gap_pt=limit)
    outward = {"left": (-1, 0), "right": (1, 0), "top": (0, -1), "bottom": (0, 1)}[side]
    vector = [end[0] - start[0], end[1] - start[1]]
    component = sum(vector[i] * outward[i] for i in (0, 1)) * (-1 if is_target else 1)
    check(result, prefix + ("_arrival_direction" if is_target else "_departure_direction"),
          component > EPS_PT, object=node["id"], port=side, vector_pt=vector,
          expected_normal_component_pt=component,
          detail="Requires a strictly positive inward/outward component, not a tangent or reversal.")


def check_attachment(result, line, endpoint_key, node_id, label):
    attachment = line["attachments"][endpoint_key]
    if attachment is not None:
        check(result, label + "_attachment_id", attachment["shape_id"] == node_id,
              expected_shape_id=node_id, actual=attachment, native_endpoint=endpoint_key,
              detail="Stored ID only; site index and drag behavior are not verified.")


def check_directed_edge(slide, rule, result, tolerance):
    source = select_shape(slide, rule["source"], result)
    target = select_shape(slide, rule["target"], result)
    ids = rule.get("connectors", [rule.get("connector")])
    lines = []
    limit = rule.get("maximum_endpoint_gap_pt", 2) + tolerance
    for number, shape_id in enumerate(ids):
        shape = select_shape(slide, shape_id, result, geometry=False)
        line = shape["line"] if shape else None
        lines.append(line)
        if shape is not None and line is None:
            custom = shape["geometry"]["custom"]
            check(result, "connector_geometry", None if custom else False, object=shape_id,
                  detail="Custom route geometry is unsupported." if custom else "Object is not a native line/connector.")
        if line is None:
            continue
        if line["endpoints_pt"] is None:
            check(result, "straight_route_geometry", object=shape_id, detail=line["limitations"])
        else:
            length = distance(line["endpoints_pt"]["start"], line["endpoints_pt"]["end"])
            check(result, "nonzero_segment", length > EPS_PT, object=shape_id, length_pt=length)
        head, tail = line["headEnd"]["type"], line["tailEnd"]["type"]
        if head is None or tail is None:
            check(result, "explicit_arrow_direction", object=shape_id, detail="Line decorations are unresolved.")
        elif number < len(ids) - 1:
            check(result, "intermediate_segment_has_no_arrow", head == tail == "none", object=shape_id,
                  head_end=head, tail_end=tail)
        else:
            check(result, "single_final_directional_arrow", line["direction"] in ("start_to_end", "end_to_start"),
                  object=shape_id, head_end=head, tail_end=tail, actual_direction=line["direction"])
    final = lines[-1]
    if final is None or final["endpoints_pt"] is None or final["direction"] not in ("start_to_end", "end_to_start"):
        check(result, "ordered_directed_route", detail="The final directed segment cannot be established.")
        return
    reverse = final["direction"] == "end_to_start"
    start_key, end_key = ("end", "start") if reverse else ("start", "end")
    last_start, last_end = (final["endpoints_pt"][key] for key in (start_key, end_key))
    check_port(result, target, rule["target_port"], last_start, last_end, True, limit)
    check_attachment(result, final, end_key, rule["target"], "target")
    if any(line is None or line["endpoints_pt"] is None for line in lines):
        check(result, "ordered_directed_route", detail="One or more segment transforms/routes are unsupported.")
        return
    route = [{"object": ids[-1], "start_pt": last_start, "end_pt": last_end,
              "native_start_key": start_key, "native_end_key": end_key}]
    for index in range(len(lines) - 2, -1, -1):
        endpoints = lines[index]["endpoints_pt"]
        next_start = route[0]["start_pt"]
        forward_gap = distance(endpoints["end"], next_start)
        reverse_gap = distance(endpoints["start"], next_start)
        if max(forward_gap, reverse_gap) <= limit + EPS_PT:
            check(result, "segment_orientation", object=ids[index],
                  detail="Both ends can meet the next segment within tolerance; traversal is ambiguous.")
            # Do not report a source/join violation based on an arbitrary choice.
            result["resolved_tail_route"] = route
            return
        reverse = reverse_gap < forward_gap
        start_key, end_key = ("end", "start") if reverse else ("start", "end")
        gap = min(forward_gap, reverse_gap)
        check(result, "consecutive_segments_meet", gap <= limit + EPS_PT,
              object=ids[index], next_object=ids[index + 1], gap_pt=gap, allowed_gap_pt=limit)
        route.insert(0, {"object": ids[index], "start_pt": endpoints[start_key], "end_pt": endpoints[end_key],
                         "native_start_key": start_key, "native_end_key": end_key})
    first = route[0]
    check_port(result, source, rule["source_port"], first["start_pt"], first["end_pt"], False, limit)
    check_attachment(result, lines[0], first["native_start_key"], rule["source"], "source")
    result["ordered_route"] = route


def evaluate_contracts(report, document):
    result = {"status": "not_requested", "tolerance_pt": 0.75, "counts": {"pass": 0, "fail": 0, "unverified": 0},
              "rules": []}
    if document is None:
        return result
    tolerance, rules = validate_contracts(document)
    result["tolerance_pt"] = tolerance
    for number, rule in enumerate(rules, 1):
        item = {"rule_index": number, "type": rule["type"], "slide": rule["slide"],
                "contract": rule, "checks": []}
        result["rules"].append(item)
        if rule["slide"] > report["slide_count"]:
            check(item, "slide_exists", False, detail="Slide is absent from presentation order.")
        else:
            slide = report["slides"][rule["slide"] - 1]
            tol = rule.get("tolerance_pt", tolerance)
            kind = rule["type"]
            if kind in ("alignment", "text_alignment"):
                shapes = [select_shape(slide, i, item) for i in rule["objects"]]
                shapes = [shape for shape in shapes if shape is not None]
                if kind == "alignment" and len(shapes) >= 2:
                    values = {str(shape["id"]): box_edge(shape["bbox_pt"], rule["edge"]) for shape in shapes}
                    spread = max(values.values()) - min(values.values())
                    check(item, "bbox_alignment", spread <= tol + EPS_PT, edge=rule["edge"],
                          positions_pt=values, spread_pt=spread, tolerance_pt=tol)
                elif kind == "text_alignment":
                    for shape in shapes:
                        check_text_alignment(shape, rule, item)
            elif kind == "containment":
                parent = select_shape(slide, rule["parent"], item)
                children = [select_shape(slide, i, item) for i in rule["children"]]
                if parent is not None:
                    check_containment(parent, [shape for shape in children if shape is not None], rule, item, tol)
            elif kind == "gap":
                first = select_shape(slide, rule["first"], item)
                second = select_shape(slide, rule["second"], item)
                if first is not None and second is not None:
                    axis, extent = ("x", "width") if rule["axis"] == "x" else ("y", "height")
                    actual = second["bbox_pt"][axis] - first["bbox_pt"][axis] - first["bbox_pt"][extent]
                    check(item, "minimum_gap", actual + tol + EPS_PT >= rule["minimum_pt"],
                          gap_pt=actual, minimum_pt=rule["minimum_pt"], tolerance_pt=tol)
            else:
                check_directed_edge(slide, rule, item, tol)
        item["status"] = status_of(item["checks"], empty="unverified")
        result["counts"][item["status"]] += 1
    result["status"] = status_of(result["rules"])
    return result


def exit_code(report):
    if report.get("status") == "error":
        return 2
    return {"fail": 1, "unverified": 3}.get(report["status"], 0)


def load_contracts(path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InputError("Duplicate contract JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def json_text(report):
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pptx", help="Input PPTX; never modified.")
    parser.add_argument("--contracts", help="Optional explicit contract JSON.")
    parser.add_argument("--output", default="-", help="JSON output path (default: stdout).")
    args = parser.parse_args(argv)
    output = Path(args.output).expanduser() if args.output != "-" else None
    try:
        if output is not None:
            for name in (args.pptx, args.contracts):
                if name is None:
                    continue
                source = Path(name).expanduser()
                if output.resolve() == source.resolve() or (
                        output.exists() and source.exists() and output.samefile(source)):
                    output = None
                    raise InputError("--output must not overwrite the input PPTX or contracts.")
        document = load_contracts(args.contracts) if args.contracts else None
        if args.contracts:
            validate_contracts(document)
        report = inspect_pptx(args.pptx, document)
    except (InputError, OSError, BadZipFile, ValueError, OverflowError, RuntimeError) as exc:
        report = {"schema_version": 1, "status": "error", "errors": [str(exc)]}
    try:
        text = json_text(report)
        if output is None:
            sys.stdout.write(text)
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
    except (OSError, ValueError) as exc:
        sys.stderr.write("Cannot write inventory JSON: {}\n".format(exc))
        return 2
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
