#!/usr/bin/env python3
"""Independent stdlib tests for inspect-layout.py.

Run: python3 -B test_inspect_layout.py [--output results.json]
     [--fixtures-dir directory-for-temporary-cli-fixtures]

Fixtures use literal native EMU values and independently worked point results.
They are minimal ZIP/XML packages, not application-rendered presentations.
The CLI tests write only temporary fixtures and the requested test report.
"""

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).with_name("inspect-layout.py")
SPEC = importlib.util.spec_from_file_location("native_layout_inspector", SCRIPT)
INSPECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSPECTOR)

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
FIXTURES_DIR = None


def xfrm(raw_box, attributes="", prefix="a", child_coordinates=""):
    x, y, width, height = raw_box
    return (
        f'<{prefix}:xfrm {attributes}><a:off x="{x}" y="{y}"/>'
        f'<a:ext cx="{width}" cy="{height}"/>{child_coordinates}</{prefix}:xfrm>'
    )


def text_body(text="Sample", insets=(0, 0, 0, 0), anchor="t", align="l",
              extra="", paragraphs="", list_style="", prefix="p"):
    # Insets are raw EMU in top/right/bottom/left order, never inspector units.
    margin = "" if insets is None else " ".join(
        f'{key}="{value}"' for key, value in zip(("tIns", "rIns", "bIns", "lIns"), insets))
    vertical = "" if anchor is None else f'anchor="{anchor}"'
    horizontal = "" if align is None else f'algn="{align}"'
    return (
        f'<{prefix}:txBody><a:bodyPr {margin} {vertical}>{extra}</a:bodyPr>'
        f'<a:lstStyle>{list_style}</a:lstStyle>'
        f'<a:p><a:pPr {horizontal} marL="25400" indent="-12700">'
        '<a:lnSpc><a:spcPct val="125000"/></a:lnSpc>'
        '<a:spcAft><a:spcPts val="250"/></a:spcAft></a:pPr>'
        '<a:r><a:rPr sz="2250"><a:latin typeface="Example Latin"/>'
        '<a:ea typeface="Example East Asian"/></a:rPr>'
        f'<a:t>{escape(text)}</a:t></a:r></a:p>{paragraphs}</{prefix}:txBody>'
    )


def shape(shape_id, raw_box, body="", transform="", preset="rect", geometry=None):
    geometry = (f'<a:prstGeom prst="{preset}"><a:avLst/></a:prstGeom>'
                if geometry is None else geometry)
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Shape {shape_id}"/>'
        '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr>{xfrm(raw_box, transform)}{geometry}</p:spPr>{body}</p:sp>'
    )


def connector(shape_id, raw_box, transform="", head="none", tail="triangle",
              preset="line", start_id=41, end_id=7, style=""):
    attachments = "".join(
        f'<a:{tag} id="{native_id}" idx="{site}"/>'
        for tag, native_id, site in (("stCxn", start_id, 3), ("endCxn", end_id, 1))
        if native_id is not None)
    decorations = "".join(f'<a:{tag} type="{value}"/>'
                          for tag, value in (("headEnd", head), ("tailEnd", tail))
                          if value is not None)
    return (
        f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{shape_id}" name="Edge {shape_id}"/>'
        f'<p:cNvCxnSpPr>{attachments}</p:cNvCxnSpPr><p:nvPr/></p:nvCxnSpPr>'
        f'<p:spPr>{xfrm(raw_box, transform)}<a:prstGeom prst="{preset}">'
        f'<a:avLst/></a:prstGeom><a:ln w="9525">{decorations}</a:ln></p:spPr>'
        f'{style}</p:cxnSp>'
    )


def group(children, transform="", raw_box=(127000, 254000, 2743200, 1270000)):
    return (
        '<p:grpSp><p:nvGrpSpPr><p:cNvPr id="90" name="Component"/>'
        '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr>'
        + xfrm(raw_box, transform, child_coordinates=(
            '<a:chOff x="0" y="0"/><a:chExt cx="1371600" cy="635000"/>'))
        + '</p:grpSpPr>' + children + '</p:grpSp>'
    )


def table(frame_height=635000, margin_left=12700, margin_right=25400,
          first_merge="", cell_orientation="", body_anchor="b", body_insets=(0, 0, 0, 0),
          frame_width=1371600, column_widths=(914400, 457200), row_heights=(254000, 381000)):
    rows = []
    for row, height in enumerate(row_heights):
        cells = []
        for col in range(len(column_widths)):
            merge = first_merge if row == col == 0 else ""
            body = text_body(f"Cell {row + 1},{col + 1}", anchor=body_anchor, prefix="a", insets=body_insets)
            cells.append(
                f'<a:tc {merge}>{body}<a:tcPr marL="{margin_left}" marR="{margin_right}" '
                f'marT="38100" marB="50800" anchor="t" {cell_orientation}/></a:tc>')
        rows.append(f'<a:tr h="{height}">{"".join(cells)}</a:tr>')
    return (
        '<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="87" name="Native table"/>'
        '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>'
        + xfrm((127000, 254000, frame_width, frame_height), prefix="p")
        + '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
        '<a:tbl><a:tblPr/><a:tblGrid>'
        + "".join(f'<a:gridCol w="{width}"/>' for width in column_widths)
        + '</a:tblGrid>' + "".join(rows) + '</a:tbl></a:graphicData></a:graphic></p:graphicFrame>'
    )


