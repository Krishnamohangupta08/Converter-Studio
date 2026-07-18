"""
engine.py
---------
Pure Python font conversion engine built on fontTools. No GUI dependencies
live here, so it can be reused from a CLI, a test suite, or any front end.

Supported conversions
    TTF  -> OTF     real outline conversion: quadratic (glyf) -> cubic (CFF)
    OTF  -> TTF     real outline conversion: cubic (CFF) -> quadratic (glyf)
    *    -> WOFF    repackage existing outlines as WOFF
    *    -> WOFF2   repackage existing outlines as WOFF2 (brotli compressed)
    *    -> EOT     repackage TTF/OTF as Embedded OpenType (EOT)
    *    -> SVG     repackage existing outlines as an SVG Font wrapper
    *    -> same    fast "clean copy" (recompiles the font, fixes checksums)

The TTF<->OTF paths do a real glyph-outline conversion (via fontTools'
Qu2CuPen / Cu2QuPen + FontBuilder) rather than just renaming the file
extension, so the result is a spec-correct, standalone font.
"""

from __future__ import annotations

import os
import shutil
import time
import struct
import tempfile
from dataclasses import dataclass
from enum import Enum


class FontFormat(str, Enum):
    TTF = "ttf"
    OTF = "otf"
    WOFF = "woff"
    WOFF2 = "woff2"
    EOT = "eot"
    SVG = "svg"


# Approximation error budget for curve conversion, expressed as a fraction
# of the font's units-per-em. Smaller = more accurate but slightly slower
# and slightly larger output.
PRECISION_PRESETS = {
    "Fast": 0.0035,
    "Balanced": 0.0010,
    "Precise": 0.00025,
}


class ConversionError(Exception):
    pass


@dataclass
class FontInfo:
    path: str
    family: str
    style: str
    format: str          # "TTF" or "OTF"
    glyph_count: int
    units_per_em: int
    is_variable: bool
    size_bytes: int


@dataclass
class ConversionResult:
    input_path: str
    output_path: str
    ok: bool
    message: str
    seconds: float


def _lazy_import_fonttools():
    """Import fontTools lazily so the module can be introspected/tested
    even in environments where the dependency isn't installed yet."""
    from fontTools.ttLib import TTFont  # noqa: F401
    return TTFont


def detect_format(path: str) -> str:
    """Return 'TTF' or 'OTF' based on the actual sfnt table content,
    not the file extension (some files are mislabeled)."""
    TTFont = _lazy_import_fonttools()
    font = TTFont(path, lazy=True, fontNumber=0)
    try:
        return "OTF" if "CFF " in font or "CFF2" in font else "TTF"
    finally:
        font.close()


def inspect_font(path: str) -> FontInfo:
    TTFont = _lazy_import_fonttools()
    font = TTFont(path, lazy=True, fontNumber=0)
    try:
        name_table = font["name"]
        family = name_table.getDebugName(16) or name_table.getDebugName(1) or "Unknown"
        style = name_table.getDebugName(17) or name_table.getDebugName(2) or "Regular"
        fmt = "OTF" if ("CFF " in font or "CFF2" in font) else "TTF"
        glyph_count = font["maxp"].numGlyphs
        upem = font["head"].unitsPerEm
        is_variable = "fvar" in font
        return FontInfo(
            path=path,
            family=family,
            style=style,
            format=fmt,
            glyph_count=glyph_count,
            units_per_em=upem,
            is_variable=is_variable,
            size_bytes=os.path.getsize(path),
        )
    finally:
        font.close()


def _name_strings(font):
    nt = font["name"]
    family = nt.getDebugName(1) or "ConvertedFont"
    style = nt.getDebugName(2) or "Regular"
    full = nt.getDebugName(4) or f"{family} {style}"
    ps = nt.getDebugName(6) or (family + "-" + style).replace(" ", "")
    version = nt.getDebugName(5) or "Version 1.0"
    return dict(
        familyName=family,
        styleName=style,
        uniqueFontIdentifier=f"{ps}:{int(time.time())}",
        fullName=full,
        psName=ps,
        version=version,
    )


def _copy_layout_tables(src_font, dst_fb):
    for tag in ("GSUB", "GPOS", "GDEF"):
        if tag in src_font:
            dst_fb.font[tag] = src_font[tag]


