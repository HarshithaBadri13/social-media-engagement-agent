"""Social media agent: Hindsight memory layer and LLM logic."""
import os
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BANK = os.getenv("BANK_ID", "socialspark-agent")
MODELS = [os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
          os.getenv("LLM_FALLBACK_MODEL", "qwen/qwen3.8-27b")]

memory = Hindsight(base_url=os.getenv("HINDSIGHT_URL", "http://localhost:8888"),
                   api_key=os.getenv("HINDSIGHT_API_KEY") or None)
llm = None
MEMORY_TIMEOUT_SECONDS = 8

BASE_SYSTEM = ("You are SocialSpark, a flexible social media engagement agent. Write "
               "concise, engaging content tailored to the user's exact topic and "
               "selected platform. Do not inject a product category, brand, or theme "
               "that the user did not request. Support any reasonable topic and adapt "
               "the tone to the subject.\n\n"
               "Context relevance rule: Never mention, recommend, reference, or assume "
               "Brewline Coffee unless the user explicitly asks about Brewline Coffee or "
               "the current conversation is clearly and directly about that business. "
               "For general or unrelated questions, answer only the user's question. "
               "Ignore old brand memories unless they are directly relevant and the user "
               "has asked about that brand.")


def _memory_call(method, **kwargs):
    """Run Hindsight's async client outside Streamlit's event loop."""
    def execute():
        return asyncio.run(method(**kwargs))

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(execute)
    try:
        return future.result(timeout=MEMORY_TIMEOUT_SECONDS)
    except TimeoutError:
        future.cancel()
        raise TimeoutError("Hindsight request timed out")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _try_memory_call(method, **kwargs):
    try:
        return _memory_call(method, **kwargs)
    except Exception:
        return None


def _text(x) -> str:
    return getattr(x, "text", None) or str(x)


def chat(system: str, user: str) -> str:
    """Call Groq, falling back to the second configured model on errors."""
    global llm
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "[LLM unavailable: set GROQ_API_KEY in your .env file]"
    if llm is None:
        llm = Groq(api_key=api_key)
    last = None
    for model in MODELS:
        try:
            response = llm.chat.completions.create(
                model=model, temperature=0.7,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}])
            return response.choices[0].message.content.strip()
        except Exception as error:
            last = error
    return f"[LLM error: {last}]"


def _platform_guidance(platform: str) -> str:
    guidance = {
        "Instagram": "visual and engaging caption, optional emojis, concise hashtags",
        "LinkedIn": "professional, business-oriented, and thought-leadership focused",
        "Twitter": "concise, hook-first, and short-form",
        "X": "concise, hook-first, and short-form",
        "Facebook": "conversational and community-oriented",
    }
    return guidance.get(platform, "clear, engaging, and appropriate for the selected platform")


def _brand_requested(user_text: str) -> bool:
    return "brewline" in user_text.casefold()


def _coffee_requested(user_text: str) -> bool:
    text = user_text.casefold()
    return any(term in text for term in ("coffee", "espresso", "latte", "caffeine", "brew"))


def _enforce_brand_context(response: str, user_text: str, system: str, request: str) -> str:
    """Retry and neutralize stale brand references in unrelated responses."""
    response_text = response.casefold()
    has_unrequested_brand = "brewline" in response_text and not _brand_requested(user_text)
    has_unrequested_coffee = (
        not _coffee_requested(user_text)
        and any(term in response_text for term in ("coffee", "espresso", "latte", "caffeine", "brew"))
    )
    if not has_unrequested_brand and not has_unrequested_coffee:
        return response
    strict_system = (system + "\n\nFINAL CHECK: The user did not ask about Brewline Coffee. "
                     "Return the same answer without any Brewline, BrewlineLabs, coffee, "
                     "espresso, latte, caffeine, or brew references unless the user asked "
                     "about that subject. Keep the user's requested subject unchanged.")
    retry = chat(strict_system, request)
    retry_text = retry.casefold()
    if "brewline" not in retry_text and (
        _coffee_requested(user_text)
        or not any(term in retry_text for term in ("coffee", "espresso", "latte", "caffeine", "brew"))
    ):
        return retry
    return re.sub(r"(?i)#?brewline\w*|coffee|espresso|latte|caffeine|brew", "", retry).strip()


