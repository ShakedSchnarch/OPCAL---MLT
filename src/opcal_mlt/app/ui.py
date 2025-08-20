from __future__ import annotations
import streamlit as st

# --- Default palette and helper ---
DEFAULT_PALETTE = {
    "bg": "#f8fafc",            # slate-50
    "panel": "#ffffff",         # white
    "border": "#e5e7eb",        # slate-200
    "text": "#0f172a",          # slate-900
    "muted": "#64748b",         # slate-500
    "accent": "#2563eb",        # blue-600
    # Extras used by screens.py
    "status_unlabeled": "#e5e7eb",  # slate-200
    "status_labeled": "#10b981",    # emerald-500
    # Soft band fills (pre/post) for threshold shading
    "shade_pre": "rgba(99,102,241,0.10)",   # indigo-500 @ 10%
    "shade_post": "rgba(16,185,129,0.10)",  # emerald-500 @ 10%
}

def build_palette(overrides: dict | None = None) -> dict:
    """Return a complete palette, filling missing keys with defaults."""
    pal = dict(DEFAULT_PALETTE)
    if overrides:
        pal.update({k: v for k, v in overrides.items() if v is not None})
    return pal

def inject_theme_css(palette: dict) -> None:
    palette = build_palette(palette)
    # Build CSS in two parts to avoid f-string `{}` parsing problems
    css_vars = f"""
    :root {{
      --bg: {palette["bg"]};
      --panel: {palette["panel"]};
      --border: {palette["border"]};
      --text: {palette["text"]};
      --muted: {palette["muted"]};
      --accent: {palette["accent"]};
      --shade-pre: {palette["shade_pre"]};
      --shade-post: {palette["shade_post"]};
      --status-unlabeled: {palette["status_unlabeled"]};
      --status-labeled: {palette["status_labeled"]};
    }}
    """

    css_static = """
    html, body, [data-testid="stAppViewContainer"] {
      background: var(--bg) !important;
      color: var(--text) !important;
    }
    [data-testid="stSidebar"] {
      background: var(--panel) !important;
      border-right: 1px solid var(--border);
      width: 320px !important;
      min-width: 320px !important;
    }
    /* Force sidebar to be visible (no collapse, no translate) */
    [data-testid="stSidebar"] {
      transform: none !important;
      opacity: 1 !important;
      pointer-events: auto !important;
      visibility: visible !important;
      display: block !important;
    }
    /* Hide built-in sidebar collapse/expand chevron */
    button[aria-label="Toggle sidebar"],
    button[title="Toggle sidebar"],
    [data-testid="baseButton-headerNoPadding"][aria-label*="sidebar"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
      display: none !important;
    }
    /* Safety: defeat any upstream body-based collapse states */
    body[class*="collapsed"], body.sb-collapsed {
      overflow: auto !important;
    }
    body[class*="collapsed"] [data-testid="stSidebar"],
    body.sb-collapsed [data-testid="stSidebar"] {
      transform: none !important;
      opacity: 1 !important;
      pointer-events: auto !important;
      visibility: visible !important;
      display: block !important;
    }
    /* Some Streamlit builds wrap the content in an inner container */
    [data-testid="stSidebar"] section[tabindex="0"] {
      width: 320px !important;
      min-width: 320px !important;
    }

    [data-testid="stStatusWidget"], #MainMenu, footer { visibility: hidden !important; }
    [data-testid="stToolbar"] { display: none !important; }
    .block-container { padding-top: 3.2rem; }
    .block-container { padding-right: 0; }
    /* legacy in-panel logo rules no longer used */
    h1, h2, h3 { overflow: visible !important; }

    /* Hide Streamlit's heading anchor (paperclip) across versions */
    .stHeading a.anchor-link,
    .stHeading .heading-anchor,
    .stHeading button[aria-label="Copy header link"] {
      display: none !important;
    }

    .stMarkdown p, label, .stTextInput>div>div>input {
      font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, 'Apple Color Emoji','Segoe UI Emoji';
    }
    /* Text inputs: ensure visible, bordered, padded, white background */
    div[data-testid="stTextInput"] input,
    .stTextInput input {
      background-color: #fff !important;
      border: 1px solid #ccc !important;
      padding: 6px 10px !important;
      color: var(--text) !important;
      opacity: 1 !important;
    }

    /* App title */
    .app-title {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 10px;
      margin-bottom: .5rem;
      position: relative;
    }
    .app-title-main {font-size: 2.35rem; font-weight: 800; letter-spacing:0.2px; margin:0; color: var(--text); text-align:center;}
    .app-title-sub {color: var(--muted); font-size: 1.05rem; text-align:center;}

    /* Panels */
    .block-container > div:first-child {background: var(--panel); border:1px solid var(--border); border-radius:12px; padding:12px 16px;}
    /* Reusable card container */
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
    }
    .hint {margin: 0.25rem 0 0.5rem 0; color: var(--muted); font-size: 0.95rem;}

    .step-header { font-size: 2rem; font-weight: 800; margin: 0.5rem 0 1rem; }
    .section-title { font-size: 1.25rem; font-weight: 700; margin: 0.75rem 0 0.5rem; }
    .subsection-title { font-size: 1.05rem; font-weight: 600; margin: 0.5rem 0 0.25rem; }
    .stMarkdown p { line-height: 1.45; }

    /* Section headings */
    .stHeading h2 {font-size:1.35rem;}
    .stHeading h3 {font-size:1.1rem;}
    .disabled-pane {opacity: .45; pointer-events: none; filter: grayscale(20%);}
    /* Buttons — consistent academic look */
    .stButton > button {
      border-radius: 8px !important;
      border: 1px solid var(--border) !important;
      padding: 6px 14px !important;
      font-weight: 600 !important;
      letter-spacing: .2px !important;
      box-shadow: 0 1px 2px rgba(0,0,0,.06) !important;
    }
    .stButton > button:hover { box-shadow: 0 2px 6px rgba(0,0,0,.12) !important; }

    /* --- Differentiated button groups (stronger) --- */
    .btn-nav .stButton > button {
      background: transparent !important;
      color: var(--accent) !important;
      border-color: var(--accent) !important;
    }
    .btn-nav .stButton > button:hover {
      background: rgba(37, 99, 235, .08) !important;
      box-shadow: 0 2px 6px rgba(0,0,0,.12) !important;
    }
    .btn-nav .stButton > button:disabled {
      opacity: .45 !important;
      color: var(--muted) !important;
      border-color: var(--border) !important;
      background: #fff !important;
    }

    .btn-action .stButton > button {
      background: #10b981 !important;     /* emerald-500 */
      color: #ffffff !important;
      border-color: #059669 !important;   /* emerald-600 */
    }
    .btn-action .stButton > button:hover {
      background: #059669 !important;     /* emerald-600 */
      border-color: #047857 !important;   /* emerald-700 */
      box-shadow: 0 2px 8px rgba(16,185,129,.35) !important;
    }
    .btn-action .stButton > button:disabled {
      background: #a7f3d0 !important;     /* emerald-200 */
      color: #065f46 !important;          /* emerald-800 */
      border-color: #6ee7b7 !important;   /* emerald-300 */
      opacity: .6 !important;
    }

    .btn-utility .stButton > button {
      background: #ffffff !important;
      color: #0f172a !important;
      border-color: #cbd5e1 !important;   /* slate-300 */
    }
    .btn-utility .stButton > button:hover {
      background: #f1f5f9 !important;     /* slate-100 */
      border-color: #94a3b8 !important;   /* slate-400 */
    }
    .btn-utility .stButton > button:disabled {
      opacity: .5 !important;
      background: #f8fafc !important;     /* slate-50 */
      border-color: #e2e8f0 !important;   /* slate-200 */
    }

    /* Button size variants */
    .btn-lg .stButton > button { padding: 10px 18px !important; font-size: 1rem !important; }
    .btn-sm .stButton > button { padding: 4px 10px !important; font-size: .9rem !important; }

    /* Tighter default gap in columns (helps reduce "holes") */
    .element-container:has(> div[data-testid="column"]) { margin-bottom: 0.4rem; }

    /* --- Custom progress bar for labeling step --- */
    .progress-track {
      width: 100%; height: 10px; background: #e5e7eb; border-radius: 999px; overflow: hidden;
      border: 1px solid var(--border);
    }
    .progress-fill {
      height: 100%; background: var(--accent); transition: width .3s ease;
    }

    /* Optional: CSS hooks for DOM-based shaded bands */
    .band-pre { background-color: var(--shade-pre); }
    .band-post { background-color: var(--shade-post); }
    """

    st.markdown(f"<style>{css_vars}{css_static}</style>", unsafe_allow_html=True)

