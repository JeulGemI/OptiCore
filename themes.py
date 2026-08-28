# -*- coding: utf-8 -*-
"""
themes.py — 다중 테마 시스템 (색상 토큰 + QSS 스타일시트 생성기)

의존: PyQt6 뿐 (프로젝트 내부 모듈을 import 하지 않는다 → 순환 참조 없음)

블랙 / 그레이 / 화이트 + 퍼플/블루/그린/레드/오렌지 총 8종.
각 테마는 색상 토큰만 다르고 구조는 동일한 QSS 템플릿을 공유한다.
QLabel/QCheckBox/QGroupBox 등에 여유 있는 padding을 줘서 텍스트가
위아래로 잘리는 현상을 테마 차원에서도 방지한다.
"""

from PyQt6.QtWidgets import QApplication


# =====================================================================
# 8. 다중 테마 시스템 (THEMES + QSS 생성기)
# =====================================================================
# [신규 기능] 블랙 / 그레이 / 화이트 + 다양한 색상 테마.
# 각 테마는 색상 토큰만 다르고 구조는 동일한 QSS 템플릿을 공유한다.
# QLabel/QCheckBox/QGroupBox 등에 여유 있는 padding을 줘서 텍스트가
# 위아래로 잘리는 현상을 테마 차원에서도 방지한다.
THEME_QSS_TEMPLATE = """
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 10pt;
}}
QMainWindow {{ background-color: {bg_main}; }}
QLabel {{ padding: 2px 0px; }}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 8px;
    background-color: {panel};
}}
QTabBar::tab {{
    background: {panel};
    color: {subtext};
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
}}
QTabBar::tab:selected {{ background: {accent}; color: {tab_selected_text}; }}
QTabBar::tab:hover:!selected {{ background: {panel_hover}; }}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 10px 10px 10px;
    font-weight: bold;
    color: {accent_text};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
QCheckBox {{ spacing: 8px; padding: 5px 2px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 4px;
    border: 1px solid {border_strong}; background: {panel};
}}
QCheckBox::indicator:checked {{ background: {accent}; border: 1px solid {accent}; }}
QPushButton {{
    background-color: {accent}; color: {button_text}; border: none;
    border-radius: 8px; padding: 10px 16px; font-weight: bold;
}}
QPushButton:hover {{ background-color: {accent_hover}; }}
QPushButton:pressed {{ background-color: {accent_pressed}; }}
QPushButton:disabled {{ background-color: {disabled_bg}; color: {disabled_text}; }}
QPushButton#secondaryButton {{ background-color: {panel_hover}; color: {text}; }}
QPushButton#secondaryButton:hover {{ background-color: {border}; }}
QSlider::groove:horizontal {{ height: 6px; background: {border}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {progress}; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px;
}}
QSlider::sub-page:horizontal {{ background: {progress}; border-radius: 3px; }}
QListWidget {{
    background-color: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 4px;
}}
QListWidget::item {{ padding: 7px 4px; border-radius: 4px; }}
QListWidget::item:hover {{ background-color: {panel_hover}; }}
QProgressBar {{
    border: 1px solid {border}; border-radius: 8px; background-color: {panel};
    text-align: center; height: 24px; padding: 1px; color: {text};
}}
QProgressBar::chunk {{ background-color: {progress}; border-radius: 8px; }}
QLineEdit, QSpinBox, QComboBox {{
    background-color: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 7px;
    color: {text};
}}
QComboBox QAbstractItemView {{
    background-color: {panel}; color: {text}; border: 1px solid {border};
    selection-background-color: {accent}; selection-color: {button_text};
}}
QTextEdit {{
    background-color: {panel}; border: 1px solid {border}; border-radius: 6px;
    padding: 6px; color: {text};
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: {bg}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {border_strong}; border-radius: 6px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {accent}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
"""


def make_theme_qss(colors: dict) -> str:
    """색상 토큰 dict를 받아 완성된 QSS 문자열을 생성한다."""
    return THEME_QSS_TEMPLATE.format(**colors)


