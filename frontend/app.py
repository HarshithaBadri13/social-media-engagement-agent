import re
import sys
import textwrap
from pathlib import Path
import streamlit as st


def render_html_block(html_content: str):
    """
    Renders pure HTML/SVG components cleanly without Markdown indented-code-block artifacts.
    Prefers st.html (Streamlit 1.34+) to bypass Markdown parsing entirely,
    ensuring that raw HTML/SVG elements are rendered as visual components
    instead of being converted into <pre><code> text blocks.
    Falls back to st.markdown with dedented content.
    """
    cleaned = textwrap.dedent(html_content).strip()
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


# Ensure workspace root is always on sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend import agent
try:
    from backend.database import (
        get_brand_profile,
        save_brand_profile,
        reset_brand_profile,
        save_emotion_reply,
        get_saved_emotion_replies,
    )
except ImportError:
    from database import (
        get_brand_profile,
        save_brand_profile,
        reset_brand_profile,
        save_emotion_reply,
        get_saved_emotion_replies,
    )

# Attach database methods to agent module to handle running Streamlit caches
if not hasattr(agent, "get_brand_profile"):
    agent.get_brand_profile = get_brand_profile
if not hasattr(agent, "save_brand_profile"):
    agent.save_brand_profile = save_brand_profile
if not hasattr(agent, "reset_brand_profile"):
    agent.reset_brand_profile = reset_brand_profile
if not hasattr(agent, "save_emotion_reply"):
    agent.save_emotion_reply = save_emotion_reply
if not hasattr(agent, "get_saved_emotion_replies"):
    agent.get_saved_emotion_replies = get_saved_emotion_replies

