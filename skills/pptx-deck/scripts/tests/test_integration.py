"""Regression tests for cross-track behaviour: measurement, big titles, bullet lists."""
import shutil
import sys
from pathlib import Path

import pytest
import yaml
from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from deckkit import build, load_brand  # noqa: E402
from deckkit import measure  # noqa: E402
from lint_deck import lint  # noqa: E402

CONTRACT = {"audience": "a", "objective": "o", "desired_action": "d"}


def deck(tmp_path, slides, brand=None):
    p = tmp_path / "d.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": CONTRACT, "slides": slides}, allow_unicode=True), encoding="utf-8")
    out = tmp_path / "d.pptx"
    report = build(p, out, brand)
    return Presentation(str(out)), report


def test_heuristic_fallback_without_fonts():
    measure._FILES.clear()
    assert measure.text_width("abc", 10) == pytest.approx(sum(measure.char_em(c) for c in "abc") * 10)


@pytest.mark.skipif(not shutil.which("fc-match"), reason="fontconfig not available")
def test_real_font_measurement_tracks_the_face(tmp_path):
    narrow, wide = tmp_path / "narrow.yaml", tmp_path / "wide.yaml"
    narrow.write_text("fonts: {body: {latin: Liberation Serif}}\n", encoding="utf-8")
    wide.write_text("fonts: {body: {latin: DejaVu Sans}}\n", encoding="utf-8")
    text = "Most blockers surface only after the branch is cut"
    measure.set_fonts(load_brand(narrow))
    w_narrow = measure.text_width(text, 20)
    measure.set_fonts(load_brand(wide))
    w_wide = measure.text_width(text, 20)
    assert w_wide > w_narrow * 1.1
    measure.set_fonts(load_brand())


def test_brand_font_file_overrides_fontconfig(tmp_path):
    match = measure._match("DejaVu Sans")
    if not match:
        pytest.skip("fontconfig not available")
    brand = tmp_path / "b.yaml"
    brand.write_text(f"fonts: {{body: {{latin: Not A Real Face, file: '{match}'}}}}\n", encoding="utf-8")
    measure.set_fonts(load_brand(brand))
    assert measure._FILES["body"][0] == match
    measure.set_fonts(load_brand())


def test_big_titles_grow_upward(tmp_path):
    prs, _ = deck(tmp_path, [
        {"layout": "cover", "title": "A cover title", "subtitle": "Sub", "notes": "n"},
        {"layout": "statement", "text": "One sentence to keep", "notes": "n"}])
    for slide, name in ((prs.slides[0], "Title"), (prs.slides[1], "Statement")):
        box = next(s for s in slide.shapes if s.name == name)
        assert box.text_frame.vertical_anchor == MSO_ANCHOR.BOTTOM


def test_bullets_are_one_text_box_with_paragraphs(tmp_path):
    prs, report = deck(tmp_path, [{
        "layout": "bullets", "title": "Three points carry the decision today", "notes": "n",
        "bullets": ["First point", {"text": "Second point", "sub": ["detail a", "detail b"]}, "Third"]}])
    boxes = [s for s in prs.slides[0].shapes if s.name == "Bullets"]
    assert len(boxes) == 1
    assert [p.text for p in boxes[0].text_frame.paragraphs] == [
        "First point", "Second point", "detail a", "detail b", "Third"]
    assert not [w for w in report["warnings"] if w["level"] == "ERROR"]


def test_summary_expected_only_in_sectioned_decks(tmp_path):
    body = [{"layout": "bullets", "title": f"Finding {k} changes the plan for us", "bullets": ["a"],
             "notes": "n"} for k in range(10)]
    p = tmp_path / "c.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": CONTRACT, "slides": body}), encoding="utf-8")
    assert not any("no summary" in f["message"] for f in lint(p))


def test_matrix_commentary_is_supported(tmp_path):
    spec = {"layout": "matrix", "title": "Two options combine high impact with low effort", "notes": "n",
            "x": {"label": "Ease", "low": "Hard", "high": "Easy"},
            "y": {"label": "Value", "low": "Low", "high": "High"},
            "quadrants": [{"name": n} for n in ("A", "B", "C", "D")],
            "commentary": {"text": "Start with B."}}
    p = tmp_path / "m.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": CONTRACT, "slides": [spec]}), encoding="utf-8")
    assert not any("commentary has no effect" in f["message"] for f in lint(p))


