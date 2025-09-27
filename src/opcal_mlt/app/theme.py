"""Theme utilities shared across the Streamlit app."""
from __future__ import annotations

from typing import Dict

_THEMES: Dict[str, Dict[str, str]] = {
    "Light": {
        "bg": "#f7f9fb",
        "panel": "#ffffff",
        "border": "#e6edf3",
        "text": "#111827",
        "muted": "#6b7280",
        "accent": "#2563eb",
        "ok": "#2ca02c",
        "warn": "#d97706",
        "err": "#dc2626",
        "shade_pre": "rgba(0,160,0,0.14)",
        "shade_post": "rgba(200,0,0,0.14)",
        "status_unlabeled": "#d1d5db",
        "status_labeled": "#2ca02c",
        "plotly_tpl": "plotly_white",
    },
    "Dark": {
        "bg": "#0f172a",
        "panel": "#0b1220",
        "border": "#1f2a44",
        "text": "#e5e7eb",
        "muted": "#9ca3af",
        "accent": "#60a5fa",
        "ok": "#34d399",
        "warn": "#f59e0b",
        "err": "#f87171",
        "shade_pre": "rgba(16,185,129,0.16)",
        "shade_post": "rgba(239,68,68,0.16)",
        "status_unlabeled": "#334155",
        "status_labeled": "#34d399",
        "plotly_tpl": "plotly_dark",
    },
}


def get_theme(name: str) -> Dict[str, str]:
    return dict(_THEMES.get(name, _THEMES["Light"]))


__all__ = ["get_theme"]