# 필수 3종(블랙/그레이/화이트) + 다양한 색상 테마
THEMES = {
    "black": {
        "label": "⚫ 블랙",
        "colors": {
            "bg": "#0d0d0f", "bg_main": "#0a0a0b", "panel": "#19191c",
            "panel_hover": "#242427", "border": "#2c2c30", "border_strong": "#3f3f45",
            "text": "#eaeaea", "subtext": "#9a9a9f", "accent": "#3b82f6",
            "accent_hover": "#5b9bfa", "accent_pressed": "#2f68c9", "accent_text": "#93c5fd",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#2a2a2e", "disabled_text": "#77777c", "progress": "#22d3ee",
        },
    },
    "gray": {
        "label": "⚪ 그레이",
        "colors": {
            "bg": "#28292d", "bg_main": "#222327", "panel": "#323338",
            "panel_hover": "#3c3d43", "border": "#46474e", "border_strong": "#5a5b63",
            "text": "#f2f2f3", "subtext": "#b7b8bf", "accent": "#14b8a6",
            "accent_hover": "#2dd4bf", "accent_pressed": "#0f9488", "accent_text": "#5eead4",
            "button_text": "#0a0a0a", "tab_selected_text": "#0a0a0a",
            "disabled_bg": "#3a3b41", "disabled_text": "#8a8b92", "progress": "#38bdf8",
        },
    },
    "white": {
        "label": "⚪ 화이트",
        "colors": {
            "bg": "#f4f5f7", "bg_main": "#eceef1", "panel": "#ffffff",
            "panel_hover": "#eef0f4", "border": "#d8dae0", "border_strong": "#b9bcc4",
            "text": "#20222a", "subtext": "#5b5e69", "accent": "#4f46e5",
            "accent_hover": "#6366f1", "accent_pressed": "#4338ca", "accent_text": "#4338ca",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#e4e5e9", "disabled_text": "#a0a2aa", "progress": "#06b6d4",
        },
    },
    "purple": {
        "label": "🟣 퍼플(게이밍)",
        "colors": {
            "bg": "#14151b", "bg_main": "#101116", "panel": "#1a1c26",
            "panel_hover": "#262838", "border": "#2a2c3d", "border_strong": "#45475a",
            "text": "#e6e6e6", "subtext": "#9a9ab0", "accent": "#7c3aed",
            "accent_hover": "#9061f9", "accent_pressed": "#6425d0", "accent_text": "#c4b5fd",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#33354a", "disabled_text": "#888888", "progress": "#00e5ff",
        },
    },
    "blue": {
        "label": "🔵 블루",
        "colors": {
            "bg": "#0b1220", "bg_main": "#080e1a", "panel": "#101a2e",
            "panel_hover": "#182541", "border": "#1f2b45", "border_strong": "#33456b",
            "text": "#e4e9f2", "subtext": "#8b98b3", "accent": "#2563eb",
            "accent_hover": "#3b82f6", "accent_pressed": "#1d4ed8", "accent_text": "#93c5fd",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#25324d", "disabled_text": "#7c879e", "progress": "#38bdf8",
        },
    },
    "green": {
        "label": "🟢 그린",
        "colors": {
            "bg": "#0e1512", "bg_main": "#0a100d", "panel": "#16211b",
            "panel_hover": "#1e2e26", "border": "#26362c", "border_strong": "#3c5245",
            "text": "#e4efe7", "subtext": "#93a89b", "accent": "#16a34a",
            "accent_hover": "#22c55e", "accent_pressed": "#15803d", "accent_text": "#86efac",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#243830", "disabled_text": "#7e9186", "progress": "#4ade80",
        },
    },
    "red": {
        "label": "🔴 레드",
        "colors": {
            "bg": "#160d0f", "bg_main": "#100a0b", "panel": "#221317",
            "panel_hover": "#2e1a20", "border": "#3a1e23", "border_strong": "#57303a",
            "text": "#f1e4e6", "subtext": "#b08890", "accent": "#dc2626",
            "accent_hover": "#ef4444", "accent_pressed": "#b91c1c", "accent_text": "#fca5a5",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#3a2328", "disabled_text": "#93777c", "progress": "#fb7185",
        },
    },
    "orange": {
        "label": "🟠 오렌지",
        "colors": {
            "bg": "#181209", "bg_main": "#120d07", "panel": "#241a0d",
            "panel_hover": "#302512", "border": "#3a2a14", "border_strong": "#5a4020",
            "text": "#f3e9d8", "subtext": "#c2a173", "accent": "#ea580c",
            "accent_hover": "#f97316", "accent_pressed": "#c2410c", "accent_text": "#fdba74",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#3d2e18", "disabled_text": "#9c8560", "progress": "#fbbf24",
        },
    },
}

DEFAULT_THEME_KEY = "purple"


def apply_theme(theme_key: str):
    """QApplication 전체에 테마 QSS를 적용한다. 알 수 없는 키는 기본 테마로 대체."""
    theme = THEMES.get(theme_key, THEMES[DEFAULT_THEME_KEY])
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(make_theme_qss(theme["colors"]))