# -- review regressions ------------------------------------------------------

def chart_slide(chart, **extra):
    return {"layout": "chart", "title": "The value changed over the four periods", "notes": "n",
            "source": "s", "chart": chart, **extra}


def test_numeric_highlight_is_an_index(tmp_path):
    from deckkit import exhibits
    assert exhibits.category_index([1, 2, 3, 4, 5], 3) == 3
    assert exhibits.category_index([1, 2, 3, 4, 5], "3") == 2
    assert exhibits.category_index(["a", "b"], 5) is None


def test_line_axis_spans_narrow_data_bars_keep_zero():
    from deckkit import exhibits
    lo, hi = exhibits.data_extent("line", [{"name": "s", "values": [95.1, 96.3, 97.8, 99.2]}])
    assert lo > 90 and hi < 101
    lo, _ = exhibits.data_extent("column", [{"name": "s", "values": [95.1, 99.2]}])
    assert lo == 0
    lo, _ = exhibits.data_extent("line", [{"name": "s", "values": [3, 40]}])
    assert lo == 0  # data close to zero keeps the zero baseline


def test_own_series_palette_is_kept(tmp_path):
    from deckkit import exhibits
    own = tmp_path / "b.yaml"
    own.write_text("colors: {series: [112233, 445566, 778899]}\n", encoding="utf-8")
    assert exhibits.series_mode(load_brand(own)) == "palette"
    assert exhibits.series_mode(load_brand()) == "ramp"
    forced = tmp_path / "f.yaml"
    forced.write_text("colors: {series: [112233, 445566], series_mode: ramp}\n", encoding="utf-8")
    assert exhibits.series_mode(load_brand(forced)) == "ramp"


@pytest.mark.parametrize("bad", [
    {"type": "column", "categories": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}], "min": 100, "max": 0},
    {"type": "waterfall", "start": 100, "steps": [{"label": "x", "value": 3}]},
    {"type": "waterfall", "start": {"label": "S"}, "steps": [{"label": "x", "value": 3}]},
    {"type": "line", "categories": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}], "estimates": "b"},
])
def test_malformed_chart_keys_are_lint_errors(tmp_path, bad):
    p = tmp_path / "d.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": CONTRACT, "slides": [chart_slide(bad)]}), encoding="utf-8")
    assert any(f["level"] == "ERROR" for f in lint(p))  # reported, no traceback


def test_malformed_story_keys_are_lint_errors(tmp_path):
    slides = [{"layout": "section", "number": 1, "title": "One"},
              {"layout": "bullets", "title": "A point that closes the argument here", "bullets": ["a"],
               "notes": "n", "next_steps": "Do X"},
              {"layout": "summary", "title": "The summary of the argument in one line", "notes": "n",
               "blocks": [{"section": "two", "points": ["a"]}, {"heading": "H", "points": ["b"]}]}]
    p = tmp_path / "d.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": CONTRACT, "slides": slides}), encoding="utf-8")
    msgs = [f["message"] for f in lint(p) if f["level"] == "ERROR"]
    assert any("next_steps" in m for m in msgs) and any("section is a number" in m for m in msgs)


def test_regional_language_code_is_korean(tmp_path):
    from deckkit.brand import deck_language
    assert deck_language({"language": "ko-KR"}, load_brand()) == "ko"
    assert deck_language({"language": "KO_kr"}, load_brand()) == "ko"
    prs, _ = deck(tmp_path, [chart_slide({"type": "column", "categories": ["a", "b"],
                                          "series": [{"name": "s", "values": [1, 2]}]})],)
    meta = {**CONTRACT, "language": "ko-KR"}
    p = tmp_path / "k.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": meta, "slides": [chart_slide(
        {"type": "column", "categories": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}]},
        source="예시 데이터")]}, allow_unicode=True), encoding="utf-8")
    build(p, tmp_path / "k.pptx")
    texts = [s.text_frame.text for s in Presentation(str(tmp_path / "k.pptx")).slides[0].shapes
             if s.has_text_frame]
    assert any(t.startswith("출처") for t in texts)