# --- Plotly theme helpers -----------------------------------------------------

def resolve_theme(palette: dict | None = None) -> dict:
    """Return a complete theme/palette dict safe for both CSS and Plotly.

    Accepts a partial dict and fills missing keys from DEFAULT_PALETTE.
    """
    return build_palette(palette or {})


def default_theme() -> dict:
    """Convenience accessor for a full default theme."""
    return build_palette({})


def apply_plotly_theme(fig, theme: dict | None = None):
    """Apply a lightweight Plotly skin aligned with the app theme.

    This avoids using a global Plotly template and instead sets layout fields
    directly on the figure passed in. Safe to call multiple times.
    """
    th = resolve_theme(theme)

    # Backgrounds and base font
    fig.update_layout(
        template=None,  # avoid external/global templates overriding our vars
        paper_bgcolor=th["bg"],
        plot_bgcolor=th["panel"],
        font=dict(color=th["text"]),
        legend=dict(bgcolor=th["panel"], bordercolor=th["border"], borderwidth=1),
    )

    # Axes styling (gridlines and zero lines)
    fig.update_xaxes(
        showline=True,
        linewidth=1,
        linecolor=th["border"],
        gridcolor=th["border"],
        zerolinecolor=th["border"],
    )
    fig.update_yaxes(
        showline=True,
        linewidth=1,
        linecolor=th["border"],
        gridcolor=th["border"],
        zerolinecolor=th["border"],
    )

    return fig

