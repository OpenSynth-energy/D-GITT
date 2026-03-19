#!/usr/bin/env python3
"""Generate a PDF version of the challenge specification using reportlab.

Equations are rendered as PNG images via matplotlib's mathtext engine,
giving proper LaTeX-style output (subscripts, Greek letters, fractions, etc.).
"""

import io
import os
import re
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import mathtext

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, Color
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image,
    Flowable,
)

MD_FILE = "challenge_specification.md"
PDF_FILE = "challenge_specification.pdf"

WIDTH, HEIGHT = A4
GREY = Color(0.4, 0.4, 0.4)
LIGHT_GREY = Color(0.85, 0.85, 0.85)
VERY_LIGHT_GREY = Color(0.96, 0.96, 0.96)
DARK = Color(0.15, 0.15, 0.15)

# Temp directory for equation images
EQ_DIR = tempfile.mkdtemp(prefix="eq_")
_eq_counter = 0

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    "DocTitle", parent=styles["Title"], fontSize=22, leading=28,
    textColor=black, spaceAfter=8, alignment=1,
))
styles.add(ParagraphStyle(
    "Subtitle", parent=styles["Normal"], fontSize=11,
    textColor=GREY, alignment=1, spaceAfter=4,
))
styles.add(ParagraphStyle(
    "H2", parent=styles["Heading2"], fontSize=15, leading=20,
    textColor=black, spaceBefore=18, spaceAfter=6,
))
styles.add(ParagraphStyle(
    "H3", parent=styles["Heading3"], fontSize=12, leading=16,
    textColor=Color(0.2, 0.2, 0.2), spaceBefore=14, spaceAfter=4,
))
styles.add(ParagraphStyle(
    "H4", parent=styles["Heading4"], fontSize=10.5, leading=14,
    textColor=Color(0.3, 0.3, 0.3), spaceBefore=10, spaceAfter=3,
))
styles.add(ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=10, leading=14,
    textColor=DARK, spaceAfter=6,
))
styles.add(ParagraphStyle(
    "BulletItem", parent=styles["Normal"], fontSize=10, leading=14,
    textColor=DARK, leftIndent=16, bulletIndent=6, spaceAfter=3,
))
styles.add(ParagraphStyle(
    "Equation", parent=styles["Normal"], fontSize=9, leading=13,
    textColor=Color(0.3, 0.3, 0.3), alignment=1, fontName="Courier",
    spaceBefore=6, spaceAfter=6, leftIndent=20, rightIndent=20,
))
styles.add(ParagraphStyle(
    "NumberedItem", parent=styles["Normal"], fontSize=10, leading=14,
    textColor=DARK, leftIndent=16, bulletIndent=6, spaceAfter=3,
))
styles.add(ParagraphStyle(
    "TableCell", parent=styles["Normal"], fontSize=9, leading=12,
    textColor=DARK,
))


# ---------------------------------------------------------------------------
# Equation rendering via matplotlib
# ---------------------------------------------------------------------------

def latex_to_mathtext(latex):
    """Convert LaTeX notation to matplotlib mathtext notation."""
    s = latex.strip()
    # \text{...} -> \mathrm{...}  (mathtext uses \mathrm)
    s = s.replace("\\text{", "\\mathrm{")
    # \left| ... \right| -> | ... |
    s = s.replace("\\left|", "|").replace("\\right|", "|")
    # \, thin space
    s = s.replace("\\,", "\\;")
    # \circ for degree symbol
    s = s.replace("\\circ", "\\degree")
    # Escaped backslash-space for explicit space in mathtext
    s = s.replace("\\ ", "\\;")
    return s


def render_equation_image(latex, fontsize=11, dpi=200):
    """Render a LaTeX equation to a PNG file and return the path."""
    global _eq_counter
    _eq_counter += 1
    path = os.path.join(EQ_DIR, f"eq_{_eq_counter}.png")

    mt = latex_to_mathtext(latex)

    fig, ax = plt.subplots(figsize=(0.01, 0.01))
    ax.axis("off")
    fig.patch.set_alpha(0.0)

    text = ax.text(
        0.5, 0.5, f"${mt}$",
        fontsize=fontsize,
        ha="center", va="center",
        transform=ax.transAxes,
        color="#333333",
    )

    fig.savefig(
        path, dpi=dpi, bbox_inches="tight",
        pad_inches=0.05, transparent=True,
    )
    plt.close(fig)
    return path


class CenteredImage(Flowable):
    """A flowable that centers an image horizontally on the page."""

    def __init__(self, img_path, max_width, space_before=4, space_after=4):
        super().__init__()
        from reportlab.lib.utils import ImageReader
        img = ImageReader(img_path)
        iw, ih = img.getSize()
        # Scale to fit max_width while keeping aspect ratio
        scale = min(max_width / iw, 1.0)
        self.img_path = img_path
        self.img_w = iw * scale
        self.img_h = ih * scale
        self.space_before = space_before
        self.space_after = space_after

    def wrap(self, availWidth, availHeight):
        return availWidth, self.img_h + self.space_before + self.space_after

    def draw(self):
        self.canv.translate(0, self.space_after)
        x = (self.canv._pagesize[0] - self.canv._currentMatrix[4] * 2 - self.img_w) / 2
        # Center within available width
        avail = self.canv._pagesize[0] - 40 * mm  # approximate usable width
        x = (avail - self.img_w) / 2
        self.canv.drawImage(
            self.img_path, x, 0,
            width=self.img_w, height=self.img_h,
            mask="auto",
        )


