"""
FontShift Studio — a fast, batch font format converter.

TTF <-> OTF outline conversion, WOFF / WOFF2 / EOT / SVG packaging.

Run:
    python app.py
"""

from __future__ import annotations

import os
import sys
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QMimeData, QUrl, QPropertyAnimation, QTimer, QPoint, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QPalette, QColor, QIcon, QFont, QDragEnterEvent, QDropEvent, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QToolButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox, QLineEdit, QCheckBox,
    QFileDialog, QProgressBar, QPlainTextEdit, QGroupBox, QFrame,
    QSizePolicy, QMessageBox, QStyle, QGraphicsOpacityEffect, QGraphicsBlurEffect,
    QMenuBar, QMenu, QSlider, QScrollArea
)

import qtawesome as qta

import engine

APP_NAME = "FontShift Studio"
INPUT_EXTS = (".ttf", ".otf", ".woff", ".woff2", ".eot", ".svg")

ACCENT = "#1E90FF"  # Dodger Blue
SUCCESS = "#10B981"  # Emerald
DANGER = "#EF4444"  # Rose
WARN = "#F59E0B"  # Amber
TEXT_MUTED_DARK = "#9CA3AF"
TEXT_MUTED_LIGHT = "#6B7280"

DARK_THEME_COLORS = {
    'text': '#E5E7EB',
    'accent': '#1E90FF',  # Dodger Blue
    'border': '#1F2026',
    'text_muted': '#9CA3AF',
    'card_bg': '#0B0B0E'
}

LIGHT_THEME_COLORS = {
    'text': '#20232B',
    'accent': '#4F5DFF',
    'border': '#E6E8EC',
    'text_muted': '#6B7280',
    'card_bg': '#FFFFFF'
}


# --------------------------------------------------------------------------
# Stylesheets
# --------------------------------------------------------------------------

STYLE_SHEET_DARK = f"""
QMainWindow {{
    background-color: transparent;
}}
QWidget#CentralWidget {{
    background-color: #000000;
    border: 1px solid #202026;
    border-radius: 16px;
}}
QMenuBar {{
    background-color: transparent;
    color: #E5E7EB;
    border: none;
    font-size: 12px;
    font-weight: 600;
}}
QMenuBar::item {{
    background-color: transparent;
    padding: 6px 10px 4px 10px;
    margin-top: 4px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: #121217;
    color: {ACCENT};
}}
QMenu {{
    background-color: #0A0A0C;
    color: #E5E7EB;
    border: 1px solid #202026;
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 6px;
    margin: 2px 4px;
    font-size: 12px;
}}
QMenu::item:selected {{
    background-color: #121A2E;
    color: {ACCENT};
}}
QMenu::separator {{
    height: 1px;
    background-color: #202026;
    margin: 6px 4px;
}}
QWidget#Card {{
    background-color: #0B0B0E;
    border: 1px solid #1F2026;
    border-radius: 12px;
}}
QFrame#OptionCard {{
    background-color: #0C0C0F;
    border: 1px solid #1F2026;
    border-radius: 12px;
}}
QLabel#Title {{
    font-size: 20px;
    font-weight: 700;
    color: #F9FAFB;
}}
QLabel#Subtitle {{
    font-size: 12px;
    color: {TEXT_MUTED_DARK};
}}
QLabel#SectionLabel {{
    font-size: 11px;
    font-weight: 700;
    color: {ACCENT};
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 2px;
}}
QPushButton {{
    background-color: #121217;
    border: 1px solid #1F2026;
    border-radius: 8px;
    padding: 8px 16px;
    color: #E5E7EB;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #1C1E26;
    border-color: #374151;
}}
QPushButton:pressed {{
    background-color: #0B0B0E;
}}
QPushButton:disabled {{
    color: #4B5563;
    background-color: #0B0B0E;
    border-color: #1F2026;
}}
QPushButton#Primary {{
    background-color: {ACCENT};
    border: 1px solid #1C86EE;
    color: #FFFFFF;
    font-weight: 700;
    padding: 10px 22px;
    font-size: 13px;
}}
QPushButton#Primary:hover {{
    background-color: #1C86EE;
}}
QPushButton#Primary:disabled {{
    background-color: #183A5E;
    border-color: #183A5E;
    color: #6B7280;
}}
QPushButton#Danger {{
    color: {DANGER};
}}
QPushButton#Danger:hover {{
    background-color: #261212;
    border-color: #991B1B;
}}
QPushButton#Ghost {{
    border: none;
    background: transparent;
    color: {TEXT_MUTED_DARK};
}}
QPushButton#Ghost:hover {{
    background-color: #121217;
    color: #F9FAFB;
}}
QTableWidget {{
    background-color: #0B0B0E;
    border: 1px solid #1F2026;
    border-radius: 12px;
    gridline-color: #17181F;
    selection-background-color: #1C1E26;
    selection-color: #FFFFFF;
    font-size: 12px;
    color: #E5E7EB;
}}
QTableWidget QWidget {{
    background-color: transparent;
}}
QHeaderView {{
    background-color: transparent;
}}
QHeaderView::section {{
    background-color: #0C0C0F;
    color: {TEXT_MUTED_DARK};
    border: none;
    border-bottom: 1px solid #1F2026;
    padding: 10px;
    font-weight: 700;
    font-size: 11px;
}}
QHeaderView::section:horizontal:first {{
    border-top-left-radius: 10px;
}}
QHeaderView::section:horizontal:last {{
    border-top-right-radius: 10px;
}}
QTableWidget::item {{
    padding: 6px;
}}
QLineEdit {{
    background-color: #0F0F14;
    border: 1px solid #1F2026;
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 12px;
    color: #F9FAFB;
    min-height: 20px;
}}
QLineEdit:hover {{
    border-color: {ACCENT};
}}
QComboBox {{
    background-color: #0F0F14;
    border: 1px solid #1F2026;
    border-radius: 8px;
    padding: 8px 30px 8px 12px;
    font-size: 12px;
    color: #F9FAFB;
    min-height: 24px;
}}
QComboBox:hover {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_MUTED_DARK};
    width: 0;
    height: 0;
    margin-right: 8px;
}}
QComboBox::down-arrow:on {{
    border-top: none;
    border-bottom: 5px solid {ACCENT};
}}
QComboBox QAbstractItemView {{
    background-color: #0A0A0C;
    color: #E5E7EB;
    border: 1px solid #202026;
    border-radius: 8px;
    selection-background-color: #121A2E;
    selection-color: {ACCENT};
    outline: none;
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding-left: 8px;
    border-radius: 4px;
    margin: 2px;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: #121A2E;
    color: {ACCENT};
}}
QCheckBox {{
    font-size: 12px;
    color: #E5E7EB;
    spacing: 8px;
}}
QProgressBar {{
    background-color: #0C0C0F;
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 6px;
}}
QPlainTextEdit#Log {{
    background-color: #050507;
    color: #38BDF8;
    border: 1px solid #121217;
    border-radius: 12px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 11px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background-color: #1F2026;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #374151;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QWidget#StatusBar {{
    background-color: #000000;
    border-top: 1px solid #121217;
    border-bottom-left-radius: 15px;
    border-bottom-right-radius: 15px;
}}
QLabel#DevLabel {{
    font-size: 11px;
    font-weight: 700;
    color: #3B82F6;
    padding: 6px;
}}
QLabel#DevLabel:hover {{
    color: #60A5FA;
    text-decoration: underline;
}}
QToolButton#ThemeToggleButton {{
    border: 1px solid #1F2026;
    border-radius: 15px;
    padding: 5px;
    background-color: #121217;
}}
QToolButton#ThemeToggleButton:hover {{
    background-color: #1C1E26;
    border-color: #374151;
}}
"""

STYLE_SHEET_LIGHT = f"""
QMainWindow {{
    background-color: transparent;
}}
QWidget#CentralWidget {{
    background-color: #F4F5F8;
    border: 1px solid #D9DCE3;
    border-radius: 16px;
}}
QMenuBar {{
    background-color: transparent;
    color: #20232B;
    border: none;
    font-size: 12px;
    font-weight: 600;
}}
QMenuBar::item {{
    background-color: transparent;
    padding: 6px 10px 4px 10px;
    margin-top: 4px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: #EEF0F4;
    color: #4F5DFF;
}}
QMenu {{
    background-color: #FFFFFF;
    color: #20232B;
    border: 1px solid #E6E8EC;
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 6px;
    margin: 2px 4px;
    font-size: 12px;
}}
QMenu::item:selected {{
    background-color: #E9EBFF;
    color: #4F5DFF;
}}
QMenu::separator {{
    height: 1px;
    background-color: #E6E8EC;
    margin: 6px 4px;
}}
QWidget#Card {{
    background: #FFFFFF;
    border: 1px solid #E6E8EC;
    border-radius: 12px;
}}
QFrame#OptionCard {{
    background-color: #FFFFFF;
    border: 1px solid #E6E8EC;
    border-radius: 12px;
}}
QLabel#Title {{
    font-size: 20px;
    font-weight: 700;
    color: #20232B;
}}
QLabel#Subtitle {{
    font-size: 12px;
    color: {TEXT_MUTED_LIGHT};
}}
QLabel#SectionLabel {{
    font-size: 11px;
    font-weight: 700;
    color: #4F5DFF;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 2px;
}}
QPushButton {{
    background: #FFFFFF;
    border: 1px solid #D9DCE3;
    border-radius: 8px;
    padding: 8px 16px;
    color: #2A2E37;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: #F0F2F6;
    border-color: #C7CBD4;
}}
QPushButton:pressed {{
    background: #E7E9EE;
}}
QPushButton:disabled {{
    color: #B2B7C1;
    background: #F7F8FA;
    border-color: #ECEEF1;
}}
QPushButton#Primary {{
    background: #4F5DFF;
    border: 1px solid #3D48D6;
    color: #FFFFFF;
    font-weight: 700;
    padding: 10px 22px;
    font-size: 13px;
}}
QPushButton#Primary:hover {{
    background: #3D48D6;
}}
QPushButton#Primary:disabled {{
    background: #BFC4F5;
    border-color: #BFC4F5;
    color: #FFFFFF;
}}
QPushButton#Danger {{
    color: {DANGER};
}}
QPushButton#Danger:hover {{
    background: #FFEAEA;
    border-color: #FCA5A5;
}}
QPushButton#Ghost {{
    border: none;
    background: transparent;
    color: {TEXT_MUTED_LIGHT};
}}
QPushButton#Ghost:hover {{
    background: #EEF0F4;
    color: #2A2E37;
}}
QTableWidget {{
    background: #FFFFFF;
    border: 1px solid #E6E8EC;
    border-radius: 12px;
    gridline-color: #EEF0F4;
    selection-background-color: #E9EBFF;
    selection-color: #20232B;
    font-size: 12px;
    color: #20232B;
}}
QTableWidget QWidget {{
    background-color: transparent;
}}
QHeaderView {{
    background-color: transparent;
}}
QHeaderView::section {{
    background: #FAFBFC;
    color: {TEXT_MUTED_LIGHT};
    border: none;
    border-bottom: 1px solid #E6E8EC;
    padding: 10px;
    font-weight: 700;
    font-size: 11px;
}}
QHeaderView::section:horizontal:first {{
    border-top-left-radius: 10px;
}}
QHeaderView::section:horizontal:last {{
    border-top-right-radius: 10px;
}}
QTableWidget::item {{
    padding: 6px;
}}
QLineEdit {{
    background: #FFFFFF;
    border: 1px solid #D9DCE3;
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 12px;
    color: #20232B;
    min-height: 20px;
}}
QLineEdit:hover {{
    border-color: #4F5DFF;
}}
QComboBox {{
    background: #FFFFFF;
    border: 1px solid #D9DCE3;
    border-radius: 8px;
    padding: 8px 30px 8px 12px;
    font-size: 12px;
    color: #20232B;
    min-height: 24px;
}}
QComboBox:hover {{
    border-color: #4F5DFF;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_MUTED_LIGHT};
    width: 0;
    height: 0;
    margin-right: 8px;
}}
QComboBox::down-arrow:on {{
    border-top: none;
    border-bottom: 5px solid #4F5DFF;
}}
QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    color: #20232B;
    border: 1px solid #E6E8EC;
    border-radius: 8px;
    selection-background-color: #E9EBFF;
    selection-color: #4F5DFF;
    outline: none;
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding-left: 8px;
    border-radius: 4px;
    margin: 2px;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: #E9EBFF;
    color: #4F5DFF;
}}
QCheckBox {{
    font-size: 12px;
    color: #2A2E37;
    spacing: 8px;
}}
QProgressBar {{
    background: #EEF0F4;
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: #4F5DFF;
    border-radius: 6px;
}}
QPlainTextEdit#Log {{
    background: #14161B;
    color: #D7DAE0;
    border: 1px solid #22252C;
    border-radius: 12px;
    font-family: "Menlo", "Consolas", monospace;
    font-size: 11px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: #D3D6DD;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #B7BBC6;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QWidget#StatusBar {{
    background-color: #F4F5F8;
    border-top: 1px solid #E6E8EC;
    border-bottom-left-radius: 15px;
    border-bottom-right-radius: 15px;
}}
QLabel#DevLabel {{
    font-size: 11px;
    font-weight: 700;
    color: #4F5DFF;
    padding: 6px;
}}
QLabel#DevLabel:hover {{
    color: #3D48D6;
    text-decoration: underline;
}}
QToolButton#ThemeToggleButton {{
    border: 1px solid #D9DCE3;
    border-radius: 15px;
    padding: 5px;
    background-color: #FFFFFF;
}}
QToolButton#ThemeToggleButton:hover {{
    background-color: #F0F2F6;
    border-color: #C7CBD4;
}}
"""