def ttf_to_otf(input_path: str, output_path: str, precision: str = "Balanced") -> int:
    """Convert TrueType (glyf/quadratic) outlines to CFF (cubic) outlines
    and write a real OpenType-CFF (.otf) file. Returns the glyph count."""
    from fontTools.ttLib import TTFont
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.qu2cuPen import Qu2CuPen
    from fontTools.pens.t2CharStringPen import T2CharStringPen

    font = TTFont(input_path)
    try:
        if "gvar" in font:
            raise ConversionError("Variable fonts are not supported for outline conversion")
        if "glyf" not in font:
            raise ConversionError("Source has no TrueType outlines to convert")

        upem = font["head"].unitsPerEm
        glyph_order = font.getGlyphOrder()
        glyph_set = font.getGlyphSet()
        max_err = PRECISION_PRESETS.get(precision, 0.001) * upem

        charstrings = {}
        for name in glyph_order:
            glyph = glyph_set[name]
            t2pen = T2CharStringPen(glyph.width, glyph_set)
            glyph.draw(Qu2CuPen(t2pen, max_err=max_err, all_cubic=True))
            charstrings[name] = t2pen.getCharString()

        cmap = font.getBestCmap() or {}
        names = _name_strings(font)

        fb = FontBuilder(upem, isTTF=False)
        fb.setupGlyphOrder(glyph_order)
        fb.setupCharacterMap(cmap)
        fb.setupCFF(
            names["psName"],
            dict(FullName=names["fullName"], FamilyName=names["familyName"], Weight=names["styleName"]),
            charstrings,
            {},
        )

        lsb = {}
        for gn, cs in charstrings.items():
            bounds = cs.calcBounds(None)
            lsb[gn] = bounds[0] if bounds else 0

        hmtx = font["hmtx"]
        metrics = {gn: (hmtx[gn][0], lsb.get(gn, 0)) for gn in glyph_order}
        fb.setupHorizontalMetrics(metrics)

        hhea = font["hhea"]
        fb.setupHorizontalHeader(ascent=hhea.ascender, descent=hhea.descender, lineGap=hhea.lineGap)
        fb.setupNameTable(names)

        os2 = font["OS/2"]
        fb.setupOS2(
            sTypoAscender=os2.sTypoAscender,
            sTypoDescender=os2.sTypoDescender,
            sTypoLineGap=os2.sTypoLineGap,
            usWinAscent=os2.usWinAscent,
            usWinDescent=os2.usWinDescent,
            usWeightClass=getattr(os2, "usWeightClass", 400),
            usWidthClass=getattr(os2, "usWidthClass", 5),
            fsType=getattr(os2, "fsType", 0),
            sxHeight=getattr(os2, "sxHeight", 0),
            sCapHeight=getattr(os2, "sCapHeight", 0),
        )

        post = font.get("post")
        fb.setupPost(
            italicAngle=getattr(post, "italicAngle", 0) if post else 0,
            underlinePosition=getattr(post, "underlinePosition", -100) if post else -100,
            underlineThickness=getattr(post, "underlineThickness", 50) if post else 50,
        )

        _copy_layout_tables(font, fb)
        fb.save(output_path)
        return len(glyph_order)
    finally:
        font.close()