def package(slides, order=None, hidden=(), strict=False):
    """Slides maps physical part numbers to XML; order is (native slide ID, part)."""
    order = order or [(900 + index, part) for index, part in enumerate(slides)]
    parts = {
        "_rels/.rels": (f'<Relationships xmlns="{PKG}"><Relationship Id="doc" '
                       f'Type="{R}/officeDocument" Target="ppt/presentation.xml"/></Relationships>'),
        "ppt/presentation.xml": (
            f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>'
            + "".join(f'<p:sldId id="{native_id}" r:id="s{index}"/>'
                      for index, (native_id, _) in enumerate(order))
            + '</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/></p:presentation>'),
        "ppt/_rels/presentation.xml.rels": (
            f'<Relationships xmlns="{PKG}">'
            + "".join(f'<Relationship Id="s{index}" Type="{R}/slide" Target="slides/slide{part}.xml"/>'
                      for index, (_, part) in enumerate(order))
            + '</Relationships>'),
    }
    for part, contents in slides.items():
        parts[f"ppt/slides/slide{part}.xml"] = (
            f'<p:sld xmlns:p="{P}" xmlns:a="{A}" show="{0 if part in hidden else 1}">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
            + contents + '</p:spTree></p:cSld></p:sld>')
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, xml in parts.items():
            if strict:
                for old, new in (
                    (P, "http://purl.oclc.org/ooxml/presentationml/main"),
                    (A, "http://purl.oclc.org/ooxml/drawingml/main"),
                    (R, "http://purl.oclc.org/ooxml/officeDocument/relationships"),
                ):
                    xml = xml.replace(old, new)
            archive.writestr(ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0)), xml)
    return buffer.getvalue()


def rule(kind, **properties):
    return {"type": kind, "slide": 1, **properties}


def document(*rules, tolerance=0.75):
    return {"tolerance_pt": tolerance, "rules": list(rules)}


def node_a(body=""):
    # x=1 inch=72pt, y=0.5 inch=36pt; width=100pt, height=40pt.
    return shape(41, (914400, 457200, 1270000, 508000), body)


def node_b(y=457200, x=2438400, body=""):
    # x=192pt, so the signed gap from A's right edge at 172pt is 20pt.
    return shape(7, (x, y, 1270000, 508000), body)


def edge_rule(**overrides):
    return rule("directed_edge", **{
        "connector": 80, "source": 41, "target": 7,
        "source_port": "right", "target_port": "left",
        "maximum_endpoint_gap_pt": 0, **overrides,
    })