def apply_theme(app: QApplication, theme_name: str) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    if theme_name == "Dark":
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#E5E7EB"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#0B0B0E"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0C0C0F"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#0F0F14"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#F9FAFB"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#E5E7EB"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#121217"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#E5E7EB"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#1E90FF"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#1E90FF"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#4B5563"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#4B5563"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#4B5563"))
        app.setPalette(palette)
        app.setStyleSheet(STYLE_SHEET_DARK)
    else:
        palette.setColor(QPalette.ColorRole.Window, QColor("#F4F5F8"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#20232B"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F7F8FA"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#20232B"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#20232B"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#20232B"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#4F5DFF"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#4F5DFF"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#9AA0AC"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#9AA0AC"))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#9AA0AC"))
        app.setPalette(palette)
        app.setStyleSheet(STYLE_SHEET_LIGHT)


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# --------------------------------------------------------------------------
# Background worker
# --------------------------------------------------------------------------

class ConversionWorker(QThread):
    rowUpdate = pyqtSignal(int, str, str)       # row, status, message
    overallProgress = pyqtSignal(int, int)       # done, total
    logLine = pyqtSignal(str)
    finishedAll = pyqtSignal(int, int, float)    # ok_count, fail_count, seconds

    def __init__(self, jobs, target_format, precision, options=None, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.target_format = target_format
        self.precision = precision
        self.options = options or {}
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        start = time.time()
        ok_count = 0
        fail_count = 0
        total = len(self.jobs)

        for i, (row, input_path, output_path) in enumerate(self.jobs):
            if self._cancelled:
                self.rowUpdate.emit(row, "Cancelled", "")
                continue

            name = os.path.basename(input_path)
            self.rowUpdate.emit(row, "Converting", "")
            self.logLine.emit(f"Converting {name} -> {self.target_format.upper()} ...")

            result = engine.convert_font(
                input_path, output_path, self.target_format, precision=self.precision, options=self.options
            )

            if result.ok:
                ok_count += 1
                self.rowUpdate.emit(row, "Done", result.message)
                self.logLine.emit(
                    f"  done in {result.seconds:.2f}s — {result.message} -> {os.path.basename(output_path)}"
                )
                if self.options.get("delete_source"):
                    if os.path.exists(output_path) and os.path.abspath(output_path) != os.path.abspath(input_path):
                        try:
                            os.remove(input_path)
                            self.logLine.emit(f"  Deleted original source file: {os.path.basename(input_path)}")
                        except Exception as e:
                            self.logLine.emit(f"  Failed to delete source file {os.path.basename(input_path)}: {e}")
            else:
                fail_count += 1
                self.rowUpdate.emit(row, "Failed", result.message)
                self.logLine.emit(f"  FAILED: {result.message}")

            self.overallProgress.emit(i + 1, total)

        self.finishedAll.emit(ok_count, fail_count, time.time() - start)


class PDFUnlockWorker(QThread):
    rowUpdate = pyqtSignal(int, str, str)       # row, status, message
    overallProgress = pyqtSignal(int, int)       # done, total
    logLine = pyqtSignal(str)
    finishedAll = pyqtSignal(int, int, float)    # ok_count, fail_count, seconds

    def __init__(self, jobs, default_password, compress=False, options=None, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.default_password = default_password
        self.compress = compress
        self.options = options or {}
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        start = time.time()
        ok_count = 0
        fail_count = 0
        total = len(self.jobs)

        for i, (row, input_path, output_path, file_password) in enumerate(self.jobs):
            if self._cancelled:
                self.rowUpdate.emit(row, "Cancelled", "")
                continue

            name = os.path.basename(input_path)
            # Indicate unlocking or compressing depending on state
            act_name = "Processing" if self.compress else "Unlocking"
            self.rowUpdate.emit(row, act_name, "")
            self.logLine.emit(f"Processing {name} ...")

            passwords_to_try = []
            if file_password:
                passwords_to_try.append(file_password)
            if self.default_password:
                passwords_to_try.append(self.default_password)
            if "" not in passwords_to_try:
                passwords_to_try.append("")

            cleaned_passwords = []
            for p in passwords_to_try:
                if p is not None and p not in cleaned_passwords:
                    cleaned_passwords.append(p)

            success = False
            last_message = "Unknown error"
            
            for pwd in cleaned_passwords:
                res = engine.unlock_pdf(input_path, output_path, pwd, compress=self.compress)
                if res.ok:
                    result = res
                    success = True
                    break
                else:
                    result = res
                    last_message = res.message

            if success and result:
                ok_count += 1
                self.rowUpdate.emit(row, "Done", result.message)
                self.logLine.emit(
                    f"  done in {result.seconds:.2f}s — {result.message} -> {os.path.basename(output_path)}"
                )
                if self.options.get("delete_source"):
                    if os.path.exists(output_path) and os.path.abspath(output_path) != os.path.abspath(input_path):
                        try:
                            os.remove(input_path)
                            self.logLine.emit(f"  Deleted original source file: {os.path.basename(input_path)}")
                        except Exception as e:
                            self.logLine.emit(f"  Failed to delete source file {os.path.basename(input_path)}: {e}")
            else:
                fail_count += 1
                self.rowUpdate.emit(row, "Failed", last_message)
                self.logLine.emit(f"  FAILED: {last_message}")

            self.overallProgress.emit(i + 1, total)

        self.finishedAll.emit(ok_count, fail_count, time.time() - start)


class ImageWorker(QThread):
    rowUpdate = pyqtSignal(int, str, str)       # row, status, message
    overallProgress = pyqtSignal(int, int)       # done, total
    logLine = pyqtSignal(str)
    finishedAll = pyqtSignal(int, int, float)    # ok_count, fail_count, seconds

    def __init__(self, jobs, target_format, quality, options=None, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.target_format = target_format
        self.quality = quality
        self.options = options or {}
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        start = time.time()
        ok_count = 0
        fail_count = 0
        total = len(self.jobs)

        for i, (row, input_path, output_path) in enumerate(self.jobs):
            if self._cancelled:
                self.rowUpdate.emit(row, "Cancelled", "")
                continue

            name = os.path.basename(input_path)
            self.rowUpdate.emit(row, "Converting", "")
            self.logLine.emit(f"Converting {name} -> {self.target_format.upper()} ...")

            result = engine.convert_image(input_path, output_path, self.target_format, self.quality)

            if result.ok:
                ok_count += 1
                self.rowUpdate.emit(row, "Done", result.message)
                self.logLine.emit(
                    f"  done in {result.seconds:.2f}s — {result.message} -> {os.path.basename(output_path)}"
                )
                if self.options.get("delete_source"):
                    if os.path.exists(output_path) and os.path.abspath(output_path) != os.path.abspath(input_path):
                        try:
                            os.remove(input_path)
                            self.logLine.emit(f"  Deleted original source image: {os.path.basename(input_path)}")
                        except Exception as e:
                            self.logLine.emit(f"  Failed to delete source image {os.path.basename(input_path)}: {e}")
            else:
                fail_count += 1
                self.rowUpdate.emit(row, "Failed", result.message)
                self.logLine.emit(f"  FAILED: {result.message}")

            self.overallProgress.emit(i + 1, total)

        self.finishedAll.emit(ok_count, fail_count, time.time() - start)


# --------------------------------------------------------------------------
# Custom Notification Toaster at Top Right
# --------------------------------------------------------------------------

class ToastNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToastNotification")
        self.setFixedWidth(290)
        self.setFixedHeight(64)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 10, 10)
        layout.setSpacing(10)
        
        # Icon Label
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_lbl)
        
        # Text Content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_lbl = QLabel()
        self.title_lbl.setStyleSheet("font-weight: 700; font-size: 12px; color: #FFFFFF;")
        self.body_lbl = QLabel()
        self.body_lbl.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        self.body_lbl.setWordWrap(True)
        
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.body_lbl)
        layout.addLayout(text_layout, 1)
        
        # Close Button
        self.btn_close = QToolButton()
        self.btn_close.setIcon(qta.icon("fa5s.times", color="#9CA3AF"))
        self.btn_close.setIconSize(QSize(10, 10))
        self.btn_close.setAutoRaise(True)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.hide_animated)
        self.btn_close.setStyleSheet("QToolButton:hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 4px; }")
        layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Opacity & Slide animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        self.hide()
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_animated)
        
        self.pos_anim = None
        self.opacity_anim = None
        self.anim_group = None

    def show_toast(self, title: str, body: str, toast_type: str = "info", duration_ms: int = 3500):
        # Stop existing animations
        if self.anim_group and self.anim_group.state() == QParallelAnimationGroup.State.Running:
            self.anim_group.stop()
        self.timer.stop()
        
        self.title_lbl.setText(title)
        self.body_lbl.setText(body)
        
        # Apply specific icons & colors based on type
        accent_color = "#1E90FF"
        icon_name = "fa5s.info-circle"
        
        if toast_type == "success":
            accent_color = "#10B981"
            icon_name = "fa5s.check-circle"
        elif toast_type == "error":
            accent_color = "#EF4444"
            icon_name = "fa5s.exclamation-circle"
        elif toast_type == "warning":
            accent_color = "#F59E0B"
            icon_name = "fa5s.exclamation-triangle"
            
        self.icon_lbl.setPixmap(qta.icon(icon_name, color=accent_color).pixmap(QSize(18, 18)))
        
        theme_name = self.parent().current_theme if hasattr(self.parent(), "current_theme") else "Dark"
        if theme_name == "Dark":
            self.setStyleSheet(f"""
                QWidget#ToastNotification {{
                    background-color: rgba(15, 15, 20, 0.95);
                    border: 1px solid {accent_color};
                    border-radius: 8px;
                }}
            """)
            self.title_lbl.setStyleSheet("font-weight: 700; font-size: 12px; color: #FFFFFF;")
            self.body_lbl.setStyleSheet("font-size: 11px; color: #9CA3AF;")
            self.btn_close.setIcon(qta.icon("fa5s.times", color="#9CA3AF"))
            self.btn_close.setStyleSheet("QToolButton:hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 4px; }")
        else:
            self.setStyleSheet(f"""
                QWidget#ToastNotification {{
                    background-color: rgba(255, 255, 255, 0.98);
                    border: 1px solid {accent_color};
                    border-radius: 8px;
                }}
            """)
            self.title_lbl.setStyleSheet("font-weight: 700; font-size: 12px; color: #20232B;")
            self.body_lbl.setStyleSheet("font-size: 11px; color: #6B7280;")
            self.btn_close.setIcon(qta.icon("fa5s.times", color="#6B7280"))
            self.btn_close.setStyleSheet("QToolButton:hover { background-color: rgba(0, 0, 0, 0.05); border-radius: 4px; }")
            
        self.show()
        self.raise_()
        
        # Position calculations: top right corner of parent
        parent_w = self.parent().width()
        target_x = parent_w - self.width() - 20
        start_x = parent_w  # Slide in from right edge
        target_y = 50       # Just below custom titlebar
        
        self.move(start_x, target_y)
        
        # Create sliding animation
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(300)
        self.pos_anim.setStartValue(QPoint(start_x, target_y))
        self.pos_anim.setEndValue(QPoint(target_x, target_y))
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Create opacity animation
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(1.0)
        
        # Parallel group
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.pos_anim)
        self.anim_group.addAnimation(self.opacity_anim)
        self.anim_group.start()
        
        self.timer.start(duration_ms)

    def hide_animated(self):
        if self.anim_group and self.anim_group.state() == QParallelAnimationGroup.State.Running:
            self.anim_group.stop()
        self.timer.stop()
        
        parent_w = self.parent().width()
        target_x = parent_w  # Slide back out to right edge
        target_y = self.y()
        
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(250)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(target_x, target_y))
        self.pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(250)
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(0.0)
        
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.pos_anim)
        self.anim_group.addAnimation(self.opacity_anim)
        self.anim_group.finished.connect(self.hide)
        self.anim_group.start()