def otf_to_ttf(input_path: str, output_path: str, precision: str = "Balanced") -> int:
    """Convert CFF (cubic) outlines to TrueType (glyf/quadratic) outlines
    and write a real .ttf file. Returns the glyph count."""
    from fontTools.ttLib import TTFont
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    font = TTFont(input_path)
    try:
        if "CFF " not in font and "CFF2" not in font:
            raise ConversionError("Source has no CFF outlines to convert")

        upem = font["head"].unitsPerEm
        glyph_order = font.getGlyphOrder()
        glyph_set = font.getGlyphSet()
        max_err = PRECISION_PRESETS.get(precision, 0.001) * upem

        glyphs = {}
        for name in glyph_order:
            glyph = glyph_set[name]
            ttpen = TTGlyphPen(glyph_set)
            glyph.draw(Cu2QuPen(ttpen, max_err=max_err))
            glyphs[name] = ttpen.glyph()

        cmap = font.getBestCmap() or {}
        names = _name_strings(font)

        fb = FontBuilder(upem, isTTF=True)
        fb.setupGlyphOrder(glyph_order)
        fb.setupCharacterMap(cmap)
        fb.setupGlyf(glyphs)

        hmtx = font["hmtx"]
        glyf_table = fb.font["glyf"]
        metrics = {
            gn: (hmtx[gn][0], getattr(glyf_table[gn], "xMin", 0))
            for gn in glyph_order
        }
        fb.setupHorizontalMetrics(metrics)

        hhea = font["hhea"]
        fb.setupHorizontalHeader(ascent=hhea.ascender, descent=hhea.descender, lineGap=hhea.lineGap)
        fb.setupNameTable(names)

        os2 = font["OS/2"]
        fb.setupOS2(
            sTypoAscender=os2.sTypoAscender,
            sTypoDescender=os2.sTypoDescender,
            sTypoLineGap=os2.sTypoLineGap,
            usWinAscent=os2.usWinAscent,
            usWinDescent=os2.usWinDescent,
            usWeightClass=getattr(os2, "usWeightClass", 400),
            usWidthClass=getattr(os2, "usWidthClass", 5),
            fsType=getattr(os2, "fsType", 0),
        )

        post = font.get("post")
        fb.setupPost(italicAngle=getattr(post, "italicAngle", 0) if post else 0)

        _copy_layout_tables(font, fb)
        fb.save(output_path)
        return len(glyph_order)
    finally:
        font.close()


def repackage(input_path: str, output_path: str, flavor: str | None) -> int:
    """Fast path: no outline conversion needed. Loads and re-saves the font,
    optionally as WOFF/WOFF2. Also doubles as a 'repair / recompile' pass."""
    TTFont = _lazy_import_fonttools()
    font = TTFont(input_path)
    try:
        font.flavor = flavor
        font.save(output_path)
        return font["maxp"].numGlyphs
    finally:
        font.close()


# --------------------------------------------------------------------------
# EOT and SVG Font Packaging
# --------------------------------------------------------------------------

def ttf_to_eot(input_path: str, output_path: str) -> int:
    """Convert a TrueType font to Embedded OpenType (EOT) wrapper format."""
    temp_ttf = None
    src_fmt = detect_format(input_path)
    if src_fmt == "OTF":
        temp_fd, temp_ttf = tempfile.mkstemp(suffix=".ttf")
        os.close(temp_fd)
        otf_to_ttf(input_path, temp_ttf)
        ttf_path = temp_ttf
    else:
        ttf_path = input_path

    TTFont = _lazy_import_fonttools()
    try:
        font = TTFont(ttf_path)
        try:
            with open(ttf_path, "rb") as f:
                font_data = f.read()
            font_data_size = len(font_data)

            panose = b"\x00" * 10
            italic = 0
            weight = 400
            fs_type = 0
            if "OS/2" in font:
                os2 = font["OS/2"]
                if hasattr(os2, "panose"):
                    p = os2.panose
                    if hasattr(p, "panose"):
                        p = p.panose
                    panose = bytes(p) if hasattr(p, "__iter__") else b"\x00" * 10
                    if len(panose) != 10:
                        panose = (panose + b"\x00" * 10)[:10]
                weight = getattr(os2, "usWeightClass", 400)
                fs_type = getattr(os2, "fsType", 0)
                if getattr(os2, "fsSelection", 0) & 0x01:
                    italic = 1

            names = _name_strings(font)
            family = names["familyName"]
            style = names["styleName"]
            version = names["version"]
            full_name = names["fullName"]

            def encode_str(s):
                b = s.encode("utf-16le")
                return struct.pack("<H", len(b)) + b + b"\x00\x00"

            family_b = encode_str(family)
            style_b = encode_str(style)
            version_b = encode_str(version)
            full_b = encode_str(full_name)

            magic = 0x504C
            version_eot = 0x00020001
            check_sum = font["head"].checkSumAdjustment if "head" in font else 0

            header_fixed = struct.pack(
                "<III10sBBIHHIIIIIIIIIIIH",
                0, # placeholder for size
                font_data_size,
                version_eot,
                0, # Flags
                panose,
                1, # Charset
                italic,
                weight,
                fs_type,
                magic,
                0, 0, 0, 0, # Unicode ranges
                0, 0, # Code page ranges
                check_sum,
                0, 0, 0, 0, # Reserved
                0 # Padding
            )

            header = header_fixed + family_b + style_b + version_b + full_b
            total_size = len(header) + font_data_size
            header = struct.pack("<I", total_size) + header[4:]

            with open(output_path, "wb") as f:
                f.write(header)
                f.write(font_data)

            return font["maxp"].numGlyphs
        finally:
            font.close()
    finally:
        if temp_ttf and os.path.exists(temp_ttf):
            try:
                os.remove(temp_ttf)
            except Exception:
                pass