def make_equation_flowable(latex):
    """Create a centered equation image flowable from LaTeX source."""
    img_path = render_equation_image(latex)
    max_w = WIDTH - 60 * mm  # leave margins
    return CenteredImage(img_path, max_w)


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def md_inline(text):
    """Convert markdown inline formatting to reportlab XML tags."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9">\1</font>', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Inline math $...$: clean for plain text display in paragraphs
    text = re.sub(r'\$([^$]+)\$', lambda m: clean_latex_inline(m.group(1)), text)
    return text


def clean_latex_inline(text):
    """Clean inline LaTeX for plain-text display in paragraph text.

    Uses only basic ASCII characters to avoid font rendering issues.
    Greek letters use their spelled-out English names.
    """
    subs = {
        "\\min": "min", "\\max": "max",
        "\\hat{": "", "\\text{": "", "\\mathrm{": "",
        "\\lambda": "lambda", "\\alpha": "alpha", "\\beta": "beta",
        "\\gamma": "gamma", "\\theta": "theta",
        "\\leq": "<=", "\\geq": ">=",
        "\\cdot": "*", "\\forall": "for all",
        "\\in": " in ",
    }
    for k, v in subs.items():
        text = text.replace(k, v)
    # Subscripts: _{xyz} -> _xyz
    text = re.sub(r'_\{([^}]+)\}', r'_\1', text)
    # Superscripts: ^{xyz} -> ^xyz
    text = re.sub(r'\^\{([^}]+)\}', r'^\1', text)
    text = text.replace("{", "").replace("}", "")
    return text


def is_block_start(line):
    """Check if a line starts a new block."""
    if not line:
        return True
    return (line.startswith("#") or line.startswith("- ") or
            line.startswith("|") or line.startswith("$$") or
            re.match(r'^\d+\.\s', line))


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_markdown(md_path):
    """Parse the markdown file and return a list of reportlab flowables."""
    with open(md_path, "r") as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    story = []

    # Title page
    story.append(Spacer(1, 80))
    story.append(Paragraph("RTE 7k Power Injection<br/>Replication Challenge", styles["DocTitle"]))
    story.append(Spacer(1, 16))
    story.append(Paragraph("eRoots", styles["Subtitle"]))
    story.append(Paragraph("March 2026", styles["Subtitle"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Draft for internal RTE review", styles["Subtitle"]))
    story.append(PageBreak())

    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped:
            i += 1
            continue

        # H1 -- skip (title page)
        if stripped.startswith("# ") and not stripped.startswith("##"):
            i += 1
            continue

        if stripped.startswith("#### "):
            story.append(Paragraph(md_inline(stripped[5:]), styles["H4"]))
            i += 1
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(md_inline(stripped[4:]), styles["H3"]))
            i += 1
            continue

        if stripped.startswith("## "):
            story.append(Paragraph(md_inline(stripped[3:]), styles["H2"]))
            i += 1
            continue

        # Table
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:
                headers = [c.strip() for c in table_lines[0].split("|") if c.strip()]
                data_rows = []
                for tl in table_lines[2:]:
                    cells = [c.strip() for c in tl.split("|") if c.strip() != ""]
                    is_sep = all(set(c.strip()) <= set("-| :") for c in cells)
                    if cells and not is_sep:
                        data_rows.append(cells)
                tdata = [[Paragraph("<b>%s</b>" % md_inline(h), styles["TableCell"]) for h in headers]]
                for row in data_rows:
                    tdata.append([Paragraph(md_inline(c), styles["TableCell"]) for c in row])
                col_count = len(headers)
                avail = WIDTH - 40 * mm
                col_w = avail / col_count
                t = Table(tdata, colWidths=[col_w] * col_count)
                tstyle = [
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), black),
                    ("GRID", (0, 0), (-1, -1), 0.5, Color(0.6, 0.6, 0.6)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
                for row_idx in range(1, len(tdata)):
                    if row_idx % 2 == 0:
                        tstyle.append(("BACKGROUND", (0, row_idx), (-1, row_idx), VERY_LIGHT_GREY))
                t.setStyle(TableStyle(tstyle))
                story.append(Spacer(1, 4))
                story.append(t)
                story.append(Spacer(1, 4))
            continue

        # Bullet point
        if stripped.startswith("- "):
            text = md_inline(stripped[2:])
            story.append(Paragraph(text, styles["BulletItem"], bulletText="\u2022"))
            i += 1
            continue

        # Numbered list
        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            num = m.group(1)
            text = md_inline(m.group(2))
            story.append(Paragraph(text, styles["NumberedItem"], bulletText="%s." % num))
            i += 1
            continue

        # LaTeX display equation: $$...$$ on a single line
        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
            eq_latex = stripped[2:-2].strip()
            story.append(make_equation_flowable(eq_latex))
            i += 1
            continue

        # LaTeX display equation: multi-line $$ ... $$
        if stripped.startswith("$$"):
            eq_parts = [stripped[2:]]
            i += 1
            while i < len(lines) and "$$" not in lines[i]:
                eq_parts.append(lines[i].strip())
                i += 1
            if i < len(lines):
                last = lines[i].strip()
                eq_parts.append(last.replace("$$", ""))
                i += 1
            eq_latex = " ".join(p for p in eq_parts if p)
            story.append(make_equation_flowable(eq_latex))
            continue

        # Regular paragraph
        para_text = stripped
        i += 1
        while i < len(lines):
            next_stripped = lines[i].strip()
            if is_block_start(next_stripped):
                break
            para_text += " " + next_stripped
            i += 1
        story.append(Paragraph(md_inline(para_text), styles["Body"]))

    return story


def main():
    story = parse_markdown(MD_FILE)
    doc = SimpleDocTemplate(
        PDF_FILE, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    doc.build(story)
    # Clean up temp equation images
    import shutil
    shutil.rmtree(EQ_DIR, ignore_errors=True)
    print(f"Generated {PDF_FILE}")


if __name__ == "__main__":
    main()