# --------------------------------------------------------------------------
# Drag and drop premium glass overlay
# --------------------------------------------------------------------------

class DragOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DragOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Outer layout to provide spacing
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(40, 40, 40, 40)
        
        # Content frame
        self.content_frame = QFrame()
        self.content_frame.setObjectName("DragOverlayContent")
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(15)
        
        # Glowing thumbtack/pin icon instead of cloud
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.icon_label)
        
        # Header text
        self.text_label = QLabel("Drop Font Files Here")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.text_label)
        
        # Subtext
        self.subtext = QLabel("Drag any font files (.ttf, .otf, .woff, .woff2, .eot, .svg) to convert")
        self.subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.subtext)
        
        outer_layout.addWidget(self.content_frame)
        
        self.on_theme_changed("Dark")
        
        # Opacity effect for animations
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)
        self.hide()
        
        # Animation
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(220)

    def on_theme_changed(self, theme_name: str):
        if theme_name == "Dark":
            self.setStyleSheet("""
                QWidget#DragOverlay {
                    background-color: rgba(0, 0, 0, 0.4);
                }
                QFrame#DragOverlayContent {
                    background-color: rgba(11, 11, 14, 0.85);
                    border: 3px dashed #1E90FF;
                    border-radius: 16px;
                }
            """)
            self.icon_label.setPixmap(qta.icon("fa5s.thumbtack", color="#1E90FF").pixmap(QSize(96, 96)))
            self.text_label.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: 800; font-family: system-ui;")
            self.subtext.setStyleSheet("color: #9CA3AF; font-size: 13px; font-weight: 500;")
        else:
            self.setStyleSheet("""
                QWidget#DragOverlay {
                    background-color: rgba(0, 0, 0, 0.2);
                }
                QFrame#DragOverlayContent {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 3px dashed #4F5DFF;
                    border-radius: 16px;
                }
            """)
            self.icon_label.setPixmap(qta.icon("fa5s.thumbtack", color="#4F5DFF").pixmap(QSize(96, 96)))
            self.text_label.setStyleSheet("color: #20232B; font-size: 22px; font-weight: 800; font-family: system-ui;")
            self.subtext.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 500;")

    def show_animated(self):
        if self.isVisible() and self.effect.opacity() == 1.0:
            return
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()

    def hide_animated(self):
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        try:
            self.anim.finished.disconnect(self._on_hide_finished)
        except TypeError:
            pass
        if self.effect.opacity() == 0.0:
            self.hide()


# --------------------------------------------------------------------------
# About Section custom modal overlay
# --------------------------------------------------------------------------

class AboutOverlay(QWidget):
    closeRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AboutOverlay")
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.setContentsMargins(50, 50, 50, 50)
        
        self.card = QFrame()
        self.card.setObjectName("AboutCard")
        self.card.setFixedWidth(440)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 20, 24, 24)
        card_layout.setSpacing(14)
        
        # Header with Title and Close 'X'
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        self.title_lbl = QLabel(APP_NAME)
        self.version_lbl = QLabel("Version 1.0.0  ·  Stable Release")
        
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.version_lbl)
        header_row.addLayout(title_box)
        
        header_row.addStretch(1)
        
        self.btn_close_x = QToolButton()
        self.btn_close_x.setIconSize(QSize(14, 14))
        self.btn_close_x.setAutoRaise(True)
        self.btn_close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_x.clicked.connect(self.closeRequested.emit)
        header_row.addWidget(self.btn_close_x, alignment=Qt.AlignmentFlag.AlignTop)
        
        card_layout.addLayout(header_row)
        
        # Separator line
        self.div = QFrame()
        self.div.setFrameShape(QFrame.Shape.HLine)
        card_layout.addWidget(self.div)
        
        # Developer info section
        self.dev_lbl = QLabel("Developed by")
        self.dev_name = QLabel("Krishna Mohan Gupta")
        
        dev_box = QVBoxLayout()
        dev_box.setSpacing(2)
        dev_box.addWidget(self.dev_lbl)
        dev_box.addWidget(self.dev_name)
        card_layout.addLayout(dev_box)
        
        # Description Text
        self.desc_lbl = QLabel(
            "A high-performance batch font conversion pipeline designed to convert and "
            "package TrueType (TTF), OpenType (OTF), WOFF/WOFF2 web fonts, and EOT/SVG wrappers "
            "fully offline."
        )
        self.desc_lbl.setWordWrap(True)
        card_layout.addWidget(self.desc_lbl)
        
        # Formats list / Badges
        self.formats_title = QLabel("Supported Targets")
        card_layout.addWidget(self.formats_title)
        
        self.badges_layout = QHBoxLayout()
        self.badges_layout.setSpacing(6)
        self.badges = []
        for fmt in ["TTF", "OTF", "WOFF", "WOFF2", "EOT", "SVG"]:
            b = QLabel(fmt)
            b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.badges_layout.addWidget(b)
            self.badges.append(b)
        self.badges_layout.addStretch(1)
        card_layout.addLayout(self.badges_layout)
        
        # Bottom Close Button
        self.btn_close = QPushButton("Done")
        self.btn_close.setObjectName("Primary")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.closeRequested.emit)
        card_layout.addWidget(self.btn_close)
        
        outer_layout.addWidget(self.card)
        
        self.on_theme_changed("Dark")
        
        # Opacity animation
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)
        self.hide()
        
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(220)

    def _style_badge(self, b, theme_name):
        if theme_name == "Dark":
            b.setStyleSheet(
                "background-color: #121A2E; color: #1E90FF; font-weight: 800; "
                "font-size: 10px; padding: 4px 8px; border-radius: 6px; border: 1px solid #1A2E5C;"
            )
        else:
            b.setStyleSheet(
                "background-color: #E9EBFF; color: #4F5DFF; font-weight: 800; "
                "font-size: 10px; padding: 4px 8px; border-radius: 6px; border: 1px solid #C4C9FF;"
            )

    def update_content(self, mode: str):
        # Remove old badges
        for b in self.badges:
            b.hide()
            self.badges_layout.removeWidget(b)
            b.deleteLater()
        self.badges.clear()

        # Decide descriptions and formats based on active mode
        if mode == "Font":
            self.title_lbl.setText("FontShift Studio")
            self.desc_lbl.setText(
                "A high-performance batch font conversion pipeline designed to convert and "
                "package TrueType (TTF), OpenType (OTF), WOFF/WOFF2 web fonts, and EOT/SVG wrappers "
                "fully offline."
            )
            formats = ["TTF", "OTF", "WOFF", "WOFF2", "EOT", "SVG"]
        elif mode == "PDF":
            self.title_lbl.setText("PDF Studio")
            self.desc_lbl.setText(
                "A secure, fully offline batch PDF utility designed to decrypt password-protected "
                "PDFs, remove print/copy restrictions, and optimize/compress PDF document structures."
            )
            formats = ["UNLOCK", "COMPRESS", "DECRYPT", "OPTIMIZE"]
        else:  # Image
            self.title_lbl.setText("Image Studio")
            self.desc_lbl.setText(
                "A high-speed batch image converter designed to convert and optimize images "
                "between PNG, JPEG, WEBP, BMP, GIF, and TIFF formats, fully local and offline."
            )
            formats = ["PNG", "JPEG", "WEBP", "BMP", "GIF", "TIFF"]

        # Create new badges
        theme_name = self.parent().current_theme if hasattr(self.parent(), "current_theme") else "Dark"
        for fmt in formats:
            b = QLabel(fmt)
            b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._style_badge(b, theme_name)
            self.badges_layout.insertWidget(self.badges_layout.count() - 1, b)
            self.badges.append(b)

    def on_theme_changed(self, theme_name: str):
        if theme_name == "Dark":
            self.setStyleSheet("""
                QWidget#AboutOverlay {
                    background-color: rgba(0, 0, 0, 0.4);
                }
                QFrame#AboutCard {
                    background-color: #0B0B0E;
                    border: 1px solid #202026;
                    border-radius: 16px;
                }
            """)
            self.title_lbl.setStyleSheet("color: #FFFFFF; font-size: 24px; font-weight: 800; font-family: system-ui;")
            self.version_lbl.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 500;")
            self.btn_close_x.setIcon(qta.icon("fa5s.times", color="#9CA3AF"))
            self.btn_close_x.setStyleSheet("QToolButton:hover { background-color: #202026; border-radius: 4px; }")
            self.div.setStyleSheet("background-color: #202026; max-height: 1px; border: none;")
            self.dev_lbl.setStyleSheet("color: #9CA3AF; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;")
            self.dev_name.setStyleSheet("color: #1E90FF; font-size: 18px; font-weight: 800;")
            self.desc_lbl.setStyleSheet("color: #D1D5DB; font-size: 12px; line-height: 1.4;")
            self.formats_title.setStyleSheet("color: #9CA3AF; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;")
            for b in self.badges:
                self._style_badge(b, theme_name)
        else:
            self.setStyleSheet("""
                QWidget#AboutOverlay {
                    background-color: rgba(0, 0, 0, 0.2);
                }
                QFrame#AboutCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E6E8EC;
                    border-radius: 16px;
                }
            """)
            self.title_lbl.setStyleSheet("color: #20232B; font-size: 24px; font-weight: 800; font-family: system-ui;")
            self.version_lbl.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: 500;")
            self.btn_close_x.setIcon(qta.icon("fa5s.times", color="#6B7280"))
            self.btn_close_x.setStyleSheet("QToolButton:hover { background-color: #EEF0F4; border-radius: 4px; }")
            self.div.setStyleSheet("background-color: #E6E8EC; max-height: 1px; border: none;")
            self.dev_lbl.setStyleSheet("color: #6B7280; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;")
            self.dev_name.setStyleSheet("color: #4F5DFF; font-size: 18px; font-weight: 800;")
            self.desc_lbl.setStyleSheet("color: #374151; font-size: 12px; line-height: 1.4;")
            self.formats_title.setStyleSheet("color: #6B7280; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;")
            for b in self.badges:
                self._style_badge(b, theme_name)

    def show_animated(self):
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()

    def hide_animated(self):
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        try:
            self.anim.finished.disconnect(self._on_hide_finished)
        except TypeError:
            pass
        if self.effect.opacity() == 0.0:
            self.hide()