def font_to_svg_font(input_path: str, output_path: str) -> int:
    """Convert font outlines to SVG Font XML wrapper format."""
    from fontTools.pens.svgPathPen import SVGPathPen
    TTFont = _lazy_import_fonttools()
    font = TTFont(input_path)
    try:
        upem = font["head"].unitsPerEm
        glyph_order = font.getGlyphOrder()
        glyph_set = font.getGlyphSet()

        names = _name_strings(font)
        family_name = names["familyName"]

        cmap = font.getBestCmap() or {}
        glyph_unicodes = {}
        for code, gn in cmap.items():
            if gn not in glyph_unicodes:
                glyph_unicodes[gn] = []
            glyph_unicodes[gn].append(code)

        xml = []
        xml.append('<?xml version="1.0" standalone="no"?>')
        xml.append('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
        xml.append('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">')
        xml.append('  <defs>')
        
        safe_id = family_name.replace(" ", "")
        xml.append(f'    <font id="{safe_id}" horiz-adv-x="{upem}">')
        xml.append(f'      <font-face font-family="{family_name}" units-per-em="{upem}" />')

        glyph_count = 0
        for name in glyph_order:
            if name not in glyph_set:
                continue
            glyph = glyph_set[name]
            pen = SVGPathPen(glyph_set)
            glyph.draw(pen)
            path_d = pen.getCommands()

            unicode_attr = ""
            codes = glyph_unicodes.get(name, [])
            if codes:
                unicode_entity = "".join(f"&#x{c:X};" for c in codes)
                unicode_attr = f' unicode="{unicode_entity}"'

            xml.append(f'      <glyph glyph-name="{name}"{unicode_attr} horiz-adv-x="{glyph.width}" d="{path_d}" />')
            glyph_count += 1

        xml.append('    </font>')
        xml.append('  </defs>')
        xml.append('</svg>')

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(xml))

        return glyph_count
    finally:
        font.close()


# --------------------------------------------------------------------------
# Studio & Exporters
# --------------------------------------------------------------------------

def export_glyphs_as_svg(input_path: str, output_dir: str) -> int:
    """Extract and export all glyphs as individual SVG files."""
    from fontTools.pens.svgPathPen import SVGPathPen
    TTFont = _lazy_import_fonttools()
    os.makedirs(output_dir, exist_ok=True)
    font = TTFont(input_path)
    try:
        glyph_set = font.getGlyphSet()
        glyph_order = font.getGlyphOrder()
        upem = font["head"].unitsPerEm
        
        cmap = font.getBestCmap() or {}
        glyph_to_unicode = {v: k for k, v in cmap.items()}
        
        exported = 0
        for gn in glyph_order:
            if gn not in glyph_set:
                continue
            glyph = glyph_set[gn]
            
            pen = SVGPathPen(glyph_set)
            glyph.draw(pen)
            path_d = pen.getCommands()
            
            if not path_d:
                continue
                
            bounds = glyph.calcBounds(glyph_set) if hasattr(glyph, "calcBounds") else (0, 0, upem, upem)
            if not bounds:
                bounds = (0, 0, upem, upem)
            x_min, y_min, x_max, y_max = bounds
            width = max(1, x_max - x_min)
            height = max(1, y_max - y_min)
            
            uni = glyph_to_unicode.get(gn)
            safe_name = f"uni{uni:04X}" if uni else gn
            for char in '<>:"/\\|?*':
                safe_name = safe_name.replace(char, "_")
                
            filepath = os.path.join(output_dir, f"{safe_name}.svg")
            
            svg_content = (
                f'<?xml version="1.0" standalone="no"?>\n'
                f'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">\n'
                f'  <!-- Glyph: {gn} -->\n'
                f'  <g transform="scale(1, -1) translate({-x_min}, {-y_max})">\n'
                f'    <path d="{path_d}" fill="currentColor" />\n'
                f'  </g>\n'
                f'</svg>'
            )
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(svg_content)
            exported += 1
            
        return exported
    finally:
        font.close()


