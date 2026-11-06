"""Visual theme for SkillMap (CSS + hero HTML)."""

import streamlit as st

THEME_CSS = r"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --text: #F8FAFC;
        --muted: #94A3B8;
        --cyan: #22D3EE;
        --violet: #A78BFA;
        --mono: 'JetBrains Mono', ui-monospace, monospace;
    }

    /* ---------- App background (dark + glow + faint grid) ---------- */
    .stApp {
        background:
            radial-gradient(circle at 80% 8%, rgba(124, 58, 237, 0.22), transparent 42%),
            radial-gradient(circle at 8% 92%, rgba(34, 211, 238, 0.12), transparent 40%),
            linear-gradient(rgba(148, 163, 184, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.035) 1px, transparent 1px),
            linear-gradient(135deg, #050816 0%, #070B22 55%, #0C0A2E 100%);
        background-size: auto, auto, 56px 56px, 56px 56px, auto;
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(5, 8, 22, 0.85);
    }

    h1, h2, h3, h4, p, li, label, input, textarea,
    [data-testid="stMetricValue"] * {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4 {
        color: #F8FAFC !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    p, li, label, .stMarkdown {
        color: var(--text);
    }

    /* mono small labels, like the inspiration site */
    .stCaption, [data-testid="stCaptionContainer"] *,
    [data-testid="stMetricLabel"] * {
        font-family: var(--mono) !important;
        letter-spacing: 0.04em;
        color: var(--muted);
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #050816 0%, #0B0A2E 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.2);
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 8px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        width: 100%;
        padding: 10px 16px;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: rgba(255, 255, 255, 0.03);
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
        display: none;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        border-color: #22D3EE;
        background: rgba(34, 211, 238, 0.09);
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(100deg, #22D3EE, #818CF8);
        border-color: transparent;
        box-shadow: 0 6px 18px rgba(34, 211, 238, 0.3);
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
        color: #04121F !important;
        font-weight: 700;
    }

    [data-testid="stSidebar"] button {
        background: linear-gradient(115deg, #0B1D4D, #1E1250) !important;
        color: #F8FAFC !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        border-radius: 999px !important;
        text-align: left;
        padding: 10px 16px;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] button:hover {
        background: linear-gradient(115deg, #0E7490, #5B3FD0) !important;
        border-color: #22D3EE !important;
        transform: translateY(-1px);
    }

    [data-testid="stSidebar"] button p {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem;
    }

    /* ---------- Hide helper markers (used only for card colors) ---------- */
    [data-testid="stElementContainer"]:has(.card-marker),
    .element-container:has(.card-marker) {
        display: none;
    }

    /* ---------- HERO ---------- */
    .hero {
        position: relative;
        overflow: hidden;
        min-height: 520px;
        padding: 64px 56px 56px;
        border-radius: 24px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        background:
            radial-gradient(circle at 78% 38%, rgba(124, 58, 237, 0.38), transparent 46%),
            radial-gradient(circle at 18% 95%, rgba(34, 211, 238, 0.2), transparent 42%),
            linear-gradient(135deg, #060A1E, #0A1030 60%, #130C3C);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
    }

    .hero-eyebrow {
        position: relative;
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 28px;
        font-family: var(--mono);
        font-size: 0.82rem;
        font-weight: 500;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #22D3EE;
    }

    .hero-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #22D3EE;
        box-shadow: 0 0 12px #22D3EE;
    }

    .hero-title {
        position: relative;
        z-index: 2;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: clamp(44px, 7vw, 100px);
        line-height: 1.02;
        letter-spacing: -0.045em;
        color: #FFFFFF;
    }

    .grad-text {
        background: linear-gradient(90deg, #22D3EE 0%, #818CF8 55%, #C084FC 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        -webkit-text-fill-color: transparent;
    }

    .serif-accent {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-weight: 400;
        font-size: 1.1em;
        letter-spacing: -0.02em;
    }

    .hero-sub {
        position: relative;
        z-index: 2;
        max-width: 560px;
        margin-top: 28px;
        font-size: 1.08rem;
        line-height: 1.7;
        color: #94A3B8;
    }

    .hero-ring {
        position: absolute;
        top: 50%;
        right: -140px;
        transform: translateY(-50%);
        border-radius: 50%;
        border: 1px solid rgba(148, 163, 184, 0.16);
    }

    .hero-ring.r1 { width: 640px; height: 640px; }
    .hero-ring.r2 { width: 450px; height: 450px; right: -45px; }
    .hero-ring.r3 { width: 270px; height: 270px; right: 45px; border-color: rgba(34, 211, 238, 0.25); }

    .hero-tile {
        position: absolute;
        width: 64px;
        height: 64px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 16px;
        font-size: 28px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(148, 163, 184, 0.25);
        backdrop-filter: blur(6px);
        box-shadow: 0 10px 26px rgba(0, 0, 0, 0.4);
        animation: floaty 6s ease-in-out infinite;
    }

    .hero-tile.t1 { top: 12%; right: 36%; }
    .hero-tile.t2 { top: 44%; right: 20%; animation-delay: 1s; }
    .hero-tile.t3 { bottom: 12%; right: 33%; animation-delay: 2s; }
    .hero-tile.t4 { top: 16%; right: 12%; animation-delay: 3s; }
    .hero-tile.t5 { bottom: 24%; right: 9%; animation-delay: 4s; }

    @keyframes floaty {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-12px); }
    }

    .hero-rail {
        position: absolute;
        right: 24px;
        top: 50%;
        transform: translateY(-50%);
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding: 14px 9px;
        border-radius: 30px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        background: rgba(255, 255, 255, 0.03);
    }

    .hero-rail span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #475569;
    }

    .hero-rail span.on {
        width: 14px;
        height: 14px;
        margin-left: -3px;
        background: #22D3EE;
        box-shadow: 0 0 14px #22D3EE;
    }

    @media (max-width: 900px) {
        .hero { padding: 40px 24px; min-height: 420px; }
        .hero-tile, .hero-rail, .hero-ring { display: none; }
    }

    /* ---------- Images ---------- */
    [data-testid="stImage"] img {
        border-radius: 20px;
        border: 1.5px solid rgba(34, 211, 238, 0.55);
        box-shadow: 0 12px 32px rgba(124, 58, 237, 0.35);
    }

    /* ---------- Section partitions ---------- */
    hr {
        border: 0 !important;
        height: 3px !important;
        border-radius: 4px;
        margin: 1.6rem 0 !important;
        background: linear-gradient(90deg, #22D3EE, #818CF8, #C084FC, #F472B6) !important;
        opacity: 0.9;
    }

    /* ---------- Metrics: each column gets its own gradient ---------- */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #3A1052, #A21CAF);
        border: 1.5px solid #E879F9;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0 8px 22px rgba(192, 38, 211, 0.32);
    }

    [data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"],
    [data-testid="column"]:nth-child(1) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #062B3D, #0E7490);
        border-color: #22D3EE;
        box-shadow: 0 8px 22px rgba(34, 211, 238, 0.32);
    }

    [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"],
    [data-testid="column"]:nth-child(2) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E1250, #5B3FD0);
        border-color: #A78BFA;
        box-shadow: 0 8px 22px rgba(139, 92, 246, 0.35);
    }

    [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"],
    [data-testid="column"]:nth-child(3) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0B1D4D, #2554C7);
        border-color: #60A5FA;
        box-shadow: 0 8px 22px rgba(59, 130, 246, 0.35);
    }

    [data-testid="stMetricLabel"] * {
        color: #E2E8F0 !important;
        text-transform: uppercase;
        font-size: 0.78rem;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    [data-testid="stMetricDelta"] {
        color: #E2E8F0 !important;
    }

    /* ---------- Buttons: pill style, mono text ---------- */
    .stButton > button,
    .stLinkButton > a,
    .stDownloadButton > button {
        background: linear-gradient(100deg, #22D3EE, #38BDF8);
        color: #04121F !important;
        border: 0;
        border-radius: 999px;
        font-weight: 700;
        padding: 0.55rem 1.4rem;
        transition: 0.2s ease;
    }

    .stButton > button p,
    .stLinkButton > a p,
    .stDownloadButton > button p {
        color: inherit !important;
        font-family: var(--mono) !important;
        font-size: 0.88rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    .stButton > button:hover,
    .stLinkButton > a:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(100deg, #67E8F9, #A5B4FC);
        color: #04121F !important;
        transform: translateY(-1px);
        box-shadow: 0 8px 22px rgba(34, 211, 238, 0.4);
    }

    .stButton > button:disabled {
        background: linear-gradient(100deg, #1E2547, #262E57);
        color: #6B7599 !important;
    }

    .st-key-cta_dashboard button {
        background: transparent;
        color: #F8FAFC !important;
        border: 1px solid rgba(148, 163, 184, 0.45);
    }

    .st-key-cta_dashboard button:hover {
        background: rgba(34, 211, 238, 0.08);
        color: #F8FAFC !important;
        border-color: #22D3EE;
        box-shadow: none;
    }

    /* ---------- Cards / containers (default) ---------- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(135deg, #0B1D4D, #1E1250);
        border: 1.5px solid #818CF8;
        border-radius: 18px;
        box-shadow: 0 10px 28px rgba(99, 102, 241, 0.28);
    }

    [data-testid="stExpander"] {
        background: linear-gradient(135deg, #0B1D4D, #1E1250);
        border: 1.5px solid #818CF8;
        border-radius: 16px;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.card-0) {
        background: linear-gradient(135deg, #062B3D 0%, #0E7490 100%);
        border: 1.5px solid #22D3EE;
        box-shadow: 0 10px 28px rgba(34,211,238, 0.32), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.card-1) {
        background: linear-gradient(135deg, #1E1250 0%, #5B3FD0 100%);
        border: 1.5px solid #A78BFA;
        box-shadow: 0 10px 28px rgba(139,92,246, 0.32), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.card-2) {
        background: linear-gradient(135deg, #0B1D4D 0%, #2554C7 100%);
        border: 1.5px solid #60A5FA;
        box-shadow: 0 10px 28px rgba(59,130,246, 0.32), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.card-3) {
        background: linear-gradient(135deg, #3A1052 0%, #A21CAF 100%);
        border: 1.5px solid #E879F9;
        box-shadow: 0 10px 28px rgba(192,38,211, 0.32), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.card-4) {
        background: linear-gradient(135deg, #11154A 0%, #4047D6 100%);
        border: 1.5px solid #818CF8;
        box-shadow: 0 10px 28px rgba(99,102,241, 0.32), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.card-5) {
        background: linear-gradient(135deg, #4A0F2E 0%, #BE185D 100%);
        border: 1.5px solid #F9A8D4;
        box-shadow: 0 10px 28px rgba(219,39,119, 0.32), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    /* ---------- Progress bar ---------- */
    .stProgress > div > div {
        background: rgba(255, 255, 255, 0.08);
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #22D3EE, #818CF8, #C084FC, #F472B6);
    }

    /* ---------- Inputs ---------- */
    .stRadio label,
    .stSelectbox label,
    .stTextInput label,
    .stTextArea label {
        color: #F8FAFC !important;
    }

    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] {
        background: linear-gradient(135deg, #0B1D4D, #1E1250);
        border: 1.5px solid rgba(34, 211, 238, 0.55);
        border-radius: 12px;
        color: #FFFFFF;
    }

    [data-baseweb="select"] *,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        color: #FFFFFF !important;
    }

    /* ---------- Alerts: each type has its own gradient ---------- */
    [data-testid="stAlert"] {
        background: linear-gradient(120deg, #1E1250, #3B2AA0);
        border: 1.5px solid #A78BFA;
        border-radius: 14px;
    }

    [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {
        background: linear-gradient(120deg, #062B3D, #0E7490);
        border-color: #22D3EE;
    }

    [data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {
        background: linear-gradient(120deg, #11154A, #4047D6);
        border-color: #818CF8;
    }

    [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {
        background: linear-gradient(120deg, #4A1D06, #B45309);
        border-color: #FCD34D;
    }

    [data-testid="stAlert"] p {
        color: #FFFFFF !important;
    }

    a {
        color: #22D3EE !important;
    }

    ::selection {
        background: #22D3EE;
        color: #050816;
    }

    /* ====================== EXTRA COMPONENTS ====================== */

    /* ---------- Tabs ---------- */
    [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.22);
    }

    [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 12px 12px 0 0;
    }

    [data-baseweb="tab"] p {
        font-family: var(--mono) !important;
        font-weight: 600;
        letter-spacing: 0.02em;
        color: #94A3B8;
    }

    [data-baseweb="tab"][aria-selected="true"] p {
        color: #22D3EE;
    }

    [data-baseweb="tab-highlight"] {
        background: linear-gradient(90deg, #22D3EE, #C084FC) !important;
        height: 3px !important;
    }

    /* ---------- Forms ---------- */
    [data-testid="stForm"] {
        background: linear-gradient(135deg, #0B1D4D, #1E1250);
        border: 1.5px solid rgba(34, 211, 238, 0.45);
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 10px 28px rgba(34, 211, 238, 0.12);
    }

    /* ---------- Tables ---------- */
    [data-testid="stDataFrame"] {
        border: 1.5px solid rgba(129, 140, 248, 0.5);
        border-radius: 14px;
        overflow: hidden;
    }

    /* ---------- Sidebar user box ---------- */
    .user-box {
        padding: 14px 16px;
        border-radius: 16px;
        border: 1.5px solid rgba(34, 211, 238, 0.45);
        background: linear-gradient(135deg, #062B3D, #1E1250);
        margin-bottom: 10px;
    }

    .user-box .user-name {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        color: #FFFFFF;
    }

    .user-box .user-sub {
        font-family: var(--mono);
        font-size: 0.75rem;
        color: #94A3B8;
    }

    /* ---------- Step cards on Home ---------- */
    .step-num {
        font-family: var(--mono);
        font-size: 0.8rem;
        letter-spacing: 0.15em;
        color: rgba(255, 255, 255, 0.75);
    }

    .step-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 1.35rem;
        color: #FFFFFF;
        margin: 4px 0 6px;
    }

    .step-text {
        font-size: 0.95rem;
        line-height: 1.55;
        color: rgba(255, 255, 255, 0.88);
    }

    /* ---------- Footer ---------- */
    .app-footer {
        margin-top: 48px;
        padding-top: 18px;
        border-top: 1px solid rgba(148, 163, 184, 0.2);
        text-align: center;
        font-family: var(--mono);
        font-size: 0.78rem;
        letter-spacing: 0.06em;
        color: #64748B;
    }

    /* ---------- Compact hero (login page) ---------- */
    .hero.compact {
        min-height: 380px;
        padding: 48px 48px 44px;
    }

    .hero.compact .hero-title {
        font-size: clamp(36px, 5.2vw, 70px);
    }

    /* ---------- Mobile polish ---------- */
    @media (max-width: 768px) {
        .block-container {
            padding: 1.2rem 0.9rem 3rem !important;
        }

        .hero,
        .hero.compact {
            padding: 32px 20px;
            min-height: 0;
        }

        .hero-title {
            font-size: clamp(34px, 11vw, 56px);
        }

        [data-testid="stMetric"] {
            padding: 12px;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }

        .stLinkButton > a,
        .stButton > button {
            width: 100%;
        }
    }

    /* ---------- Hide Streamlit default menu/footer for a cleaner look ---------- */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>"""


def inject_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def hide_sidebar():
    """Used on the login page, where the sidebar would be empty."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero_html(compact=False):
    """Hero banner. Written without blank lines so Markdown keeps it as HTML."""
    lines = [
        '<div class="hero compact">' if compact else '<div class="hero">',
        '<div class="hero-ring r1"></div>',
        '<div class="hero-ring r2"></div>',
        '<div class="hero-ring r3"></div>',
        '<div class="hero-tile t1">🐍</div>',
        '<div class="hero-tile t2">📊</div>',
        '<div class="hero-tile t3">🗄️</div>',
        '<div class="hero-tile t4">🌐</div>',
        '<div class="hero-tile t5">🎯</div>',
        '<div class="hero-rail"><span class="on"></span><span></span><span></span><span></span>'
        '<span></span><span></span><span></span><span></span></div>',
        '<div class="hero-eyebrow"><span class="hero-dot"></span>Career tracking studio · SkillMap · 2026</div>',
        '<div class="hero-title">We build<br><span class="grad-text">skills</span><br>'
        'into your <span class="serif-accent">career.</span></div>',
        '<div class="hero-sub">Pick a career path, learn the right skills, finish practical tasks '
        'and watch your readiness grow, all in one place.</div>',
        "</div>",
    ]
    return "\n".join(lines)