class CloseConfirmOverlay(QWidget):
    closeConfirmed = pyqtSignal()
    closeCancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CloseConfirmOverlay")
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.setContentsMargins(50, 50, 50, 50)
        
        self.card = QFrame()
        self.card.setObjectName("ConfirmCard")
        self.card.setFixedWidth(360)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)
        
        # Icon & Title Row
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon("fa5s.exclamation-triangle", color=DANGER).pixmap(QSize(24, 24)))
        header_row.addWidget(self.icon_lbl)
        
        self.title_lbl = QLabel("Exit Application?")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF;")
        header_row.addWidget(self.title_lbl)
        header_row.addStretch(1)
        card_layout.addLayout(header_row)
        
        # Message Text
        self.msg_lbl = QLabel("Are you sure you want to quit? Any unsaved list progress will be lost.")
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("color: #D1D5DB; font-size: 12px; line-height: 1.4;")
        card_layout.addWidget(self.msg_lbl)
        
        # Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("Ghost")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.closeCancelled.emit)
        
        self.btn_confirm = QPushButton("Yes, Exit")
        self.btn_confirm.setObjectName("Primary")
        self.btn_confirm.setStyleSheet("""
            QPushButton#Primary {
                background-color: #EF4444;
                border: 1px solid #DC2626;
            }
            QPushButton#Primary:hover {
                background-color: #DC2626;
            }
        """)
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.clicked.connect(self.closeConfirmed.emit)
        
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_confirm)
        card_layout.addLayout(btn_row)
        
        outer_layout.addWidget(self.card)
        
        self.on_theme_changed("Dark")
        
        # Opacity animation
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)
        self.hide()
        
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(200)

    def on_theme_changed(self, theme_name: str):
        if theme_name == "Dark":
            self.setStyleSheet("""
                QWidget#CloseConfirmOverlay {
                    background-color: rgba(0, 0, 0, 0.4);
                }
                QFrame#ConfirmCard {
                    background-color: #0B0B0E;
                    border: 1px solid #202026;
                    border-radius: 16px;
                }
                QPushButton#Ghost {
                    border: 1px solid #1F2026;
                    background-color: #121217;
                    color: #E5E7EB;
                }
                QPushButton#Ghost:hover {
                    background-color: #1C1E26;
                    border-color: #374151;
                }
            """)
            self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF;")
            self.msg_lbl.setStyleSheet("color: #D1D5DB; font-size: 12px; line-height: 1.4;")
        else:
            self.setStyleSheet("""
                QWidget#CloseConfirmOverlay {
                    background-color: rgba(0, 0, 0, 0.2);
                }
                QFrame#ConfirmCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E6E8EC;
                    border-radius: 16px;
                }
                QPushButton#Ghost {
                    border: 1px solid #E6E8EC;
                    background-color: #F4F5F8;
                    color: #20232B;
                }
                QPushButton#Ghost:hover {
                    background-color: #EEF0F4;
                }
            """)
            self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #20232B;")
            self.msg_lbl.setStyleSheet("color: #4B5563; font-size: 12px; line-height: 1.4;")

    def show_animated(self):
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()

    def hide_animated(self):
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        try:
            self.anim.finished.disconnect(self._on_hide_finished)
        except TypeError:
            pass
        if self.effect.opacity() == 0.0:
            self.hide()


# --------------------------------------------------------------------------
# Custom Frameless Window Title Bar
# --------------------------------------------------------------------------

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)
        
        # Logo Icon
        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(qta.icon("fa5s.font", color=ACCENT).pixmap(QSize(16, 16)))
        layout.addWidget(self.logo_lbl)
        
        # Title Label
        self.title_lbl = QLabel(APP_NAME)
        self.title_lbl.setStyleSheet("color: #E5E7EB; font-size: 12px; font-weight: bold; font-family: system-ui; margin-right: 12px;")
        layout.addWidget(self.title_lbl)
        
        # Integrated Menu Bar
        self.menu_bar = QMenuBar()
        self.menu_bar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.menu_bar)
        
        layout.addStretch(1)
        
        # Window Action Buttons: Minimize and Close only (no Maximize button!)
        self.btn_min = QToolButton()
        self.btn_min.setIcon(qta.icon("fa5s.minus", color="#9CA3AF"))
        self.btn_min.setIconSize(QSize(10, 10))
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_min.setStyleSheet("QToolButton { border: none; padding: 6px; } QToolButton:hover { background-color: #202026; border-radius: 4px; }")
        layout.addWidget(self.btn_min)
        
        self.btn_close = QToolButton()
        self.btn_close.setIcon(qta.icon("fa5s.times", color="#9CA3AF"))
        self.btn_close.setIconSize(QSize(12, 12))
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.parent.close)
        self.btn_close.setStyleSheet("QToolButton { border: none; padding: 6px; } QToolButton:hover { background-color: #EF4444; color: #FFFFFF; border-radius: 4px; }")
        layout.addWidget(self.btn_close)
        
        self.setStyleSheet("""
            QWidget#TitleBar { 
                background-color: #000000; 
                border-bottom: 1px solid #121217; 
                border-top-left-radius: 15px; 
                border-top-right-radius: 15px; 
            }
        """)
        
        self._drag_active = False
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.parent.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active:
            self.parent.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        event.accept()


# --------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------

