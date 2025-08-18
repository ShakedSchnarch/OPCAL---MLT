from __future__ import annotations
import streamlit as st

def inject_theme_css(palette: dict) -> None:
    # Build CSS in two parts to avoid f-string `{}` parsing problems
    css_vars = f"""
    :root {{
      --bg: {palette["bg"]};
      --panel: {palette["panel"]};
      --border: {palette["border"]};
      --text: {palette["text"]};
      --muted: {palette["muted"]};
      --accent: {palette["accent"]};
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
    /* Allow full collapse via body class */
    body.sb-collapsed [data-testid="stSidebar"] {
      transform: translateX(-110%) !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }
    /* Some Streamlit builds wrap the content in an inner container */
    [data-testid="stSidebar"] section[tabindex="0"] {
      width: 320px !important;
      min-width: 320px !important;
    }

    [data-testid="stStatusWidget"], #MainMenu, footer { visibility: hidden !important; }
    [data-testid="stToolbar"] { display: none !important; }
    .block-container { padding-top: 3.2rem; }
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
    .app-title {display:flex; align-items:center; justify-content:center; flex-direction:column; gap:4px; margin-bottom:.5rem;}
    .app-title-main {font-size: 2.35rem; font-weight: 800; letter-spacing:0.2px; margin:0; color: var(--text); text-align:center;}
    .app-title-sub {color: var(--muted); font-size: 1.05rem; text-align:center;}

    /* Panels */
    .block-container > div:first-child {background: var(--panel); border:1px solid var(--border); border-radius:12px; padding:14px 18px;}
    .top-right-logo {position: absolute; top: 16px; right: 20px; width: 96px; max-width: 20vw;}
    .hint {margin: 0.25rem 0 0.75rem 0; color: var(--muted); font-size: 0.95rem;}

    .step-header { font-size: 1.75rem; font-weight: 700; margin: 0.25rem 0 0.75rem; }

    /* Section headings */
    .stHeading h2 {font-size:1.35rem;}
    .stHeading h3 {font-size:1.1rem;}
    .disabled-pane {opacity: .45; pointer-events: none; filter: grayscale(20%);}
    """

    st.markdown(f"<style>{css_vars}{css_static}</style>", unsafe_allow_html=True)

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
        .stepper{{display:flex;gap:12px;margin:8px 0 10px 0;flex-wrap:wrap}}
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
    elif current_step == 3:
        st.markdown(
            '<div class="hint"><b>Tip:</b> Calibrate preprocessing (smoothing), set thresholds, then navigate cells and assign labels/notes. You can undo the last save.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="hint"><b>Tip:</b> Export a ZIP archive of the session folder for sharing or backup.</div>', unsafe_allow_html=True)