def test_next_steps_without_items_draws_no_band(tmp_path):
    prs, report = deck(tmp_path, [{"layout": "bullets", "title": "A point that closes the argument",
                                   "bullets": ["a"], "notes": "n", "next_steps": {"label": "X"}}])
    assert not any(s.name == "Next steps" for s in prs.slides[0].shapes)
    assert not any("overflow" in w["message"] for w in report["warnings"])


def test_mono_role_uses_monospace_face():
    m = measure._match("monospace")
    if not m:
        pytest.skip("fontconfig not available")
    measure.set_fonts(load_brand())
    assert measure.text_width("iiii", 10, "mono") == pytest.approx(measure.text_width("MMMM", 10, "mono"), rel=0.05)


# -- second review ------------------------------------------------------------

def test_shipped_palette_constant_matches_the_shipped_brand_file():
    from deckkit import exhibits
    shipped = Path(__file__).resolve().parents[2] / "brand" / "brand.yaml"
    data = yaml.safe_load(shipped.read_text(encoding="utf-8"))
    # if this fails after an intentional palette change, update SHIPPED_SERIES too
    assert [str(v).upper() for v in data["colors"]["series"]] == exhibits.SHIPPED_SERIES


def test_editing_the_brand_file_in_place_keeps_its_palette():
    from deckkit import exhibits
    from deckkit.brand import Brand
    brand = load_brand()
    edited = Brand({**brand.data, "colors": {**brand.data["colors"], "series": ["C8102E", "00843D"]}},
                   brand.root)  # same file location as brand/brand.yaml, different palette
    assert exhibits.series_mode(edited) == "palette"
    assert exhibits.series_colors(edited, "column", 2)[:2] == ["C8102E", "00843D"]


def test_extracted_brand_uses_its_theme_palette(tmp_path):
    tpl = tmp_path / "t.pptx"
    Presentation().save(str(tpl))
    out = tmp_path / "brand" / "brand.yaml"
    import subprocess
    subprocess.run([sys.executable, str(SCRIPTS / "extract_brand.py"), str(tpl), "-o", str(out)],
                   check=True, capture_output=True)
    assert load_brand(out).get("colors.series_mode") == "palette"


@pytest.mark.parametrize("chart", [
    {"type": "column", "categories": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}],
     "annotations": {"kind": "ref_line", "value": 2}},
    {"type": "column", "categories": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}],
     "annotations": ["ref_line"]},
    {"panels": {"type": "column"}},
])
def test_malformed_annotations_and_panels_are_lint_errors(tmp_path, chart):
    p = tmp_path / "d.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": CONTRACT, "slides": [chart_slide(chart)]}), encoding="utf-8")
    assert any(f["level"] == "ERROR" for f in lint(p))


def test_single_string_items_are_one_item_not_characters(tmp_path):
    prs, _ = deck(tmp_path, [{"layout": "bullets", "title": "A point that closes the argument",
                              "bullets": ["a"], "notes": "n", "next_steps": {"items": "Pilot"}}])
    names = [s.name for s in prs.slides[0].shapes]
    assert names.count("Next step 1") == 1 and "Next step 2" not in names
    from deckkit.layouts import bullet_items
    assert bullet_items("alpha") == [("alpha", [])]


def test_unquoted_year_gets_an_index_hint(tmp_path):
    ch = {"type": "column", "categories": [2024, 2025, 2026, 2027],
          "series": [{"name": "s", "values": [1, 2, 3, 4]}], "highlight": 2026}
    p = tmp_path / "d.deck.yaml"
    p.write_text(yaml.safe_dump({"meta": CONTRACT, "slides": [chart_slide(ch)]}), encoding="utf-8")
    assert any('write "2026"' in f["message"] for f in lint(p))


def test_general_format_keeps_small_values():
    from deckkit import exhibits
    assert exhibits.format_number(0.0014) == "0.0014"
    assert exhibits.format_number(0.0145) == "0.0145"
    assert exhibits.format_number(42.0) == "42"