def get_font_details(path: str) -> dict:
    """Extract detailed information from a font for the studio inspector."""
    TTFont = _lazy_import_fonttools()
    font = TTFont(path, lazy=True)
    try:
        names = _name_strings(font)
        tables = sorted(font.keys())
        cmap = font.getBestCmap() or {}
        glyph_count = font["maxp"].numGlyphs
        upem = font["head"].unitsPerEm
        fmt = "OTF" if ("CFF " in font or "CFF2" in font) else "TTF"
        
        name_records = []
        if "name" in font:
            for r in font["name"].names:
                try:
                    val = r.toUnicode()
                except Exception:
                    try:
                        val = r.string.decode("utf-8", errors="replace")
                    except Exception:
                        val = str(r.string)
                name_records.append({
                    "nameID": r.nameID,
                    "platformID": r.platformID,
                    "encodingID": r.encodingID,
                    "languageID": r.languageID,
                    "value": val
                })
        
        metrics = {}
        if "hhea" in font:
            hhea = font["hhea"]
            metrics["ascent"] = getattr(hhea, "ascender", 0)
            metrics["descent"] = getattr(hhea, "descender", 0)
            metrics["lineGap"] = getattr(hhea, "lineGap", 0)
            
        if "OS/2" in font:
            os2 = font["OS/2"]
            metrics["sTypoAscender"] = getattr(os2, "sTypoAscender", 0)
            metrics["sTypoDescender"] = getattr(os2, "sTypoDescender", 0)
            metrics["sTypoLineGap"] = getattr(os2, "sTypoLineGap", 0)
            metrics["usWinAscent"] = getattr(os2, "usWinAscent", 0)
            metrics["usWinDescent"] = getattr(os2, "usWinDescent", 0)
            metrics["xHeight"] = getattr(os2, "sxHeight", 0)
            metrics["capHeight"] = getattr(os2, "sCapHeight", 0)
            metrics["weightClass"] = getattr(os2, "usWeightClass", 400)
            metrics["widthClass"] = getattr(os2, "usWidthClass", 5)
            
        axes = []
        if "fvar" in font:
            fvar = font["fvar"]
            for axis in fvar.axes:
                axes.append({
                    "tag": axis.axisTag,
                    "min": axis.minValue,
                    "default": axis.defaultValue,
                    "max": axis.maxValue
                })
                
        return {
            "family": names.get("familyName", "Unknown"),
            "style": names.get("styleName", "Regular"),
            "fullName": names.get("fullName", "Unknown"),
            "psName": names.get("psName", "Unknown"),
            "version": names.get("version", "1.0"),
            "format": fmt,
            "glyph_count": glyph_count,
            "units_per_em": upem,
            "tables": tables,
            "name_records": name_records,
            "metrics": metrics,
            "axes": axes,
            "char_count": len(cmap),
        }
    finally:
        font.close()


# --------------------------------------------------------------------------
# Preprocessing Pipelines (Subsetting, Scaling, Stripping)
# --------------------------------------------------------------------------

def _apply_metadata_overrides(font, family=None, style=None, version=None, designer=None):
    name_table = font["name"]
    if family:
        name_table.setName(family, 1, 3, 1, 0x409)
        name_table.setName(family, 1, 1, 0, 0)
    if style:
        name_table.setName(style, 2, 3, 1, 0x409)
        name_table.setName(style, 2, 1, 0, 0)
    if family or style:
        fam = family or name_table.getDebugName(1) or "Font"
        sty = style or name_table.getDebugName(2) or "Regular"
        full = f"{fam} {sty}"
        ps = f"{fam}-{sty}".replace(" ", "")
        name_table.setName(full, 4, 3, 1, 0x409)
        name_table.setName(full, 4, 1, 0, 0)
        name_table.setName(ps, 6, 3, 1, 0x409)
        name_table.setName(ps, 6, 1, 0, 0)
    if version:
        name_table.setName(version, 5, 3, 1, 0x409)
        name_table.setName(version, 5, 1, 0, 0)
    if designer:
        name_table.setName(designer, 9, 3, 1, 0x409)
        name_table.setName(designer, 9, 1, 0, 0)
        name_table.setName(designer, 8, 3, 1, 0x409)
        name_table.setName(designer, 8, 1, 0, 0)


