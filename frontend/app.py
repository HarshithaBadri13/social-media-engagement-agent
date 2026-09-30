import re
import time

import streamlit as st

from backend import agent

st.set_page_config(page_title="SocialSpark", page_icon="✨", layout="wide")
st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        --bg: #0B1020;
        --surface: #111827;
        --card: #151D32;
        --blue: #4F8CFF;
        --violet: #8B5CF6;
        --success: #22C55E;
        --warning: #F59E0B;
        --text: #F2F5FC;
        --muted: #9AA8C1;
        --line: #29344D;
    }
    html, body, [data-testid="stAppViewContainer"], .stApp { background-color: var(--bg); color: var(--text); }
    .stApp { background-image: radial-gradient(ellipse at 12% 0%, #4f8cff17, transparent 34%), radial-gradient(ellipse at 92% 12%, #8b5cf610, transparent 30%); background-attachment: fixed; }
    [data-testid="stHeader"] { background: #0B1020D9; }
    [data-testid="stMainBlockContainer"] { max-width: 1480px; padding: 2.25rem 3rem 4rem; }
    [data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }
    h1, h2, h3, h4, p, label { color: var(--text); }
    h1, h2, h3 { letter-spacing: 0; }
    .brandline { color: var(--text); font-size: 1rem; font-weight: 750; }
    .brandline::first-letter { color: var(--blue); }
    body:has(.splash-screen) [data-testid="stHeader"],
    body:has(.splash-screen) [data-testid="stToolbar"],
    body:has(.splash-screen) [data-testid="stDecoration"],
    body:has(.splash-screen) footer { display: none !important; }
    body:has(.splash-screen) [data-testid="stMainBlockContainer"] { display: grid; width: 100%; max-width: none; min-height: 100svh; padding: 0; place-items: center; }
    .splash-screen { position: relative; isolation: isolate; display: grid; width: 100%; min-height: 100svh; overflow: hidden; place-items: center; background: var(--bg); text-align: center; animation: splashExit .48s ease-in 4.52s forwards; }
    .splash-screen::before { position: absolute; z-index: -1; content: ""; inset: -24%; background: radial-gradient(ellipse at 24% 34%, #4F8CFF25, transparent 42%), radial-gradient(ellipse at 76% 62%, #8B5CF61D, transparent 43%), radial-gradient(ellipse at 52% 85%, #22D3EE0C, transparent 35%); filter: blur(18px); animation: ambientDrift 18s ease-in-out infinite alternate; }
    .splash-content { display: grid; justify-items: center; gap: 1.4rem; padding: 2rem; }
    .splash-mark { opacity: 0; font-size: 4.6rem; line-height: 1; animation: markEnter .9s cubic-bezier(.2,.75,.25,1) forwards; }
    .splash-glyph { display: block; filter: drop-shadow(0 0 18px #4F8CFF88) drop-shadow(0 0 38px #8B5CF644); animation: markBreathe 4.2s ease-in-out 1s infinite; }
    .splash-title { margin: 0; opacity: 0; background: linear-gradient(100deg, #F2F5FC 12%, #C4D7FF 48%, #F2F5FC 82%); background-size: 220% auto; background-clip: text; color: transparent; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 4rem; font-weight: 800; line-height: 1.08; letter-spacing: 0; text-shadow: 0 0 32px #4F8CFF20; animation: titleEnter .85s ease-out .55s forwards, titleShimmer 8s ease-in-out 1.5s infinite; }
    .splash-social { position: absolute; z-index: 1; top: var(--icon-top, auto); right: var(--icon-right, auto); bottom: var(--icon-bottom, auto); left: var(--icon-left, auto); opacity: 0; animation: iconEnter .7s cubic-bezier(.2,.75,.25,1) var(--icon-delay) forwards; }
    .social-glyph { display: grid; width: 54px; aspect-ratio: 1; place-items: center; border: 1px solid color-mix(in srgb, var(--icon-color) 45%, transparent); border-radius: 17px; background: #151D327A; color: var(--icon-color); filter: drop-shadow(0 0 13px color-mix(in srgb, var(--icon-color) 38%, transparent)); animation: iconFloat var(--float-duration) ease-in-out infinite; }
    .social-glyph svg { display: block; width: 25px; height: 25px; fill: currentColor; }
    .orbit-instagram { --icon-color: #F472B6; --icon-delay: .15s; --float-duration: 5.3s; --icon-top: 23%; --icon-left: 22%; }
    .orbit-linkedin { --icon-color: #4F8CFF; --icon-delay: .35s; --float-duration: 6.1s; --icon-top: 23%; --icon-right: 22%; }
    .orbit-x { --icon-color: #67D9F2; --icon-delay: .55s; --float-duration: 5.7s; --icon-top: 51%; --icon-left: 13%; }
    .orbit-facebook { --icon-color: #A78BFA; --icon-delay: .75s; --float-duration: 6.4s; --icon-top: 51%; --icon-right: 13%; }
    .orbit-youtube { --icon-color: #F472B6; --icon-delay: .95s; --float-duration: 5.9s; --icon-bottom: 16%; --icon-left: 29%; }
    .orbit-tiktok { --icon-color: #67D9F2; --icon-delay: 1.15s; --float-duration: 6.6s; --icon-bottom: 16%; --icon-right: 29%; }
    .page-intro { max-width: 580px; margin: 1rem auto 2rem; text-align: center; animation: signupEnter .46s ease-out both; }
    [data-testid="stForm"]:has(input[type="password"]) { animation: signupEnter .46s .06s ease-out both; }
    .page-intro h1 { font-size: 2.6rem; margin-bottom: .4rem; }
    .page-intro p, .demo-note { color: var(--muted); }
    .demo-note { text-align: center; font-size: .8rem; margin-top: 1rem; }
    .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted); }
    div.stButton > button, div.stFormSubmitButton > button { min-height: 2.7rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); color: var(--text); font-weight: 650; transition: background .18s ease, border-color .18s ease, transform .18s ease; }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover { border-color: #4F8CFF88; background: #1A2540; color: #fff; transform: translateY(-1px); }
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] { background: var(--blue); border-color: var(--blue); color: #fff; box-shadow: 0 8px 22px #4F8CFF30; }
    div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover { background: #6A9CFF; border-color: #6A9CFF; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div { background: var(--card); border: 1px solid var(--line); border-radius: 8px; }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within, div[data-baseweb="select"] > div:focus-within { border-color: var(--blue); box-shadow: 0 0 0 1px var(--blue); }
    input, textarea, [data-baseweb="select"] *, [data-baseweb="input"] *, [data-baseweb="textarea"] * { color: var(--text) !important; caret-color: var(--blue); }
    input::placeholder, textarea::placeholder { color: #7786A0 !important; }
    [data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--card); border: 1px solid var(--line); }
    [role="option"] { background: var(--card); color: var(--text); }
    [role="option"]:hover, [aria-selected="true"][role="option"] { background: #243454; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid var(--line); background: transparent; }
    [data-testid="stTabs"] [data-baseweb="tab"] { height: 3.25rem; border-bottom: 2px solid transparent; color: var(--muted); background: transparent; }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] { border-bottom-color: var(--blue); color: #8BB1FF; }
    [data-testid="stTabContent"] { padding-top: 1.25rem; }
    [data-testid="stForm"] { padding: 1.2rem; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
    [data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
    [data-testid="stExpander"] summary { color: var(--text); }
    [data-testid="stAlert"] { border: 1px solid var(--line); border-radius: 8px; background: var(--surface); color: var(--text); }
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p { color: var(--text); }
    [data-testid="stAlert"] svg { fill: var(--blue); }
    [data-testid="stToast"] { border: 1px solid var(--line); background: var(--card); color: var(--text); }
    hr { border-color: var(--line); }
    a { color: #8BB1FF; }
    a:hover { color: #B8A1FF; }
    @keyframes markEnter { from { opacity: 0; transform: scale(.68); } to { opacity: 1; transform: scale(1); } }
    @keyframes markBreathe { 0%, 100% { transform: translateY(0) scale(.98); filter: brightness(1); } 50% { transform: translateY(-7px) scale(1.045); filter: brightness(1.14); } }
    @keyframes iconEnter { from { opacity: 0; transform: scale(.5) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
    @keyframes iconFloat { 0%, 100% { transform: translate(0, 0) rotate(-5deg); } 35% { transform: translate(5px, -9px) rotate(2deg); } 70% { transform: translate(-4px, -4px) rotate(6deg); } }
    @keyframes titleEnter { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes titleShimmer { 0%, 100% { background-position: 100% center; } 50% { background-position: 0% center; } }
    @keyframes ambientDrift { from { transform: translate3d(-1%, -1%, 0) scale(1); } to { transform: translate3d(1%, 1%, 0) scale(1.06); } }
    @keyframes splashExit { to { opacity: 0; transform: scale(.985); } }
    @keyframes signupEnter { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 760px) {
        [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 2rem; }
        .splash-content { gap: 1.1rem; }
        .splash-mark { font-size: 3.8rem; }
        .splash-title { font-size: 3rem; }
        .social-glyph { width: 42px; border-radius: 14px; }
        .social-glyph svg { width: 20px; height: 20px; }
        .orbit-instagram { --icon-top: 17%; --icon-left: 12%; }
        .orbit-linkedin { --icon-top: 17%; --icon-right: 12%; }
        .orbit-youtube { --icon-bottom: 17%; --icon-left: 20%; }
        .orbit-tiktok { --icon-bottom: 17%; --icon-right: 20%; }
        .orbit-x, .orbit-facebook { display: none; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; }
        .splash-screen { animation: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "page" not in st.session_state:
    st.session_state.page = "landing"

if st.session_state.page == "landing":
    st.markdown(
        """
                <main class="splash-screen" aria-label="SocialSpark">
                    <span class="splash-social orbit-instagram" aria-hidden="true"><span class="social-glyph"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.7" cy="6.5" r="1.2"/></svg></span></span>
                    <span class="splash-social orbit-linkedin" aria-hidden="true"><span class="social-glyph"><svg viewBox="0 0 24 24"><path d="M5.2 3.4a2.1 2.1 0 1 1 0 4.2 2.1 2.1 0 0 1 0-4.2ZM3.4 9h3.7v11.6H3.4V9Zm5.9 0h3.5v1.6h.1a3.8 3.8 0 0 1 3.4-1.9c3.7 0 4.4 2.4 4.4 5.5v6.4H17v-5.7c0-1.4 0-3.2-2-3.2s-2.3 1.5-2.3 3.1v5.8H9.3V9Z"/></svg></span></span>
                    <span class="splash-social orbit-x" aria-hidden="true"><span class="social-glyph"><svg viewBox="0 0 24 24"><path d="M18.9 1.2h3.7l-8.1 9.2L24 23.2h-7.4l-5.8-7.6-6.6 7.6H.5l8.6-9.8L0 1.2h7.6l5.2 6.9 6.1-6.9Zm-1.3 20h2L6.5 3.1h-2L17.6 21.2Z"/></svg></span></span>
                    <span class="splash-social orbit-facebook" aria-hidden="true"><span class="social-glyph"><svg viewBox="0 0 24 24"><path d="M24 12.1C24 5.4 18.6 0 12 0S0 5.4 0 12.1C0 18.1 4.4 23.1 10.1 24v-8.4H7.1v-3.5h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9v2.3h3.3l-.5 3.5h-2.8V24C19.6 23.1 24 18.1 24 12.1Z"/></svg></span></span>
                    <span class="splash-social orbit-youtube" aria-hidden="true"><span class="social-glyph"><svg viewBox="0 0 24 24"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.6 3.6 12 3.6 12 3.6s-7.6 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.8.5 9.4.5 9.4.5s7.6 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8ZM9.6 15.6V8.4l6.3 3.6-6.3 3.6Z"/></svg></span></span>
                    <span class="splash-social orbit-tiktok" aria-hidden="true"><span class="social-glyph"><svg viewBox="0 0 24 24"><path d="M19.6 7.5a7.2 7.2 0 0 1-4.4-1.9v8.1a6.1 6.1 0 1 1-6.1-6.1c.4 0 .8 0 1.2.1v3.4a2.8 2.8 0 1 0 1.8 2.6V2h3.5a7.2 7.2 0 0 0 4 5.5v3.6Z"/></svg></span></span>
                    <div class="splash-content">
                        <div class="splash-mark" aria-hidden="true"><span class="splash-glyph">✨</span></div>
                        <h1 class="splash-title">SocialSpark</h1>
                    </div>
                </main>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(5.0)
    st.session_state.page = "signup"
    st.rerun()

if st.session_state.page == "signup":
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        st.markdown(
            '<div class="page-intro"><div class="eyebrow">Start creating</div><h1>Your next post starts here.</h1><p>Set up your SocialSpark profile and meet your new social copilot.</p></div>',
            unsafe_allow_html=True,
        )
        with st.form("signup_form"):
            name = st.text_input("Your name", placeholder="Alex Morgan")
            email = st.text_input("Work email", placeholder="alex@yourbrand.com")
            password = st.text_input("Password", type="password", help="Use at least 8 characters.")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
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
        st.markdown('<div class="demo-note">Prototype signup: profile details stay in this session and are not saved to an account.</div>', unsafe_allow_html=True)
        if st.button("Back to Home", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
    st.stop()

st.markdown('<div class="brandline">✨ SocialSpark Engagement Agent</div>', unsafe_allow_html=True)
if st.session_state.get("profile"):
    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.caption(f"Welcome, {st.session_state.profile['name']} · {st.session_state.profile['email']}")
    with top_right:
        if st.button("Sign out", use_container_width=True):
            st.session_state.page = "landing"
            st.session_state.pop("profile", None)
            st.rerun()
st.title("Your engagement workspace")
st.caption("A flexible social media agent that adapts to any topic, audience, and platform.")

tab1, tab2, tab3 = st.tabs(["✍️ Draft a post", "💬 Reply to a comment", "🧠 What the agent learned"])


def draft_ui(kind, generate, topic_value=None):
    """Side-by-side: no memory vs Hindsight memory, then feedback -> retained."""
    first, second = st.columns(2)
    plain_panel = first.empty()
    memory_panel = second.empty()

    def show_result(panel, heading, result, use_memory=False):
        panel.empty()
        with panel.container():
            st.subheader(heading)
            draft = result["draft"]
            if draft.startswith("["):
                st.error(draft)
            elif use_memory:
                st.success(draft)
            else:
                st.info(draft)
            if use_memory:
                with st.expander("Memories used"):
                    st.text(result["memory"] or "none")

    if st.button("Generate", key=f"gen_{kind}", type="primary"):
        if kind == "post" and not (topic_value or "").strip():
            st.error("Enter a topic or subject first.")
        else:
            with plain_panel.container():
                st.subheader("Without memory")
                st.info("Generating your draft...")
            with memory_panel.container():
                st.subheader("With Hindsight memory")
                st.caption("Waiting for the first draft...")
            try:
                plain = generate(False)
            except Exception as error:
                plain = {"draft": f"[Generation error: {error}]", "memory": ""}
            st.session_state[kind] = {
                "plain": plain,
                "mem": {"draft": "", "memory": ""},
            }
            show_result(plain_panel, "Without memory", plain)
            with memory_panel.container():
                st.subheader("With Hindsight memory")
                st.info("Applying relevant memory...")
            try:
                memory_draft = generate(True)
            except Exception as error:
                memory_draft = {"draft": f"[Memory generation error: {error}]", "memory": ""}
            st.session_state[kind]["mem"] = memory_draft
            show_result(memory_panel, "With Hindsight memory", memory_draft, use_memory=True)
    output = st.session_state.get(kind)
    if not output:
        return
    if not st.session_state.get(f"gen_{kind}"):
        show_result(plain_panel, "Without memory", output["plain"])
        if output["mem"]["draft"]:
            show_result(memory_panel, "With Hindsight memory", output["mem"], use_memory=True)
    edited = st.text_area("Edit the memory-powered draft (your edits teach the agent)",
                          output["mem"]["draft"], key=f"edit_{kind}")
    approve, reject = st.columns(2)
    if approve.button("✅ Approve", key=f"ok_{kind}"):
        changed = edited != output["mem"]["draft"]
        saved = agent.remember_feedback(
            kind, output["mem"]["draft"],
            "edited" if changed else "approved", edited if changed else None)
        if saved is None:
            st.warning("Draft kept, but Hindsight could not save it. Check HINDSIGHT_API_KEY.")
        else:
            st.toast("Saved to memory. The agent will remember this.")
    if reject.button("❌ Reject", key=f"no_{kind}"):
        saved = agent.remember_feedback(kind, output["mem"]["draft"], "rejected", edited)
        if saved is None:
            st.warning("Draft kept, but Hindsight could not save it. Check HINDSIGHT_API_KEY.")
        else:
            st.toast("Rejection saved to memory.")


with tab1:
    post_platform = st.selectbox("Platform", ["Instagram", "Twitter", "LinkedIn"], key="post_platform")
    post_topic = st.text_input(
        "Topic",
        placeholder="Enter any topic...",
        value="Launching our new clothing store",
        help="Enter any topic, idea, event, product, or subject you want to write about.",
        key="post_topic",
    )
    draft_ui("post", lambda use_memory: agent.draft_post(post_platform, post_topic, use_memory), post_topic)

with tab2:
    reply_platform = st.selectbox("Platform ", ["Instagram", "Twitter"], key="reply_platform")
    user = st.text_input("Commenter", "@arjun_k")
    comment = st.text_area("Comment", "Ordered again and it's late AGAIN. Seriously?")
    draft_ui("reply", lambda use_memory: agent.draft_reply(reply_platform, user, comment, use_memory))
    if st.button("Log this interaction to memory"):
        saved = agent.remember_interaction(
            reply_platform, user, comment,
            st.session_state.get("reply", {}).get("mem", {}).get("draft", ""),
            "unknown")
        if saved is None:
            st.warning("Interaction kept locally, but Hindsight could not save it. Check HINDSIGHT_API_KEY.")
        else:
            st.toast("Interaction retained.")

with tab3:
    st.write("Reflect over every post, comment and correction the agent has seen:")
    if st.button("Generate audience insights"):
        with st.spinner("Reflecting over memory..."):
            st.markdown(agent.audience_insights())
    st.divider()
    st.subheader("Log a new post's results")
    with st.form("perf"):
        result_platform = st.selectbox("Platform", ["Instagram", "Twitter", "LinkedIn"], key="pl")
        text = st.text_input("Post text")
        likes_column, comments_column, shares_column = st.columns(3)
        likes = likes_column.number_input("Likes", 0)
        comments = comments_column.number_input("Comments", 0)
        shares = shares_column.number_input("Shares", 0)
        if st.form_submit_button("Retain"):
            saved = agent.remember_post(result_platform, text, likes, comments, shares)
            if saved is None:
                st.warning("Post kept, but Hindsight could not save it. Check HINDSIGHT_API_KEY.")
            else:
                st.success("Retained.")