class InspectorTests(unittest.TestCase):
    def inspect(self, shapes, *rules, tolerance=0.75):
        return INSPECTOR.inspect_bytes(package({9: shapes}), contracts=document(*rules, tolerance=tolerance))

    def outcome(self, report, expected):
        self.assertEqual(expected, report["contracts"]["status"])
        self.assertEqual({"pass": 0, "fail": 1, "unverified": 3, "not_requested": 0}[expected],
                         INSPECTOR.exit_code(report))
        if expected == "unverified":
            unresolved = [check for item in report["contracts"]["rules"] for check in item["checks"]
                          if check["status"] == "unverified"]
            self.assertTrue(unresolved)
            self.assertTrue(all(check.get("detail") or check.get("source") for check in unresolved))

    def test_physical_order_native_ids_hidden_and_unreferenced_parts(self):
        for strict in (False, True):
            with self.subTest(strict=strict):
                report = INSPECTOR.inspect_bytes(package(
                    {1: node_b(), 9: node_a(), 99: node_b()}, order=[(808, 9), (257, 1)],
                    hidden=(1,), strict=strict))
                self.assertEqual(["ppt/slides/slide9.xml", "ppt/slides/slide1.xml"],
                                 [slide["part"] for slide in report["slides"]])
                self.assertEqual([808, 257], [s["native_slide_id"] for s in report["slides"]])
                self.assertEqual([41, 7], [s["shapes"][0]["id"] for s in report["slides"]])
                self.assertEqual([False, True], [s["hidden"] for s in report["slides"]])
                self.assertEqual({"width": 960, "height": 540}, report["slide_size_pt"])
                self.assertEqual(2, report["slide_count"])
                self.assertEqual("inspected", report["status"])

    def test_independent_emu_points_text_and_paragraph_units(self):
        report = self.inspect(node_a(text_body(
            insets=(45720, 91440, 45720, 91440), anchor="ctr")))
        obj = report["slides"][0]["shapes"][0]
        self.assertEqual({"x": 72, "y": 36, "width": 100, "height": 40}, obj["bbox_pt"])
        self.assertAlmostEqual(79.2, obj["content_bbox_pt"]["x"])
        self.assertAlmostEqual(85.6, obj["content_bbox_pt"]["width"])
        self.assertAlmostEqual(32.8, obj["content_bbox_pt"]["height"])
        paragraph = obj["text"]["paragraphs"][0]
        self.assertEqual({"marL": 2, "marR": None, "indent": -1}, paragraph["margins_pt"])
        self.assertEqual(22.5, paragraph["runs"][0]["font"]["size_pt"])
        self.assertEqual([{"unit": "percent", "value": 125}], paragraph["spacing"]["lnSpc"])
        self.assertEqual([{"unit": "pt", "value": 2.5}], paragraph["spacing"]["spcAft"])
        self.assertEqual("center", obj["text"]["vertical_alignment"])

    def test_alignment_is_spread_with_inclusive_point_tolerance(self):
        shapes = node_a() + node_b(y=463550)  # Independent y=36.5pt.
        aligned = rule("alignment", objects=[41, 7], edge="top")
        report = self.inspect(shapes, aligned, tolerance=0.5)
        self.outcome(report, "pass")
        self.assertEqual(0.5, report["contracts"]["rules"][0]["checks"][0]["spread_pt"])
        self.outcome(self.inspect(shapes, aligned, tolerance=0.49), "fail")
        self.outcome(self.inspect(shapes, rule("alignment", objects=[41, 7], edge="left")), "fail")

    def test_signed_gap_and_boundary_tolerance(self):
        expected = rule("gap", first=41, second=7, axis="x", minimum_pt=20.75)
        report = self.inspect(node_a() + node_b(), expected)
        self.outcome(report, "pass")
        self.assertEqual(20, report["contracts"]["rules"][0]["checks"][0]["gap_pt"])
        self.outcome(self.inspect(node_a() + node_b(), dict(expected, minimum_pt=20.76)), "fail")
        overlap = self.inspect(node_a() + node_b(x=2159000), dict(expected, minimum_pt=0))
        self.outcome(overlap, "fail")
        self.assertEqual(-2, overlap["contracts"]["rules"][0]["checks"][0]["gap_pt"])

    def test_vertical_gap_measures_edges_not_center_spacing(self):
        report = self.inspect(node_a() + node_b(y=1219200),
                              rule("gap", first=41, second=7, axis="y", minimum_pt=20))
        self.outcome(report, "pass")
        self.assertEqual(20, report["contracts"]["rules"][0]["checks"][0]["gap_pt"])

    def test_explicit_alignment_and_unresolved_local_inheritance(self):
        contract = rule("text_alignment", objects=[41], horizontal="left", vertical="top")
        self.outcome(self.inspect(node_a(text_body()), contract), "pass")
        inherited = text_body(anchor=None, align=None,
                              list_style='<a:lvl1pPr algn="l"><a:defRPr sz="2250"/></a:lvl1pPr>')
        report = self.inspect(node_a(inherited), contract)
        self.outcome(report, "unverified")
        self.assertIsNone(report["slides"][0]["shapes"][0]["text"]["paragraphs"][0]["horizontal_alignment"])

    def test_every_paragraph_is_checked_and_known_failure_takes_precedence(self):
        paragraphs = '<a:p><a:pPr algn="r"/><a:r><a:t>Second</a:t></a:r></a:p>'
        report = self.inspect(node_a(text_body(anchor=None, paragraphs=paragraphs)),
                              rule("text_alignment", objects=[41], horizontal="left", vertical="top"))
        self.outcome(report, "fail")
        checks = report["contracts"]["rules"][0]["checks"]
        self.assertEqual(["unverified", "pass", "fail"], [check["status"] for check in checks])
        self.assertEqual(2, checks[-1]["paragraph"])

    def test_text_no_shape_is_not_warp_but_real_warp_is_unverified(self):
        contract = rule("text_alignment", objects=[41], horizontal="left", vertical="top")
        no_warp = '<a:prstTxWarp prst="textNoShape"><a:avLst/></a:prstTxWarp>'
        report = self.inspect(node_a(text_body(extra=no_warp)), contract)
        self.outcome(report, "pass")
        self.assertEqual(100, report["slides"][0]["shapes"][0]["content_bbox_pt"]["width"])
        arc = '<a:prstTxWarp prst="textArchUp"><a:avLst/></a:prstTxWarp>'
        self.outcome(self.inspect(node_a(text_body(extra=arc)), contract), "unverified")

    def test_omitted_insets_stay_unknown_even_when_schema_defaults_exist(self):
        container = shape(99, (635000, 254000, 3429000, 1016000), text_body(insets=None))
        report = self.inspect(container + node_a(),
                              rule("containment", parent=99, children=[41], padding_pt=[0, 0, 0, 0]))
        self.outcome(report, "unverified")
        self.assertIsNone(report["slides"][0]["shapes"][0]["content_bbox_pt"])
        self.assertTrue(all(value is None for value in report["slides"][0]["shapes"][0]["content_insets_pt"].values()))

    def test_containment_intersects_padding_and_insets_without_double_counting(self):
        parent = shape(99, (635000, 254000, 3429000, 1016000),
                       text_body(insets=(127000, 254000, 127000, 254000)))
        contract = rule("containment", parent=99, children=[41, 7], padding_pt=[5, 10, 5, 10])
        report = self.inspect(parent + node_a() + node_b(), contract)
        self.outcome(report, "pass")
        measured = report["contracts"]["rules"][0]["checks"][0]
        self.assertEqual({"top": 10, "right": 20, "bottom": 10, "left": 20},
                         measured["required_insets_pt"])
        self.assertEqual(-2, measured["excess_pt"]["left"])  # 70 - 72.
        self.outcome(self.inspect(parent + node_a() + node_b(),
                                 dict(contract, padding_pt=[24, 10, 5, 10])), "fail")

    def test_negative_content_dimensions_are_invalid_even_with_large_tolerance(self):
        parent = shape(99, (0, 0, 127000, 76200),
                       text_body(insets=(50800, 76200, 50800, 76200)))
        report = self.inspect(parent + shape(41, (76200, 50800, 0, 0)),
                              rule("containment", parent=99, children=[41]), tolerance=100)
        self.outcome(report, "fail")
        box = report["slides"][0]["shapes"][0]
        self.assertEqual("invalid", box["content_bbox_status"])
        self.assertEqual({"x": 6, "y": 4, "width": -2, "height": -2}, box["content_bbox_pt"])
        with self.assertRaises(INSPECTOR.InputError):
            INSPECTOR.map_box((1, 1, 0, 0), box["content_bbox_pt"])

    def test_negative_native_extent_is_not_turned_positive(self):
        report = self.inspect(shape(41, (914400, 457200, -127000, 508000)) + node_b(),
                              rule("alignment", objects=[41, 7], edge="top"))
        self.outcome(report, "fail")
        obj = report["slides"][0]["shapes"][0]
        self.assertIsNone(obj["bbox_pt"])
        self.assertEqual(-10, obj["transform"]["local_bbox_pt"]["width"])

    def test_zero_width_no_wrap_is_a_structural_risk_not_certified_clipping(self):
        body = text_body(insets=(36000, 72000, 0, 72000), extra="<a:noAutofit/>").replace(
            "<a:bodyPr ", '<a:bodyPr wrap="none" ', 1)
        report = self.inspect(shape(41, (914400, 457200, 0, 508000), body))
        obj = report["slides"][0]["shapes"][0]
        self.assertAlmostEqual(-11.3385826772, obj["content_bbox_pt"]["width"])
        self.assertEqual("invalid", obj["content_bbox_status"])
        self.assertEqual("unverified", obj["text"]["rendered_fit_status"])
        self.assertEqual("Sample", obj["text"]["text"])
        self.assertEqual("inspected", report["status"])

    def test_group_geometry_does_not_automatically_scale_physical_text_insets(self):
        report = self.inspect(group(node_a(text_body(insets=(0, 72000, 0, 72000)))))
        child = report["slides"][0]["shapes"][0]["children"][0]
        self.assertEqual({"x": 154, "y": 92, "width": 200, "height": 80}, child["bbox_pt"])
        self.assertAlmostEqual(5.6692913386, child["content_insets_pt"]["left"])
        self.assertAlmostEqual(5.6692913386, child["content_insets_pt"]["right"])
        self.assertIsNone(child["content_bbox_pt"])
        self.assertEqual("unverified", child["content_bbox_status"])

    def test_nonrectangular_preset_envelope_does_not_certify_containment(self):
        parent = shape(99, (635000, 254000, 3429000, 1016000), preset="ellipse")
        report = self.inspect(parent + node_a(), rule("containment", parent=99, children=[41]))
        self.outcome(report, "unverified")
        self.assertEqual(270, report["slides"][0]["shapes"][0]["bbox_pt"]["width"])
        self.assertIsNone(report["slides"][0]["shapes"][0]["content_bbox_pt"])

    def test_table_geometry_margin_units_and_tcpr_anchor(self):
        report = self.inspect(table(), rule("text_alignment", objects=[87], horizontal="left", vertical="top"))
        self.outcome(report, "pass")  # bodyPr says bottom; tcPr correctly wins for a table cell.
        grid = report["slides"][0]["shapes"][0]["table"]
        self.assertEqual([72, 36], grid["column_widths_pt"])
        self.assertEqual([20, 30], grid["row_heights_pt"])
        self.assertEqual({"width": 108, "height": 50}, grid["grid_size_pt"])
        cell = grid["cells"][3]
        self.assertEqual({"x": 82, "y": 40, "width": 36, "height": 30}, cell["bbox_pt"])
        self.assertEqual({"x": 83, "y": 43, "width": 33, "height": 23}, cell["content_bbox_pt"])
        self.assertEqual("tcPr", cell["text"]["vertical_alignment_source"])

    def test_table_margins_are_not_added_to_bodypr_insets_or_shape_defaults(self):
        grid = self.inspect(table(body_insets=(91440, 91440, 91440, 91440)))["slides"][0]["shapes"][0]["table"]
        cell = grid["cells"][3]
        self.assertEqual({"x": 83, "y": 43, "width": 33, "height": 23}, cell["content_bbox_pt"])
        self.assertAlmostEqual(7.2, cell["text"]["insets_pt"]["left"])
        self.assertIsNone(cell["text"]["schema_default_insets_pt"])

    def test_table_grid_and_frame_disagreement_is_not_rescaled(self):
        report = self.inspect(table(frame_height=1270000))
        grid = report["slides"][0]["shapes"][0]["table"]
        self.assertEqual("unverified", grid["frame_grid_status"])
        self.assertEqual({"width": 0, "height": 50}, grid["frame_minus_grid_pt"])
        self.assertEqual(100, grid["frame_bbox_pt"]["height"])
        self.assertEqual(50, grid["grid_bbox_pt"]["height"])
        self.assertIsNone(grid["cells"][3]["bbox_pt"])
        self.assertEqual({"x": 82, "y": 40, "width": 36, "height": 30},
                         grid["cells"][3]["structural_bbox_pt"])
        self.assertEqual("unverified", grid["cells"][3]["content_bbox_status"])

    def test_two_emu_table_rounding_preserves_native_dimensions(self):
        # Synthetic tables whose rounded rows and frame differ by 2-3 EMU.
        # Six rounded rows + the rounded frame allow at most 3 whole EMU.
        heights = (328613, 481012, 481012, 481012, 481012, 476250)
        for slide, widths, width_residual in (
            (7, (621655, 2176165, 5907286, 1658094), 0),
            (15, (2383482, 4974282, 3005435), 1),
        ):
            with self.subTest(slide=slide):
                grid = self.inspect(table(
                    frame_width=10363200, frame_height=2728913,
                    column_widths=widths, row_heights=heights,
                ))["slides"][0]["shapes"][0]["table"]
                rounding = grid["frame_grid_rounding"]
                self.assertEqual("pass", grid["frame_grid_status"])
                self.assertEqual("within_integer_rounding_allowance", rounding["status"])
                self.assertEqual({"width": len(widths), "height": 6}, rounding["component_count"])
                self.assertEqual({"width": 2, "height": 3}, rounding["allowance_emu"])
                self.assertEqual({"width": width_residual, "height": 2}, rounding["frame_minus_grid_emu"])
                self.assertFalse(rounding["rescaled"])
                self.assertEqual([value / 12700 for value in widths], grid["column_widths_pt"])
                self.assertEqual([value / 12700 for value in heights], grid["row_heights_pt"])
                self.assertEqual(2728911 / 12700, grid["grid_bbox_pt"]["height"])
                self.assertAlmostEqual(2728913 / 12700, grid["frame_bbox_pt"]["height"])
                for cell in grid["cells"]:
                    self.assertIsNotNone(cell["content_bbox_pt"])
                    self.assertEqual(widths[cell["column"] - 1] / 12700, cell["bbox_pt"]["width"])
                    self.assertEqual(heights[cell["row"] - 1] / 12700, cell["bbox_pt"]["height"])

    def test_table_rounding_allowance_is_axis_specific_and_bounded(self):
        # Four columns allow 2 whole EMU; six rows allow 3. Check both signs at
        # the exact boundary and 1 EMU beyond, without any point-layout tolerance.
        widths = (621655, 2176165, 5907286, 1658094)
        heights = (328613, 481012, 481012, 481012, 481012, 476250)
        for axis, allowance in (("width", 2), ("height", 3)):
            for sign in (-1, 1):
                for extra in (0, 1):
                    with self.subTest(axis=axis, sign=sign, beyond_allowance=extra):
                        frame = {"width": 10363200, "height": 2728911}
                        frame[axis] += sign * (allowance + extra)
                        grid = self.inspect(table(
                            frame_width=frame["width"], frame_height=frame["height"],
                            column_widths=widths, row_heights=heights,
                        ))["slides"][0]["shapes"][0]["table"]
                        self.assertEqual("unverified" if extra else "pass", grid["frame_grid_status"])
                        self.assertEqual(sign * (allowance + extra),
                                         grid["frame_grid_rounding"]["frame_minus_grid_emu"][axis])
                        self.assertFalse(grid["frame_grid_rounding"]["rescaled"])
                        self.assertEqual(heights[-1] / 12700, grid["cells"][-1]["grid_slot_bbox_pt"]["height"])
                        if extra:
                            self.assertTrue(grid["limitations"])
                            self.assertTrue(all(cell["bbox_pt"] is None for cell in grid["cells"]))
                        else:
                            self.assertTrue(all(cell["bbox_pt"] is not None for cell in grid["cells"]))

    def test_table_merge_metadata_does_not_invent_effective_cell_geometry(self):
        grid = self.inspect(table(first_merge='gridSpan="2"'))["slides"][0]["shapes"][0]["table"]
        cell = grid["cells"][0]
        self.assertEqual("2", cell["merge"]["gridSpan"])
        self.assertEqual(72, cell["grid_slot_bbox_pt"]["width"])
        self.assertIsNone(cell["bbox_pt"])
        self.assertIsNone(cell["structural_bbox_pt"])
        self.assertEqual("unverified", cell["content_bbox_status"])

    def test_negative_cell_content_remains_negative(self):
        grid = self.inspect(table(margin_left=254000, margin_right=254000))["slides"][0]["shapes"][0]["table"]
        cell = grid["cells"][1]
        self.assertEqual(-4, cell["content_bbox_pt"]["width"])  # 36 - 20 - 20.
        self.assertEqual("invalid", cell["content_bbox_status"])
        self.assertTrue(cell["limitations"])

    def test_vertical_cell_text_and_nested_table_transform_remain_unverified(self):
        contract = rule("text_alignment", objects=[87], horizontal="left", vertical="top")
        report = self.inspect(table(cell_orientation='vert="vert"'), contract)
        self.outcome(report, "unverified")
        self.assertIsNone(report["slides"][0]["shapes"][0]["table"]["cells"][0]["content_bbox_pt"])
        nested = self.inspect(group(table()), contract)
        self.outcome(nested, "unverified")
        child = nested["slides"][0]["shapes"][0]["children"][0]
        self.assertEqual([90], child["ancestor_ids"])
        self.assertEqual([72, 36], child["table"]["column_widths_pt"])
        self.assertIsNone(child["table"]["grid_bbox_pt"])

    def test_straight_arrow_endpoints_units_and_connection_metadata(self):
        report = self.inspect(node_a() + node_b() + connector(80, (2184400, 711200, 254000, 0)), edge_rule())
        self.outcome(report, "pass")
        line = report["slides"][0]["shapes"][2]["line"]
        self.assertEqual({"start": [172, 56], "end": [192, 56]}, line["endpoints_pt"])
        self.assertEqual(0.75, line["width_pt"])
        self.assertEqual({"shape_id": 41, "site_index": 3}, line["attachments"]["start"])
        self.assertEqual({"shape_id": 7, "site_index": 1}, line["attachments"]["end"])

    def test_flip_and_head_arrow_reverse_native_traversal(self):
        line = connector(80, (2184400, 711200, 254000, 0),
                         transform='flipH="1"', head="triangle", tail="none", start_id=7, end_id=41)
        report = self.inspect(node_a() + node_b() + line, edge_rule())
        self.outcome(report, "pass")
        obj = report["slides"][0]["shapes"][2]["line"]
        self.assertEqual({"start": [192, 56], "end": [172, 56]}, obj["endpoints_pt"])
        route = report["contracts"]["rules"][0]["ordered_route"][0]
        self.assertEqual([172, 56], route["start_pt"])
        self.assertEqual([192, 56], route["end_pt"])
        self.assertEqual("end", route["native_start_key"])

    def test_vertical_and_double_flips_preserve_geometric_direction(self):
        source = shape(41, (0, 0, 254000, 254000))
        cases = [
            (shape(7, (0, 508000, 254000, 254000)),
             connector(80, (127000, 254000, 0, 254000), transform='flipV="1"',
                       head="triangle", tail="none", start_id=7, end_id=41),
             edge_rule(source_port="bottom", target_port="top"),
             {"start": [10, 40], "end": [10, 20]}),
            (shape(7, (508000, 508000, 254000, 254000)),
             connector(80, (254000, 127000, 254000, 508000), transform='flipH="1" flipV="1"',
                       head="triangle", tail="none", start_id=7, end_id=41),
             edge_rule(), {"start": [40, 50], "end": [20, 10]}),
        ]
        for target, line, contract, endpoints in cases:
            with self.subTest(endpoints=endpoints):
                report = self.inspect(source + target + line, contract)
                self.outcome(report, "pass")
                self.assertEqual(endpoints, report["slides"][0]["shapes"][2]["line"]["endpoints_pt"])

    def test_arrow_direction_and_attachment_contradictions_fail(self):
        backward = connector(80, (2184400, 711200, 254000, 0), head="triangle", tail="none")
        self.outcome(self.inspect(node_a() + node_b() + backward, edge_rule()), "fail")
        bad_attachment = connector(80, (2184400, 711200, 254000, 0), end_id=99)
        report = self.inspect(node_a() + node_b() + bad_attachment, edge_rule())
        self.outcome(report, "fail")
        failed = [c for c in report["contracts"]["rules"][0]["checks"] if c["status"] == "fail"]
        self.assertEqual(["target_attachment_id"], [c["check"] for c in failed])

    def test_tangential_arrival_fails_even_at_exact_target_port(self):
        target = shape(7, (2311400, 711200, 254000, 254000))  # Top midpoint=(192,56).
        line = connector(80, (2184400, 711200, 254000, 0))
        report = self.inspect(node_a() + target + line, edge_rule(target_port="top"))
        self.outcome(report, "fail")
        checks = {c["check"]: c for c in report["contracts"]["rules"][0]["checks"]}
        self.assertEqual(0, checks["target_endpoint"]["gap_pt"])
        self.assertEqual(0, checks["target_arrival_direction"]["expected_normal_component_pt"])
        self.assertEqual("fail", checks["target_arrival_direction"]["status"])

    def test_ordered_multisegment_route_and_discontinuity(self):
        first = connector(80, (2184400, 711200, 127000, 0), tail="none", end_id=None)
        second = connector(81, (2311400, 711200, 0, 508000), tail="none", start_id=None, end_id=None)
        final = connector(82, (2311400, 1219200, 127000, 0), start_id=None)
        contract = edge_rule()
        contract.pop("connector")
        contract["connectors"] = [80, 81, 82]
        report = self.inspect(node_a() + node_b(y=965200) + first + second + final, contract)
        self.outcome(report, "pass")
        route = report["contracts"]["rules"][0]["ordered_route"]
        self.assertEqual([[172, 56], [182, 56], [182, 96]], [s["start_pt"] for s in route])
        self.assertEqual([[182, 56], [182, 96], [192, 96]], [s["end_pt"] for s in route])
        broken = connector(81, (2311400, 711200, 0, 254000), tail="none", start_id=None, end_id=None)
        bad = self.inspect(node_a() + node_b(y=965200) + first + broken + final, contract)
        self.outcome(bad, "fail")
        self.assertTrue(any(c.get("gap_pt") == 20 and c["status"] == "fail"
                            for c in bad["contracts"]["rules"][0]["checks"]))

    def test_ambiguous_short_segment_does_not_get_arbitrary_traversal(self):
        first = connector(80, (2178050, 711200, 6350, 0), tail="none", end_id=None)
        final = connector(81, (2184400, 711200, 254000, 0), start_id=None)
        contract = edge_rule()
        contract.pop("connector")
        contract["connectors"] = [80, 81]
        report = self.inspect(node_a() + node_b() + first + final, contract)
        self.outcome(report, "unverified")
        measured = report["contracts"]["rules"][0]
        self.assertNotIn("ordered_route", measured)
        self.assertEqual([172, 56], measured["resolved_tail_route"][0]["start_pt"])

    def test_rotation_custom_paths_and_nested_ids_never_silently_pass(self):
        aligned = rule("alignment", objects=[41, 7], edge="top")
        rotated = shape(41, (914400, 457200, 1270000, 508000), transform='rot="2700000"')
        custom = shape(41, (914400, 457200, 1270000, 508000), geometry=(
            '<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
            '<a:rect l="0" t="0" r="r" b="b"/><a:pathLst/></a:custGeom>'))
        for label, contents in (("rotated", rotated), ("custom", custom), ("nested", group(node_a()))):
            with self.subTest(kind=label):
                report = self.inspect(contents + node_b(), aligned)
                self.outcome(report, "unverified")
        self.outcome(self.inspect(node_a() + node_b() + connector(
            80, (2184400, 711200, 254000, 0), preset="bentConnector3"), edge_rule()), "unverified")

    def test_inherited_arrow_decorations_are_unverified(self):
        style = '<p:style><a:lnRef idx="1"><a:schemeClr val="accent1"/></a:lnRef></p:style>'
        line = connector(80, (2184400, 711200, 254000, 0), head=None, tail=None, style=style)
        report = self.inspect(node_a() + node_b() + line, edge_rule())
        self.outcome(report, "unverified")
        self.assertIsNone(report["slides"][0]["shapes"][2]["line"]["tailEnd"]["type"])

    def test_missing_ids_empty_contracts_and_duplicate_native_structure(self):
        self.outcome(self.inspect(node_a()), "not_requested")
        self.outcome(self.inspect(node_a(), rule("alignment", objects=[41, 99], edge="left")), "fail")
        duplicate = self.inspect(node_a() + node_a())
        self.assertEqual("fail", duplicate["structure"]["status"])
        self.assertEqual(1, duplicate["structure"]["counts"]["duplicate_native_shape_ids"])
        malformed = text_body(paragraphs='<a:p><a:pPr/><a:pPr/><a:r><a:t>Extra</a:t></a:r></a:p>')
        report = self.inspect(node_a(malformed))
        self.assertEqual(1, report["structure"]["counts"]["paragraphs_with_multiple_pPr"])
        self.assertEqual(1, INSPECTOR.exit_code(report))

    def test_contract_schema_rejects_ignored_fields_and_nonfinite_values(self):
        base = rule("gap", first=41, second=7, axis="x", minimum_pt=20)
        for invalid in (
            {"rules": [], "extra": "ignored"},
            document(dict(base, minimum_pt=float("nan"))),
            document(dict(base, minimum_pt=float("inf"))),
            document(dict(base, minimum_pt=-1)),
            document(dict(base, first=True)),
            document(dict(base, invented="ignored")),
            document(dict(base, type="unknown")),
            document(base, tolerance=-0.1),
        ):
            with self.subTest(contract=invalid), self.assertRaises(INSPECTOR.InputError):
                INSPECTOR.validate_contracts(invalid)

    def test_source_hashes_before_after_and_snapshot_binding(self):
        original = package({9: node_a()})
        changed = package({9: node_b()})
        with patch.object(Path, "read_bytes", side_effect=[original, original]):
            report = INSPECTOR.inspect_pptx("example.pptx")
        self.assertEqual(hashlib.sha256(original).hexdigest(), report["source_integrity"]["sha256_before"])
        self.assertEqual(report["source_integrity"]["sha256_before"], report["source_integrity"]["sha256_after"])
        self.assertTrue(report["source_integrity"]["unchanged"])
        with patch.object(Path, "read_bytes", side_effect=[original, changed]):
            report = INSPECTOR.inspect_pptx("example.pptx")
        self.assertEqual("fail", report["status"])
        self.assertFalse(report["source_integrity"]["unchanged"])
        self.assertEqual(41, report["slides"][0]["shapes"][0]["id"])
        self.assertEqual(hashlib.sha256(original).hexdigest(), report["artifact_sha256"])
        self.assertEqual(hashlib.sha256(changed).hexdigest(), report["source_integrity"]["sha256_after"])

    def test_cli_determinism_exit_codes_and_read_only_alias_protection(self):
        with tempfile.TemporaryDirectory(prefix="layout-test-", dir=FIXTURES_DIR) as temp:
            root = Path(temp).resolve()
            deck, rules, output = root / "deck.pptx", root / "rules.json", root / "report.json"
            data = package({9: node_a(text_body()) + node_b()})
            deck.write_bytes(data)
            rules.write_text(json.dumps(document(rule("alignment", objects=[41, 7], edge="top"))), encoding="utf-8")
            command = [sys.executable, "-B", str(SCRIPT), str(deck), "--contracts", str(rules), "--output", str(output)]
            first = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual("", first.stdout)
            saved = output.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(saved, output.read_bytes())
            self.assertEqual(hashlib.sha256(data).hexdigest(), json.loads(saved)["source_integrity"]["sha256_after"])
            for desired_exit, contract in (
                (1, document(rule("alignment", objects=[41, 7], edge="left"))),
                (3, document(rule("text_alignment", objects=[7], horizontal="left"))),
                (2, {"rules": [{"type": "unknown"}]}),
            ):
                rules.write_text(json.dumps(contract), encoding="utf-8")
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(desired_exit, result.returncode, result.stderr)
                self.assertIsInstance(json.loads(output.read_text()), dict)
            for alias_kind in ("same", "symlink", "hardlink"):
                alias = deck
                if alias_kind != "same":
                    alias = root / f"{alias_kind}.pptx"
                    if alias_kind == "symlink":
                        alias.symlink_to(deck)
                    else:
                        os.link(deck, alias)
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(deck), "--output", str(alias)],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertEqual("error", json.loads(result.stdout)["status"])
                self.assertEqual(data, deck.read_bytes())
            self.assertEqual(data, deck.read_bytes())

    def test_cli_rejects_duplicate_contract_keys_without_modifying_inputs(self):
        with tempfile.TemporaryDirectory(prefix="layout-test-", dir=FIXTURES_DIR) as temp:
            root = Path(temp).resolve()
            deck, rules = root / "deck.pptx", root / "rules.json"
            deck.write_bytes(package({9: node_a()}))
            rules.write_text('{"rules": [], "rules": []}', encoding="utf-8")
            original = rules.read_bytes()
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(deck), "--contracts", str(rules)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertEqual("error", json.loads(result.stdout)["status"])
            self.assertEqual(original, rules.read_bytes())


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []

    def startTest(self, test):
        super().startTest(test)
        self.current = {"name": test._testMethodName, "status": "pass"}

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.current.update(status="fail", detail=self._exc_info_to_string(error, test))

    def addError(self, test, error):
        super().addError(test, error)
        self.current.update(status="error", detail=self._exc_info_to_string(error, test))

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error:
            self.current.update(status="fail", detail=self._exc_info_to_string(error, test))

    def stopTest(self, test):
        self.cases.append(self.current)
        super().stopTest(test)


def main():
    global FIXTURES_DIR
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fixtures-dir", type=Path)
    args = parser.parse_args()
    if args.fixtures_dir:
        args.fixtures_dir.mkdir(parents=True, exist_ok=True)
        FIXTURES_DIR = str(args.fixtures_dir)
    if args.output:
        for protected in (SCRIPT, Path(__file__)):
            if args.output.resolve() == protected.resolve() or (
                    args.output.exists() and args.output.samefile(protected)):
                parser.error("--output must not overwrite either script")
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(InspectorTests))
    evidence = {
        "status": "pass" if result.wasSuccessful() else "fail",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "cases": result.cases,
        "scripts": [{"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                    for path in (SCRIPT, Path(__file__))],
        "scope": "Synthetic native storage and CLI contracts only; no rendering, glyph-fit, optical or drag-editability proof.",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