class MainWindow(QMainWindow):
    COL_NAME, COL_FORMAT, COL_SIZE, COL_STATUS = range(4)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1060, 740)
        self.setAcceptDrops(True)
        self.setWindowIcon(qta.icon("fa5s.font", color=ACCENT))
        
        # Transparent background for top level window rounded corners
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint)

        self.current_theme = "Dark"
        self.theme_colors = DARK_THEME_COLORS
        self.current_mode = "Font"
        self.input_exts = INPUT_EXTS
        self.worker: ConversionWorker | PDFUnlockWorker | None = None
        
        self.blur_effect: QGraphicsBlurEffect | None = None
        self.blur_anim: QPropertyAnimation | None = None
        
        self._build_ui()
        
        # Create Menu Bar
        self._build_menu_bar()
        
        # Premium Drag Overlay
        self.drag_overlay = DragOverlay(self)
        self.drag_overlay.setGeometry(self.rect())
        
        # Premium About Overlay
        self.about_overlay = AboutOverlay(self)
        self.about_overlay.setGeometry(self.rect())
        self.about_overlay.closeRequested.connect(self.hide_about_overlay)
        
        self._allow_close = False
        # Premium Close Confirmation Overlay
        self.confirm_overlay = CloseConfirmOverlay(self)
        self.confirm_overlay.setGeometry(self.rect())
        self.confirm_overlay.closeConfirmed.connect(self.confirm_exit)
        self.confirm_overlay.closeCancelled.connect(self.hide_close_confirm_overlay)
        
        # Custom Toast Notification
        self.toast = ToastNotification(self)
        
        self.on_theme_changed("Dark")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "drag_overlay") and self.drag_overlay:
            self.drag_overlay.setGeometry(self.rect())
        if hasattr(self, "about_overlay") and self.about_overlay:
            self.about_overlay.setGeometry(self.rect())
        if hasattr(self, "confirm_overlay") and self.confirm_overlay:
            self.confirm_overlay.setGeometry(self.rect())
        if hasattr(self, "toast") and self.toast and self.toast.isVisible():
            parent_w = self.width()
            target_x = parent_w - self.toast.width() - 20
            self.toast.move(target_x, 50)

    # -- UI construction ---------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(1, 1, 1, 1) # Window border thickness
        outer_layout.setSpacing(0)
        
        # Custom Title Bar
        self.title_bar = CustomTitleBar(self)
        outer_layout.addWidget(self.title_bar)
        
        # Main layout container
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(18, 14, 18, 12)
        body_layout.setSpacing(10)
        
        # Header Row
        body_layout.addLayout(self._build_header())
        
        # Main Body Splitter
        body = QHBoxLayout()
        body.setSpacing(14)
        body.addLayout(self._build_files_column(), 3)
        body.addWidget(self._build_options_column(), 2)
        body_layout.addLayout(body, 1)
        
        # Bottom Activity Log
        body_layout.addWidget(self._build_log_panel())
        
        outer_layout.addWidget(body_widget, 1)

        self._build_statusbar(outer_layout)

    def _build_header(self):
        row = QHBoxLayout()
        self.header_icon_lbl = QLabel()
        self.header_icon_lbl.setPixmap(qta.icon("fa5s.exchange-alt", color=ACCENT).pixmap(QSize(28, 28)))
        row.addWidget(self.header_icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self.header_title_lbl = QLabel(APP_NAME)
        self.header_title_lbl.setObjectName("Title")
        self.header_subtitle_lbl = QLabel("Professional Batch Font Converter & Optimizer")
        self.header_subtitle_lbl.setObjectName("Subtitle")
        title_box.addWidget(self.header_title_lbl)
        title_box.addWidget(self.header_subtitle_lbl)
        row.addLayout(title_box)
        row.addStretch(1)
        
        # Modern Sun/Moon Theme Toggle Button
        self.btn_theme_toggle = QToolButton()
        self.btn_theme_toggle.setObjectName("ThemeToggleButton")
        self.btn_theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_toggle.setIconSize(QSize(16, 16))
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        row.addWidget(self.btn_theme_toggle)
        
        return row

    def toggle_theme(self):
        if self.current_theme == "Dark":
            self.current_theme = "Light"
        else:
            self.current_theme = "Dark"
        self.on_theme_changed(self.current_theme)

    def switch_mode(self, mode):
        self.current_mode = mode
        self.clear_all()  # clear current queue
        
        # Update visibility of menu navigation links
        if hasattr(self, "menu_act_font") and self.menu_act_font:
            self.menu_act_font.setVisible(mode != "Font")
        if hasattr(self, "menu_act_pdf") and self.menu_act_pdf:
            self.menu_act_pdf.setVisible(mode != "PDF")
        if hasattr(self, "menu_act_image") and self.menu_act_image:
            self.menu_act_image.setVisible(mode != "Image")

        if mode == "Font":
            # Update title & headers
            self.title_bar.title_lbl.setText("FontShift Studio")
            self.title_bar.logo_lbl.setPixmap(qta.icon("fa5s.font", color=ACCENT).pixmap(QSize(16, 16)))
            self.header_title_lbl.setText("FontShift Studio")
            self.header_subtitle_lbl.setText("Professional Batch Font Converter & Optimizer")
            self.header_icon_lbl.setPixmap(qta.icon("fa5s.exchange-alt", color=ACCENT).pixmap(QSize(28, 28)))
            
            # Switch options widgets
            self.pdf_options_widget.hide()
            self.image_options_widget.hide()
            self.font_options_widget.show()
            
            # Reset table columns
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.setHorizontalHeaderItem(self.COL_FORMAT, QTableWidgetItem("Format"))
            
            # Reset inputs and search filters
            self.input_exts = (".ttf", ".otf", ".woff", ".woff2", ".eot", ".svg")
            self.drag_overlay.text_label.setText("Drop Font Files Here")
            self.drag_overlay.subtext.setText("Drag any font files (.ttf, .otf, .woff, .woff2, .eot, .svg) to convert")
            
            # Update main action button
            self.btn_convert.setText("  Convert All")
            self.btn_convert.setIcon(qta.icon("fa5s.bolt", color="white"))
            
        elif mode == "PDF":
            # Update title & headers
            self.title_bar.title_lbl.setText("PDF Studio")
            self.title_bar.logo_lbl.setPixmap(qta.icon("fa5s.unlock", color=ACCENT).pixmap(QSize(16, 16)))
            self.header_title_lbl.setText("PDF Studio")
            self.header_subtitle_lbl.setText("Professional PDF Decryption & Restriction Remover")
            self.header_icon_lbl.setPixmap(qta.icon("fa5s.unlock-alt", color=ACCENT).pixmap(QSize(28, 28)))
            
            # Switch options widgets
            self.font_options_widget.hide()
            self.image_options_widget.hide()
            self.pdf_options_widget.show()
            
            # Reset table columns and allow editing of Column 1 (Password)
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
            self.table.setHorizontalHeaderItem(self.COL_FORMAT, QTableWidgetItem("Password (Optional)"))
            
            # Reset inputs and search filters
            self.input_exts = (".pdf",)
            self.drag_overlay.text_label.setText("Drop PDF Files Here")
            self.drag_overlay.subtext.setText("Drag any PDF files (.pdf) to decrypt and unlock")
            
            # Update main action button
            self.btn_convert.setText("  Unlock All")
            self.btn_convert.setIcon(qta.icon("fa5s.unlock-alt", color="white"))
            
        else:  # Image Mode
            # Update title & headers
            self.title_bar.title_lbl.setText("Image Studio")
            self.title_bar.logo_lbl.setPixmap(qta.icon("fa5s.image", color=ACCENT).pixmap(QSize(16, 16)))
            self.header_title_lbl.setText("Image Studio")
            self.header_subtitle_lbl.setText("Professional Batch Image Format Converter & Optimizer")
            self.header_icon_lbl.setPixmap(qta.icon("fa5s.file-image", color=ACCENT).pixmap(QSize(28, 28)))
            
            # Switch options widgets
            self.font_options_widget.hide()
            self.pdf_options_widget.hide()
            self.image_options_widget.show()
            
            # Reset table columns to read-only format
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.setHorizontalHeaderItem(self.COL_FORMAT, QTableWidgetItem("Source Format"))
            
            # Reset inputs and search filters
            self.input_exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff")
            self.drag_overlay.text_label.setText("Drop Image Files Here")
            self.drag_overlay.subtext.setText("Drag any image files (.png, .jpg, .jpeg, .webp, .bmp, .gif, .tiff) to convert")
            
            # Update main action button
            self.btn_convert.setText("  Convert Images")
            self.btn_convert.setIcon(qta.icon("fa5s.images", color="white"))
            
        # Apply theme styling updates
        self.on_theme_changed(self.current_theme)

    def _on_pdf_action_changed(self, text):
        if text == "Compress Only":
            self.txt_default_password.setEnabled(False)
            self.txt_default_password.setPlaceholderText("Password not required")
        else:
            self.txt_default_password.setEnabled(True)
            self.txt_default_password.setPlaceholderText("Enter default password...")

    def _on_quality_changed(self, val):
        self.lbl_image_quality.setText(f"Quality: {val}%")

    def _on_image_format_changed(self, fmt):
        if fmt in ("JPEG", "WEBP"):
            self.slider_image_quality.setEnabled(True)
            self.lbl_image_quality.setEnabled(True)
        else:
            self.slider_image_quality.setEnabled(False)
            self.lbl_image_quality.setEnabled(False)

    def _build_menu_bar(self):
        menubar = self.title_bar.menu_bar
        
        # File Menu
        self.file_menu = menubar.addMenu("&File")
        
        self.add_files_act = self.file_menu.addAction(qta.icon("fa5s.file-import", color=ACCENT), "Add &Files...")
        self.add_files_act.setShortcut("Ctrl+O")
        self.add_files_act.triggered.connect(self.add_files)
        
        self.add_folder_act = self.file_menu.addAction(qta.icon("fa5s.folder-plus", color=ACCENT), "Add &Folder...")
        self.add_folder_act.setShortcut("Ctrl+D")
        self.add_folder_act.triggered.connect(self.add_folder)
        
        self.file_menu.addSeparator()
        
        # Dynamic mode switcher actions
        self.menu_act_font = self.file_menu.addAction(qta.icon("fa5s.font", color=ACCENT), "Font Studio")
        self.menu_act_font.triggered.connect(lambda: self.switch_mode("Font"))

        self.menu_act_pdf = self.file_menu.addAction(qta.icon("fa5s.unlock", color=ACCENT), "PDF Studio (PDF Unlock)")
        self.menu_act_pdf.triggered.connect(lambda: self.switch_mode("PDF"))

        self.menu_act_image = self.file_menu.addAction(qta.icon("fa5s.image", color=ACCENT), "Image Studio")
        self.menu_act_image.triggered.connect(lambda: self.switch_mode("Image"))
        
        # Initially hide the current active mode link
        self.menu_act_font.setVisible(False)
        
        self.file_menu.addSeparator()
        
        self.clear_act = self.file_menu.addAction(qta.icon("fa5s.broom", color=ACCENT), "&Clear All")
        self.clear_act.setShortcut("Ctrl+L")
        self.clear_act.triggered.connect(self.clear_all)
        
        self.file_menu.addSeparator()
        
        self.exit_act = self.file_menu.addAction(qta.icon("fa5s.times-circle", color=DANGER), "E&xit")
        self.exit_act.setShortcut("Ctrl+Q")
        self.exit_act.triggered.connect(self.close)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        about_act = help_menu.addAction(qta.icon("fa5s.info-circle", color=ACCENT), "&About")
        about_act.setShortcut("F1")
        about_act.triggered.connect(self.show_about_dialog)

    # -- Files column (Left side) -------------------------------------------

    def _build_files_column(self):
        col = QVBoxLayout()
        col.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_add_files = self._btn("Add Files", "fa5s.file-import", self.add_files)
        self.btn_add_folder = self._btn("Add Folder", "fa5s.folder-plus", self.add_folder)
        self.btn_remove = self._btn("Remove", "fa5s.trash-alt", self.remove_selected)
        self.btn_clear = self._btn("Clear All", "fa5s.broom", self.clear_all)

        toolbar.addWidget(self.btn_add_files)
        toolbar.addWidget(self.btn_add_folder)
        toolbar.addWidget(self.btn_remove)
        toolbar.addWidget(self.btn_clear)
        toolbar.addStretch(1)
        
        # Search & Filter QLineEdit with magnifying glass icon inside
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter files...")
        self.txt_search.setFixedWidth(160)
        self.txt_search.textChanged.connect(self._filter_table)
        self.txt_search.addAction(
            qta.icon("fa5s.search", color=self.theme_colors['text_muted']),
            QLineEdit.ActionPosition.LeadingPosition
        )
        toolbar.addWidget(self.txt_search)
        
        self.lbl_count = QLabel("0 files")
        self.lbl_count.setObjectName("Subtitle")
        toolbar.addWidget(self.lbl_count)
        col.addLayout(toolbar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File", "Format", "Size", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Clean arranged column sizes
        self.table.horizontalHeader().setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(self.COL_FORMAT, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(self.COL_SIZE, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(self.COL_FORMAT, 90)
        self.table.setColumnWidth(self.COL_SIZE, 90)
        self.table.setColumnWidth(self.COL_STATUS, 130)
        self.table.setMinimumHeight(280)
        
        # Column sorting
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().sectionClicked.connect(self._sort_table)
        
        col.addWidget(self.table, 1)

        # drop hint
        self.drop_hint = QLabel("Drag & drop font files or folders here")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setStyleSheet(f"color: {TEXT_MUTED_DARK}; font-size: 12px; padding: 6px;")
        col.addWidget(self.drop_hint)

        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        progress_row.addWidget(self.progress, 1)
        self.lbl_progress = QLabel("")
        self.lbl_progress.setObjectName("Subtitle")
        progress_row.addWidget(self.lbl_progress)
        col.addLayout(progress_row)

        action_row = QHBoxLayout()
        self.btn_convert = QPushButton("  Convert All")
        self.btn_convert.setObjectName("Primary")
        self.btn_convert.setIcon(qta.icon("fa5s.bolt", color="white"))
        self.btn_convert.clicked.connect(self.start_conversion)

        self.btn_cancel = self._btn("Cancel", "fa5s.times", self.cancel_conversion)
        self.btn_cancel.setVisible(False)

        self.btn_open_output = self._btn("Open Output Folder", "fa5s.folder-open", self.open_output_folder)

        action_row.addWidget(self.btn_convert)
        action_row.addWidget(self.btn_cancel)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_open_output)
        col.addLayout(action_row)

        return col

    def _btn(self, text, icon_name, slot, color="#3B82F6"):
        b = QPushButton(f"  {text}" if text else "")
        b.setIcon(qta.icon(icon_name, color=color))
        b.setIconSize(QSize(14, 14))
        b.clicked.connect(slot)
        return b

    # -- Options sidebar (Right side) ---------------------------------------

    def _build_options_column(self):
        self.options_scroll = QScrollArea()
        self.options_scroll.setObjectName("OptionsScrollArea")
        self.options_scroll.setWidgetResizable(True)
        self.options_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.options_scroll.viewport().setStyleSheet("background: transparent;")

        container = QWidget()
        container.setObjectName("OptionsContainer")
        container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # ---------------- FONT OPTIONS WIDGET ----------------
        self.font_options_widget = QWidget()
        font_layout = QVBoxLayout(self.font_options_widget)
        font_layout.setContentsMargins(0, 0, 0, 0)
        font_layout.setSpacing(10)

        # target format card
        fmt_group = QFrame()
        fmt_group.setObjectName("OptionCard")
        fmt_layout = QVBoxLayout(fmt_group)
        fmt_layout.setContentsMargins(12, 12, 12, 12)
        fmt_layout.setSpacing(6)
        
        lbl_fmt = QLabel("Convert to")
        lbl_fmt.setObjectName("SectionLabel")
        fmt_layout.addWidget(lbl_fmt)
        
        self.combo_format = QComboBox()
        self.combo_format.addItems(["OTF", "TTF", "WOFF", "WOFF2", "EOT", "SVG"])
        
        self.combo_format.setItemIcon(0, qta.icon("fa5s.font", color=ACCENT))
        self.combo_format.setItemIcon(1, qta.icon("fa5s.font", color=ACCENT))
        self.combo_format.setItemIcon(2, qta.icon("fa5s.compress", color=ACCENT))
        self.combo_format.setItemIcon(3, qta.icon("fa5s.compress", color=ACCENT))
        self.combo_format.setItemIcon(4, qta.icon("fa5s.file-code", color=ACCENT))
        self.combo_format.setItemIcon(5, qta.icon("fa5s.code", color=ACCENT))
        
        fmt_layout.addWidget(self.combo_format)
        self.lbl_format_hint = QLabel("TrueType outlines are converted to real CFF curves.")
        self.lbl_format_hint.setObjectName("Subtitle")
        self.lbl_format_hint.setWordWrap(True)
        fmt_layout.addWidget(self.lbl_format_hint)
        self.combo_format.currentTextChanged.connect(self._update_format_hint)
        font_layout.addWidget(fmt_group)

        # precision card
        prec_group = QFrame()
        prec_group.setObjectName("OptionCard")
        prec_layout = QVBoxLayout(prec_group)
        prec_layout.setContentsMargins(12, 12, 12, 12)
        prec_layout.setSpacing(6)
        
        lbl_prec = QLabel("Conversion precision")
        lbl_prec.setObjectName("SectionLabel")
        prec_layout.addWidget(lbl_prec)
        
        self.combo_precision = QComboBox()
        self.combo_precision.addItems(list(engine.PRECISION_PRESETS.keys()))
        self.combo_precision.setCurrentText("Balanced")
        
        prec_layout.addWidget(self.combo_precision)
        prec_hint = QLabel("Fast is lightest, Precise keeps curves closest to the original.")
        prec_hint.setObjectName("Subtitle")
        prec_hint.setWordWrap(True)
        prec_layout.addWidget(prec_hint)
        font_layout.addWidget(prec_group)

        # output location card
        out_group = QFrame()
        out_group.setObjectName("OptionCard")
        out_layout = QVBoxLayout(out_group)
        out_layout.setContentsMargins(12, 12, 12, 12)
        out_layout.setSpacing(8)
        
        lbl_out = QLabel("Output options")
        lbl_out.setObjectName("SectionLabel")
        out_layout.addWidget(lbl_out)

        self.chk_overwrite = QCheckBox("Overwrite existing files")
        self.chk_overwrite.setChecked(True)
        out_layout.addWidget(self.chk_overwrite)
        
        self.chk_delete_source = QCheckBox("Delete source files after conversion")
        self.chk_delete_source.setChecked(True)
        out_layout.addWidget(self.chk_delete_source)
        font_layout.addWidget(out_group)

        layout.addWidget(self.font_options_widget)

        # ---------------- PDF OPTIONS WIDGET ----------------
        self.pdf_options_widget = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_options_widget)
        pdf_layout.setContentsMargins(0, 0, 0, 0)
        pdf_layout.setSpacing(10)

        # Task Action Card
        pdf_act_card = QFrame()
        pdf_act_card.setObjectName("OptionCard")
        pdf_act_layout = QVBoxLayout(pdf_act_card)
        pdf_act_layout.setContentsMargins(12, 12, 12, 12)
        pdf_act_layout.setSpacing(6)

        lbl_pdf_act = QLabel("PDF Task")
        lbl_pdf_act.setObjectName("SectionLabel")
        pdf_act_layout.addWidget(lbl_pdf_act)

        self.combo_pdf_action = QComboBox()
        self.combo_pdf_action.addItems(["Unlock Only", "Compress Only", "Unlock & Compress"])
        self.combo_pdf_action.setItemIcon(0, qta.icon("fa5s.unlock", color=ACCENT))
        self.combo_pdf_action.setItemIcon(1, qta.icon("fa5s.compress-arrows-alt", color=ACCENT))
        self.combo_pdf_action.setItemIcon(2, qta.icon("fa5s.file-signature", color=ACCENT))
        pdf_act_layout.addWidget(self.combo_pdf_action)

        pdf_act_hint = QLabel("Select whether to decrypt, compress, or perform both operations on the PDFs.")
        pdf_act_hint.setObjectName("Subtitle")
        pdf_act_hint.setWordWrap(True)
        pdf_act_layout.addWidget(pdf_act_hint)
        pdf_layout.addWidget(pdf_act_card)

        # default password card
        pdf_pwd_group = QFrame()
        pdf_pwd_group.setObjectName("OptionCard")
        pdf_pwd_layout = QVBoxLayout(pdf_pwd_group)
        pdf_pwd_layout.setContentsMargins(12, 12, 12, 12)
        pdf_pwd_layout.setSpacing(6)

        lbl_pdf_title = QLabel("PDF Unlock Settings")
        lbl_pdf_title.setObjectName("SectionLabel")
        pdf_pwd_layout.addWidget(lbl_pdf_title)

        lbl_pdf_pwd = QLabel("Default Password (Optional)")
        lbl_pdf_pwd.setStyleSheet("font-size: 11px; font-weight: 600; color: #9CA3AF;")
        pdf_pwd_layout.addWidget(lbl_pdf_pwd)

        self.txt_default_password = QLineEdit()
        self.txt_default_password.setPlaceholderText("Enter default password...")
        self.txt_default_password.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        pdf_pwd_layout.addWidget(self.txt_default_password)

        pdf_pwd_hint = QLabel("This password will be tried for password-protected PDFs unless overridden in the file table.")
        pdf_pwd_hint.setObjectName("Subtitle")
        pdf_pwd_hint.setWordWrap(True)
        pdf_pwd_layout.addWidget(pdf_pwd_hint)
        pdf_layout.addWidget(pdf_pwd_group)
        
        self.combo_pdf_action.currentTextChanged.connect(self._on_pdf_action_changed)

        # pdf output options card
        pdf_out_group = QFrame()
        pdf_out_group.setObjectName("OptionCard")
        pdf_out_layout = QVBoxLayout(pdf_out_group)
        pdf_out_layout.setContentsMargins(12, 12, 12, 12)
        pdf_out_layout.setSpacing(8)

        lbl_pdf_out = QLabel("Output options")
        lbl_pdf_out.setObjectName("SectionLabel")
        pdf_out_layout.addWidget(lbl_pdf_out)

        self.chk_pdf_overwrite = QCheckBox("Overwrite existing files")
        self.chk_pdf_overwrite.setChecked(True)
        pdf_out_layout.addWidget(self.chk_pdf_overwrite)

        self.chk_pdf_delete_source = QCheckBox("Delete source files after unlocking")
        self.chk_pdf_delete_source.setChecked(False)
        pdf_out_layout.addWidget(self.chk_pdf_delete_source)
        pdf_layout.addWidget(pdf_out_group)

        layout.addWidget(self.pdf_options_widget)
        self.pdf_options_widget.hide()

        # ---------------- IMAGE OPTIONS WIDGET ----------------
        self.image_options_widget = QWidget()
        image_layout = QVBoxLayout(self.image_options_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(10)

        # target image format card
        img_fmt_group = QFrame()
        img_fmt_group.setObjectName("OptionCard")
        img_fmt_layout = QVBoxLayout(img_fmt_group)
        img_fmt_layout.setContentsMargins(12, 12, 12, 12)
        img_fmt_layout.setSpacing(6)

        lbl_img_fmt = QLabel("Convert to format")
        lbl_img_fmt.setObjectName("SectionLabel")
        img_fmt_layout.addWidget(lbl_img_fmt)

        self.combo_image_format = QComboBox()
        self.combo_image_format.addItems(["PNG", "JPEG", "WEBP", "BMP", "GIF", "TIFF"])
        self.combo_image_format.setItemIcon(0, qta.icon("fa5s.file-image", color=ACCENT))
        self.combo_image_format.setItemIcon(1, qta.icon("fa5s.file-image", color=ACCENT))
        self.combo_image_format.setItemIcon(2, qta.icon("fa5s.file-image", color=ACCENT))
        self.combo_image_format.setItemIcon(3, qta.icon("fa5s.file-image", color=ACCENT))
        self.combo_image_format.setItemIcon(4, qta.icon("fa5s.file-image", color=ACCENT))
        self.combo_image_format.setItemIcon(5, qta.icon("fa5s.file-image", color=ACCENT))
        img_fmt_layout.addWidget(self.combo_image_format)

        # Image quality slider
        self.lbl_image_quality = QLabel("Quality: 85%")
        self.lbl_image_quality.setStyleSheet("font-size: 11px; font-weight: 600; color: #9CA3AF;")
        img_fmt_layout.addWidget(self.lbl_image_quality)

        self.slider_image_quality = QSlider(Qt.Orientation.Horizontal)
        self.slider_image_quality.setRange(1, 100)
        self.slider_image_quality.setValue(85)
        self.slider_image_quality.valueChanged.connect(self._on_quality_changed)
        img_fmt_layout.addWidget(self.slider_image_quality)

        self.lbl_image_hint = QLabel("PNG, BMP, GIF, and TIFF use lossless compression. Quality settings apply only to JPEG and WEBP.")
        self.lbl_image_hint.setObjectName("Subtitle")
        self.lbl_image_hint.setWordWrap(True)
        img_fmt_layout.addWidget(self.lbl_image_hint)
        
        self.combo_image_format.currentTextChanged.connect(self._on_image_format_changed)
        image_layout.addWidget(img_fmt_group)

        # Image output options card
        img_out_group = QFrame()
        img_out_group.setObjectName("OptionCard")
        img_out_layout = QVBoxLayout(img_out_group)
        img_out_layout.setContentsMargins(12, 12, 12, 12)
        img_out_layout.setSpacing(8)

        lbl_img_out = QLabel("Output options")
        lbl_img_out.setObjectName("SectionLabel")
        img_out_layout.addWidget(lbl_img_out)

        self.chk_image_overwrite = QCheckBox("Overwrite existing files")
        self.chk_image_overwrite.setChecked(True)
        img_out_layout.addWidget(self.chk_image_overwrite)

        self.chk_image_delete_source = QCheckBox("Delete source files after conversion")
        self.chk_image_delete_source.setChecked(False)
        img_out_layout.addWidget(self.chk_image_delete_source)
        image_layout.addWidget(img_out_group)

        layout.addWidget(self.image_options_widget)
        self.image_options_widget.hide()

        # footer attribution
        lbl_dev = QLabel("Developed by Krishna Mohan Gupta")
        lbl_dev.setObjectName("DevLabel")
        lbl_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dev.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl_dev.mousePressEvent = lambda e: self.show_about_dialog()
        layout.addWidget(lbl_dev)

        # summary card
        self.lbl_summary = QLabel("Ready.")
        self.lbl_summary.setObjectName("Subtitle")
        self.lbl_summary.setWordWrap(True)
        layout.addWidget(self.lbl_summary)

        layout.addStretch(1)
        self.options_scroll.setWidget(container)
        return self.options_scroll

    def _update_format_hint(self, fmt):
        hints = {
            "OTF": "TrueType outlines are converted to real CFF curves.",
            "TTF": "CFF outlines are converted to real quadratic curves.",
            "WOFF": "Existing outlines are repackaged as compressed WOFF.",
            "WOFF2": "Existing outlines are repackaged as Brotli-compressed WOFF2.",
            "EOT": "TrueType outlines packaged as Embedded OpenType (EOT) format.",
            "SVG": "Outlines exported to an SVG font wrapper XML file.",
        }
        self.lbl_format_hint.setText(hints.get(fmt, ""))

    # -- Bottom Log panel ----------------------------------------------------

    def _build_log_panel(self):
        wrap = QWidget()
        wrap.setObjectName("Card")
        v = QVBoxLayout(wrap)
        v.setContentsMargins(14, 8, 14, 10)
        v.setSpacing(6)

        header = QHBoxLayout()
        lbl = QLabel("Activity Log")
        lbl.setObjectName("SectionLabel")
        header.addWidget(lbl)
        header.addStretch(1)
        self.btn_toggle_log = QToolButton()
        self.btn_toggle_log.setIcon(qta.icon("fa5s.chevron-up", color=TEXT_MUTED_DARK))
        self.btn_toggle_log.setAutoRaise(True)
        self.btn_toggle_log.clicked.connect(self._toggle_log)
        header.addWidget(self.btn_toggle_log)
        v.addLayout(header)

        self.log = QPlainTextEdit()
        self.log.setObjectName("Log")
        self.log.setReadOnly(True)
        self.log.setFixedHeight(120)
        v.addWidget(self.log)

        return wrap

    def _toggle_log(self):
        visible = self.log.isVisible()
        self.log.setVisible(not visible)
        icon = "fa5s.chevron-down" if visible else "fa5s.chevron-up"
        self.btn_toggle_log.setIcon(qta.icon(icon, color=TEXT_MUTED_DARK))

    def _build_statusbar(self, outer_layout):
        # Custom nested statusbar to follow rounded window corners
        self.status_bar_widget = QWidget()
        self.status_bar_widget.setObjectName("StatusBar")
        
        status_layout = QHBoxLayout(self.status_bar_widget)
        status_layout.setContentsMargins(14, 6, 14, 6)
        
        self.lbl_status = QLabel("0 queued  ·  0 done  ·  0 failed")
        self.lbl_status.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        status_layout.addWidget(self.lbl_status)
        status_layout.addStretch(1)
        
        from PyQt6.QtWidgets import QSizeGrip
        self.size_grip = QSizeGrip(self.status_bar_widget)
        status_layout.addWidget(self.size_grip)
        
        outer_layout.addWidget(self.status_bar_widget)

    # -- Drag & Drop --------------------------------------------------------

    def show_drag_overlay(self):
        if hasattr(self, "drag_overlay") and self.drag_overlay:
            self.drag_overlay.show_animated()
            
            # Animate blur effect on central widget
            if not self.blur_effect:
                self.blur_effect = QGraphicsBlurEffect(self)
                self.centralWidget().setGraphicsEffect(self.blur_effect)
            
            if self.blur_anim:
                self.blur_anim.stop()
                
            self.blur_anim = QPropertyAnimation(self.blur_effect, b"blurRadius")
            self.blur_anim.setDuration(220)
            self.blur_anim.setStartValue(self.blur_effect.blurRadius())
            self.blur_anim.setEndValue(16.0)
            self.blur_anim.start()

    def hide_drag_overlay(self):
        if hasattr(self, "drag_overlay") and self.drag_overlay:
            self.drag_overlay.hide_animated()
            
            if self.blur_effect:
                if self.blur_anim:
                    self.blur_anim.stop()
                
                self.blur_anim = QPropertyAnimation(self.blur_effect, b"blurRadius")
                self.blur_anim.setDuration(220)
                self.blur_anim.setStartValue(self.blur_effect.blurRadius())
                self.blur_anim.setEndValue(0.0)
                self.blur_anim.finished.connect(self._clear_blur_effect)
                self.blur_anim.start()

    def _clear_blur_effect(self):
        if self.blur_anim:
            try:
                self.blur_anim.finished.disconnect(self._clear_blur_effect)
            except TypeError:
                pass
        self.centralWidget().setGraphicsEffect(None)
        self.blur_effect = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.show_drag_overlay()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        pos = self.mapFromGlobal(self.cursor().pos())
        if not self.rect().contains(pos):
            self.hide_drag_overlay()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.hide_drag_overlay()
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self._add_paths(paths)

    # -- About Modal Overlay ------------------------------------------------

    def show_about_overlay(self):
        if hasattr(self, "about_overlay") and self.about_overlay:
            self.about_overlay.show_animated()
            
            # Animate blur effect on central widget
            if not self.blur_effect:
                self.blur_effect = QGraphicsBlurEffect(self)
                self.centralWidget().setGraphicsEffect(self.blur_effect)
            
            if self.blur_anim:
                self.blur_anim.stop()
                
            self.blur_anim = QPropertyAnimation(self.blur_effect, b"blurRadius")
            self.blur_anim.setDuration(220)
            self.blur_anim.setStartValue(self.blur_effect.blurRadius())
            self.blur_anim.setEndValue(16.0)
            self.blur_anim.start()

    def hide_about_overlay(self):
        if hasattr(self, "about_overlay") and self.about_overlay:
            self.about_overlay.hide_animated()
            
            if self.blur_effect:
                if self.blur_anim:
                    self.blur_anim.stop()
                
                self.blur_anim = QPropertyAnimation(self.blur_effect, b"blurRadius")
                self.blur_anim.setDuration(220)
                self.blur_anim.setStartValue(self.blur_effect.blurRadius())
                self.blur_anim.setEndValue(0.0)
                self.blur_anim.finished.connect(self._clear_blur_effect)
                self.blur_anim.start()

    # -- Sorting helper slot ------------------------------------------------

    def _sort_table(self, column):
        header = self.table.horizontalHeader()
        current_col = header.sortIndicatorSection()
        current_order = header.sortIndicatorOrder()
        
        # Toggle order if clicked on same column
        if current_col == column:
            new_order = (
                Qt.SortOrder.DescendingOrder 
                if current_order == Qt.SortOrder.AscendingOrder 
                else Qt.SortOrder.AscendingOrder
            )
        else:
            new_order = Qt.SortOrder.AscendingOrder
            
        header.setSortIndicator(column, new_order)
        self.table.sortByColumn(column, new_order)

    # -- File list management -----------------------------------------------

    def add_files(self):
        if self.current_mode == "Font":
            title = "Add font files"
            filt = "Fonts (*.ttf *.otf *.woff *.woff2 *.eot *.svg);;All files (*)"
        elif self.current_mode == "PDF":
            title = "Add PDF files"
            filt = "PDF Files (*.pdf);;All files (*)"
        else:
            title = "Add image files"
            filt = "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff);;All files (*)"
        paths, _ = QFileDialog.getOpenFileNames(self, title, "", filt)
        self._add_paths(paths)

    def add_folder(self):
        if self.current_mode == "Font":
            title = "Add folder of fonts"
        elif self.current_mode == "PDF":
            title = "Add folder of PDFs"
        else:
            title = "Add folder of images"
        folder = QFileDialog.getExistingDirectory(self, title)
        if folder:
            self._add_paths([folder])

    def _add_paths(self, paths):
        new_files = []
        for p in paths:
            if os.path.isdir(p):
                for root_dir, _dirs, files in os.walk(p):
                    for f in files:
                        if f.lower().endswith(self.input_exts):
                            new_files.append(os.path.join(root_dir, f))
            elif p.lower().endswith(self.input_exts):
                new_files.append(p)

        existing = {self.table.item(r, self.COL_NAME).data(Qt.ItemDataRole.UserRole)
                    for r in range(self.table.rowCount())}

        added = 0
        for f in new_files:
            if f in existing:
                continue
            self._add_row(f)
            existing.add(f)
            added += 1

        if added:
            self.log.appendPlainText(f"Added {added} file(s).")
            if self.current_mode == "Font":
                msg = f"Successfully added {added} font file(s)."
            elif self.current_mode == "PDF":
                msg = f"Successfully added {added} PDF file(s)."
            else:
                msg = f"Successfully added {added} image file(s)."
            self.show_toast("Import Completed", msg, "success")
        self._refresh_counts()

    def _add_row(self, path):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(os.path.basename(path))
        name_item.setData(Qt.ItemDataRole.UserRole, path)
        name_item.setIcon(qta.icon("fa5s.file-alt", color=self.theme_colors['text_muted']))
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, self.COL_NAME, name_item)

        if self.current_mode == "Font":
            try:
                info = engine.inspect_font(path)
                fmt_text = info.format
                size_text = human_size(info.size_bytes)
            except Exception:
                fmt_text = "?"
                size_text = human_size(os.path.getsize(path)) if os.path.exists(path) else "-"

            fmt_item = QTableWidgetItem(fmt_text)
            fmt_item.setFlags(fmt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, self.COL_FORMAT, fmt_item)
            
            size_item = QTableWidgetItem(size_text)
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, self.COL_SIZE, size_item)
        elif self.current_mode == "PDF":
            pwd_item = QTableWidgetItem("")
            pwd_item.setFlags(pwd_item.flags() | Qt.ItemFlag.ItemIsEditable)
            pwd_item.setToolTip("Double-click to enter specific password for this PDF")
            self.table.setItem(row, self.COL_FORMAT, pwd_item)

            size_text = human_size(os.path.getsize(path)) if os.path.exists(path) else "-"
            size_item = QTableWidgetItem(size_text)
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, self.COL_SIZE, size_item)
        else:  # Image Mode
            # Read format from extension
            fmt_text = os.path.splitext(path)[1].replace(".", "").upper()
            fmt_item = QTableWidgetItem(fmt_text)
            fmt_item.setFlags(fmt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, self.COL_FORMAT, fmt_item)

            size_text = human_size(os.path.getsize(path)) if os.path.exists(path) else "-"
            size_item = QTableWidgetItem(size_text)
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, self.COL_SIZE, size_item)

        status_item = self._status_item("Queued")
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, self.COL_STATUS, status_item)

    def _status_item(self, status, message=""):
        item = QTableWidgetItem(status)
        colors = {
            "Queued": self.theme_colors['text_muted'],
            "Converting": WARN,
            "Unlocking": WARN,
            "Done": SUCCESS,
            "Failed": DANGER,
            "Cancelled": self.theme_colors['text_muted'],
            "Ignored": self.theme_colors['text_muted'],
        }
        item.setForeground(QColor(colors.get(status, self.theme_colors['text_muted'])))
        if message:
            item.setToolTip(message)
        return item

    def remove_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)
        self._refresh_counts()
        if rows:
            self.show_toast("Files Removed", f"Removed {len(rows)} selected file(s).", "info")

    def clear_all(self):
        n = self.table.rowCount()
        self.table.setRowCount(0)
        self.log.clear()
        self.progress.setValue(0)
        self.lbl_progress.setText("")
        self._refresh_counts()
        if n > 0:
            self.show_toast("Queue Cleared", "All files removed from conversion list.", "info")

    def _refresh_counts(self):
        n = self.table.rowCount()
        self.lbl_count.setText(f"{n} file{'s' if n != 1 else ''}")
        self.drop_hint.setVisible(n == 0)
        self.lbl_status.setText(f"{n} queued  ·  0 done  ·  0 failed")

    def _filter_table(self, text):
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, self.COL_NAME)
            if name_item:
                match = text.lower() in name_item.text().lower()
                self.table.setRowHidden(row, not match)

    def on_theme_changed(self, theme_name):
        self.theme_colors = DARK_THEME_COLORS if theme_name == "Dark" else LIGHT_THEME_COLORS
        apply_theme(QApplication.instance(), theme_name)
        
        # Decide icons based on current mode
        if self.current_mode == "Font":
            titlebar_icon_name = "fa5s.font"
            header_icon_name = "fa5s.exchange-alt"
            theme_accent = "#1E90FF" if theme_name == "Dark" else "#4F5DFF"
        elif self.current_mode == "PDF":
            titlebar_icon_name = "fa5s.unlock"
            header_icon_name = "fa5s.unlock-alt"
            theme_accent = "#1E90FF" if theme_name == "Dark" else "#4F5DFF"
        else:
            titlebar_icon_name = "fa5s.image"
            header_icon_name = "fa5s.file-image"
            theme_accent = "#1E90FF" if theme_name == "Dark" else "#4F5DFF"

        # Update custom titlebar colors and icons to match theme completely
        if theme_name == "Dark":
            self.title_bar.setStyleSheet("""
                QWidget#TitleBar { 
                    background-color: #000000; 
                    border-bottom: 1px solid #121217; 
                    border-top-left-radius: 15px; 
                    border-top-right-radius: 15px; 
                }
            """)
            self.title_bar.title_lbl.setStyleSheet("color: #E5E7EB; font-size: 12px; font-weight: bold; font-family: system-ui; margin-right: 12px;")
            self.title_bar.btn_min.setIcon(qta.icon("fa5s.minus", color="#9CA3AF"))
            self.title_bar.btn_close.setIcon(qta.icon("fa5s.times", color="#9CA3AF"))
            self.btn_theme_toggle.setIcon(qta.icon("fa5s.moon", color="#1E90FF"))
            self.btn_theme_toggle.setToolTip("Switch to Light Mode")
            if hasattr(self, "options_scroll") and self.options_scroll:
                self.options_scroll.setStyleSheet("""
                    QScrollArea#OptionsScrollArea {
                        background-color: #0B0B0E;
                        border: 1px solid #1F2026;
                        border-radius: 12px;
                    }
                """)
        else:
            self.title_bar.setStyleSheet("""
                QWidget#TitleBar { 
                    background-color: #F4F5F8; 
                    border-bottom: 1px solid #E6E8EC; 
                    border-top-left-radius: 15px; 
                    border-top-right-radius: 15px; 
                }
            """)
            self.title_bar.title_lbl.setStyleSheet("color: #20232B; font-size: 12px; font-weight: bold; font-family: system-ui; margin-right: 12px;")
            self.title_bar.btn_min.setIcon(qta.icon("fa5s.minus", color="#6B7280"))
            self.title_bar.btn_close.setIcon(qta.icon("fa5s.times", color="#6B7280"))
            self.btn_theme_toggle.setIcon(qta.icon("fa5s.sun", color="#4F5DFF"))
            self.btn_theme_toggle.setToolTip("Switch to Dark Mode")
            if hasattr(self, "options_scroll") and self.options_scroll:
                self.options_scroll.setStyleSheet("""
                    QScrollArea#OptionsScrollArea {
                        background-color: #FFFFFF;
                        border: 1px solid #E6E8EC;
                        border-radius: 12px;
                    }
                """)

        # Update the active icons
        self.title_bar.logo_lbl.setPixmap(qta.icon(titlebar_icon_name, color=theme_accent).pixmap(QSize(16, 16)))
        if hasattr(self, "header_icon_lbl") and self.header_icon_lbl:
            self.header_icon_lbl.setPixmap(qta.icon(header_icon_name, color=theme_accent).pixmap(QSize(28, 28)))
        
        if hasattr(self, "about_overlay") and self.about_overlay:
            self.about_overlay.on_theme_changed(theme_name)
        if hasattr(self, "drag_overlay") and self.drag_overlay:
            self.drag_overlay.on_theme_changed(theme_name)
        if hasattr(self, "confirm_overlay") and self.confirm_overlay:
            self.confirm_overlay.on_theme_changed(theme_name)
            
        for r in range(self.table.rowCount()):
            status_item = self.table.item(r, self.COL_STATUS)
            if status_item:
                status_item.setForeground(QColor(self.theme_colors['text_muted'] if status_item.text() in ("Queued", "Cancelled", "Ignored") else SUCCESS if status_item.text() == "Done" else DANGER if status_item.text() == "Failed" else WARN))

    def closeEvent(self, event):
        if hasattr(self, "_allow_close") and self._allow_close:
            event.accept()
        else:
            event.ignore()
            self.show_close_confirm_overlay()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if hasattr(self, "about_overlay") and self.about_overlay and self.about_overlay.isVisible():
                self.hide_about_overlay()
                event.accept()
                return
            if hasattr(self, "confirm_overlay") and self.confirm_overlay and self.confirm_overlay.isVisible():
                self.hide_close_confirm_overlay()
                event.accept()
                return
        super().keyPressEvent(event)

    def show_close_confirm_overlay(self):
        if hasattr(self, "confirm_overlay") and self.confirm_overlay:
            self.confirm_overlay.show_animated()
            
            # Animate blur effect on central widget
            if not self.blur_effect:
                self.blur_effect = QGraphicsBlurEffect(self)
                self.centralWidget().setGraphicsEffect(self.blur_effect)
            
            if self.blur_anim:
                self.blur_anim.stop()
                
            self.blur_anim = QPropertyAnimation(self.blur_effect, b"blurRadius")
            self.blur_anim.setDuration(220)
            self.blur_anim.setStartValue(self.blur_effect.blurRadius())
            self.blur_anim.setEndValue(16.0)
            self.blur_anim.start()

    def hide_close_confirm_overlay(self):
        if hasattr(self, "confirm_overlay") and self.confirm_overlay:
            self.confirm_overlay.hide_animated()
            
            if self.blur_effect:
                if self.blur_anim:
                    self.blur_anim.stop()
                
                self.blur_anim = QPropertyAnimation(self.blur_effect, b"blurRadius")
                self.blur_anim.setDuration(220)
                self.blur_anim.setStartValue(self.blur_effect.blurRadius())
                self.blur_anim.setEndValue(0.0)
                self.blur_anim.finished.connect(self._clear_blur_effect)
                self.blur_anim.start()

    def confirm_exit(self):
        self._allow_close = True
        self.close()

    def show_about_dialog(self):
        if hasattr(self, "about_overlay") and self.about_overlay:
            self.about_overlay.update_content(self.current_mode)
        self.show_about_overlay()

    def show_toast(self, title: str, body: str, toast_type: str = "info"):
        if hasattr(self, "toast") and self.toast:
            self.toast.show_toast(title, body, toast_type)

    # -- Output helpers ----------------------------------------------------

    def open_output_folder(self):
        if self.table.rowCount() == 0:
            self.show_toast("No Files", "Add some files first.", "warning")
            return
        path = self.table.item(0, self.COL_NAME).data(Qt.ItemDataRole.UserRole)
        folder = os.path.dirname(path)
        if folder and os.path.isdir(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            self.show_toast("Error", "No valid output folder yet.", "error")

    # -- conversion ---------------------------------------------------

    def start_conversion(self):
        if self.worker and self.worker.isRunning():
            return
        n = self.table.rowCount()
        if n == 0:
            if self.current_mode == "Font":
                self.show_toast("No Files", "Add some font files or folders first.", "warning")
            elif self.current_mode == "PDF":
                self.show_toast("No Files", "Add some PDF files or folders first.", "warning")
            else:
                self.show_toast("No Files", "Add some image files or folders first.", "warning")
            return

        if self.current_mode == "Font":
            target_format = self.combo_format.currentText().lower()
            precision = self.combo_precision.currentText()
            overwrite = self.chk_overwrite.isChecked()

            options = {}
            if self.chk_delete_source.isChecked():
                options["delete_source"] = True

            jobs = []
            skipped = 0
            for row in range(n):
                input_path = self.table.item(row, self.COL_NAME).data(Qt.ItemDataRole.UserRole)
                base = os.path.splitext(os.path.basename(input_path))[0]
                folder = os.path.dirname(input_path)
                output_path = os.path.join(folder, f"{base}.{target_format}")

                try:
                    src_format = self.table.item(row, self.COL_FORMAT).text().strip().lower()
                except Exception:
                    src_format = ""

                if src_format == target_format:
                    self.table.setItem(row, self.COL_STATUS, self._status_item("Ignored", "Same format conversion ignored"))
                    skipped += 1
                    continue

                if os.path.abspath(output_path) == os.path.abspath(input_path):
                    self.table.setItem(row, self.COL_STATUS, self._status_item("Failed", "Source and target are identical"))
                    skipped += 1
                    continue
                if os.path.exists(output_path) and not overwrite:
                    self.table.setItem(row, self.COL_STATUS, self._status_item("Failed", "Already exists (overwrite is off)"))
                    skipped += 1
                    continue

                self.table.setItem(row, self.COL_STATUS, self._status_item("Queued"))
                jobs.append((row, input_path, output_path))

            if not jobs:
                self.show_toast("Conversion Cancelled", "No files required conversion.", "warning")
                return

            self.log.appendPlainText(f"— Starting batch: {len(jobs)} file(s) → {target_format.upper()} ({precision}) —")
            self.progress.setMaximum(len(jobs))
            self.progress.setValue(0)
            self.lbl_progress.setText(f"0 / {len(jobs)}")

            self.btn_convert.setEnabled(False)
            self.btn_cancel.setVisible(True)
            self._set_controls_enabled(False)

            self.worker = ConversionWorker(jobs, target_format, precision, options=options)
            self.worker.rowUpdate.connect(self._on_row_update)
            self.worker.overallProgress.connect(self._on_progress)
            self.worker.logLine.connect(self.log.appendPlainText)
            self.worker.finishedAll.connect(self._on_finished)
            self.worker.start()
            
        elif self.current_mode == "PDF":
            overwrite = self.chk_pdf_overwrite.isChecked()
            default_password = self.txt_default_password.text()
            pdf_action = self.combo_pdf_action.currentText()
            
            # Action options:
            # - Unlock Only: compress = False
            # - Compress Only: compress = True
            # - Unlock & Compress: compress = True
            compress = (pdf_action in ("Compress Only", "Unlock & Compress"))

            options = {}
            if self.chk_pdf_delete_source.isChecked():
                options["delete_source"] = True

            jobs = []
            skipped = 0
            for row in range(n):
                input_path = self.table.item(row, self.COL_NAME).data(Qt.ItemDataRole.UserRole)
                base = os.path.splitext(os.path.basename(input_path))[0]
                folder = os.path.dirname(input_path)
                
                if overwrite:
                    output_path = input_path
                else:
                    suffix = "_compressed.pdf" if pdf_action == "Compress Only" else "_unlocked.pdf"
                    output_path = os.path.join(folder, f"{base}{suffix}")

                if os.path.exists(output_path) and output_path != input_path and not overwrite:
                    self.table.setItem(row, self.COL_STATUS, self._status_item("Failed", "Output file already exists"))
                    skipped += 1
                    continue

                file_password = self.table.item(row, self.COL_FORMAT).text().strip()
                # If compress only, we don't try passwords
                if pdf_action == "Compress Only":
                    file_password = ""
                    
                self.table.setItem(row, self.COL_STATUS, self._status_item("Queued"))
                jobs.append((row, input_path, output_path, file_password))

            if not jobs:
                self.show_toast("Processing Cancelled", "No PDFs required processing.", "warning")
                return

            self.log.appendPlainText(f"— Starting PDF {pdf_action}: {len(jobs)} file(s) —")
            self.progress.setMaximum(len(jobs))
            self.progress.setValue(0)
            self.lbl_progress.setText(f"0 / {len(jobs)}")

            self.btn_convert.setEnabled(False)
            self.btn_cancel.setVisible(True)
            self._set_controls_enabled(False)

            self.worker = PDFUnlockWorker(jobs, default_password, compress=compress, options=options)
            self.worker.rowUpdate.connect(self._on_row_update)
            self.worker.overallProgress.connect(self._on_progress)
            self.worker.logLine.connect(self.log.appendPlainText)
            self.worker.finishedAll.connect(self._on_finished)
            self.worker.start()
            
        else:  # Image Mode
            target_format = self.combo_image_format.currentText().lower()
            quality = self.slider_image_quality.value()
            overwrite = self.chk_image_overwrite.isChecked()

            options = {}
            if self.chk_image_delete_source.isChecked():
                options["delete_source"] = True

            jobs = []
            skipped = 0
            for row in range(n):
                input_path = self.table.item(row, self.COL_NAME).data(Qt.ItemDataRole.UserRole)
                base = os.path.splitext(os.path.basename(input_path))[0]
                folder = os.path.dirname(input_path)
                output_path = os.path.join(folder, f"{base}.{target_format}")

                try:
                    src_format = self.table.item(row, self.COL_FORMAT).text().strip().lower()
                except Exception:
                    src_format = ""

                # Allow conversion to same format only for lossy formats (to adjust quality/size)
                src_comp = "jpeg" if src_format == "jpg" else src_format
                tgt_comp = "jpeg" if target_format == "jpg" else target_format

                if src_comp == tgt_comp and tgt_comp not in ("jpeg", "webp"):
                    self.table.setItem(row, self.COL_STATUS, self._status_item("Ignored", "Same format conversion ignored"))
                    skipped += 1
                    continue

                if os.path.abspath(output_path) == os.path.abspath(input_path) and not overwrite:
                    self.table.setItem(row, self.COL_STATUS, self._status_item("Failed", "Overwrite is required for identical files"))
                    skipped += 1
                    continue
                if os.path.exists(output_path) and not overwrite and os.path.abspath(output_path) != os.path.abspath(input_path):
                    self.table.setItem(row, self.COL_STATUS, self._status_item("Failed", "Already exists (overwrite is off)"))
                    skipped += 1
                    continue

                self.table.setItem(row, self.COL_STATUS, self._status_item("Queued"))
                jobs.append((row, input_path, output_path))

            if not jobs:
                self.show_toast("Conversion Cancelled", "No images required conversion.", "warning")
                return

            self.log.appendPlainText(f"— Starting Image Batch: {len(jobs)} file(s) → {target_format.upper()} (Quality: {quality}%) —")
            self.progress.setMaximum(len(jobs))
            self.progress.setValue(0)
            self.lbl_progress.setText(f"0 / {len(jobs)}")

            self.btn_convert.setEnabled(False)
            self.btn_cancel.setVisible(True)
            self._set_controls_enabled(False)

            self.worker = ImageWorker(jobs, target_format, quality, options=options)
            self.worker.rowUpdate.connect(self._on_row_update)
            self.worker.overallProgress.connect(self._on_progress)
            self.worker.logLine.connect(self.log.appendPlainText)
            self.worker.finishedAll.connect(self._on_finished)
            self.worker.start()

    def cancel_conversion(self):
        if self.worker:
            self.worker.cancel()
            self.log.appendPlainText("Cancelling after the current file…")
            self.show_toast("Cancelling", "Process is stopping...", "warning")

    def _set_controls_enabled(self, enabled):
        if self.current_mode == "Font":
            widgets = (
                self.btn_add_files, self.btn_add_folder, self.btn_remove, self.btn_clear,
                self.combo_format, self.combo_precision,
                self.chk_overwrite, self.chk_delete_source
            )
        elif self.current_mode == "PDF":
            widgets = (
                self.btn_add_files, self.btn_add_folder, self.btn_remove, self.btn_clear,
                self.combo_pdf_action, self.txt_default_password, self.chk_pdf_overwrite, self.chk_pdf_delete_source
            )
        else:  # Image Mode
            widgets = (
                self.btn_add_files, self.btn_add_folder, self.btn_remove, self.btn_clear,
                self.combo_image_format, self.slider_image_quality, self.chk_image_overwrite, self.chk_image_delete_source
            )
        for w in widgets:
            w.setEnabled(enabled)

    def _on_row_update(self, row, status, message):
        self.table.setItem(row, self.COL_STATUS, self._status_item(status, message))

    def _on_progress(self, done, total):
        self.progress.setValue(done)
        self.lbl_progress.setText(f"{done} / {total}")

    def _on_finished(self, ok_count, fail_count, seconds):
        self.btn_convert.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self._set_controls_enabled(True)

        total = ok_count + fail_count
        self.lbl_status.setText(f"{total} processed  ·  {ok_count} done  ·  {fail_count} failed")
        
        if self.current_mode == "Font":
            self.lbl_summary.setText(f"Finished in {seconds:.1f}s — {ok_count} converted, {fail_count} failed.")
            self.log.appendPlainText(f"— Batch finished in {seconds:.1f}s: {ok_count} ok, {fail_count} failed —")
            if fail_count > 0:
                self.show_toast("Conversion Finished", f"{ok_count} succeeded, {fail_count} failed.", "warning" if ok_count else "error")
            else:
                self.show_toast("Conversion Successful", f"{ok_count} file(s) converted successfully.", "success")
        elif self.current_mode == "PDF":
            self.lbl_summary.setText(f"Finished in {seconds:.1f}s — {ok_count} processed, {fail_count} failed.")
            self.log.appendPlainText(f"— Batch finished in {seconds:.1f}s: {ok_count} ok, {fail_count} failed —")
            if fail_count > 0:
                self.show_toast("PDF Processing Finished", f"{ok_count} succeeded, {fail_count} failed.", "warning" if ok_count else "error")
            else:
                self.show_toast("PDF Processing Successful", f"{ok_count} PDF file(s) processed successfully.", "success")
        else:  # Image Mode
            self.lbl_summary.setText(f"Finished in {seconds:.1f}s — {ok_count} converted, {fail_count} failed.")
            self.log.appendPlainText(f"— Batch finished in {seconds:.1f}s: {ok_count} ok, {fail_count} failed —")
            if fail_count > 0:
                self.show_toast("Conversion Finished", f"{ok_count} succeeded, {fail_count} failed.", "warning" if ok_count else "error")
            else:
                self.show_toast("Conversion Successful", f"{ok_count} image(s) converted successfully.", "success")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    apply_theme(app, "Dark")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
