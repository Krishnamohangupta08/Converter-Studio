# FontShift Studio

**FontShift Studio** is a desktop batch-conversion utility built with PyQt6. Despite the name, it has grown into three tools in one app:

- **Font Studio** — real outline-level font format conversion (not just file renaming)
- **PDF Studio** — PDF unlocking (password removal) and compression
- **Image Studio** — batch image format conversion

All heavy lifting (font/PDF/image processing) lives in `engine.py`, a pure-Python module with no GUI dependencies. The GUI itself lives in `app.py`.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Usage Guide](#usage-guide)
- [How Conversion Works (Engine Details)](#how-conversion-works-engine-details)
- [Troubleshooting](#troubleshooting)

---

## Features

### 🔤 Font Studio
- Batch conversion between font formats: **TTF, OTF, WOFF, WOFF2, EOT, SVG**
- **Real outline conversion** between TTF and OTF — quadratic (`glyf`) ↔ cubic (`CFF`) curves — using `fontTools` (`Qu2CuPen` / `Cu2QuPen` + `FontBuilder`), not just a file-extension swap
- Three precision presets (**Fast**, **Balanced**, **Precise**) that control curve-fitting error tolerance
- Preserves layout tables (`GSUB`, `GPOS`, `GDEF`) across conversion where possible
- Optional font preprocessing: subsetting by Unicode range, scaling units-per-em, overriding family/style/version/designer metadata, and stripping layout/hinting/legacy/name-table data
- Drag-and-drop or folder-based batch import
- Live progress table with per-file status and a log console

### 🔒 PDF Studio
- Unlock password-protected PDFs (with optional per-file password / default password)
- Compress PDFs (re-encodes embedded images to JPEG, downsamples large images, compresses/linearizes the PDF stream) via `pikepdf` + `Pillow`
- Combined "Unlock & Compress" mode

### 🖼️ Image Studio
- Batch convert between **PNG, JPEG, WEBP, BMP, GIF, TIFF**
- Adjustable JPEG/WEBP quality slider
- Automatic transparency (RGBA) flattening onto a white background for formats that don't support alpha

### General
- Dark and light themes with a custom frameless title bar
- Toast notifications, drag-and-drop overlay, and an animated "About" panel
- Optional "delete source file after conversion" and "overwrite existing output" toggles
- Background processing via `QThread` workers, with cancel support

---

## Project Structure

```
.
├── app.py       # PyQt6 GUI application (windows, widgets, workers, styling)
└── engine.py    # Pure-Python conversion engine (fontTools / pikepdf / Pillow)
```

> Note: this README documents only these two files as provided. If your full project includes additional assets (icons, `requirements.txt`, packaging scripts, etc.), add them alongside these files.

`app.py` imports `engine.py` directly (`import engine`), so both files must sit in the same directory.

---

## Requirements

- **Python 3.10+** (the code uses `from __future__ import annotations` and modern type hints; PyQt6 also requires a reasonably recent Python)
- **OS**: Windows, macOS, or Linux (anywhere PyQt6 runs)

### Python packages

| Package | Used for |
|---|---|
| `PyQt6` | GUI framework |
| `qtawesome` | Icon set used throughout the UI |
| `fontTools` | Font parsing, outline conversion, WOFF/WOFF2/EOT/SVG packaging |
| `pikepdf` | PDF unlocking, compression, linearization |
| `Pillow` | Image conversion, and image re-compression inside PDFs |

`fontTools`' WOFF2 support requires the `brotli` compression backend, which is normally pulled in automatically via the `fonttools[woff]` extra.

---

## Installation

1. **Clone or download the project** (place `app.py` and `engine.py` in the same folder).

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   ```

   Activate it:

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**

   ```bash
   pip install PyQt6 qtawesome "fonttools[woff]" pikepdf Pillow
   ```

   Or, if you prefer a `requirements.txt` file, create one with:

   ```
   PyQt6
   qtawesome
   fonttools[woff]
   pikepdf
   Pillow
   ```

   and install with:

   ```bash
   pip install -r requirements.txt
   ```

---

## Running the App

From the project directory (with your virtual environment activated):

```bash
python app.py
```

This launches the main window in **Font Studio** mode by default, styled with the dark theme.

---

## Usage Guide

### 1. Choose a mode
Use the **File** menu (or the mode-switch links inside it) to switch between:
- **Font Studio**
- **PDF Studio (PDF Unlock)**
- **Image Studio**

Switching modes clears the current file queue and updates which file types are accepted.

### 2. Add files
- Click **Add Files...** or **Add Folder...**, or
- Drag and drop files/folders directly onto the window

Accepted extensions depend on the active mode:

| Mode | Accepted extensions |
|---|---|
| Font Studio | `.ttf` `.otf` `.woff` `.woff2` `.eot` `.svg` |
| PDF Studio | `.pdf` |
| Image Studio | `.png` `.jpg` `.jpeg` `.webp` `.bmp` `.gif` `.tiff` |

### 3. Configure options

**Font Studio**
- Target format: OTF, TTF, WOFF, WOFF2, EOT, or SVG
- Precision: Fast / Balanced / Precise (affects TTF↔OTF curve conversion accuracy)
- Overwrite existing output / delete source after conversion

**PDF Studio**
- Action: **Unlock Only**, **Compress Only**, or **Unlock & Compress**
- Optional default password (used when a file needs one and none is set per-row)
- Overwrite in place / delete source after processing

**Image Studio**
- Target format: PNG, JPEG, WEBP, BMP, GIF, TIFF
- Quality slider (applies to JPEG/WEBP output)
- Overwrite existing output / delete source after conversion

### 4. Convert
Click the **Convert** button to start a background batch job. Progress, per-file status, and a running log are shown live. You can **Cancel** a running batch; it stops after the file currently being processed finishes.

### 5. Review results
Each row in the table updates with a status (Queued, Done, Failed, Ignored, etc.) and a message (e.g., glyph count converted, or an error reason). A summary toast and status line appear once the batch finishes.

---

## How Conversion Works (Engine Details)

`engine.py` is deliberately GUI-free so it can be reused from a CLI or test suite. Key entry points:

- **`convert_font(...)`** — main font conversion dispatcher. Detects the real source format from the font's `sfnt` tables (not the file extension), optionally runs preprocessing (subsetting, upem scaling, metadata overrides, stripping tables), then routes to:
  - `ttf_to_otf()` / `otf_to_ttf()` — true outline conversion using fontTools pens (`Qu2CuPen` for quadratic→cubic, and the equivalent path for cubic→quadratic), rebuilding a fresh font via `FontBuilder`
  - `repackage()` — for WOFF/WOFF2/same-format "clean copy" (recompiles and fixes checksums without changing outlines)
  - `ttf_to_eot()` — wraps TTF/OTF as Embedded OpenType
  - `font_to_svg_font()` — wraps outlines in an SVG Font container
- **`inspect_font()` / `get_font_details()`** — reads family/style/format/glyph count/units-per-em/variable-font status for display in the UI
- **`unlock_pdf()`** — opens a PDF with `pikepdf` (using a supplied password if needed), optionally compresses embedded images (`compress_pdf_images()`, which uses Pillow to re-encode as JPEG and downsample large images) and linearizes the output
- **`convert_image()`** — opens with Pillow, flattens alpha onto white where the target format doesn't support transparency, and saves with a quality parameter for JPEG/WEBP

Precision presets (`PRECISION_PRESETS` in `engine.py`) control the curve-fitting error budget as a fraction of units-per-em:

| Preset | Error budget |
|---|---|
| Fast | 0.0035 × UPM |
| Balanced | 0.0010 × UPM |
| Precise | 0.00025 × UPM |

Lower values produce more accurate curves at the cost of slightly larger files and slower conversion.

---

## Troubleshooting

- **"Variable fonts are not supported for outline conversion"** — `ttf_to_otf`/`otf_to_ttf` intentionally reject fonts containing a `gvar` table; only static (non-variable) fonts can have their outlines converted.
- **WOFF2 output fails / missing brotli** — install `fonttools[woff]` rather than plain `fonttools` so the brotli codec is available.
- **PDF says "Password required or incorrect password"** — set a per-file password in the table, or a default password in PDF Studio's options, before converting.
- **App window doesn't appear / import errors on launch** — confirm `PyQt6` and `qtawesome` are installed in the active environment, and that `engine.py` sits next to `app.py`.