def _scale_upem(font, new_upem):
    if "head" not in font:
        return
    old_upem = font["head"].unitsPerEm
    if old_upem == new_upem:
        return
    
    scale = new_upem / old_upem
    
    font["head"].unitsPerEm = new_upem
    for attr in ("xMin", "yMin", "xMax", "yMax"):
        val = getattr(font["head"], attr, 0)
        setattr(font["head"], attr, int(round(val * scale)))
        
    if "hhea" in font:
        hhea = font["hhea"]
        for attr in ("ascender", "descender", "lineGap", "advanceWidthMax", 
                    "minLeftSideBearing", "minRightSideBearing", "xMaxExtent"):
            if hasattr(hhea, attr):
                val = getattr(hhea, attr, 0)
                setattr(hhea, attr, int(round(val * scale)))
            
    if "hmtx" in font:
        hmtx = font["hmtx"]
        for gn in hmtx.metrics.keys():
            width, lsb = hmtx[gn]
            hmtx[gn] = (int(round(width * scale)), int(round(lsb * scale)))
            
    if "glyf" in font:
        glyf = font["glyf"]
        for gn in glyf.keys():
            glyph = glyf[gn]
            if hasattr(glyph, "coordinates"):
                from fontTools.misc.transform import Transform
                t = Transform().scale(scale)
                glyph.coordinates.transform(t)
            for attr in ("xMin", "yMin", "xMax", "yMax"):
                if hasattr(glyph, attr):
                    val = getattr(glyph, attr)
                    if val is not None:
                        setattr(glyph, attr, int(round(val * scale)))
                
    if "OS/2" in font:
        os2 = font["OS/2"]
        for attr in ("sTypoAscender", "sTypoDescender", "sTypoLineGap", 
                    "usWinAscent", "usWinDescent", "sxHeight", "sCapHeight",
                    "ySubscriptXSize", "ySubscriptYSize", "ySubscriptXOffset", "ySubscriptYOffset",
                    "ySuperscriptXSize", "ySuperscriptYSize", "ySuperscriptXOffset", "ySuperscriptYOffset",
                    "yStrikeoutSize", "yStrikeoutPosition"):
            if hasattr(os2, attr):
                val = getattr(os2, attr)
                if val is not None:
                    setattr(os2, attr, int(round(val * scale)))


def _strip_layout_tables(font):
    for tag in ("GSUB", "GPOS", "GDEF", "BASE", "JSTF", "MATH"):
        if tag in font:
            del font[tag]


def _strip_hinting(font):
    for tag in ("fpgm", "prep", "cvt ", "gasp"):
        if tag in font:
            del font[tag]
    if "glyf" in font:
        glyf = font["glyf"]
        for gn in glyf.keys():
            glyph = glyf[gn]
            if hasattr(glyph, "program"):
                glyph.program = None


def _strip_legacy(font):
    legacy = ("kern", "hdmx", "VDMX", "LTSH", "PCLT", "DSIG", "FFTM", "TTFA", "META", "prop")
    for tag in legacy:
        if tag in font:
            del font[tag]


def _strip_name_table(font):
    if "name" not in font:
        return
    name_table = font["name"]
    essential = {1, 2, 4, 5, 6}
    new_names = []
    for rec in name_table.names:
        if rec.nameID in essential:
            if (rec.platformID == 3 and rec.encodingID == 1 and rec.languageID == 0x0409) or \
               (rec.platformID == 1 and rec.encodingID == 0 and rec.languageID == 0):
                new_names.append(rec)
    name_table.names = new_names


