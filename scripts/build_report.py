"""REPORT.md -> REPORT.pdf (markdown -> HTML -> WeasyPrint), same route as Assignments 1, 4 and 5.
The brief asks for 10 to 12 pages, so the body is 8.6pt (A5 needed 8.4pt to fit 6 pages).
Math: $...$ in REPORT.md is LaTeX (GitHub renders it too; a literal dollar is written \\$). WeasyPrint cannot run a
JavaScript math engine, so each formula is typeset here with matplotlib's mathtext in Computer Modern and placed on the
line as a small vector (SVG) image, sized to the text and sitting on its baseline."""
import _bootstrap  # noqa: F401
import base64
import html as htmlmod
import io
import re

import matplotlib
import numpy as np
from markdown_it import MarkdownIt
from PIL import Image
from weasyprint import HTML

from src.config import ROOT

matplotlib.use("Agg")
matplotlib.rcParams["mathtext.fontset"] = "cm"
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.mathtext import MathTextParser, math_to_image  # noqa: E402

_PARSER, _DPI = MathTextParser("path"), 100


def tex(expr: str, size_pt: float) -> str:
    """One LaTeX expression -> an inline <img> (SVG data URI) on the text baseline, at the given font size.
    The layout box can carry a little blank space at its sides, so the image is trimmed to its ink (found on a
    high-resolution raster of the same layout), keeping the vertical box so it still sits on the baseline."""
    prop = FontProperties(size=size_pt)
    w, h, d = _PARSER.parse(f"${expr}$", dpi=_DPI, prop=prop)[:3]
    ras = io.BytesIO()
    math_to_image(f"${expr}$", ras, prop=prop, dpi=8 * _DPI, format="png")
    a = np.asarray(Image.open(ras).convert("L"))
    ink = np.where((a < 250).any(axis=0))[0]
    f0, f1 = (ink.min() / a.shape[1], (ink.max() + 1) / a.shape[1]) if len(ink) else (0.0, 1.0)
    buf = io.BytesIO()
    math_to_image(f"${expr}$", buf, prop=prop, dpi=_DPI, format="svg", color="#0b0b0b")
    svg = buf.getvalue().decode()
    m = re.search(r'width="([\d.]+)pt" height="([\d.]+)pt" viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    W, H = float(m.group(3)), float(m.group(4))
    pad = 0.04 * size_pt   # a hair of space so glyphs are not clipped
    x0, vw = max(0.0, f0 * W - pad), min(W, (f1 - f0) * W + 2 * pad)
    svg = svg.replace(m.group(0), f'width="{vw:.3f}pt" height="{m.group(2)}pt" viewBox="{x0:.3f} 0 {vw:.3f} {H}"', 1)
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    k = 72 / _DPI   # pixels at _DPI -> points
    return (f'<img class="math" src="{uri}" alt="{htmlmod.escape(expr, quote=True)}" '
            f'style="height:{h * k:.2f}pt; width:{vw * (h * k) / H:.2f}pt; vertical-align:{-d * k:.2f}pt" />')


MATH = re.compile(r"(?<!\\)\$(.+?)(?<!\\)\$")


def render_math(md: str) -> str:
    """Replace $...$ outside code with typeset images; table rows use the table font size."""
    out = []
    for line in md.split("\n"):
        size = 7.8 if line.lstrip().startswith("|") else 8.6
        out.append(MATH.sub(lambda m: tex(m.group(1), size), line))
    return "\n".join(out)

CSS = """
@page { size: Letter; margin: 1.0cm 1.2cm 1.0cm 1.2cm;
        @bottom-center { content: counter(page); font-size: 8pt; color: #898781; } }
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 8.6pt;
       line-height: 1.21; color: #0b0b0b; }
h1 { font-size: 15pt; margin: 0 0 2pt 0; }
h3 { font-size: 10.5pt; margin: 0 0 6pt 0; color: #52514e; font-weight: normal; }
h2 { font-size: 10.8pt; margin: 8pt 0 3pt 0; border-bottom: 0.6pt solid #c3c2b7; padding-bottom: 1pt; }
h4 { font-size: 9.8pt; margin: 7pt 0 2pt 0; }
p { margin: 0 0 3pt 0; text-align: justify; }
ul, ol { margin: 0 0 3pt 0; padding-left: 13pt; }
li > ul { margin: 1pt 0 1pt 0; }
li p { margin: 0; }
li { margin-bottom: 0.5pt; }
p + table { break-before: avoid; page-break-before: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 7.8pt; margin: 3pt 0 6pt 0; }
th { border-bottom: 0.8pt solid #52514e; text-align: left; padding: 1.5pt 4pt; }
td { border-bottom: 0.4pt solid #e1e0d9; padding: 1.2pt 4pt; }
tr { break-inside: avoid; page-break-inside: avoid; }
h2, h3, h4 { break-after: avoid; page-break-after: avoid; }
h2 + p { break-after: avoid; page-break-after: avoid; }
img { display: block; margin: 2pt auto 0 auto; max-width: 100%; max-height: 2.72in; }
em.cap, p.cap { font-size: 8pt; color: #52514e; }
.fig { break-inside: avoid; page-break-inside: avoid; }
hr { border: none; border-top: 0.6pt solid #c3c2b7; margin: 6pt 0; }
code { font-size: 8.4pt; }
.refs { font-size: 7.5pt; line-height: 1.18; color: #52514e; }
img.math { display: inline; margin: 0; max-height: none; }
"""

md = render_math((ROOT / "REPORT.md").read_text())
# CommonMark: lists may follow a paragraph line directly and nest with 2 spaces
# (Python-Markdown needed blank lines + 4-space indents and ran the bullets together)
html = MarkdownIt("commonmark", {"html": True}).enable("table").render(md)
# keep each figure with its caption (the image and its italic caption render as one <p>)
html = html.replace("<p><img src=", "<p class=\"fig\"><img src=")   # figures only, not inline math
# Figure 3 a little shorter so it fits under Section 4 (keeps the report at 12 pages without a blank half page)
html = html.replace('alt="Figure 3" />', 'alt="Figure 3" style="max-height: 2.4in" />')
page = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html}</body></html>"
(ROOT / "outputs" / "REPORT.html").write_text(page)
HTML(string=page, base_url=str(ROOT)).write_pdf(ROOT / "REPORT.pdf")
print("wrote REPORT.pdf")
