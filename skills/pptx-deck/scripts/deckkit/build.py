"""Build a PPTX from a deck spec (deck.yaml) and a brand profile."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.util import Pt

from .brand import Brand, load_brand
from .canvas import Canvas, Warnings
from .layouts import LAYOUTS

ROLE = {"cover": "cover", "section": "section", "closing": "closing"}
TITLE_TYPES = (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)
SUBTITLE_TYPES = (PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY)


class Context:
    def __init__(self, brand: Brand, deck_dir: Path, prs, warnings: Warnings):
        self.brand = brand
        self.deck_dir = deck_dir
        self.prs = prs
        self.warnings = warnings
        self.template = bool(brand.get("template.path"))
        self.total = 0
        self._slide_layout = None

    # -- assets -------------------------------------------------------------
    def asset(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (self.deck_dir / p)

    def icon(self, name: str, c: Canvas) -> Path | None:
        """Resolve an icon from the deck folder first, then the brand icon library."""
        direct = self.asset(name)
        if direct.suffix and direct.exists():
            return direct
        root = self.brand.path("icons.path")
        if root and root.exists():
            for fmt in self.brand.get("icons.formats", ["png", "svg"]):
                hits = sorted(root.rglob(f"{name}.{fmt}")) or sorted(root.rglob(f"*{name}*.{fmt}"))
                if hits:
                    return hits[0]
        c.warn(f"icon '{name}' not found in the deck folder or brand icons.path; "
               "run scripts/find_icon.py to search")
        return None

    # -- template placeholders ------------------------------------------------
    def title_placeholder(self, c: Canvas, title: str, subtitle: str | None = None) -> bool:
        """Fill the template's title placeholder when the slide layout has one."""
        if not (self.template and self.brand.get("template.use_placeholders", True)):
            return False
        title_ph = next((ph for ph in c.slide.placeholders
                         if ph.placeholder_format.type in TITLE_TYPES), None)
        if title_ph is None:
            return False
        title_ph.text_frame.text = title
        if subtitle:
            sub = next((ph for ph in c.slide.placeholders
                        if ph.placeholder_format.type in SUBTITLE_TYPES), None)
            if sub is not None:
                sub.text_frame.text = subtitle
        return True

    # -- chrome ---------------------------------------------------------------
    def background(self, c: Canvas, role: str, spec: dict):
        b = self.brand
        bg = copy.deepcopy(b.get(f"backgrounds.{role}") or {})
        if spec.get("dark") is True:
            bg = {"color": "dark", "image": None}
        if self.template and not spec.get("dark") and not b.get("template.draw_backgrounds"):
            return False  # the master supplies the background
        image = b.path(f"backgrounds.{role}.image") if bg.get("image") else None
        color = bg.get("color") or "surface"
        if image:
            c.image(image, 0, 0, b.width, b.height, fit="cover", name="Background")
        elif not (role == "content" and b.hex(color) == "FFFFFF" and not self.template):
            fill = c.slide.background.fill  # native slide background, editable in Format Background
            fill.solid()
            fill.fore_color.rgb = b.rgb(color)
        return b.is_dark(color) if not image else bool(bg.get("dark"))

    def cover_logo(self, c: Canvas):
        if self.template and not self.brand.get("template.draw_chrome"):
            return
        logo = self.brand.path("chrome.logo.path_on_dark" if c.dark else "chrome.logo.path") \
            or self.brand.path("chrome.logo.path")
        if logo:
            w = float(self.brand.get("chrome.cover_logo_width", 96))
            c.image(logo, self.brand.content_left, 40, w, w * 0.5, name="Logo")

    def footer(self, c: Canvas, number: int):
        b = self.brand
        if self.template and not b.get("template.draw_chrome"):
            return
        y = float(b["layout.footer_y"])
        x0, x1 = b.content_left, b.content_right
        size = b["type.label"]
        if b.get("chrome.footer_rule"):
            c.line(x0, y - 8, x1, y - 8, color="line", width=0.5, name="Footer rule")
        right = x1
        logo = b.path("chrome.logo.path")
        lw = float(b.get("chrome.logo.width", 64))
        pos = b.get("chrome.logo.position", "footer-right")
        if logo and pos == "footer-right":
            c.image(logo, x1 - lw, y - 2, lw, size * 2, name="Logo")
            right = x1 - lw - 16
        elif logo and pos == "footer-left":
            c.image(logo, x0, y - 2, lw, size * 2, name="Logo")
            x0 += lw + 16
        elif logo and pos == "top-right":
            c.image(logo, x1 - lw, 24, lw, size * 2.4, name="Logo")
        if b.get("chrome.footer_text"):
            c.text(x0, y, 520, size * 1.5, b["chrome.footer_text"], size="label", color=c.muted,
                   check_fit=False, name="Footer")
        if b.get("chrome.page_numbers"):
            c.text(right - 60, y, 60, size * 1.5, str(number), size="label", font="mono",
                   color=c.muted, align="right", check_fit=False, name="Page number")

    # -- slides ---------------------------------------------------------------
    def new_slide(self, role: str):
        layouts = list(self.prs.slide_layouts)
        if self.template:
            wanted = self.brand.get(f"template.layouts.{role}") or self.brand.get("template.layouts.blank")
            for lay in layouts:
                if wanted and lay.name == wanted:
                    return self.prs.slides.add_slide(lay)
            if wanted:
                self.warnings.add(0, f"template layout '{wanted}' not found; using the last layout")
        blank = next((lay for lay in layouts if lay.name.lower() in ("blank", "빈 화면")),
                     layouts[min(6, len(layouts) - 1)])
        return self.prs.slides.add_slide(blank)