def preprocess_font(input_path: str, temp_path: str, options: dict) -> None:
    """Preprocess a font to apply subsetting, scaling, metadata edits, and table stripping."""
    TTFont = _lazy_import_fonttools()
    font = TTFont(input_path)
    try:
        # 1. Subsetting
        subset_range = options.get("subset_range")
        if subset_range:
            from fontTools.subset import Subsetter, Options as SubsetterOptions
            sub_opt = SubsetterOptions()
            sub_opt.layout_features = ["*"]
            sub_opt.hinting = True
            
            subsetter = Subsetter(options=sub_opt)
            if subset_range == "Basic Latin":
                subsetter.populate(unicodes=range(0x0020, 0x007F))
            elif subset_range == "Latin-1 Supplement":
                subsetter.populate(unicodes=range(0x0080, 0x0100))
            elif subset_range == "ASCII + Common Punctuation":
                subsetter.populate(unicodes=list(range(0x0020, 0x007F)) + [0x2018, 0x2019, 0x201C, 0x201D, 0x2013, 0x2014, 0x2022])
            else:
                subsetter.populate(text=subset_range)
            subsetter.subset(font)

        # 2. Scale UPEM
        scale_upem = options.get("scale_upem")
        if scale_upem:
            _scale_upem(font, scale_upem)

        # 3. Metadata Overrides
        fam = options.get("family_name")
        sty = options.get("style_name")
        ver = options.get("version_str")
        des = options.get("designer_str")
        if fam or sty or ver or des:
            _apply_metadata_overrides(font, fam, sty, ver, des)

        # 4. Table Stripping
        if options.get("strip_layout"):
            _strip_layout_tables(font)
        if options.get("strip_hinting"):
            _strip_hinting(font)
        if options.get("strip_legacy"):
            _strip_legacy(font)
        if options.get("strip_name_table"):
            _strip_name_table(font)

        font.save(temp_path)
    finally:
        font.close()


# --------------------------------------------------------------------------
# Main convert entry point
# --------------------------------------------------------------------------

def convert_font(
    input_path: str,
    output_path: str,
    target_format: str,
    precision: str = "Balanced",
    options: dict | None = None,
) -> ConversionResult:
    """High level entry point. Preprocesses and converts a font file to the target format."""
    start = time.time()
    target_format = target_format.lower()
    temp_processed = None
    
    try:
        run_preprocessing = False
        if options:
            preprocess_triggers = (
                "subset_range", "scale_upem", "family_name", "style_name",
                "version_str", "designer_str", "strip_layout", "strip_hinting",
                "strip_legacy", "strip_name_table"
            )
            if any(options.get(k) for k in preprocess_triggers):
                run_preprocessing = True
                
        if run_preprocessing and options:
            temp_fd, temp_processed = tempfile.mkstemp(suffix=".ttf")
            os.close(temp_fd)
            preprocess_font(input_path, temp_processed, options)
            convert_src = temp_processed
        else:
            convert_src = input_path

        src_fmt = detect_format(convert_src)

        if target_format == FontFormat.OTF.value:
            if src_fmt == "OTF":
                glyphs = repackage(convert_src, output_path, flavor=None)
            else:
                glyphs = ttf_to_otf(convert_src, output_path, precision=precision)
        elif target_format == FontFormat.TTF.value:
            if src_fmt == "TTF":
                glyphs = repackage(convert_src, output_path, flavor=None)
            else:
                glyphs = otf_to_ttf(convert_src, output_path, precision=precision)
        elif target_format in (FontFormat.WOFF.value, FontFormat.WOFF2.value):
            glyphs = repackage(convert_src, output_path, flavor=target_format)
        elif target_format == FontFormat.EOT.value:
            glyphs = ttf_to_eot(convert_src, output_path)
        elif target_format == FontFormat.SVG.value:
            glyphs = font_to_svg_font(convert_src, output_path)
        else:
            raise ConversionError(f"Unsupported target format: {target_format}")

        elapsed = time.time() - start
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            ok=True,
            message=f"{glyphs} glyphs converted",
            seconds=elapsed,
        )
    except Exception as exc:
        elapsed = time.time() - start
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            ok=False,
            message=str(exc),
            seconds=elapsed,
        )
    finally:
        if temp_processed and os.path.exists(temp_processed):
            try:
                os.remove(temp_processed)
            except Exception:
                pass