st.set_page_config(
    page_title="Social Media Engagement Agent",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# GLOBAL STYLING & DESIGN SYSTEM
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        color-scheme: dark;
        --bg: #070A14;
        --surface: #0E1424;
        --card: rgba(17, 24, 39, 0.72);
        --card-hover: rgba(26, 36, 60, 0.85);
        --card-border: rgba(255, 255, 255, 0.08);
        --card-border-hover: rgba(139, 92, 246, 0.4);
        --blue: #3B82F6;
        --blue-bright: #4F8CFF;
        --violet: #8B5CF6;
        --pink: #EC4899;
        --cyan: #06B6D4;
        --amber: #F59E0B;
        --emerald: #10B981;
        --text: #F8FAFC;
        --muted: #94A3B8;
        --line: rgba(255, 255, 255, 0.08);
        --font-main: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
    }

    html {
        scroll-behavior: smooth;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: var(--bg);
        color: var(--text);
        font-family: var(--font-main);
    }

    .stApp {
        background-image: 
            radial-gradient(ellipse at 15% 8%, rgba(79, 140, 255, 0.14), transparent 38%),
            radial-gradient(ellipse at 85% 16%, rgba(139, 92, 246, 0.15), transparent 42%),
            radial-gradient(ellipse at 50% 65%, rgba(236, 72, 153, 0.07), transparent 45%),
            radial-gradient(ellipse at 20% 90%, rgba(6, 182, 212, 0.06), transparent 35%);
        background-attachment: fixed;
    }

    /* Streamlit Main Container Adjustment */
    [data-testid="stHeader"] {
        background: rgba(7, 10, 20, 0.8) !important;
        backdrop-filter: blur(12px) !important;
    }

    [data-testid="stToolbar"] {
        right: 1.5rem;
    }

    /* Typography */
    h1, h2, h3, h4, p, label, span {
        font-family: var(--font-main);
    }

    /* Common Custom Button Styles */
    div.stButton > button {
        min-height: 2.85rem;
        border-radius: 10px;
        font-weight: 600;
        font-family: var(--font-main);
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }

    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%) !important;
        border: none !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 18px rgba(139, 92, 246, 0.35) !important;
        transition: all 0.22s ease !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(139, 92, 246, 0.55) !important;
        filter: brightness(1.08);
    }

    /* Landing Page Get Started Buttons Override (Solid Vibrant Blue) */
    button[key="nav_get_started"],
    button[key="hero_get_started"],
    button[key="bottom_cta_get_started"] {
        background: #1D8CF8 !important;
        border: none !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(29, 140, 248, 0.45) !important;
    }

    button[key="nav_get_started"]:hover,
    button[key="hero_get_started"]:hover,
    button[key="bottom_cta_get_started"]:hover {
        background: #1577D6 !important;
        box-shadow: 0 6px 20px rgba(29, 140, 248, 0.6) !important;
    }

    div.stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid var(--card-border) !important;
        color: var(--text) !important;
        backdrop-filter: blur(8px);
    }

    div.stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: var(--blue-bright) !important;
        transform: translateY(-1px);
    }

    /* ------------------------------------------------------------- */
    /* LANDING PAGE HERO & SECTIONS STYLES                          */
    /* ------------------------------------------------------------- */
    
    /* Top Navigation Bar */
    .landing-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 1.5rem;
        background: rgba(14, 20, 36, 0.75);
        backdrop-filter: blur(16px);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
    }

    .landing-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        text-decoration: none;
    }

    .brand-bubble-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: #1D8CF8;
        box-shadow: 0 0 16px rgba(29, 140, 248, 0.55);
        flex-shrink: 0;
    }

    .brand-title-text {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.01em;
    }

    .nav-links {
        display: flex;
        align-items: center;
        gap: 1.8rem;
    }

    .nav-link {
        color: #94A3B8 !important;
        text-decoration: none !important;
        font-size: 0.95rem;
        font-weight: 500;
        transition: color 0.2s ease;
    }

    .nav-link:hover {
        color: #ffffff !important;
    }

    /* Hero Container */
    .hero-wrapper {
        position: relative;
        padding: 3.2rem 1.5rem 2.2rem;
        text-align: center;
        overflow: visible;
        isolation: isolate;
        max-width: 1200px;
        margin: 0 auto;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.42rem 1.25rem;
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-radius: 9999px;
        font-size: 0.88rem;
        font-weight: 600;
        color: #D8B4FE;
        margin-bottom: 1.4rem;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
    }

    .hero-badge-spark {
        display: inline-block;
        font-size: 0.95rem;
    }

    .hero-title {
        font-size: 4.8rem;
        font-weight: 800;
        line-height: 1.08;
        letter-spacing: -0.035em;
        margin: 0 auto 0.9rem;
    }

    .title-white {
        color: #FFFFFF;
    }

    .title-spark {
        background: linear-gradient(135deg, #A855F7 0%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }

    .hero-subtitle {
        font-size: 1.55rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.4;
        max-width: 760px;
        margin: 0 auto 1.1rem;
        letter-spacing: -0.01em;
    }

    .hero-intro {
        font-size: 1.05rem;
        color: #94A3B8;
        line-height: 1.65;
        max-width: 660px;
        margin: 0 auto 2.2rem;
    }

    /* Floating Social Media Squircles (Instagram, LinkedIn, X, YouTube) */
    .hero-orb {
        position: absolute;
        z-index: 2;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 58px;
        height: 58px;
        border-radius: 16px;
        backdrop-filter: blur(12px);
        transition: transform 0.35s ease, box-shadow 0.35s ease;
        animation: floatMotion var(--float-duration, 5s) ease-in-out var(--float-delay, 0s) infinite alternate;
    }

    .hero-orb:hover {
        transform: scale(1.15) translateY(-4px) !important;
        z-index: 10;
    }

    .hero-orb svg {
        display: block;
    }

    /* Exact 4 Squircles Placements from Screenshot */
    .orb-instagram {
        top: 10%;
        left: 5%;
        background: rgba(11, 15, 34, 0.9);
        border: 1.8px solid #E1306C;
        box-shadow: 0 0 24px rgba(225, 48, 108, 0.45);
        --float-duration: 4.8s;
        --float-delay: 0s;
    }

    .orb-linkedin {
        top: 48%;
        left: 7.5%;
        background: #0A66C2;
        border: 1.5px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 0 24px rgba(10, 102, 194, 0.5);
        --float-duration: 5.6s;
        --float-delay: 0.8s;
    }

    .orb-x {
        top: 25%;
        right: 7.5%;
        background: #0B132B;
        border: 1.8px solid #38BDF8;
        box-shadow: 0 0 24px rgba(56, 189, 248, 0.45);
        --float-duration: 5.2s;
        --float-delay: 0.4s;
    }

    .orb-youtube {
        top: 44%;
        right: 5%;
        background: #0B132B;
        border: 1.5px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 0 24px rgba(255, 0, 0, 0.38);
        --float-duration: 6s;
        --float-delay: 1.2s;
    }

    /* Ambient Curved Light Flares from Screenshot */
    .hero-light-arc-left {
        position: absolute;
        top: 16%;
        left: -6%;
        width: 560px;
        height: 440px;
        border-radius: 50%;
        border-bottom: 3px solid rgba(56, 189, 248, 0.6);
        box-shadow: 0 18px 48px rgba(56, 189, 248, 0.38), inset 0 -6px 20px rgba(56, 189, 248, 0.2);
        transform: rotate(-22deg);
        pointer-events: none;
        z-index: 1;
        filter: blur(0.5px);
    }

    .hero-light-arc-right {
        position: absolute;
        top: 20%;
        right: -6%;
        width: 560px;
        height: 440px;
        border-radius: 50%;
        border-bottom: 3px solid rgba(59, 130, 246, 0.6);
        box-shadow: 0 18px 48px rgba(59, 130, 246, 0.38), inset 0 -6px 20px rgba(59, 130, 246, 0.2);
        transform: rotate(22deg);
        pointer-events: none;
        z-index: 1;
        filter: blur(0.5px);
    }

    /* Floating Keyframe */
    @keyframes floatMotion {
        0% { transform: translateY(0px) rotate(-2deg); }
        50% { transform: translateY(-10px) rotate(2deg); }
        100% { transform: translateY(-3px) rotate(-1deg); }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 15px rgba(139, 92, 246, 0.2); }
        100% { box-shadow: 0 0 28px rgba(139, 92, 246, 0.45); }
    }

    @keyframes sparkSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @keyframes titleShimmer {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }

    /* Explore Features Anchor Button (Dark Translucent with Fire Emoji) */
    .hero-explore-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        min-height: 2.85rem;
        padding: 0 1.5rem;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #FFFFFF !important;
        font-weight: 600;
        text-decoration: none !important;
        backdrop-filter: blur(8px);
        transition: all 0.22s ease;
        box-sizing: border-box;
        width: 100%;
    }

    .hero-explore-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.3);
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }

    /* Hero Showcase Card (Matching Reference Picture) */
    .hero-showcase-wrapper {
        max-width: 880px;
        margin: 2.2rem auto 2.8rem;
        padding: 0 1rem;
        position: relative;
        z-index: 3;
    }

    .hero-showcase-card {
        background: rgba(10, 18, 40, 0.72);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1.5px solid rgba(59, 130, 246, 0.42);
        border-radius: 20px;
        padding: 2.4rem 2rem 2.6rem;
        text-align: center;
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6), 0 0 35px rgba(59, 130, 246, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.12);
        position: relative;
        overflow: hidden;
    }

    .hero-showcase-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 20%;
        right: 20%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #38BDF8, #A855F7, transparent);
    }

    .showcase-card-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.38rem 1.15rem;
        border-radius: 9999px;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.35);
        color: #7DD3FC;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1.25rem;
        box-shadow: 0 0 16px rgba(56, 189, 248, 0.2);
    }

    .showcase-card-title {
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin: 0 auto 0.6rem;
        line-height: 1.15;
    }

    .showcase-card-subtitle {
        font-size: 1.3rem;
        font-weight: 600;
        color: #FFFFFF;
        margin: 0;
        letter-spacing: -0.01em;
    }

    /* Section Headers */
    .landing-section {
        padding: 4rem 1rem 2rem;
        max-width: 1240px;
        margin: 0 auto;
    }

    .section-badge {
        display: inline-block;
        padding: 0.35rem 0.95rem;
        border-radius: 9999px;
        background: rgba(79, 140, 255, 0.1);
        border: 1px solid rgba(79, 140, 255, 0.3);
        color: #93C5FD;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
    }

    .section-title {
        font-size: 2.45rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #FFFFFF;
        margin-bottom: 0.85rem;
    }

    .section-subtitle {
        font-size: 1.15rem;
        color: var(--muted);
        line-height: 1.6;
        max-width: 680px;
        margin-bottom: 2.5rem;
    }

    .section-lead {
        font-size: 1.18rem;
        color: #CBD5E1;
        line-height: 1.7;
        max-width: 860px;
        margin-bottom: 2.5rem;
    }

    /* About Section Grid */
    .about-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin-top: 1.5rem;
    }

    .about-card {
        background: var(--card);
        backdrop-filter: blur(14px);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 2rem 1.6rem;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }

    .about-card:hover {
        transform: translateY(-5px);
        border-color: var(--card-border-hover);
        background: var(--card-hover);
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
    }

    .about-icon-box {
        width: 52px;
        height: 52px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 1.25rem;
    }

    .about-icon-box.pink { background: rgba(236, 72, 153, 0.15); border: 1px solid rgba(236, 72, 153, 0.3); color: #F472B6; }
    .about-icon-box.purple { background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.3); color: #A78BFA; }
    .about-icon-box.blue { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #60A5FA; }

    .about-card h3 {
        font-size: 1.28rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.65rem;
    }

    .about-card p {
        font-size: 0.96rem;
        color: var(--muted);
        line-height: 1.6;
        margin: 0;
    }

    /* How It Works Timeline */
    .timeline-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        position: relative;
    }

    .timeline-card {
        background: var(--card);
        backdrop-filter: blur(14px);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 1.85rem 1.5rem;
        position: relative;
        transition: all 0.3s ease;
    }

    .timeline-card:hover {
        transform: translateY(-4px);
        border-color: rgba(79, 140, 255, 0.4);
        background: var(--card-hover);
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.35);
    }

    .timeline-step-badge {
        display: inline-block;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #60A5FA;
        background: rgba(59, 130, 246, 0.12);
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }

    .timeline-icon {
        font-size: 1.8rem;
        margin-bottom: 0.85rem;
    }

    .timeline-card h4 {
        font-size: 1.18rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.55rem;
    }

    .timeline-card p {
        font-size: 0.92rem;
        color: var(--muted);
        line-height: 1.55;
        margin: 0;
    }

    /* Unique Features Grid */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.6rem;
    }

    .feature-card {
        background: var(--card);
        backdrop-filter: blur(14px);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 2.1rem 1.6rem;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .feature-card:hover {
        transform: translateY(-6px);
        border-color: rgba(139, 92, 246, 0.5);
        background: var(--card-hover);
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
    }

    .feature-icon-wrapper {
        width: 54px;
        height: 54px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.6rem;
        margin-bottom: 1.35rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .feature-card h3 {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.65rem;
    }

    .feature-card p {
        font-size: 0.94rem;
        color: var(--muted);
        line-height: 1.6;
        margin: 0 0 1.25rem;
    }

    .feature-tag {
        display: inline-block;
        font-size: 0.76rem;
        font-weight: 600;
        color: #C4D7FF;
        background: rgba(139, 92, 246, 0.14);
        padding: 0.28rem 0.75rem;
        border-radius: 9999px;
        border: 1px solid rgba(139, 92, 246, 0.25);
        align-self: flex-start;
    }

    /* Why Choose Our Agent Grid */
    .why-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.6rem;
    }

    .why-card {
        background: var(--card);
        backdrop-filter: blur(14px);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        padding: 2.2rem 1.8rem;
        transition: all 0.3s ease;
        position: relative;
    }

    .why-card:hover {
        transform: translateY(-4px);
        border-color: rgba(79, 140, 255, 0.4);
        background: var(--card-hover);
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.35);
    }

    .why-number {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--blue-bright), var(--violet));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.85rem;
    }

    .why-card h3 {
        font-size: 1.3rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.65rem;
    }

    .why-card p {
        font-size: 0.98rem;
        color: var(--muted);
        line-height: 1.65;
        margin: 0;
    }

    /* Call to Action Banner */
    .cta-container {
        margin: 4.5rem auto 2.5rem;
        padding: 3.5rem 2rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(30, 41, 75, 0.7) 0%, rgba(49, 29, 90, 0.7) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-radius: 28px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(139, 92, 246, 0.2);
        max-width: 1080px;
        position: relative;
        overflow: hidden;
    }

    .cta-title {
        font-size: 2.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #FFFFFF;
        margin-bottom: 0.85rem;
    }

    .cta-subtitle {
        font-size: 1.22rem;
        color: #E2E8F0;
        max-width: 620px;
        margin: 0 auto 2.2rem;
    }

    /* Footer */
    .landing-footer {
        padding: 3.5rem 1.5rem 2rem;
        border-top: 1px solid var(--line);
        margin-top: 4rem;
        color: var(--muted);
    }

    .footer-content {
        max-width: 1240px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1.5rem;
    }

    .footer-left {
        max-width: 480px;
    }

    .footer-brand {
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.45rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .footer-desc {
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0;
    }

    .footer-tags {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .platform-pill {
        display: inline-block;
        font-size: 0.82rem;
        padding: 0.3rem 0.85rem;
        border-radius: 9999px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--card-border);
        color: #CBD5E1;
    }

    .footer-bottom {
        max-width: 1240px;
        margin: 2rem auto 0;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.85rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* ------------------------------------------------------------- */
    /* DASHBOARD SIDEBAR & WORKSPACE STYLING                         */
    /* ------------------------------------------------------------- */
    div[data-testid="stSidebar"] {
        background: #060913 !important;
        background-color: #060913 !important;
        background-image: 
            radial-gradient(circle at 12% 10%, rgba(56, 189, 248, 0.22), transparent 42%),
            radial-gradient(circle at 88% 38%, rgba(168, 85, 247, 0.2), transparent 48%),
            radial-gradient(circle at 18% 70%, rgba(236, 72, 153, 0.16), transparent 45%),
            radial-gradient(circle at 82% 94%, rgba(20, 184, 166, 0.18), transparent 42%),
            linear-gradient(180deg, #090E24 0%, #060914 100%) !important;
        background-attachment: fixed !important;
        border-right: 1px solid rgba(56, 189, 248, 0.35) !important;
        box-shadow: 6px 0 38px rgba(0, 0, 0, 0.65), inset -1px 0 16px rgba(168, 85, 247, 0.1) !important;
        overflow-x: hidden !important;
    }

    div[data-testid="stSidebar"] > div:first-child,
    div[data-testid="stSidebarContent"],
    div[data-testid="stSidebarUserContent"] {
        background: transparent !important;
    }

    /* Responsive Sidebar Width */
    @media (min-width: 992px) {
        div[data-testid="stSidebar"] {
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
        }
        div[data-testid="stSidebar"] > div:first-child {
            width: 320px !important;
        }
    }

    @media (min-width: 768px) and (max-width: 991px) {
        div[data-testid="stSidebar"] {
            width: 285px !important;
            min-width: 285px !important;
            max-width: 285px !important;
        }
        div[data-testid="stSidebar"] > div:first-child {
            width: 285px !important;
        }
    }

    /* Sidebar Brand & Workspace Header */
    .sidebar-brand-box {
        padding: 0.75rem 0.25rem 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .sidebar-brand-header {
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }

    .sidebar-brand-logo {
        filter: drop-shadow(0 0 12px rgba(29, 140, 248, 0.75));
        flex-shrink: 0;
        transition: transform 0.25s ease;
    }

    .sidebar-brand-logo:hover {
        transform: rotate(5deg) scale(1.08);
    }

    .sidebar-brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin: 0;
    }

    .brand-text-white {
        color: #FFFFFF;
    }

    .brand-text-agent-grad {
        background: linear-gradient(135deg, #A855F7 0%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }

    .sidebar-brand-sub {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: #64748B;
        padding-left: 2.7rem;
        margin-top: 0.15rem;
    }

    .sparkle-cyan {
        color: #38BDF8;
        font-size: 1.35rem;
        filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.8));
        animation: pulseSparkle 3s ease-in-out infinite alternate;
    }

    @keyframes pulseSparkle {
        0% { transform: scale(1); filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.7)); }
        100% { transform: scale(1.1); filter: drop-shadow(0 0 14px rgba(168, 85, 247, 0.9)); }
    }

    /* Sidebar User Profile Card (Obsidian Cyber-Glass) */
    .sidebar-user-card {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        background: linear-gradient(135deg, rgba(14, 23, 50, 0.75) 0%, rgba(25, 20, 60, 0.6) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 4px 22px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12);
        transition: all 0.25s ease;
    }

    .sidebar-user-card:hover {
        border-color: rgba(168, 85, 247, 0.65);
        background: linear-gradient(135deg, rgba(20, 32, 70, 0.85) 0%, rgba(40, 24, 75, 0.75) 100%);
        box-shadow: 0 6px 28px rgba(56, 189, 248, 0.25), 0 0 18px rgba(168, 85, 247, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.18);
        transform: translateY(-1px);
    }

    .user-avatar-wrap {
        position: relative;
        flex-shrink: 0;
    }

    .avatar-online-dot {
        position: absolute;
        bottom: -2px;
        right: -2px;
        width: 10px;
        height: 10px;
        background: #10B981;
        border: 2px solid #060913;
        border-radius: 50%;
        box-shadow: 0 0 10px #10B981, 0 0 16px rgba(16, 185, 129, 0.8);
    }

    .user-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 11px;
        font-weight: 700;
        color: #5EEAD4;
        background: linear-gradient(135deg, rgba(13, 148, 136, 0.22), rgba(16, 185, 129, 0.16));
        border: 1px solid rgba(20, 184, 166, 0.45);
        padding: 0.22rem 0.55rem;
        border-radius: 9999px;
        flex-shrink: 0;
        box-shadow: 0 0 10px rgba(20, 184, 166, 0.25);
    }

    .user-online-ping {
        font-size: 8px;
        color: #14B8A6;
        display: inline-block;
        animation: pingDot 2s infinite ease-in-out;
    }

    @keyframes pingDot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.45; transform: scale(0.85); }
    }

    .user-avatar {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 40%, #8B5CF6 75%, #EC4899 100%);
        box-shadow: 0 0 16px rgba(6, 182, 212, 0.55), 0 0 10px rgba(236, 72, 153, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }

    .user-info {
        flex-grow: 1;
        overflow: hidden;
    }

    .user-name {
        font-size: 15px;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.25;
        letter-spacing: -0.01em;
    }

    .user-email {
        font-size: 12.5px;
        color: #93C5FD;
        line-height: 1.25;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-top: 0.15rem;
        font-weight: 400;
    }

    .sidebar-divider {
        height: 2px;
        background: linear-gradient(90deg, rgba(56, 189, 248, 0) 0%, rgba(56, 189, 248, 0.5) 20%, rgba(168, 85, 247, 0.65) 50%, rgba(236, 72, 153, 0.5) 80%, rgba(20, 184, 166, 0) 100%);
        border: none;
        margin: 1.2rem 0 1.15rem;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.35);
    }

    /* Navigation Heading & Section Layout */
    .sidebar-section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.85rem;
        padding: 0 0.2rem;
    }

    .sidebar-nav-heading {
        font-size: 11.5px;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0;
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }

    .sidebar-section-badge {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #38BDF8;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 0.18rem 0.55rem;
        border-radius: 9999px;
    }

    /* ------------------------------------------------------------- */
    /* STANDALONE BOX FOR EVERY NAVIGATION TAB                      */
    /* ------------------------------------------------------------- */
    div[data-testid="stSidebar"] [data-testid="stRadio"] > label,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] {
        display: none !important;
    }

    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 0.85rem !important;
        width: 100% !important;
    }

    /* Tab Box Item Wrapper across Streamlit DOM versions */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"] {
        display: block !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Dedicated Standalone Box Card for Each Tab */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"] label,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: center !important;
        position: relative !important;
        overflow: hidden !important;
        padding: 0.95rem 1.15rem 0.95rem 1.25rem !important;
        border-radius: 14px !important;
        background: linear-gradient(135deg, rgba(14, 23, 48, 0.82) 0%, rgba(20, 30, 65, 0.55) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.18) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        color: #CBD5E1 !important;
        cursor: pointer !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        margin: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
    }

    /* Completely hide standard radio dot circle & input */
    div[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"],
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label > div:first-child,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"] > label > div:first-child,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Tab Box Title Typography */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label p,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
        color: #F8FAFC !important;
        font-size: 14.5px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: -0.01em !important;
        line-height: 1.3 !important;
        display: block !important;
        padding-right: 4.8rem !important; /* Prevents text overlapping with the category badge */
    }

    /* Tab Box Caption / Subtitle Typography */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label span,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stCaptionContainer"],
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[data-testid="stMarkdownContainer"] + span,
    div[data-testid="stSidebar"] [data-testid="stRadio"] p ~ span {
        color: #94A3B8 !important;
        font-size: 11.5px !important;
        font-weight: 400 !important;
        margin-top: 0.28rem !important;
        line-height: 1.35 !important;
        letter-spacing: 0.01em !important;
        display: block !important;
        padding-right: 1.5rem !important;
    }

    /* Category Badges for each Tab Box */
    /* Tab Box 1 Badge: Composer */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(1) label::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1)::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(1) label::after {
        content: 'Composer' !important;
        position: absolute !important;
        right: 0.95rem !important;
        top: 0.95rem !important;
        font-size: 9.5px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        padding: 0.18rem 0.52rem !important;
        border-radius: 9999px !important;
        background: rgba(56, 189, 248, 0.14) !important;
        color: #38BDF8 !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.2) !important;
    }

    /* Tab Box 2 Badge: Empathy */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(2) label::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2)::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(2) label::after {
        content: 'Empathy' !important;
        position: absolute !important;
        right: 0.95rem !important;
        top: 0.95rem !important;
        font-size: 9.5px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        padding: 0.18rem 0.52rem !important;
        border-radius: 9999px !important;
        background: rgba(236, 72, 153, 0.14) !important;
        color: #F472B6 !important;
        border: 1px solid rgba(236, 72, 153, 0.35) !important;
        box-shadow: 0 0 10px rgba(236, 72, 153, 0.2) !important;
    }

    /* Tab Box 3 Badge: Memory */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(3) label::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3)::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(3) label::after {
        content: 'Memory' !important;
        position: absolute !important;
        right: 0.95rem !important;
        top: 0.95rem !important;
        font-size: 9.5px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        padding: 0.18rem 0.52rem !important;
        border-radius: 9999px !important;
        background: rgba(168, 85, 247, 0.14) !important;
        color: #C084FC !important;
        border: 1px solid rgba(168, 85, 247, 0.35) !important;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.2) !important;
    }

    /* Tab Box 4 Badge: Identity */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(4) label::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4)::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(4) label::after {
        content: 'Identity' !important;
        position: absolute !important;
        right: 0.95rem !important;
        top: 0.95rem !important;
        font-size: 9.5px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        padding: 0.18rem 0.52rem !important;
        border-radius: 9999px !important;
        background: rgba(20, 184, 166, 0.14) !important;
        color: #2DD4BF !important;
        border: 1px solid rgba(20, 184, 166, 0.35) !important;
        box-shadow: 0 0 10px rgba(20, 184, 166, 0.2) !important;
    }

    /* Distinct Hover state for each Tab Box */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {
        transform: translateY(-2px) translateX(3px) !important;
        color: #FFFFFF !important;
    }

    /* Tab Box 1: Create a Post - Blue/Cyan Hover */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(1) label:hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1):hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(1) label:hover {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.22) 0%, rgba(59, 130, 246, 0.18) 100%) !important;
        border-color: rgba(56, 189, 248, 0.65) !important;
        box-shadow: 0 6px 24px rgba(6, 182, 212, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
    }

    /* Tab Box 2: Emotion Replies - Pink/Rose Hover */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(2) label:hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2):hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(2) label:hover {
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.22) 0%, rgba(244, 63, 94, 0.18) 100%) !important;
        border-color: rgba(236, 72, 153, 0.65) !important;
        box-shadow: 0 6px 24px rgba(236, 72, 153, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
    }

    /* Tab Box 3: What Agent Learned - Purple/Violet Hover */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(3) label:hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3):hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(3) label:hover {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.22) 0%, rgba(139, 92, 246, 0.18) 100%) !important;
        border-color: rgba(168, 85, 247, 0.65) !important;
        box-shadow: 0 6px 24px rgba(168, 85, 247, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
    }

    /* Tab Box 4: Brand Voice - Teal/Emerald Hover */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(4) label:hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4)::hover,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:nth-child(4) label:hover {
        background: linear-gradient(135deg, rgba(20, 184, 166, 0.22) 0%, rgba(16, 185, 129, 0.18) 100%) !important;
        border-color: rgba(20, 184, 166, 0.65) !important;
        box-shadow: 0 6px 24px rgba(20, 184, 166, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
    }

    /* Active Selected Tab Box: Multi-vibrant gradient with neon glow */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"],
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:has(input:checked) label,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:has(input:checked) label,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked) {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.42) 0%, rgba(79, 70, 229, 0.45) 38%, rgba(124, 58, 237, 0.42) 72%, rgba(219, 39, 119, 0.38) 100%) !important;
        border: 1.5px solid rgba(56, 189, 248, 0.85) !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 30px rgba(14, 165, 233, 0.42), 0 0 24px rgba(124, 58, 237, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
        padding-left: 1.45rem !important;
        transform: translateX(4px) !important;
    }

    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] p,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] span,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) span,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:has(input:checked) span {
        color: #BAE6FD !important;
        font-weight: 500 !important;
    }

    /* Luminous neon indicator pill on active box */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"]::before,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked)::before,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:has(input:checked) label::before,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:has(input:checked) label::before,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked)::before {
        content: '' !important;
        position: absolute !important;
        left: 0 !important;
        top: 10% !important;
        bottom: 10% !important;
        width: 5px !important;
        border-radius: 0 6px 6px 0 !important;
        background: linear-gradient(180deg, #38BDF8 0%, #A855F7 50%, #EC4899 100%) !important;
        box-shadow: 0 0 14px #38BDF8, 0 0 26px rgba(236, 72, 153, 0.95) !important;
    }

    /* Active Box Badge override */
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"]::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked)::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > div:has(input:checked) label::after,
    div[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioButton"]:has(input:checked) label::after {
        content: '● ACTIVE' !important;
        background: rgba(255, 255, 255, 0.22) !important;
        color: #FFFFFF !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        box-shadow: 0 0 12px rgba(255, 255, 255, 0.45) !important;
    }

    /* Sidebar Footer Box & Sign Out */
    .sidebar-footer-box {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.65rem 0.95rem;
        border-radius: 12px;
        background: rgba(14, 23, 48, 0.5);
        border: 1px solid rgba(56, 189, 248, 0.12);
        margin-top: 1.25rem;
        margin-bottom: 0.6rem;
    }

    .sidebar-footer-info {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
    }

    .footer-status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 8px #10B981;
    }

    .footer-status-text {
        font-size: 11px;
        font-weight: 600;
        color: #94A3B8;
        letter-spacing: 0.02em;
    }

    .sidebar-footer-version {
        font-size: 10px;
        font-weight: 700;
        color: #64748B;
        background: rgba(255, 255, 255, 0.05);
        padding: 0.15rem 0.45rem;
        border-radius: 6px;
    }

    div[data-testid="stSidebar"] div.stButton > button#sidebar_sign_out,
    div[data-testid="stSidebar"] div.stButton > button {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #CBD5E1 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stSidebar"] div.stButton > button:hover {
        background: rgba(239, 68, 68, 0.15) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        color: #FCA5A5 !important;
        box-shadow: 0 4px 18px rgba(239, 68, 68, 0.25) !important;
    }

    /* AI Status Container (System Diagnostics) */
    .ai-status-container {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        margin-top: 0.4rem;
        background: linear-gradient(135deg, rgba(11, 19, 44, 0.75) 0%, rgba(18, 26, 60, 0.6) 100%);
        border: 1px solid rgba(56, 189, 248, 0.28);
        border-radius: 14px;
        padding: 0.9rem 1.05rem;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        transition: border-color 0.25s ease;
    }

    .ai-status-container:hover {
        border-color: rgba(168, 85, 247, 0.45);
    }

    .status-row {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        font-size: 13.5px;
    }

    .status-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* Glowing Dots */
    .dot-amber {
        background: #F59E0B;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.9);
    }

    .dot-green {
        background: #10B981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.9);
    }

    .dot-teal {
        background: #14B8A6;
        box-shadow: 0 0 12px rgba(20, 184, 166, 0.9);
    }

    .dot-purple {
        background: #A855F7;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.9);
    }

    .dot-cyan {
        background: #06B6D4;
        box-shadow: 0 0 12px rgba(6, 182, 212, 0.9);
    }

    .dot-pink {
        background: #EC4899;
        box-shadow: 0 0 12px rgba(236, 72, 153, 0.9);
    }

    .status-label {
        color: #E2E8F0;
        font-weight: 500;
        font-size: 13.5px;
        letter-spacing: -0.01em;
    }

    /* Status Badges */
    .status-badge {
        padding: 0.22rem 0.65rem;
        border-radius: 8px;
        font-size: 11.5px;
        font-weight: 700;
        margin-left: auto;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
        letter-spacing: 0.02em;
    }

    .status-badge-teal {
        color: #5EEAD4;
        border: 1px solid rgba(20, 184, 166, 0.5);
        background: linear-gradient(135deg, rgba(13, 148, 136, 0.25) 0%, rgba(6, 182, 212, 0.12) 100%);
        box-shadow: 0 0 12px rgba(20, 184, 166, 0.22);
    }

    .status-badge-purple {
        color: #E879F9;
        border: 1px solid rgba(168, 85, 247, 0.5);
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.25) 0%, rgba(217, 70, 239, 0.12) 100%);
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.22);
    }

    .status-badge-cyan {
        color: #67E8F9;
        border: 1px solid rgba(6, 182, 212, 0.5);
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.25) 0%, rgba(59, 130, 246, 0.12) 100%);
        box-shadow: 0 0 12px rgba(6, 182, 212, 0.22);
    }

    .status-badge-pink {
        color: #F472B6;
        border: 1px solid rgba(236, 72, 153, 0.5);
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.25) 0%, rgba(244, 63, 94, 0.12) 100%);
        box-shadow: 0 0 12px rgba(236, 72, 153, 0.22);
    }

    .status-badge-amber {
        color: #FCD34D;
        border: 1px solid rgba(245, 158, 11, 0.5);
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(217, 119, 6, 0.12) 100%);
        box-shadow: 0 0 12px rgba(245, 158, 11, 0.22);
    }

    .badge-dot-pink {
        color: #EC4899;
        font-size: 8px;
        filter: drop-shadow(0 0 5px rgba(236, 72, 153, 0.9));
    }

    /* Sidebar Sign Out Button */
    div[data-testid="stSidebar"] div.stButton > button {
        background: linear-gradient(135deg, rgba(244, 63, 94, 0.1) 0%, rgba(168, 85, 247, 0.08) 100%) !important;
        border: 1px solid rgba(244, 63, 94, 0.35) !important;
        border-radius: 12px !important;
        color: #FDA4AF !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        box-shadow: 0 2px 14px rgba(244, 63, 94, 0.15) !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
        letter-spacing: 0.01em !important;
    }

    div[data-testid="stSidebar"] div.stButton > button:hover {
        background: linear-gradient(135deg, rgba(244, 63, 94, 0.28) 0%, rgba(236, 72, 153, 0.25) 100%) !important;
        border-color: rgba(244, 63, 94, 0.7) !important;
        color: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(244, 63, 94, 0.4) !important;
    }

    /* Dashboard Workspace Main Layout */
    .workspace-main-header {
        margin-bottom: 2rem;
    }

    .engagement-title {
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin: 0 0 0.5rem 0;
        line-height: 1.15;
    }

    .sparkle-cyan-lg {
        color: #38BDF8;
        font-size: 2.3rem;
        filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.75));
    }

    .text-engagement-grad {
        background: linear-gradient(135deg, #A855F7 0%, #C084FC 45%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }

    .engagement-desc {
        font-size: 1.05rem;
        color: #CBD5E1;
        margin: 0;
        line-height: 1.6;
    }

    .module-header-row {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        margin-top: 1.8rem;
        margin-bottom: 0.75rem;
    }

    .module-header-icon {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
        flex-shrink: 0;
    }

    .icon-pink {
        background: rgba(236, 72, 153, 0.18);
        border: 1px solid rgba(236, 72, 153, 0.45);
        box-shadow: 0 0 16px rgba(236, 72, 153, 0.25);
    }

    .icon-purple {
        background: rgba(139, 92, 246, 0.18);
        border: 1px solid rgba(139, 92, 246, 0.45);
        box-shadow: 0 0 16px rgba(139, 92, 246, 0.25);
    }

    .icon-blue {
        background: rgba(59, 130, 246, 0.18);
        border: 1px solid rgba(59, 130, 246, 0.45);
        box-shadow: 0 0 16px rgba(59, 130, 246, 0.25);
    }

    .module-header-text h3 {
        font-size: 1.45rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
        line-height: 1.3;
    }

    .module-header-text p {
        font-size: 0.98rem;
        color: #CBD5E1;
        margin: 0.2rem 0 0;
    }

    /* Form Input Fields styling */
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stTextArea"] textarea {
        background-color: #0A1226 !important;
        border: 1px solid rgba(59, 130, 246, 0.35) !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
        font-size: 0.98rem !important;
        padding: 0.65rem 0.95rem !important;
        transition: all 0.22s ease !important;
    }

    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #7E90B0 !important;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.3), 0 0 16px rgba(56, 189, 248, 0.2) !important;
    }

    div[data-testid="stTextInput"] label p,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stTextArea"] label p {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #F8FAFC !important;
        margin-bottom: 0.35rem !important;
    }

    /* Primary Generate Button Gradient with scale-up */
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 0.72rem 2.2rem !important;
        box-shadow: 0 4px 22px rgba(139, 92, 246, 0.45) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        filter: brightness(1.1) !important;
        box-shadow: 0 6px 30px rgba(139, 92, 246, 0.65), 0 0 20px rgba(236, 72, 153, 0.4) !important;
    }

    /* ------------------------------------------------------------- */
    /* HERO FLOATING ELEMENTS & LIGHT BEAM ENHANCEMENTS              */
    /* ------------------------------------------------------------- */
    .hero-title .title-white {
        color: #FFFFFF;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
    }

    .hero-title .title-spark {
        background: linear-gradient(135deg, #A855F7 0%, #C084FC 35%, #EC4899 75%, #F43F5E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        filter: drop-shadow(0 0 35px rgba(236, 72, 153, 0.6));
    }

    /* Responsive adjustments */
    @media (max-width: 1024px) {
        .orb-instagram { left: 2%; }
        .orb-linkedin { left: 3%; }
        .orb-x { right: 3%; }
        .orb-youtube { right: 2%; }
    }

    @media (max-width: 960px) {
        .hero-title { font-size: 3.4rem; }
        .about-grid, .timeline-grid, .features-grid, .why-grid {
            grid-template-columns: 1fr !important;
        }
        .hero-orb {
            transform: scale(0.85);
        }
    }

    @media (max-width: 680px) {
        .hero-title { font-size: 2.5rem; }
        .hero-orb { display: none !important; }
        .hero-light-arc-left, .hero-light-arc-right { display: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# SESSION STATE & ROUTING
# -----------------------------------------------------------------------------
VALID_PAGES = ["landing", "signup", "dashboard"]
if "page" not in st.session_state or st.session_state.page not in VALID_PAGES:
    st.session_state.page = "landing"

# -----------------------------------------------------------------------------
# VIEW 1: LANDING PAGE
# -----------------------------------------------------------------------------
if st.session_state.page == "landing":
    # Hide sidebar strictly on the landing page and apply landing theme styling
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 100% !important;
            padding: 1.5rem 2.5rem 4rem !important;
        }

        /* Solid Vibrant Blue for All Landing Page Buttons */
        [data-testid="stAppViewContainer"] div.stButton > button[kind="primary"],
        [data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        [data-testid="stAppViewContainer"] div.stButton > button {
            background: #1D8CF8 !important;
            border: none !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            box-shadow: 0 4px 14px rgba(29, 140, 248, 0.45) !important;
            transition: all 0.2s ease !important;
        }

        [data-testid="stAppViewContainer"] div.stButton > button:hover {
            background: #1577D6 !important;
            box-shadow: 0 6px 20px rgba(29, 140, 248, 0.65) !important;
            transform: translateY(-1px) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. TOP NAVIGATION BAR
    top_c1, top_c2, top_c3 = st.columns([3, 5, 2])
    with top_c1:
        render_html_block(
            """<div class="landing-brand" style="display:flex; align-items:center; gap:0.65rem; min-height:44px;">
<svg viewBox="0 0 32 32" width="30" height="30" fill="none" style="filter: drop-shadow(0 0 10px rgba(29, 140, 248, 0.6)); flex-shrink: 0;">
<path d="M28 14.5C28 20.85 22.63 26 16 26C14.07 26 12.24 25.56 10.63 24.78L4 27L6.44 20.91C4.91 19.06 4 16.88 4 14.5C4 8.15 9.37 3 16 3C22.63 3 28 8.15 28 14.5Z" fill="#1D8CF8"/>
<circle cx="10.5" cy="14.5" r="1.8" fill="#FFFFFF"/>
<circle cx="16" cy="14.5" r="1.8" fill="#FFFFFF"/>
<circle cx="21.5" cy="14.5" r="1.8" fill="#FFFFFF"/>
</svg>
<span class="brand-title-text" style="font-size: 1.35rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.01em;">SocialSpark</span>
</div>"""
        )
    with top_c2:
        render_html_block(
            """<div style="display:flex; justify-content:center; align-items:center; height:100%; min-height:44px; gap:2.2rem;">
<a href="#about" class="nav-link">About</a>
<a href="#how-it-works" class="nav-link">How It Works</a>
<a href="#features" class="nav-link">Features</a>
<a href="#why-us" class="nav-link">Why Us</a>
</div>"""
        )
    with top_c3:
        if st.button("Get Started →", key="nav_get_started", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

    # 2. HERO SECTION & FLOATING ANIMATED SOCIAL ICONS WITH CURVED LIGHT BEAMS
    render_html_block(
        """<div class="hero-wrapper">
<div class="hero-light-arc-left"></div>
<div class="hero-light-arc-right"></div>
<div class="hero-orb orb-instagram" title="Instagram">
<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
<circle cx="17.5" cy="6.5" r="1.5" fill="#FFFFFF"></circle>
</svg>
</div>
<div class="hero-orb orb-linkedin" title="LinkedIn">
<svg viewBox="0 0 24 24" width="26" height="26" fill="#FFFFFF">
<path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.45 1.45 0 1 0 0-2.9 1.45 1.45 0 0 0 0 2.9m1.4 9.74v-8.37H5.06v8.37h2.8z"/>
</svg>
</div>
<div class="hero-orb orb-x" title="X">
<svg viewBox="0 0 24 24" width="25" height="25" fill="#FFFFFF">
<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
</svg>
</div>
<div class="hero-orb orb-youtube" title="YouTube">
<svg viewBox="0 0 24 24" width="28" height="28" fill="none">
<rect x="2" y="4" width="20" height="16" rx="4" fill="#FF0000"/>
<path d="M10 8.5L15.5 12L10 15.5V8.5Z" fill="#FFFFFF"/>
</svg>
</div>
<div class="hero-badge">
<span class="hero-badge-spark">✨</span>
<span>AI-Powered Social Media Agent</span>
<span class="hero-badge-spark">✨</span>
</div>
<h1 class="hero-title"><span class="title-white">Social</span><span class="title-spark">Spark</span></h1>
<p class="hero-subtitle">Smarter Engagement. Stronger Connections.</p>
<p class="hero-intro">
Understand what your audience loves, create better content,<br>and grow your social media presence with AI.
</p>
</div>"""
    )

    # Hero Action Buttons
    h_col1, h_col2, h_col3 = st.columns([1, 1.2, 1])
    with h_col2:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("Get Started →", key="hero_get_started", type="primary", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
        with btn_c2:
            render_html_block(
                '<a href="#features" class="hero-explore-btn">🔥 Explore Features</a>'
            )

    # Hero Showcase Card (from reference photo)
    render_html_block(
        """<div class="hero-showcase-wrapper">
<div class="hero-showcase-card">
<div class="showcase-card-pill">
<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"></circle>
<line x1="2" y1="12" x2="22" y2="12"></line>
<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
</svg>
<span>THE COGNITIVE AI ENGAGEMENT PLATFORM</span>
</div>
<h2 class="showcase-card-title"><span class="title-white">Social</span><span class="title-spark">Spark</span></h2>
<p class="showcase-card-subtitle">Smarter Engagement. Stronger Connections.</p>
</div>
</div>"""
    )

    # 3. ABOUT THE WEBSITE SECTION
    render_html_block(
        """<div id="about" class="landing-section">
<span class="section-badge">About The Website</span>
<h2 class="section-title">What is Social Media Engagement Agent?</h2>
<p class="section-lead">
Our AI-powered Social Media Engagement Agent helps businesses and content creators understand their audience, respond intelligently, and build stronger online relationships.<br><br>
It combines AI-powered emotion detection, brand voice memory, intelligent conversation prioritization, and response safety checking to make social media engagement more personalized and efficient.
</p>
<div class="about-grid">
<div class="about-card">
<div class="about-icon-box pink">🎭</div>
<h3>Cognitive Emotion Detection</h3>
<p>Decodes underlying sentiment, frustration, urgency, or appreciation in comments before formulating a reply.</p>
</div>
<div class="about-card">
<div class="about-icon-box purple">🧠</div>
<h3>Brand Voice Memory</h3>
<p>Powered by Hindsight vector memory to retain manager corrections, style preferences, and past winning posts.</p>
</div>
<div class="about-card">
<div class="about-icon-box blue">🛡️</div>
<h3>Safety & Prioritization</h3>
<p>Filters out hallucinated brand claims, ensures compliance, and highlights high-urgency customer threads.</p>
</div>
</div>
</div>"""
    )

    # 4. HOW IT WORKS SECTION
    render_html_block(
        """<div id="how-it-works" class="landing-section">
<span class="section-badge">Workflow Architecture</span>
<h2 class="section-title">How It Works</h2>
<p class="section-subtitle">A seamless 6-step loop from incoming comment to long-term memory refinement</p>
<div class="timeline-grid">
<div class="timeline-card">
<span class="timeline-step-badge">Step 01</span>
<div class="timeline-icon">💬</div>
<h4>Enter Social Media Comments</h4>
<p>Input customer queries, mentions, or creative post ideas from Instagram, LinkedIn, Facebook, X, or Reddit.</p>
</div>
<div class="timeline-card">
<span class="timeline-step-badge">Step 02</span>
<div class="timeline-icon">🔍</div>
<h4>AI Understands Emotion & Intent</h4>
<p>The agent detects mood, urgency, sarcasm, and inquiry intent to adapt response tone precisely.</p>
</div>
<div class="timeline-card">
<span class="timeline-step-badge">Step 03</span>
<div class="timeline-icon">🧠</div>
<h4>Retrieve Your Brand Voice</h4>
<p>Queries stored long-term memory for relevant past interactions and manager style guidelines.</p>
</div>
<div class="timeline-card">
<span class="timeline-step-badge">Step 04</span>
<div class="timeline-icon">⚡</div>
<h4>Generate Personalized Responses</h4>
<p>Groq ultra-fast LLM crafts human-like, platform-adapted copy tailored to the exact user context.</p>
</div>
<div class="timeline-card">
<span class="timeline-step-badge">Step 05</span>
<div class="timeline-icon">🛡️</div>
<h4>Check Response Safety</h4>
<p>Multi-layer guardrails check for compliance, remove unrequested brand bias, and eliminate hallucinations.</p>
</div>
<div class="timeline-card">
<span class="timeline-step-badge">Step 06</span>
<div class="timeline-icon">📈</div>
<h4>Save Feedback & Improve Future Suggestions</h4>
<p>Manager approvals and edits are retained to memory, refining every future draft automatically.</p>
</div>
</div>
</div>"""
    )

    # 5. UNIQUE FEATURES SECTION
    render_html_block(
        """<div id="features" class="landing-section">
<span class="section-badge">Core Capabilities</span>
<h2 class="section-title">Unique Features</h2>
<p class="section-subtitle">Engineered specifically to transform casual followers into lifelong loyal brand advocates</p>
<div class="features-grid">
<div class="feature-card">
<div class="feature-icon-wrapper">🧠</div>
<div>
<h3>Brand Voice Memory</h3>
<p>Learns the brand's communication style and remembers preferences across every campaign and platform.</p>
</div>
<span class="feature-tag">Adaptive Memory</span>
</div>
<div class="feature-card">
<div class="feature-icon-wrapper">🎭</div>
<div>
<h3>Emotion-Aware Reply Generator</h3>
<p>Understands audience emotions and generates contextual responses that build genuine connection.</p>
</div>
<span class="feature-tag">Sentiment Intelligence</span>
</div>
<div class="feature-card">
<div class="feature-icon-wrapper">⚡</div>
<div>
<h3>Smart Engagement Priority</h3>
<p>Identifies important conversations that need attention first, turning escalations into loyalty.</p>
</div>
<span class="feature-tag">Automated Triage</span>
</div>
<div class="feature-card">
<div class="feature-icon-wrapper">🛡️</div>
<div>
<h3>AI Reply Safety Checker</h3>
<p>Reviews responses for inappropriate language, privacy concerns, and unsupported promises.</p>
</div>
<span class="feature-tag">Enterprise Guardrails</span>
</div>
<div class="feature-card">
<div class="feature-icon-wrapper">🔄</div>
<div>
<h3>Engagement Learning Loop</h3>
<p>Uses user feedback to personalize future response suggestions, evolving with your team daily.</p>
</div>
<span class="feature-tag">Active Reinforcement</span>
</div>
<div class="feature-card">
<div class="feature-icon-wrapper">🌐</div>
<div>
<h3>Multi-Platform Support</h3>
<p>Adapts response styles for Instagram, LinkedIn, Facebook, X, and Reddit with native platform nuances.</p>
</div>
<span class="feature-tag">Omnichannel Native</span>
</div>
</div>
</div>"""
    )

    # 6. WHY CHOOSE OUR AGENT SECTION
    render_html_block(
        """<div id="why-us" class="landing-section">
<span class="section-badge">The Advantage</span>
<h2 class="section-title">Why Choose Our Agent</h2>
<p class="section-subtitle">Move beyond generic LLM copywriters with true cognitive, memory-backed social intelligence</p>
<div class="why-grid">
<div class="why-card">
<div class="why-number">01</div>
<h3>Personalized AI responses</h3>
<p>Every response is context-rich and tuned to individual commenters, replacing generic robotic templates with memorable human warmth.</p>
</div>
<div class="why-card">
<div class="why-number">02</div>
<h3>Better audience understanding</h3>
<p>Synthesizes weeks of interaction patterns and comments into actionable reflection reports showing what content drives real engagement.</p>
</div>
<div class="why-card">
<div class="why-number">03</div>
<h3>Efficient conversation management</h3>
<p>Respond to customer inquiries, mentions, and community debates in seconds rather than spending hours manually drafting replies.</p>
</div>
<div class="why-card">
<div class="why-number">04</div>
<h3>Continuous preference-based improvement</h3>
<p>Human-in-the-loop active memory retains every edit and approval you make, so the agent writes more like your team every single day.</p>
</div>
</div>
</div>"""
    )

    # 7. CALL-TO-ACTION (CTA) SECTION
    render_html_block(
        """<div class="cta-container">
<h2 class="cta-title">Make Every Social Interaction Smarter.</h2>
<p class="cta-subtitle">Start building meaningful conversations with the power of AI.</p>
</div>"""
    )
    cta_c1, cta_c2, cta_c3 = st.columns([1, 1.2, 1])
    with cta_c2:
        if st.button("🚀 Get Started Now", key="bottom_cta_get_started", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

    # 8. FOOTER
    render_html_block(
        """<footer class="landing-footer">
<div class="footer-content">
<div class="footer-left">
<div class="footer-brand">
<span>✨</span>
<span>SocialSpark</span>
</div>
<p class="footer-desc">
Your AI-powered partner for smarter, personalized, and meaningful social media engagement across modern networks.
</p>
</div>
<div class="footer-tags">
<span class="platform-pill">Instagram</span>
<span class="platform-pill">LinkedIn</span>
<span class="platform-pill">Facebook</span>
<span class="platform-pill">X</span>
<span class="platform-pill">Reddit</span>
<span class="platform-pill">YouTube</span>
</div>
</div>
<div class="footer-bottom">
<span>© 2026 SocialSpark · Social Media Engagement Agent. All rights reserved.</span>
<span>Smarter Engagement. Stronger Connections.</span>
</div>
</footer>"""
    )
    st.stop()


# -----------------------------------------------------------------------------
# VIEW 2: SIGNUP / AUTHENTICATION PAGE
# -----------------------------------------------------------------------------
if st.session_state.page == "signup":
    # Hide sidebar strictly on the signup page
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 580px !important;
            margin: 3.5rem auto 5rem !important;
            padding: 1rem 1.5rem !important;
        }
        .signup-header-box {
            text-align: center;
            margin-bottom: 2rem;
        }
        .signup-brand-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 1.1rem;
        }
        .signup-brand-logo {
            filter: drop-shadow(0 0 12px rgba(29, 140, 248, 0.7));
            flex-shrink: 0;
        }
        .signup-brand-text {
            font-size: 1.65rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        .signup-header-box h1 {
            font-size: 2.15rem;
            font-weight: 800;
            margin-bottom: 0.6rem;
            color: #FFFFFF;
            letter-spacing: -0.02em;
        }
        .signup-header-box p {
            color: #94A3B8;
            font-size: 1rem;
            line-height: 1.55;
            margin: 0;
        }
        /* Cyber-glass Form Container */
        div[data-testid="stForm"] {
            background: rgba(14, 23, 50, 0.72) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(59, 130, 246, 0.3) !important;
            border-radius: 18px !important;
            padding: 2.2rem 2rem 2.4rem !important;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), 0 0 25px rgba(59, 130, 246, 0.15) !important;
        }
        div[data-testid="stForm"] div.stButton > button[kind="primary"],
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button {
            background: #1D8CF8 !important;
            border: none !important;
            color: #FFFFFF !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            padding: 0.75rem 1.5rem !important;
            box-shadow: 0 4px 16px rgba(29, 140, 248, 0.45) !important;
            margin-top: 1rem !important;
            transition: all 0.22s ease !important;
        }
        div[data-testid="stForm"] div.stButton > button[kind="primary"]:hover,
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button:hover {
            background: #1577D6 !important;
            box-shadow: 0 6px 22px rgba(29, 140, 248, 0.65) !important;
            transform: translateY(-1px) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="signup-header-box">
            <div class="signup-brand-row">
                <svg viewBox="0 0 32 32" width="32" height="32" fill="none" class="signup-brand-logo">
                    <path d="M28 14.5C28 20.85 22.63 26 16 26C14.07 26 12.24 25.56 10.63 24.78L4 27L6.44 20.91C4.91 19.06 4 16.88 4 14.5C4 8.15 9.37 3 16 3C22.63 3 28 8.15 28 14.5Z" fill="#1D8CF8"/>
                    <circle cx="10.5" cy="14.5" r="1.8" fill="#FFFFFF"/>
                    <circle cx="16" cy="14.5" r="1.8" fill="#FFFFFF"/>
                    <circle cx="21.5" cy="14.5" r="1.8" fill="#FFFFFF"/>
                </svg>
                <div class="signup-brand-text">
                    <span style="color: #FFFFFF;">Social</span><span style="background: linear-gradient(135deg, #A855F7 0%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Spark</span>
                </div>
            </div>
            <h1>Your next post starts here.</h1>
            <p>Set up your profile to start automating and optimizing your social media engagement.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("signup_form"):
        name = st.text_input("Your name", placeholder="Alex Morgan")
        email = st.text_input("Work email", placeholder="alex@yourbrand.com")
        password = st.text_input("Password", type="password", help="Use at least 8 characters.")
        submitted = st.form_submit_button("Create account →", type="primary", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Enter your name to continue.")
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
            st.error("Enter a valid email address.")
        elif len(password) < 8:
            st.error("Your password must be at least 8 characters.")
        else:
            st.session_state.profile = {"name": name.strip(), "email": email.strip()}
            st.session_state.page = "dashboard"
            st.rerun()

    st.write("")
    if st.button("← Back to Home", use_container_width=True):
        st.session_state.page = "landing"
        st.rerun()

    st.stop()


# -----------------------------------------------------------------------------
# VIEW 3: INTERNAL DASHBOARD WORKSPACE (WITH LEFT-SIDE VERTICAL SIDEBAR)
# -----------------------------------------------------------------------------

# Ensure sidebar and main block container are explicitly restored on dashboard view
st.markdown(
    """
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"] {
        display: block !important;
        visibility: visible !important;
    }
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        margin: 0 !important;
        padding: 2rem 3rem 4rem 3rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Ensure default profile matching user's account in screenshot
if "profile" not in st.session_state or not st.session_state.profile:
    st.session_state.profile = {
        "name": "harshitha",
        "email": "harshu123@gmail.com",
    }
user_name = st.session_state.profile.get("name", "harshitha")
user_email = st.session_state.profile.get("email", "harshu123@gmail.com")

try:
    saved_brand = get_brand_profile(user_email)
except Exception:
    saved_brand = getattr(agent, "get_brand_profile", lambda e: None)(user_email)
brand_configured = bool(saved_brand and saved_brand.get("brand_name"))

NAV_POST = "✏️  Create a Post"
NAV_REPLIES = "😊  Emotion-Aware Replies"
NAV_LEARNED = "🧠  What the Agent Learned"
NAV_BRAND = "🎨  Brand Voice Memory"

MODULE_OPTIONS = [
    NAV_POST,
    NAV_REPLIES,
    NAV_LEARNED,
    NAV_BRAND,
]

# Map legacy radio selection if present
legacy_map = {
    "🏠  Home": NAV_BRAND,
    "Home": NAV_BRAND,
    "🎨 Brand Voice Memory": NAV_BRAND,
    "🎨  Brand Voice Memory": NAV_BRAND,
    "✍️ Draft a Post": NAV_POST,
    "✏️  Create a Post": NAV_POST,
    "🎭 Emotion-Aware Replies": NAV_REPLIES,
    "😊  Emotion-Aware Replies": NAV_REPLIES,
    "💬 Reply to a Comment": NAV_REPLIES,
    "🧠 What the Agent Learned": NAV_LEARNED,
    "🧠  What the Agent Learned": NAV_LEARNED,
}
if st.session_state.get("dash_sidebar_radio") in legacy_map:
    st.session_state["dash_sidebar_radio"] = legacy_map[st.session_state["dash_sidebar_radio"]]

if "dash_sidebar_radio" not in st.session_state or st.session_state["dash_sidebar_radio"] not in MODULE_OPTIONS:
    st.session_state["dash_sidebar_radio"] = NAV_POST

# Internal Left-Side Vertical Sidebar Navigation matching picture
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-box">
            <div class="sidebar-brand-header">
                <svg viewBox="0 0 32 32" width="28" height="28" fill="none" class="sidebar-brand-logo">
                    <path d="M28 14.5C28 20.85 22.63 26 16 26C14.07 26 12.24 25.56 10.63 24.78L4 27L6.44 20.91C4.91 19.06 4 16.88 4 14.5C4 8.15 9.37 3 16 3C22.63 3 28 8.15 28 14.5Z" fill="url(#brandLogoGrad)"/>
                    <circle cx="10.5" cy="14.5" r="1.8" fill="#FFFFFF"/>
                    <circle cx="16" cy="14.5" r="1.8" fill="#FFFFFF"/>
                    <circle cx="21.5" cy="14.5" r="1.8" fill="#FFFFFF"/>
                    <defs>
                        <linearGradient id="brandLogoGrad" x1="4" y1="3" x2="28" y2="27" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#38BDF8"/>
                            <stop offset="0.5" stop-color="#818CF8"/>
                            <stop offset="1" stop-color="#EC4899"/>
                        </linearGradient>
                    </defs>
                </svg>
                <div class="sidebar-brand-title">
                    <span class="brand-text-white">Social</span><span class="brand-text-agent-grad">Spark</span>
                </div>
            </div>
            <div class="sidebar-brand-sub">
                <span class="brand-platform-pill">AI Engagement Platform</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="sidebar-user-card">
            <div class="user-avatar-wrap">
                <div class="user-avatar">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="white">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                </div>
                <span class="avatar-online-dot"></span>
            </div>
            <div class="user-info">
                <div class="user-name">{user_name}</div>
                <div class="user-email">{user_email}</div>
            </div>
            <div class="user-status-pill">
                <span class="user-online-ping">●</span> Active
            </div>
        </div>
        <div class="sidebar-divider"></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-section-header">
            <div class="sidebar-nav-heading">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.35rem; display:inline-block; vertical-align:middle;">
                    <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                    <polyline points="2 17 12 22 22 17"></polyline>
                    <polyline points="2 12 12 17 22 12"></polyline>
                </svg>
                WORKSPACE MODULES
            </div>
            <span class="sidebar-section-badge">4 TABS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    MODULE_CAPTIONS = [
        "AI post composer & multi-platform studio",
        "Audience sentiment & empathy replies",
        "Hindsight cognitive graph & learnings",
        "Brand persona, tone & guidelines",
    ]
    try:
        dashboard_view = st.radio(
            "NAVIGATION",
            MODULE_OPTIONS,
            captions=MODULE_CAPTIONS,
            label_visibility="collapsed",
            key="dash_sidebar_radio",
        )
    except TypeError:
        dashboard_view = st.radio(
            "NAVIGATION",
            MODULE_OPTIONS,
            label_visibility="collapsed",
            key="dash_sidebar_radio",
        )

    # AI ENGINE STATUS Section with glowing dots & badge pills
    voice_dot = "dot-teal" if brand_configured else "dot-amber"
    voice_badge_cls = "status-badge-teal" if brand_configured else "status-badge-amber"
    voice_val = saved_brand['brand_name'] if brand_configured else "Not Configured"
    st.markdown(
        f"""
        <div class="sidebar-nav-heading" style="margin-top: 1.85rem; margin-bottom: 0.8rem;">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.35rem; display:inline-block; vertical-align:middle;">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 6v6l4 2"></path>
            </svg>
            AI SYSTEM DIAGNOSTICS
        </div>
        <div class="ai-status-container">
            <div class="status-row">
                <span class="status-dot {voice_dot}"></span>
                <span class="status-label">Brand Voice</span>
                <span class="status-badge {voice_badge_cls}">{voice_val}</span>
            </div>
            <div class="status-row">
                <span class="status-dot dot-purple"></span>
                <span class="status-label">Memory Engine</span>
                <span class="status-badge status-badge-purple">Hindsight DB</span>
            </div>
            <div class="status-row">
                <span class="status-dot dot-cyan"></span>
                <span class="status-label">Fast LLM</span>
                <span class="status-badge status-badge-cyan">Groq Turbo</span>
            </div>
            <div class="status-row">
                <span class="status-dot dot-pink"></span>
                <span class="status-label">Guardrails</span>
                <span class="status-badge status-badge-pink"><span class="badge-dot-pink">●</span> Active</span>
            </div>
        </div>
        <div class="sidebar-footer-box">
            <div class="sidebar-footer-info">
                <span class="footer-status-dot"></span>
                <span class="footer-status-text">Workspace Connected</span>
            </div>
            <span class="sidebar-footer-version">v2.4 Pro</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("↪  Sign out", use_container_width=True, key="sidebar_sign_out"):
        st.session_state.page = "landing"
        st.session_state.pop("profile", None)
        st.rerun()


def draft_ui(kind, generate, topic_value=None):
    """Side-by-side: no memory vs Hindsight memory, then feedback -> retained."""
    first, second = st.columns(2)
    plain_panel = first.empty()
    memory_panel = second.empty()

    def normalize_result(result):
        if isinstance(result, dict):
            return {
                "draft": result.get("draft") or "",
                "memory": result.get("memory") or "",
            }
        if isinstance(result, str):
            return {"draft": result, "memory": ""}
        if result is None:
            return {"draft": "", "memory": ""}
        return {"draft": str(result), "memory": ""}

    def show_result(panel, heading, result, use_memory=False):
        panel.empty()
        result = normalize_result(result)
        with panel.container():
            st.subheader(heading)
            draft = result["draft"]
            if not draft:
                draft = "[No draft generated]"
            if draft.startswith("["):
                st.error(draft)
            elif use_memory:
                st.success(draft)
            else:
                st.info(draft)
            if use_memory:
                with st.expander("Memories used"):
                    st.text(result["memory"] or "none")

    if st.button("⚡ Generate Post Drafts", key=f"gen_{kind}", type="primary", use_container_width=True):
        if kind == "post" and not (topic_value or "").strip():
            st.error("Enter a topic or subject first.")
        else:
            with plain_panel.container():
                st.subheader("Without memory")
                st.info("⚡ Generating baseline draft...")
            with memory_panel.container():
                st.subheader("With Hindsight memory")
                st.info("🧠 Applying brand voice & cognitive memory...")

            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2) as executor:
                fut_plain = executor.submit(generate, False)
                fut_mem = executor.submit(generate, True)

                try:
                    plain = normalize_result(fut_plain.result())
                except Exception as error:
                    plain = {"draft": f"[Generation error: {error}]", "memory": ""}
                show_result(plain_panel, "Without memory", plain)

                try:
                    memory_draft = normalize_result(fut_mem.result())
                except Exception as error:
                    memory_draft = {"draft": f"[Memory generation error: {error}]", "memory": ""}
                show_result(memory_panel, "With Hindsight memory", memory_draft, use_memory=True)

            st.session_state[kind] = {
                "plain": plain,
                "mem": memory_draft,
            }
            # Synchronize text area with newly generated draft
            st.session_state[f"edit_{kind}"] = memory_draft["draft"]

    output = st.session_state.get(kind)
    if not output:
        return
    output["plain"] = normalize_result(output.get("plain"))
    output["mem"] = normalize_result(output.get("mem"))
    if not st.session_state.get(f"gen_{kind}"):
        show_result(plain_panel, "Without memory", output["plain"])
        if output["mem"]["draft"]:
            show_result(memory_panel, "With Hindsight memory", output["mem"], use_memory=True)

    edited = st.text_area(
        "Edit the memory-powered draft (your edits teach the agent)",
        value=output["mem"]["draft"],
        key=f"edit_{kind}",
    )
    approve, reject = st.columns(2)
    if approve.button("✅ Approve", key=f"ok_{kind}", type="primary", use_container_width=True):
        changed = edited != output["mem"]["draft"]
        saved = agent.remember_feedback(
            kind,
            output["mem"]["draft"],
            "edited" if changed else "approved",
            edited if changed else None,
        )
        st.session_state[kind]["mem"]["draft"] = edited
        if saved is None:
            st.success("✅ Draft approved! Saved to current session (Hindsight memory offline).")
        else:
            st.success("✅ Draft approved and permanently saved to agent memory! The agent will remember your preferences.")
        st.toast("Saved to memory.")
    if reject.button("❌ Reject", key=f"no_{kind}", type="secondary", use_container_width=True):
        saved = agent.remember_feedback(kind, output["mem"]["draft"], "rejected", edited)
        if saved is None:
            st.info("❌ Draft rejected. Noted for future generations (Hindsight memory offline).")
        else:
            st.info("❌ Rejection feedback saved to memory. The agent will adapt next time.")
        st.toast("Rejection saved to memory.")


# -----------------------------------------------------------------------------
# WORKSPACE MODULE: BRAND VOICE MEMORY STUDIO
# -----------------------------------------------------------------------------
if dashboard_view in [NAV_BRAND, "🎨 Brand Voice Memory", "🎨  Brand Voice Memory", "🏠  Home", "Home"]:
    st.markdown(
        """
        <div class="workspace-main-header">
            <h1 class="engagement-title">
                <span class="sparkle-cyan-lg">✦</span>
                <span class="text-white">Brand Voice </span><span class="text-engagement-grad">Memory</span>
            </h1>
            <p class="engagement-desc">Train and refine how your AI agent captures, retains, and communicates your brand identity.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_email = st.session_state.get("profile", {}).get("email", "default")
    try:
        current_brand = get_brand_profile(user_email) or {}
    except Exception:
        current_brand = getattr(agent, "get_brand_profile", lambda e: {})(user_email) or {}
    has_saved_brand = bool(current_brand.get("brand_name"))

    st.markdown(
        """
        <div class="module-header-row">
            <div class="module-header-icon icon-pink">
                <span>🎨</span>
            </div>
            <div class="module-header-text">
                <h3>Brand Voice Memory</h3>
                <p>Train the AI to understand how your brand communicates.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="module-header-row" style="margin-top: 1.8rem;">
            <div class="module-header-icon icon-purple">
                <span>📝</span>
            </div>
            <div class="module-header-text">
                <h3>Brand Profile & Linguistic Style</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("brand_voice_input_form"):
        brand_name = st.text_input(
            "Brand Name *",
            value=current_brand.get("brand_name", ""),
            placeholder="e.g. Brewline, Lumina Tech, Aura Studios",
        )

        industry_options = [
            "Tech & SaaS", "E-commerce & Retail", "Food & Beverage",
            "Health & Wellness", "Fashion & Apparel", "Finance & Fintech",
            "Creative & Media", "Education & Coaching", "Other"
        ]
        cur_ind = current_brand.get("industry", "Tech & SaaS")
        ind_idx = industry_options.index(cur_ind) if cur_ind in industry_options else 0
        industry = st.selectbox("Industry / Category", industry_options, index=ind_idx)

        tone_options = [
            "Warm, witty, and approachable",
            "Bold, visionary, and high-energy",
            "Professional, insightful, and authoritative",
            "Playful, humorous, and relatable",
            "Empathetic, supportive, and community-first",
            "Concise, direct, and action-oriented"
        ]
        cur_tone = current_brand.get("preferred_tone", "Warm, witty, and approachable")
        tone_idx = tone_options.index(cur_tone) if cur_tone in tone_options else 0
        preferred_tone = st.selectbox("Preferred Communication Tone", tone_options, index=tone_idx)

        st.markdown(
            """
            <div class="module-header-row" style="margin-top: 1.8rem; margin-bottom: 0.5rem;">
                <div class="module-header-icon icon-blue">
                    <span>🌄</span>
                </div>
                <div class="module-header-text">
                    <h3>Sample Writing & Historical Posts</h3>
                    <p>Previous Social Media Posts (3–10 past posts preferred)</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        previous_posts = st.text_area(
            "Previous Social Media Posts (3–10 past posts preferred)",
            value=current_brand.get("previous_posts", ""),
            placeholder="Paste your past posts, captions, or content samples here...",
            height=125,
            label_visibility="collapsed",
        )

        with st.expander("➕ Additional Sample Content or Document Attachment (Optional)"):
            brand_desc = st.text_area(
                "Brand Description / Target Audience",
                value=current_brand.get("brand_description", ""),
                placeholder="Describe what your brand does, target audience, and core values...",
                height=90,
            )
            uploaded_file = st.file_uploader(
                "Upload Sample Content File (.txt, .md, .csv)",
                type=["txt", "md", "csv"],
            )
            extra_sample = st.text_area(
                "Extra writing samples or manifesto",
                value=current_brand.get("sample_content", ""),
                placeholder="Additional notes...",
                height=80,
            )

        uploaded_file_text = ""
        if 'uploaded_file' in locals() and uploaded_file is not None:
            try:
                uploaded_file_text = uploaded_file.read().decode("utf-8", errors="ignore")
                st.caption(f"📄 Attached file: **{uploaded_file.name}**")
            except Exception as err:
                st.warning(f"Could not read uploaded file: {err}")

        # Exact button from screenshot: ✦ Generate
        generate_clicked = st.form_submit_button("✦  Generate", type="primary")

    # Combine samples
    user_desc = brand_desc.strip() if 'brand_desc' in locals() and brand_desc else ""
    if not user_desc:
        user_desc = f"{brand_name} operates in {industry} with a {preferred_tone} voice."

    combined_sample_content = extra_sample.strip() if 'extra_sample' in locals() and extra_sample else ""
    if uploaded_file_text.strip():
        if combined_sample_content:
            combined_sample_content = f"{combined_sample_content}\n\n[Uploaded Document Content]:\n{uploaded_file_text.strip()}"
        else:
            combined_sample_content = uploaded_file_text.strip()

    if generate_clicked:
        if not brand_name.strip():
            st.error("Please provide a Brand Name.")
        else:
            with st.spinner("Analyzing linguistic patterns, vocabulary, tone, and brand persona using AI..."):
                analysis = agent.analyze_brand_voice(
                    brand_name=brand_name,
                    brand_description=user_desc,
                    industry=industry,
                    preferred_tone=preferred_tone,
                    previous_posts=previous_posts,
                    sample_content=combined_sample_content,
                )

            if "error" in analysis:
                st.error(f"⚠️ AI Analysis could not complete: {analysis['error']}")
                st.info("💡 Storing baseline brand profile to SQLite so you can proceed.")
                payload = {
                    "brand_name": brand_name,
                    "brand_description": user_desc,
                    "industry": industry,
                    "preferred_tone": preferred_tone,
                    "previous_posts": previous_posts,
                    "sample_content": combined_sample_content,
                    "personality": f"{preferred_tone}, Engaging, Authentic",
                    "vocabulary": "Community-focused, value-driven, conversational",
                    "sentence_structure": "Punchy hooks, clear body, concise call-to-action",
                    "communication_tone": preferred_tone,
                    "preferred_expressions": "Friendly openings, actionable questions",
                    "voice_summary": f"Speak authentically representing {brand_name} with a {preferred_tone} tone.",
                }
                try:
                    save_brand_profile(payload, user_email)
                except Exception:
                    getattr(agent, "save_brand_profile", lambda p, e: True)(payload, user_email)
                st.toast("Brand preferences saved to SQLite!")
                st.rerun()
            else:
                payload = {
                    "brand_name": brand_name,
                    "brand_description": user_desc,
                    "industry": industry,
                    "preferred_tone": preferred_tone,
                    "previous_posts": previous_posts,
                    "sample_content": combined_sample_content,
                    "personality": analysis.get("personality", ""),
                    "vocabulary": analysis.get("vocabulary", ""),
                    "sentence_structure": analysis.get("sentence_structure", ""),
                    "communication_tone": analysis.get("communication_tone", ""),
                    "preferred_expressions": analysis.get("preferred_expressions", ""),
                    "voice_summary": analysis.get("voice_summary", ""),
                }
                try:
                    save_brand_profile(payload, user_email)
                except Exception:
                    getattr(agent, "save_brand_profile", lambda p, e: True)(payload, user_email)
                st.session_state.pop(f"brand_profile_{user_email}", None)
                st.toast("Brand Voice analyzed and permanently saved to SQLite!")
                st.rerun()

    # Display Analyzed Brand Voice Cards below if profile is saved
    if has_saved_brand:
        st.write("")
        st.markdown("<hr style='border-color: rgba(255, 255, 255, 0.08); margin: 2.2rem 0 1.5rem;'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Analyzed Brand Voice Intelligence")

        c_card1, c_card2 = st.columns(2)
        with c_card1:
            st.markdown(
                f"""
                <div style="background: #0A1226; border: 1px solid rgba(59, 130, 246, 0.28); border-radius: 16px; padding: 1.5rem; height: 100%; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);">
                    <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.85rem;">
                        <span style="font-size: 1.4rem;">🎭</span>
                        <h4 style="margin: 0; color: #FFFFFF; font-size: 1.15rem; font-weight: 700;">Brand Personality</h4>
                    </div>
                    <p style="color: #CBD5E1; line-height: 1.65; font-size: 0.98rem; margin: 0;">
                        {current_brand.get('personality', 'Not analyzed yet')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_card2:
            st.markdown(
                f"""
                <div style="background: #0A1226; border: 1px solid rgba(59, 130, 246, 0.28); border-radius: 16px; padding: 1.5rem; height: 100%; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);">
                    <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.85rem;">
                        <span style="font-size: 1.4rem;">🎯</span>
                        <h4 style="margin: 0; color: #FFFFFF; font-size: 1.15rem; font-weight: 700;">Communication Tone</h4>
                    </div>
                    <p style="color: #CBD5E1; line-height: 1.65; font-size: 0.98rem; margin: 0;">
                        {current_brand.get('communication_tone', current_brand.get('preferred_tone', 'Not analyzed yet'))}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        c_card3, c_card4 = st.columns(2)
        with c_card3:
            st.markdown(
                f"""
                <div style="background: #0A1226; border: 1px solid rgba(59, 130, 246, 0.28); border-radius: 16px; padding: 1.5rem; height: 100%; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);">
                    <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.85rem;">
                        <span style="font-size: 1.4rem;">📚</span>
                        <h4 style="margin: 0; color: #FFFFFF; font-size: 1.15rem; font-weight: 700;">Signature Vocabulary</h4>
                    </div>
                    <p style="color: #CBD5E1; line-height: 1.65; font-size: 0.98rem; margin: 0;">
                        {current_brand.get('vocabulary', 'Not analyzed yet')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_card4:
            st.markdown(
                f"""
                <div style="background: #0A1226; border: 1px solid rgba(59, 130, 246, 0.28); border-radius: 16px; padding: 1.5rem; height: 100%; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);">
                    <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.85rem;">
                        <span style="font-size: 1.4rem;">💡</span>
                        <h4 style="margin: 0; color: #FFFFFF; font-size: 1.15rem; font-weight: 700;">Preferred Expressions</h4>
                    </div>
                    <p style="color: #CBD5E1; line-height: 1.65; font-size: 0.98rem; margin: 0;">
                        {current_brand.get('preferred_expressions', 'Not analyzed yet')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown(
            f"""
            <div style="background: radial-gradient(circle at 50% 20%, rgba(30, 58, 138, 0.35) 0%, #0E1528 100%); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 16px; padding: 1.6rem;">
                <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.85rem;">
                    <span style="font-size: 1.4rem;">🧠</span>
                    <h4 style="margin: 0; color: #FFFFFF; font-size: 1.15rem;">Cognitive Brand Voice Directive</h4>
                </div>
                <p style="color: #E2E8F0; line-height: 1.7; font-size: 0.98rem; margin: 0;">
                    {current_brand.get('voice_summary', 'No summary generated yet.')}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        col_res1, col_res2 = st.columns([1.5, 4])
        with col_res1:
            if st.button("🔄 Reset Profile", type="secondary", use_container_width=True, key="btn_reset_home_prof"):
                st.session_state.pop(f"brand_profile_{user_email}", None)
                try:
                    reset_brand_profile(user_email)
                except Exception:
                    getattr(agent, "reset_brand_profile", lambda e: True)(user_email)
                st.toast("Brand Voice profile reset from SQLite.")
                st.rerun()


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# WORKSPACE MODULE 2: CREATE A POST
# -----------------------------------------------------------------------------
elif dashboard_view in [NAV_POST, "✍️ Draft a Post"]:
    st.markdown(
        """
        <div class="workspace-main-header">
            <h1 class="engagement-title">
                <span class="sparkle-cyan-lg">✦</span>
                <span class="text-white">Create a </span><span class="text-engagement-grad">Post</span>
            </h1>
            <p class="engagement-desc">Draft high-converting social media posts adapted to your brand voice and cognitive memory.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    user_email = st.session_state.get("profile", {}).get("email", "default")
    if f"brand_profile_{user_email}" not in st.session_state:
        st.session_state[f"brand_profile_{user_email}"] = agent.get_brand_profile(user_email)
    active_brand = st.session_state[f"brand_profile_{user_email}"]

    if active_brand and active_brand.get("brand_name"):
        st.info(f"✨ **Active Brand Voice:** `{active_brand['brand_name']}` ({active_brand.get('industry', 'General')}) · **Tone:** {active_brand.get('communication_tone', active_brand.get('preferred_tone', ''))}")
    else:
        st.caption("💡 _Tip: Configure your Brand Voice Memory under Home to generate posts tailored to your exact brand identity._")

    # Quick topic presets for instant testing
    st.markdown('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.4rem; font-weight: 600;">⚡ Quick Topic Ideas:</div>', unsafe_allow_html=True)
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    if p_col1.button("🚀 New Product Launch", use_container_width=True, key="preset_post_launch"):
        st.session_state.post_topic = "Launching our new summer clothing line with sustainable fabrics"
        st.session_state.post_platform = "Instagram"
        st.rerun()
    if p_col2.button("🎉 Weekend Flash Sale", use_container_width=True, key="preset_post_sale"):
        st.session_state.post_topic = "Limited 48-hour flash sale: 30% off all bestsellers this weekend"
        st.session_state.post_platform = "Instagram"
        st.rerun()
    if p_col3.button("💡 Behind The Scenes", use_container_width=True, key="preset_post_bts"):
        st.session_state.post_topic = "Behind the scenes: How our design team crafts each product from scratch"
        st.session_state.post_platform = "LinkedIn"
        st.rerun()
    if p_col4.button("📈 Industry Growth Tips", use_container_width=True, key="preset_post_tips"):
        st.session_state.post_topic = "5 lessons we learned scaling our brand from 0 to 10k customers"
        st.session_state.post_platform = "Twitter"
        st.rerun()

    st.write("")

    if "post_topic" not in st.session_state:
        st.session_state.post_topic = "Launching our new clothing store"

    c_plat, c_top = st.columns([1, 3])
    with c_plat:
        platforms = ["Instagram", "Twitter", "LinkedIn"]
        cur_plat = st.session_state.get("post_platform", "Instagram")
        plat_idx = platforms.index(cur_plat) if cur_plat in platforms else 0
        post_platform = st.selectbox("Platform", platforms, index=plat_idx, key="post_platform")
    with c_top:
        post_topic = st.text_input(
            "Topic / Angle",
            placeholder="Enter any topic or angle...",
            value=st.session_state.post_topic,
            help="Enter any topic, idea, event, product, or subject you want to write about.",
            key="post_topic",
        )

    draft_ui(
        "post",
        lambda use_memory: agent.draft_post(post_platform, post_topic, use_memory, user_email=user_email),
        post_topic,
    )


# -----------------------------------------------------------------------------
# WORKSPACE MODULE 3: EMOTION-AWARE REPLY GENERATOR
# -----------------------------------------------------------------------------
elif dashboard_view in [NAV_REPLIES, "🎭 Emotion-Aware Replies", "💬 Reply to a Comment", "🎭 Emotion-Aware Reply Generator"]:
    st.markdown(
        """
        <div class="workspace-main-header">
            <h1 class="engagement-title">
                <span class="sparkle-cyan-lg">✦</span>
                <span class="text-white">Emotion-Aware </span><span class="text-engagement-grad">Replies</span>
            </h1>
            <p class="engagement-desc">Understand audience emotions, sentiment, and intent before generating tailored responses across platforms.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_email = st.session_state.get("profile", {}).get("email", "default")
    active_brand = agent.get_brand_profile(user_email)

    # Active Brand Voice Notice
    if active_brand and active_brand.get("brand_name"):
        st.markdown(
            f"""
            <div style="background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 0.85rem 1.2rem; margin-bottom: 1.2rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.6rem;">
                <div>
                    <span style="font-weight: 700; color: #FFFFFF;">✨ Active Brand Voice:</span>
                    <span style="color: #A78BFA; font-weight: 600;">{active_brand['brand_name']}</span>
                    <span style="color: #94A3B8; font-size: 0.88rem;">({active_brand.get('industry', 'General')})</span>
                </div>
                <div style="color: #94A3B8; font-size: 0.85rem;">
                    <strong>Tone:</strong> {active_brand.get('communication_tone') or active_brand.get('preferred_tone', 'Warm & engaging')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("💡 _Tip: Configure your Brand Voice Memory in the sidebar to have all three responses automatically embody your authentic brand style._")

    # Quick test sample presets
    st.markdown('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.4rem; font-weight: 600;">⚡ Quick Test Samples:</div>', unsafe_allow_html=True)
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    if q_col1.button("😤 Late Order Delivery", use_container_width=True, key="preset_late"):
        st.session_state.ea_comment = "Ordered again and it's late AGAIN. Seriously frustrated with this service!"
        st.session_state.ea_platform = "Instagram"
        st.session_state.ea_commenter = "@alex_k"
        st.session_state.pop("ea_result", None)
        st.session_state.pop("ea_analysis", None)
        st.rerun()
    if q_col2.button("😍 Product Praise", use_container_width=True, key="preset_praise"):
        st.session_state.ea_comment = "Just received my package today and honestly blown away by the quality! You gained a customer for life."
        st.session_state.ea_platform = "X"
        st.session_state.ea_commenter = "@creator_sam"
        st.session_state.pop("ea_result", None)
        st.session_state.pop("ea_analysis", None)
        st.rerun()
    if q_col3.button("🤔 Pricing Question", use_container_width=True, key="preset_price"):
        st.session_state.ea_comment = "Looks interesting, but is this suitable for small bootstrap teams or is the pricing geared only toward enterprise?"
        st.session_state.ea_platform = "LinkedIn"
        st.session_state.ea_commenter = "Marcus Vance"
        st.session_state.pop("ea_result", None)
        st.session_state.pop("ea_analysis", None)
        st.rerun()
    if q_col4.button("💡 Feature Request", use_container_width=True, key="preset_feature"):
        st.session_state.ea_comment = "Any plans to add multi-user workspace permissions and export to CSV? Would make this a 10/10 for our agency."
        st.session_state.ea_platform = "Reddit"
        st.session_state.ea_commenter = "u/dev_mark"
        st.session_state.pop("ea_result", None)
        st.session_state.pop("ea_analysis", None)
        st.rerun()

    st.write("")

    # Inputs Layout
    inp_c1, inp_c2 = st.columns([1.3, 2.7])
    with inp_c1:
        platforms = ["Instagram", "LinkedIn", "Facebook", "X", "Reddit"]
        cur_plat = st.session_state.get("ea_platform", "Instagram")
        plat_idx = platforms.index(cur_plat) if cur_plat in platforms else 0
        selected_platform = st.selectbox("Target Social Platform *", platforms, index=plat_idx, key="ea_platform_select")
        st.session_state.ea_platform = selected_platform

        commenter_handle = st.text_input(
            "Commenter Username / Handle (Optional)",
            value=st.session_state.get("ea_commenter", "@arjun_k"),
            placeholder="e.g. @sarah_m, u/techlead",
            key="ea_commenter_input",
        )
        st.session_state.ea_commenter = commenter_handle

    with inp_c2:
        comment_text = st.text_area(
            "Social Media Comment *",
            value=st.session_state.get("ea_comment", "Ordered again and it's late AGAIN. Seriously frustrated with this service!"),
            height=125,
            placeholder="Paste or type any social media comment, question, complaint, or review...",
            key="ea_comment_area",
        )
        st.session_state.ea_comment = comment_text

    # Action Toolbar
    act_col1, act_col2, act_col3, act_col4 = st.columns([1.4, 1.6, 1.2, 1.0])
    with act_col1:
        btn_analyze = st.button("🔍 Analyze Comment", key="btn_ea_analyze", use_container_width=True)
    with act_col2:
        btn_generate = st.button("⚡ Generate Replies", key="btn_ea_generate", type="primary", use_container_width=True)
    with act_col3:
        btn_regenerate = st.button("🔄 Regenerate", key="btn_ea_regen", use_container_width=True)
    with act_col4:
        btn_clear = st.button("🧹 Clear", key="btn_ea_clear", use_container_width=True)

    # Clear Action
    if btn_clear:
        st.session_state.ea_comment = ""
        st.session_state.ea_commenter = ""
        st.session_state.pop("ea_result", None)
        st.session_state.pop("ea_analysis", None)
        st.rerun()

    # Analyze Action
    if btn_analyze:
        if not comment_text.strip():
            st.error("Please enter a social media comment to analyze.")
        else:
            with st.spinner("Decoding emotion, sentiment, intention, and conversational requirement..."):
                analysis_data = agent.analyze_comment(comment_text, platform=selected_platform)
            if "error" in analysis_data:
                st.error(f"Analysis could not complete: {analysis_data['error']}")
            else:
                st.session_state.ea_analysis = analysis_data
                st.toast("Emotion & intent analysis complete!")

    # Generate or Regenerate Action
    if btn_generate or btn_regenerate:
        if not comment_text.strip():
            st.error("Please enter a social media comment to generate replies.")
        else:
            with st.spinner(f"Analyzing comment & crafting 3 platform-tailored responses for {selected_platform}..."):
                gen_data = agent.analyze_and_generate_replies(
                    comment=comment_text,
                    platform=selected_platform,
                    user_email=user_email,
                    commenter=commenter_handle,
                )
            if "error" in gen_data:
                st.error(f"Reply generation failed: {gen_data['error']}")
            else:
                st.session_state.ea_result = gen_data
                st.session_state.ea_analysis = gen_data
                st.toast(f"Generated 3 emotion-aware responses for {selected_platform}!")

    # Display Emotion & Sentiment Indicators
    analysis = st.session_state.get("ea_analysis")
    if analysis and not analysis.get("error"):
        st.write("")
        st.markdown("#### 🧠 Cognitive Emotion & Intent Intelligence")

        # Color and Emoji mappings
        emotion_val = analysis.get("emotion", "Neutral")
        sentiment_val = analysis.get("sentiment", "Neutral")

        # Sentiment styling
        sent_color = "#34D399" if "positive" in sentiment_val.lower() else ("#F87171" if "negative" in sentiment_val.lower() else "#FBBF24")
        sent_bg = "rgba(16, 185, 129, 0.15)" if "positive" in sentiment_val.lower() else ("rgba(239, 68, 68, 0.15)" if "negative" in sentiment_val.lower() else "rgba(245, 158, 11, 0.15)")
        sent_icon = "🟢" if "positive" in sentiment_val.lower() else ("🔴" if "negative" in sentiment_val.lower() else "🟡")

        # Emotion emoji
        em_lower = emotion_val.lower()
        em_icon = "😤" if any(w in em_lower for w in ["frustrat", "anger", "angry", "upset"]) else (
            "😍" if any(w in em_lower for w in ["delight", "love", "excite", "happy", "praise"]) else (
                "🤔" if any(w in em_lower for w in ["curious", "question", "skeptic", "doubt"]) else (
                    "🙏" if any(w in em_lower for w in ["grate", "thank", "appreciat"]) else (
                        "😟" if any(w in em_lower for w in ["anxious", "worried", "disappoint"]) else "😐"
                    )
                )
            )
        )

        # 4 Indicators Grid
        ind_c1, ind_c2, ind_c3, ind_c4 = st.columns(4)
        with ind_c1:
            st.markdown(
                f"""
                <div style="background: var(--card); border: 1px solid var(--card-border); border-radius: 14px; padding: 1.1rem; text-align: center;">
                    <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.4rem;">Detected Emotion</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF; display: flex; align-items: center; justify-content: center; gap: 0.4rem;">
                        <span>{em_icon}</span>
                        <span>{emotion_val}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with ind_c2:
            st.markdown(
                f"""
                <div style="background: var(--card); border: 1px solid var(--card-border); border-radius: 14px; padding: 1.1rem; text-align: center;">
                    <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.4rem;">Sentiment Polar</div>
                    <div style="display: inline-flex; align-items: center; gap: 0.35rem; background: {sent_bg}; border: 1px solid {sent_color}; color: {sent_color}; font-size: 1.05rem; font-weight: 800; padding: 0.35rem 0.9rem; border-radius: 9999px;">
                        <span>{sent_icon}</span>
                        <span>{sentiment_val}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with ind_c3:
            st.markdown(
                f"""
                <div style="background: var(--card); border: 1px solid var(--card-border); border-radius: 14px; padding: 1.1rem;">
                    <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.25rem;">User Intention</div>
                    <div style="color: #E2E8F0; font-size: 0.92rem; font-weight: 600; line-height: 1.4;">
                        🎯 {analysis.get('intent', 'General communication')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with ind_c4:
            st.markdown(
                f"""
                <div style="background: var(--card); border: 1px solid var(--card-border); border-radius: 14px; padding: 1.1rem;">
                    <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.25rem;">Core Requirement</div>
                    <div style="color: #E2E8F0; font-size: 0.92rem; font-weight: 600; line-height: 1.4;">
                        📌 {analysis.get('requirement', 'Constructive reply')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Context summary line
        if analysis.get("context"):
            st.caption(f"💬 **Conversation Context:** {analysis.get('context')}")

    # Display Three Response Cards
    result = st.session_state.get("ea_result")
    if result and not result.get("error"):
        st.write("")
        st.markdown(f"#### 📬 Tailored Responses for **{selected_platform}**")
        st.caption("Review the three distinct communication styles below. Click **Copy Response** to use immediately, or log to memory bank.")

        r_card1, r_card2, r_card3 = st.columns(3)

        # 1. Friendly Response Card
        with r_card1:
            friendly_text = result.get("friendly_response", "").strip()
            st.markdown(
                """
                <div style="background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 16px; padding: 1.25rem 1.4rem; height: 100%; box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                        <span style="background: rgba(59, 130, 246, 0.2); color: #93C5FD; font-size: 0.78rem; font-weight: 800; padding: 0.25rem 0.65rem; border-radius: 9999px;">
                            😊 FRIENDLY
                        </span>
                        <span style="font-size: 0.8rem; color: #CBD5E1; font-weight: 500;">Warm & Engaging</span>
                    </div>
                    <div style="color: #F8FAFC; line-height: 1.65; font-size: 0.96rem; min-height: 140px; margin-bottom: 0.85rem;">
                """ + friendly_text.replace("\n", "<br>") + """
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(friendly_text, language=None)
            fc1, fc2 = st.columns([1.2, 1])
            with fc1:
                if st.button("📋 Copy Response", key="copy_friendly", use_container_width=True):
                    st.toast("Friendly response copied to view!")
            with fc2:
                if st.button("🧠 Save to Memory", key="mem_friendly", use_container_width=True):
                    agent.remember_interaction(selected_platform, commenter_handle, comment_text, friendly_text, analysis.get("sentiment", "positive"))
                    st.success("Saved to agent memory!")

        # 2. Professional Response Card
        with r_card2:
            prof_text = result.get("professional_response", "").strip()
            st.markdown(
                """
                <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.35); border-radius: 16px; padding: 1.25rem 1.4rem; height: 100%; box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                        <span style="background: rgba(139, 92, 246, 0.2); color: #C4B5FD; font-size: 0.78rem; font-weight: 800; padding: 0.25rem 0.65rem; border-radius: 9999px;">
                            💼 PROFESSIONAL
                        </span>
                        <span style="font-size: 0.8rem; color: #CBD5E1; font-weight: 500;">Polished & Solution-Driven</span>
                    </div>
                    <div style="color: #F8FAFC; line-height: 1.65; font-size: 0.96rem; min-height: 140px; margin-bottom: 0.85rem;">
                """ + prof_text.replace("\n", "<br>") + """
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(prof_text, language=None)
            pc1, pc2 = st.columns([1.2, 1])
            with pc1:
                if st.button("📋 Copy Response", key="copy_prof", use_container_width=True):
                    st.toast("Professional response copied to view!")
            with pc2:
                if st.button("🧠 Save to Memory", key="mem_prof", use_container_width=True):
                    agent.remember_interaction(selected_platform, commenter_handle, comment_text, prof_text, analysis.get("sentiment", "neutral"))
                    st.success("Saved to agent memory!")

        # 3. Empathetic Response Card
        with r_card3:
            empathy_text = result.get("empathetic_response", "").strip()
            st.markdown(
                """
                <div style="background: rgba(236, 72, 153, 0.08); border: 1px solid rgba(236, 72, 153, 0.35); border-radius: 16px; padding: 1.25rem 1.4rem; height: 100%; box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                        <span style="background: rgba(236, 72, 153, 0.2); color: #F472B6; font-size: 0.78rem; font-weight: 800; padding: 0.25rem 0.65rem; border-radius: 9999px;">
                            ❤️ EMPATHETIC
                        </span>
                        <span style="font-size: 0.8rem; color: #CBD5E1; font-weight: 500;">High Emotional IQ</span>
                    </div>
                    <div style="color: #F8FAFC; line-height: 1.65; font-size: 0.96rem; min-height: 140px; margin-bottom: 0.85rem;">
                """ + empathy_text.replace("\n", "<br>") + """
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(empathy_text, language=None)
            ec1, ec2 = st.columns([1.2, 1])
            with ec1:
                if st.button("📋 Copy Response", key="copy_empathy", use_container_width=True):
                    st.toast("Empathetic response copied to view!")
            with ec2:
                if st.button("🧠 Save to Memory", key="mem_empathy", use_container_width=True):
                    agent.remember_interaction(selected_platform, commenter_handle, comment_text, empathy_text, analysis.get("sentiment", "empathetic"))
                    st.success("Saved to agent memory!")

        st.caption(f"💾 *Responses automatically saved to SQLite (`socialspark.db`, record #{result.get('saved_id')}).*")

    # Expandable History of Saved Responses from SQLite
    st.write("")
    with st.expander("📜 Previously Generated Responses (Saved in SQLite Database)"):
        saved_records = agent.get_saved_emotion_replies(user_email, limit=6)
        if not saved_records:
            st.caption("No saved responses yet in this session.")
        else:
            for rec in saved_records:
                st.markdown(
                    f"""
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.85rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                            <span style="font-weight: 700; color: #FFFFFF;">{rec.get('platform', 'Social')} · <span style="color: #94A3B8;">{rec.get('commenter') or 'User'}</span></span>
                            <span style="background: rgba(139, 92, 246, 0.2); color: #C4B5FD; font-size: 0.78rem; font-weight: 700; padding: 0.15rem 0.55rem; border-radius: 9999px;">
                                {rec.get('emotion', 'Neutral')} ({rec.get('sentiment', 'Neutral')})
                            </span>
                        </div>
                        <div style="color: #CBD5E1; font-style: italic; font-size: 0.92rem; margin-bottom: 0.6rem;">"{rec.get('comment')}"</div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.6rem; font-size: 0.86rem;">
                            <div style="background: rgba(59, 130, 246, 0.08); padding: 0.6rem; border-radius: 8px; color: #E2E8F0;">
                                <strong>Friendly:</strong> {rec.get('friendly_response')}
                            </div>
                            <div style="background: rgba(139, 92, 246, 0.08); padding: 0.6rem; border-radius: 8px; color: #E2E8F0;">
                                <strong>Professional:</strong> {rec.get('professional_response')}
                            </div>
                            <div style="background: rgba(236, 72, 153, 0.08); padding: 0.6rem; border-radius: 8px; color: #E2E8F0;">
                                <strong>Empathetic:</strong> {rec.get('empathetic_response')}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# -----------------------------------------------------------------------------
# WORKSPACE MODULE 4: AGENT LEARNING & INSIGHTS
# -----------------------------------------------------------------------------
elif dashboard_view in [NAV_LEARNED, "🧠 What the Agent Learned"]:
    st.markdown(
        """
        <div class="workspace-main-header">
            <h1 class="engagement-title">
                <span class="sparkle-cyan-lg">✦</span>
                <span class="text-white">What the Agent </span><span class="text-engagement-grad">Learned</span>
            </h1>
            <p class="engagement-desc">Transparent cognitive memory logs, manager approvals, and active learning reflections.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    user_email = st.session_state.get("profile", {}).get("email", "default")

    col_ins1, col_ins2 = st.columns([1.4, 1])
    with col_ins1:
        if st.button("Generate audience insights", type="primary", key="btn_gen_insights"):
            with st.spinner("Synthesizing memory bank reflections & audience intelligence..."):
                st.session_state.audience_insights = agent.audience_insights(user_email=user_email)
    with col_ins2:
        if st.session_state.get("audience_insights"):
            if st.button("Clear insights", key="btn_clear_insights", use_container_width=True):
                st.session_state.audience_insights = None
                st.rerun()

    if st.session_state.get("audience_insights"):
        st.markdown(
            f"""
            <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 16px; padding: 1.5rem; margin-top: 1rem; margin-bottom: 1.5rem; box-shadow: 0 8px 24px rgba(0,0,0,0.25);">
                <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.85rem;">
                    <span style="font-size: 1.4rem;">🔍</span>
                    <h4 style="margin: 0; color: #FFFFFF; font-size: 1.15rem;">Audience Intelligence Synthesis</h4>
                </div>
                <div style="color: #CBD5E1; line-height: 1.7; font-size: 0.95rem;">
                    {st.session_state.audience_insights.replace(chr(10), '<br>')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("Log a new post's results")
    st.caption("Record performance metrics so the AI agent learns which formats and topics work best.")
    with st.form("perf"):
        result_platform = st.selectbox("Platform", ["Instagram", "Twitter", "LinkedIn"], key="pl")
        text = st.text_input("Post text", placeholder="Paste the posted caption, tweet, or article snippet...")
        likes_column, comments_column, shares_column = st.columns(3)
        likes = likes_column.number_input("Likes", min_value=0, value=0)
        comments = comments_column.number_input("Comments", min_value=0, value=0)
        shares = shares_column.number_input("Shares", min_value=0, value=0)
        submit_retain = st.form_submit_button("Retain", type="primary")

    if submit_retain:
        if not text.strip():
            st.error("Please enter the post text before retaining.")
        else:
            saved = agent.remember_post(result_platform, text.strip(), likes, comments, shares)
            if saved is None:
                st.info(f"Post metrics for {result_platform} noted locally (Hindsight memory service offline).")
            else:
                st.success(f"✅ Successfully retained post metrics for {result_platform} ({likes} likes, {comments} comments, {shares} shares)!")

else:
    # Fallback for unrecognized module selection
    st.error(f"⚠️ Unrecognized workspace module: '{dashboard_view}'.")
    st.info("Please select a module from the left sidebar navigation, or use the button below to restore the default view.")
    if st.button("Reset to Create a Post", type="primary", key="btn_reset_module_fallback"):
        st.session_state["dash_sidebar_radio"] = NAV_POST
        st.rerun()

# Fallback for unrecognized top-level page state
if st.session_state.get("page") not in ["landing", "signup", "dashboard"]:
    st.error(f"⚠️ Unrecognized page state: '{st.session_state.get('page')}'.")
    if st.button("Return to Landing Page", type="primary", key="btn_invalid_page_fallback"):
        st.session_state.page = "landing"
        st.rerun()