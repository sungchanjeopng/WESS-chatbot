"""Redirect the legacy Streamlit URL to WESS AI support."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

TARGET_URL = "https://ai.wessglobal.com/"
LOGO_DATA = base64.b64encode(
    Path(__file__).with_name("wessglobal-logo.png").read_bytes()
).decode("ascii")

st.set_page_config(
    page_title="WESS AI 기술지원으로 이동",
    page_icon="wessglobal-logo.png",
    layout="centered",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": None,
    },
)

st.iframe(
    f"""
    <!doctype html>
    <html lang="ko">
    <head><meta charset="utf-8"><title>WESS AI 기술지원으로 이동</title></head>
    <body>
      <script>
        (() => {{
          const target = {TARGET_URL!r};
          try {{
            const topWindow = window.top;
            const preview = new URL(topWindow.location.href).searchParams.has("preview");
            if (preview) return;
            const meta = topWindow.document.createElement("meta");
            meta.httpEquiv = "refresh";
            meta.content = `0; url=${{target}}`;
            topWindow.document.head.appendChild(meta);
          }} catch (error) {{
            window.open(target, "_top");
          }}
        }})();
      </script>
    </body>
    </html>
    """,
    height=1,
)

redirect_fallback_html = """
    <style>
      .stApp {
        background: #f3f6f9;
      }
      [data-testid="stHeader"], [data-testid="stToolbar"], footer {
        display: none;
      }
      .block-container {
        max-width: 560px;
        padding-top: 18vh;
        text-align: center;
      }
      .redirect-card {
        padding: 2.5rem;
        text-align: center;
        background: #ffffff;
        border: 1px solid #dce4ec;
        border-radius: 18px;
        box-shadow: 0 18px 50px rgba(12, 49, 92, 0.09);
      }
      .redirect-card img {
        width: 116px;
        margin-bottom: 1.5rem;
      }
      .redirect-card h1 {
        margin: 0;
        color: #072544;
        font-size: clamp(1.7rem, 6vw, 2.35rem);
        line-height: 1.3;
        letter-spacing: -0.035em;
        word-break: keep-all;
      }
      .redirect-card p {
        margin: 1rem 0 1.5rem;
        color: #5e6c7d;
        line-height: 1.7;
      }
      .redirect-card a {
        min-height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.8rem 1.25rem;
        color: #ffffff !important;
        background: #0c315c;
        border-radius: 10px;
        font-weight: 800;
        text-decoration: none;
      }
      @media (max-width: 480px) {
        .block-container { padding: 12vh 1rem 1rem; }
        .redirect-card { padding: 2rem 1.5rem; }
      }
    </style>
    <section class="redirect-card" aria-labelledby="redirect-title">
      <img src="data:image/png;base64,__LOGO_DATA__" alt="WESSGLOBAL">
      <h1 id="redirect-title">WESS AI 기술지원으로 이동합니다</h1>
      <p>자동으로 이동하지 않으면 아래 버튼을 눌러 주세요.</p>
      <a href="https://ai.wessglobal.com/" target="_self">WESS AI 기술지원 접속</a>
    </section>
    """.replace("__LOGO_DATA__", LOGO_DATA)

st.markdown(
    redirect_fallback_html,
    unsafe_allow_html=True,
)