def render_stepper_and_tips(stage: int) -> None:
    labels_steps = [
        "Start session",
        "Upload & indexing",
        "Label files",
        "Finish & export",
    ]
    current_step = int(stage)
    st.markdown(
        f"""
        <style>
        .stepper{{display:flex;gap:12px;margin:8px 0 10px 0;flex-wrap:wrap;justify-content:center}}
        .step{{display:flex;align-items:center;gap:8px;color:var(--muted);}}
        .step .num{{width:22px;height:22px;border-radius:50%;border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-weight:600;font-size:.9rem;}}
        .step.active{{color:var(--text);}}
        .step.active .num{{background:var(--accent); border-color:var(--accent); color:#fff;}}
        .step.done .num{{background:var(--border); color:var(--text);}}
        </style>
        <div class="stepper">
          <div class="step {'active' if current_step==1 else ('done' if current_step>1 else '')}"><div class="num">1</div><div>{labels_steps[0]}</div></div>
          <div class="step {'active' if current_step==2 else ('done' if current_step>2 else '')}"><div class="num">2</div><div>{labels_steps[1]}</div></div>
          <div class="step {'active' if current_step==3 else ('done' if current_step>3 else '')}"><div class="num">3</div><div>{labels_steps[2]}</div></div>
          <div class="step {'active' if current_step==4 else ''}"><div class="num">4</div><div>{labels_steps[3]}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if current_step == 1:
        st.markdown(
            '<div class="hint"><b>Tip:</b> Set annotator and save folder, then start a new session — or resume/load an existing one.</div>',
            unsafe_allow_html=True,
        )
    elif current_step == 2:
        st.markdown('<div class="hint"><b>Tip:</b> Upload a CSV/NPZ and choose how to assign cell IDs (from file or auto-generate).</div>', unsafe_allow_html=True)
    # Step 3 hint intentionally removed
    elif current_step == 4:
        st.markdown('<div class="hint"><b>Tip:</b> Export a ZIP archive of the session folder for sharing or backup.</div>', unsafe_allow_html=True)