def _clear_slides(prs):
    sld_ids = prs.slides._sldIdLst
    for sld_id in list(sld_ids):
        prs.part.drop_rel(sld_id.rId)
        sld_ids.remove(sld_id)


def _remove_empty_placeholders(slide):
    for ph in list(slide.placeholders):
        if ph.has_text_frame and not ph.text_frame.text.strip():
            ph._element.getparent().remove(ph._element)


APP_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    '<Application>deckkit (python-pptx)</Application><PresentationFormat>{fmt}</PresentationFormat>'
    '<Slides>{slides}</Slides><Notes>{notes}</Notes></Properties>')


def _rewrite_app_props(path: Path, slides: int, notes: int, width: float, height: float):
    """Replace docProps/app.xml. python-pptx never updates it, so it would keep the
    base template's slide count, format and company name."""
    import os
    import tempfile
    import zipfile
    fmt = "On-screen Show (16:9)" if abs(width / height - 16 / 9) < 0.01 else "Custom"
    xml = APP_XML.format(fmt=fmt, slides=slides, notes=notes).encode("utf-8")
    fd, tmp = tempfile.mkstemp(suffix=".pptx", dir=str(path.parent))
    os.close(fd)
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = xml if item.filename == "docProps/app.xml" else src.read(item.filename)
            dst.writestr(item, data)
    os.replace(tmp, path)


def build(deck_path: str | Path, out_path: str | Path, brand_path: str | Path | None = None) -> dict:
    deck_path = Path(deck_path)
    spec = yaml.safe_load(deck_path.read_text(encoding="utf-8"))
    meta = spec.get("meta", {})
    if brand_path is None and meta.get("brand"):
        brand_path = deck_path.parent / meta["brand"]
    brand = load_brand(brand_path)
    warnings = Warnings()

    template = brand.path("template.path")
    if template:
        prs = Presentation(str(template))
        _clear_slides(prs)
    else:
        prs = Presentation()
        prs.slide_width, prs.slide_height = Pt(brand.width), Pt(brand.height)
    if abs(prs.slide_width - Pt(brand.width)) > Pt(1) or abs(prs.slide_height - Pt(brand.height)) > Pt(1):
        warnings.add(0, "template slide size differs from brand canvas; run extract_brand.py to sync canvas values")
    ctx = Context(brand, deck_path.parent, prs, warnings)
    slides = spec.get("slides", [])
    ctx.total = len(slides)

    for i, s in enumerate(slides, start=1):
        name = s.get("layout", "bullets")
        fn = LAYOUTS.get(name)
        if fn is None:
            warnings.add(i, f"unknown layout '{name}'", "ERROR")
            continue
        role = ROLE.get(name, "content")
        slide = ctx.new_slide(role if name in ROLE else ("blank" if name == "image" and s.get("full_bleed") else "content"))
        c = Canvas(slide, brand, i, warnings)
        c.language = str(meta.get("language") or brand.get("copy.default_language", "en"))
        bg_role = role if role != "content" else ("cover" if s.get("dark") else "content")
        c.dark = bool(ctx.background(c, bg_role, s))
        fn(c, s, ctx)
        if not fn.structural and not s.get("no_footer"):
            ctx.footer(c, i)
        if ctx.template:
            _remove_empty_placeholders(slide)
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = str(s["notes"]).strip()
        else:
            warnings.add(i, "no speaker notes")

    # Reset document properties: the base template (python-pptx's default or a company
    # file) carries its own author, revision and dates, which must not leak into decks.
    import datetime as _dt
    props = prs.core_properties
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0, tzinfo=None)
    author = str(meta.get("author") or "")
    props.title = str(meta.get("title") or "")
    props.subject = str(meta.get("objective") or "")
    props.author = author
    props.last_modified_by = author
    props.keywords = props.comments = props.category = ""
    props.revision = 1
    props.created = props.modified = now
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    notes = sum(1 for s in prs.slides if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())
    _rewrite_app_props(out_path, len(prs.slides), notes, brand.width, brand.height)
    report = {"output": str(out_path), "slides": len(slides), "brand": brand.get("name"),
              "warnings": warnings.items}
    out_path.with_suffix(".build.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                                    encoding="utf-8")
    return report