def generate_post(platform: str, topic: str) -> str:
    """Generate content for any non-empty user-supplied topic."""
    topic = topic.strip()
    if not topic:
        return "[Please enter a topic or subject]"
    system = (BASE_SYSTEM + "\n\nAddress the exact user topic directly; never replace it "
              "with a predefined topic or unrelated theme.\n\n" +
              f"Platform guidance for {platform}: {_platform_guidance(platform)}")
    request = (f"Create a {platform} social media post for this exact user topic:\n"
               f"{topic}\n\nInclude an engaging caption, suitable hashtags, a call to "
               "action, and a suggested tone. Output only the finished content.")
    return _enforce_brand_context(chat(system, request), topic, system, request)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def remember_post(platform, text, likes, comments, shares, posted_at=None):
    return _try_memory_call(memory.aretain, bank_id=BANK, context="post_performance",
                            timestamp=posted_at or now(),
                            content=f'{platform} post: "{text}" -> {likes} likes, '
                                    f"{comments} comments, {shares} shares.")


def remember_interaction(platform, user, comment, our_reply, sentiment):
    return _try_memory_call(
        memory.aretain, bank_id=BANK, context="community_interaction", timestamp=now(),
        content=f'On {platform}, {user} commented: "{comment}" '
                f'(sentiment: {sentiment}). We replied: "{our_reply}"')


def remember_feedback(kind, draft, decision, edited=None):
    message = f'Manager {decision} this {kind} draft: "{draft}".'
    if edited:
        message += f' They rewrote it as: "{edited}".'
    return _try_memory_call(memory.aretain, bank_id=BANK, context="manager_feedback",
                            timestamp=now(), content=message)


def recall_context(query: str, budget: str = "mid") -> str:
    try:
        result = _memory_call(memory.arecall, bank_id=BANK, query=query, budget=budget)
        items = getattr(result, "results", result) or []
        return "\n".join(f"- {_text(item)}" for item in items[:12])
    except Exception as error:
        return f"(memory unavailable: {error})"


def audience_insights() -> str:
    try:
        return _text(_memory_call(memory.areflect,
            bank_id=BANK,
            budget="high",
            query="""Analyze every post, engagement result, community comment, sentiment,
and manager correction stored in this memory bank. Use the actual evidence in memory,
not generic social media advice.

Remember what worked and what failed. Identify which post styles, topics, formats, and
posting times drive engagement for this specific audience. Include patterns from past
conversations, user sentiment, and manager feedback. Do not invent metrics or facts.

Return exactly these seven numbered sections:
1. What Audience Likes Most
2. What Audience Dislikes / Ignores
3. Best Post Styles for this audience
4. Best Topics
5. Best Time to Post
6. Community Sentiment Summary
7. 3 Things to do better next time

Be specific about the evidence behind each conclusion. Do not mention, recommend, or
assume Brewline Coffee unless the stored user data or an explicit request is directly
about Brewline Coffee. Otherwise, answer from the audience data only."""))
    except Exception as error:
        return f"(reflect unavailable: {error})"


def draft_post(platform: str, topic: str, use_memory: bool = True) -> dict:
    topic = topic.strip()
    if not topic:
        return {"draft": "[Please enter a topic or subject]", "memory": ""}
    if not use_memory:
        return {"draft": generate_post(platform, topic),
                "memory": ""}
    recalled = recall_context(f"Exact topic: {topic}; platform: {platform}; related manager feedback")
    system = (BASE_SYSTEM + "\n\nUse the memories below only when they directly relate to "
              "the user's exact topic or selected platform. Ignore unrelated memories, "
              "including memories from a different product category or industry. Do not "
              "copy an unrelated brand, product, or theme into this post. If the user did "
              "not explicitly ask about Brewline Coffee, do not mention it.\n\n"
              "TOPIC-RELEVANT MEMORIES:\n" + recalled +
              "\n\nApply only relevant lessons and output only the post text.")
    request = (f"Create a {platform} social media post for this exact user topic:\n"
               f"{topic}\n\nAddress this topic directly. Include an engaging caption, suitable hashtags, a call to "
               "action, and a suggested tone. Output only the finished content.")
    draft = chat(system, request)
    draft = _enforce_brand_context(draft, topic, system, request)
    return {"draft": draft,
            "memory": recalled}


def draft_reply(platform: str, user: str, comment: str, use_memory: bool = True) -> dict:
    if not use_memory:
        return {"draft": chat(BASE_SYSTEM, f"Reply to this {platform} comment: {comment}"),
                "memory": ""}
    recalled = recall_context(f"{user} past interactions, sentiment, issues; {comment}")
    system = (BASE_SYSTEM + "\n\nWhat we remember about this person/topic:\n" + recalled +
              "\n\nReference relevant history naturally, match the tone that worked "
              "before, and never repeat a mistake. Keep it under 50 words. Do not "
              "mention Brewline Coffee unless the user's comment explicitly asks about it.")
    request = f'{user} wrote on {platform}: "{comment}". Write our reply.'
    draft = chat(system, request)
    draft = _enforce_brand_context(draft, comment, system, request)
    return {"draft": draft,
            "memory": recalled}