def compress_pdf_images(pdf_obj, quality: int = 70) -> None:
    """Optimize/compress PDF images inside the pikepdf object using Pillow."""
    from PIL import Image
    import io
    import pikepdf
    from pikepdf import PdfImage

    for obj in pdf_obj.objects:
        
        if isinstance(obj, pikepdf.Stream) and "/Subtype" in obj and obj["/Subtype"] == "/Image":
            try:
                pdf_img = PdfImage(obj)
                with pdf_img.as_pil_image() as pil_img:
                    # Convert to RGB (JPEG doesn't support transparency/RGBA)
                    if pil_img.mode in ("RGBA", "LA"):
                        bg = Image.new("RGBA", pil_img.size, (255, 255, 255, 255))
                        bg.paste(pil_img, (0, 0), pil_img)
                        pil_img = bg.convert("RGB")
                    elif pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")
                    
                    # Downsample if it is very large
                    max_size = 1200
                    if max(pil_img.size) > max_size:
                        pil_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        
                    out_bio = io.BytesIO()
                    pil_img.save(out_bio, format="JPEG", quality=quality)
                    compressed_data = out_bio.getvalue()
                    
                    original_size = len(obj.read_raw_bytes())
                    if len(compressed_data) < original_size:
                        obj.write(compressed_data, filter=pikepdf.Name("/DCTDecode"))
                        obj["/ColorSpace"] = pikepdf.Name("/DeviceRGB")
                        obj["/Filter"] = pikepdf.Name("/DCTDecode")
                        if "/DecodeParms" in obj:
                            del obj["/DecodeParms"]
                        obj["/Width"] = pil_img.width
                        obj["/Height"] = pil_img.height
            except Exception:
                continue


def unlock_pdf(
    input_path: str,
    output_path: str,
    password: str = "",
    compress: bool = False,
) -> ConversionResult:
    """Decrypt / unlock and optionally compress a PDF file using pikepdf."""
    import pikepdf
    start = time.time()
    try:
        def save_pdf(pdf_obj, out_path):
            if compress:
                # First optimize and compress image streams
                compress_pdf_images(pdf_obj, quality=70)
                # compress_streams=True compresses page contents and other streams.
                # linearize=True optimizes the PDF for fast web view and reduces structure redundancy.
                pdf_obj.save(out_path, compress_streams=True, linearize=True)
            else:
                pdf_obj.save(out_path)

        if os.path.abspath(input_path) == os.path.abspath(output_path):
            temp_fd, temp_out = tempfile.mkstemp(suffix=".pdf", dir=os.path.dirname(output_path))
            os.close(temp_fd)
            try:
                with pikepdf.open(input_path, password=password) as pdf:
                    save_pdf(pdf, temp_out)
                shutil.move(temp_out, input_path)
            except Exception as e:
                if os.path.exists(temp_out):
                    try:
                        os.remove(temp_out)
                    except:
                        pass
                raise e
        else:
            with pikepdf.open(input_path, password=password) as pdf:
                save_pdf(pdf, output_path)
            
        elapsed = time.time() - start
        msg = "Unlocked & Compressed" if compress else "Unlocked successfully"
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            ok=True,
            message=msg,
            seconds=elapsed,
        )
    except pikepdf.PasswordError:
        elapsed = time.time() - start
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            ok=False,
            message="Password required or incorrect password",
            seconds=elapsed,
        )
    except Exception as exc:
        elapsed = time.time() - start
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            ok=False,
            message=str(exc),
            seconds=elapsed,
        )


def convert_image(
    input_path: str,
    output_path: str,
    target_format: str,
    quality: int = 85,
) -> ConversionResult:
    """Batch convert images to major formats (PNG, JPEG, WEBP, BMP, GIF, TIFF) using Pillow."""
    from PIL import Image
    start = time.time()
    try:
        target_format = target_format.upper()
        # Map JPG -> JPEG for PIL
        pil_format = "JPEG" if target_format == "JPG" else target_format
        
        with Image.open(input_path) as img:
            # Handle alpha channel when converting to format that doesn't support transparency
            if img.mode in ("RGBA", "LA") and pil_format in ("JPEG", "BMP"):
                bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                bg.paste(img, (0, 0), img)
                img = bg.convert("RGB")
            elif img.mode != "RGB" and pil_format in ("JPEG", "BMP"):
                img = img.convert("RGB")

            # Save JPEG and WEBP with quality parameters
            if pil_format in ("JPEG", "WEBP"):
                img.save(output_path, format=pil_format, quality=quality)
            else:
                img.save(output_path, format=pil_format)

        elapsed = time.time() - start
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            ok=True,
            message=f"Converted to {target_format}",
            seconds=elapsed,
        )
    except Exception as exc:
        elapsed = time.time() - start
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            ok=False,
            message=str(exc),
            seconds=elapsed,
        )