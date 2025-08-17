from __future__ import annotations
import streamlit as st

def inject_theme_css(palette: dict) -> None:
    st.markdown(
        f"""
        <style>
        :root {{
          --bg: {palette["bg"]};
          --panel: {palette["panel"]};
          --border: {palette["border"]};
          --text: {palette["text"]};
          --muted: {palette["muted"]};
          --accent: {palette["accent"]};
        }}
        html, body, [data-testid="stAppViewContainer"] {{
          background: var(--bg) !important;
          color: var(--text) !important;
        }}
        [data-testid="stSidebar"] {{
          background: var(--panel) !important;
          border-right: 1px solid var(--border);
        }}
        [data-testid="stStatusWidget"], #MainMenu, footer {{visibility: hidden !important;}}
        .block-container {{padding-top: 1.25rem;}}
        h1, h2, h3 {{overflow: visible !important;}}
        .stMarkdown p, label, .stTextInput>div>div>input {{font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, 'Apple Color Emoji','Segoe UI Emoji';}}
        .small-muted {{color: var(--muted); font-size:0.85rem;}}
        .app-title {{display:flex; flex-direction:column; gap:2px;}}
        .app-title-main {{font-size:1.9rem; font-weight:700; letter-spacing:0.2px; margin-bottom:0; color: var(--text);}}
        .app-title-sub {{color: var(--muted); font-size:0.95rem;}}
        .block-container > div:first-child {{background: var(--panel); border:1px solid var(--border); border-radius:10px; padding:12px 16px;}}
        .top-right-logo {{position: absolute; top: 16px; right: 20px; width: 96px; max-width: 20vw;}}
        .hint {{margin: 0.25rem 0 0.75rem 0; color: var(--muted); font-size: 0.95rem;}}
        .disabled-pane {{opacity: .45; pointer-events: none; filter: grayscale(20%);}}
        .stepper {{overflow: visible;}}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_stepper_and_tips(stage: int) -> None:
    labels_steps = [
        "Start new session",
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
        st.markdown('<div class="hint"><b>Tip:</b> Set annotator and save folder, then start a new session.</div>', unsafe_allow_html=True)
    elif current_step == 2:
        st.markdown('<div class="hint"><b>Tip:</b> Upload a CSV/NPZ and choose how to assign cell IDs (from file or auto-generate).</div>', unsafe_allow_html=True)
    elif current_step == 3:
        st.markdown('<div class="hint"><b>Tip:</b> Navigate cells, assign labels and notes. You can undo the last save.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="hint"><b>Tip:</b> Export a ZIP archive of the session folder for sharing or backup.</div>', unsafe_allow_html=True)