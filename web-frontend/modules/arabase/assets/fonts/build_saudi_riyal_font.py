"""Builds saudi-riyal.woff2: a one-glyph font for U+20C1 SAUDI RIYAL SIGN.

The outline is the Saudi Central Bank's public domain artwork (saudi-riyal.svg,
from Wikimedia Commons, "File:Saudi Riyal Symbol.svg"). Needs fontTools and
brotli:

    python3 build_saudi_riyal_font.py saudi-riyal.svg saudi-riyal.woff2

Then paste the base64 of the result into assets/scss/saudi_riyal.scss.
"""

import re
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

svg = open(sys.argv[1]).read()
paths = re.findall(r' d="([^"]+)"', svg)
vb_w, vb_h = 1124.14, 1256.39
UPM, HEIGHT, SIDE = 1000, 720, 60
s = HEIGHT / vb_h
advance = round(2 * SIDE + vb_w * s)

pen = T2CharStringPen(advance, None)
tpen = TransformPen(pen, (s, 0, 0, -s, SIDE, vb_h * s))
for d in paths:
    parse_path(d, tpen)
riyal = pen.getCharString()
notdef = T2CharStringPen(500, None).getCharString()

fb = FontBuilder(UPM, isTTF=False)
fb.setupGlyphOrder([".notdef", "riyal"])
fb.setupCharacterMap({0x20C1: "riyal"})
fb.setupCFF(
    "SaudiRiyal-Regular",
    {"FullName": "Saudi Riyal Sign"},
    {".notdef": notdef, "riyal": riyal},
    {},
)
fb.setupHorizontalMetrics({".notdef": (500, 0), "riyal": (advance, SIDE)})
fb.setupHorizontalHeader(ascent=900, descent=-200)
fb.setupNameTable({"familyName": "Saudi Riyal Sign", "styleName": "Regular"})
fb.setupOS2(
    sTypoAscender=900,
    sTypoDescender=-200,
    usWinAscent=900,
    usWinDescent=200,
    sCapHeight=HEIGHT,
    sxHeight=500,
)
fb.setupPost()
fb.font.flavor = "woff2"
fb.save(sys.argv[2])
print(sys.argv[2], "advance", advance)
