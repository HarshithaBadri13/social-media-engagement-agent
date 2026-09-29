import streamlit as st

from backend import agent

st.set_page_config(page_title="SocialSpark Agent", page_icon="✨", layout="wide")
st.title("✨ SocialSpark Engagement Agent")
st.caption("A flexible social media agent that adapts to any topic, audience, and platform.")

tab1, tab2, tab3 = st.tabs(["✍️ Draft a post", "💬 Reply to a comment", "🧠 What the agent learned"])


def draft_ui(kind, generate, topic_value=None):
    """Side-by-side: no memory vs Hindsight memory, then feedback -> retained."""
    first, second = st.columns(2)
    if st.button("Generate", key=f"gen_{kind}", type="primary"):
        if kind == "post" and not (topic_value or "").strip():
            st.error("Enter a topic or subject first.")
        else:
            with st.spinner("Thinking..."):
                try:
                    plain = generate(False)
                except Exception as error:
                    plain = {"draft": f"[Generation error: {error}]", "memory": ""}
                try:
                    memory_draft = generate(True)
                except Exception as error:
                    memory_draft = {"draft": f"[Memory generation error: {error}]", "memory": ""}
                st.session_state[kind] = {"plain": plain, "mem": memory_draft}
    output = st.session_state.get(kind)
    if not output:
        return
    first.subheader("Without memory")
    plain_draft = output["plain"]["draft"]
    if plain_draft.startswith("["):
        first.error(plain_draft)
    else:
        first.info(plain_draft)
    second.subheader("With Hindsight memory")
    memory_draft = output["mem"]["draft"]
    if memory_draft.startswith("["):
        second.error(memory_draft)
    else:
        second.success(memory_draft)
    with second.expander("Memories used"):
        st.text(output["mem"]["memory"] or "none")
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