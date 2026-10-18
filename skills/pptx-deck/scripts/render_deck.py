#!/usr/bin/env python3
"""Render a PPTX to PNG slides and a contact sheet for visual QA.

    python scripts/render_deck.py out/deck.pptx [--out out/deck.render] [--dpi 110] [--slides 3,5-7]

Needs LibreOffice (`soffice`) and Poppler (`pdftoppm`). Output:
    <out>/deck.pdf, <out>/slide-01.png ..., <out>/contact.png

LibreOffice is an approximation of PowerPoint: font substitution and line
breaks can differ. Final sign-off belongs in the application your audience uses.
"""
import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_range(text: str | None, total: int) -> list[int]:
    if not text:
        return list(range(1, total + 1))
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [n for n in out if 1 <= n <= total]


def to_pdf(pptx: Path, out: Path) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("LibreOffice not found: install it (soffice) to render slides")
    with tempfile.TemporaryDirectory() as profile:
        # a private profile avoids clashing with a running LibreOffice instance
        subprocess.run([soffice, f"-env:UserInstallation=file://{profile}", "--headless",
                        "--convert-to", "pdf", "--outdir", str(out), str(pptx)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    pdf = out / (pptx.stem + ".pdf")
    if not pdf.exists():
        sys.exit(f"conversion failed: {pdf} was not produced")
    return pdf


def to_png(pdf: Path, out: Path, dpi: int) -> list[Path]:
    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm not found: install poppler-utils")
    for old in out.glob("slide-*.png"):
        old.unlink()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(out / "slide")], check=True)
    pngs = sorted(out.glob("slide-*.png"))
    width = len(str(len(pngs)))
    renamed = []
    for p in pngs:  # normalise names to slide-01.png regardless of poppler padding
        n = int(p.stem.split("-")[-1])
        target = out / f"slide-{n:0{max(2, width)}d}.png"
        p.rename(target)
        renamed.append(target)
    return sorted(renamed)


def contact_sheet(pngs: list[Path], out: Path, cols: int = 4) -> Path:
    from PIL import Image, ImageDraw
    thumbs = [Image.open(p).convert("RGB") for p in pngs]
    tw = 480
    th = round(thumbs[0].height * tw / thumbs[0].width)
    gap, label = 16, 22
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * (tw + gap) + gap, rows * (th + gap + label) + gap), "#E9EBEE")
    draw = ImageDraw.Draw(sheet)
    for i, (img, path) in enumerate(zip(thumbs, pngs)):
        x = gap + (i % cols) * (tw + gap)
        y = gap + (i // cols) * (th + gap + label)
        draw.text((x, y), path.stem.replace("slide-", ""), fill="#333333")
        sheet.paste(img.resize((tw, th)), (x, y + label))
    target = out / "contact.png"
    sheet.save(target)
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("--out", help="output folder (default: <pptx without suffix>.render)")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--slides", help="subset for the contact sheet, e.g. 3,5-7")
    args = ap.parse_args()
    pptx = Path(args.pptx).resolve()
    out = Path(args.out) if args.out else pptx.with_suffix(".render")
    out.mkdir(parents=True, exist_ok=True)
    pdf = to_pdf(pptx, out)
    pngs = to_png(pdf, out, args.dpi)
    chosen = [pngs[n - 1] for n in parse_range(args.slides, len(pngs))]
    sheet = contact_sheet(chosen, out)
    print(f"{len(pngs)} slides rendered to {out}")
    print(f"contact sheet: {sheet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
