"""Social media agent: Hindsight memory layer, Brand Voice, and LLM logic."""
import os
import asyncio
import re
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight
try:
    from backend.database import (
        get_brand_profile,
        save_brand_profile,
        reset_brand_profile,
        save_emotion_reply,
        get_saved_emotion_replies,
    )
except ImportError:
    try:
        from database import (
            get_brand_profile,
            save_brand_profile,
            reset_brand_profile,
            save_emotion_reply,
            get_saved_emotion_replies,
        )
    except ImportError:
        def get_brand_profile(user_email: str = "default"):
            return None
        def save_brand_profile(data: dict, user_email: str = "default"):
            return True
        def reset_brand_profile(user_email: str = "default"):
            return True
        def save_emotion_reply(data: dict, user_email: str = "default"):
            return 1
        def get_saved_emotion_replies(user_email: str = "default", limit: int = 20):
            return []

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)
BANK = os.getenv("BANK_ID", "socialspark-agent")

_configured_models = [os.getenv("LLM_MODEL"), os.getenv("LLM_FALLBACK_MODEL")]
_standard_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
MODELS = [m for m in _configured_models if m] + [m for m in _standard_models if m not in _configured_models]

memory = Hindsight(base_url=os.getenv("HINDSIGHT_URL", "http://localhost:8888"),
                   api_key=os.getenv("HINDSIGHT_API_KEY") or None)
llm = None
openai_client = None
MEMORY_TIMEOUT_SECONDS = 6

# Dedicated persistent event loop worker for Hindsight to maintain alive sessions and connection pooling
import threading
_memory_loop = None
_memory_thread = None
_memory_client = None
_memory_lock = threading.Lock()
_recall_cache = {}

def clear_recall_cache():
    global _recall_cache
    _recall_cache.clear()

def _get_memory_client():
    global _memory_loop, _memory_thread, _memory_client
    with _memory_lock:
        if _memory_client is None:
            _memory_loop = asyncio.new_event_loop()
            _memory_thread = threading.Thread(target=_memory_loop.run_forever, daemon=True, name="HindsightWorker")
            _memory_thread.start()
            
            async def _init():
                return Hindsight(
                    base_url=os.getenv("HINDSIGHT_URL", "http://localhost:8888"),
                    api_key=os.getenv("HINDSIGHT_API_KEY") or None
                )
            fut = asyncio.run_coroutine_threadsafe(_init(), _memory_loop)
            _memory_client = fut.result(timeout=10)
    return _memory_client, _memory_loop

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
    """Run Hindsight client calls safely inside a persistent background event loop."""
    client, loop = _get_memory_client()
    if callable(method):
        name = getattr(method, "__name__", None)
        if name and hasattr(client, name):
            coro = getattr(client, name)(**kwargs)
        else:
            coro = method(**kwargs)
    elif isinstance(method, str) and hasattr(client, method):
        coro = getattr(client, method)(**kwargs)
    else:
        raise ValueError(f"Invalid memory method: {method}")

    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return fut.result(timeout=MEMORY_TIMEOUT_SECONDS)
    except TimeoutError:
        fut.cancel()
        raise TimeoutError("Hindsight request timed out")


def _try_memory_call(method, **kwargs):
    try:
        res = _memory_call(method, **kwargs)
        clear_recall_cache()
        return res
    except Exception:
        return None


def _text(x) -> str:
    return getattr(x, "text", None) or str(x)


_working_model = None
_groq_clients = {}

def chat(system: str, user: str, max_tokens: int = 700) -> str:
    """Call LLM (Groq or OpenAI fallback), caching clients & models for ultra-low latency."""
    global llm, openai_client, _working_model, _groq_clients
    load_dotenv(ENV_PATH, override=True)
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_API_KEY") or "").strip()

    # 1. Try Groq if key is present
    if groq_key:
        try:
            if groq_key not in _groq_clients:
                _groq_clients[groq_key] = Groq(api_key=groq_key)
            client = _groq_clients[groq_key]

            configured = [m for m in [os.getenv("LLM_MODEL"), os.getenv("LLM_FALLBACK_MODEL")] if m]
            fast_groq_defaults = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

            # Put last working model first for instantaneous response
            all_models = []
            if _working_model and (_working_model in configured or _working_model in fast_groq_defaults):
                all_models.append(_working_model)
            for m in configured + fast_groq_defaults:
                if m not in all_models:
                    all_models.append(m)

            for model in all_models:
                try:
                    kwargs = {
                        "model": model,
                        "temperature": 0.7,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    }
                    if max_tokens:
                        kwargs["max_tokens"] = max_tokens
                    response = client.chat.completions.create(**kwargs)
                    content = response.choices[0].message.content
                    if content and content.strip():
                        _working_model = model
                        return content.strip()
                except Exception as model_err:
                    err_str = str(model_err)
                    if "401" in err_str or "invalid_api_key" in err_str:
                        break  # Key is invalid, proceed to fallback provider
                    continue
        except Exception:
            pass

    # 2. Try OpenAI if key is present
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            for model in ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]:
                try:
                    kwargs = {
                        "model": model,
                        "temperature": 0.7,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    }
                    if max_tokens:
                        kwargs["max_tokens"] = max_tokens
                    response = client.chat.completions.create(**kwargs)
                    content = response.choices[0].message.content
                    if content and content.strip():
                        return content.strip()
                except Exception:
                    continue
        except Exception:
            pass

    if not groq_key and not openai_key:
        return "[LLM unavailable: please set a valid GROQ_API_KEY or OPENAI_API_KEY in your .env file]"
    return "[LLM error: Invalid or expired API Key. Please verify GROQ_API_KEY or OPENAI_API_KEY in your .env file]"


def _platform_guidance(platform: str) -> str:
    guidance = {
        "Instagram": "visually engaging, warm, community-first, optional natural emojis",
        "LinkedIn": "professional, insightful, courteous, business-oriented, polished and constructive",
        "Facebook": "conversational, helpful, friendly, and community-centered",
        "X": "concise, direct, punchy, hook-first, strictly under 280 characters",
        "Twitter": "concise, direct, punchy, hook-first, strictly under 280 characters",
        "Reddit": "authentic, down-to-earth, direct, genuinely helpful, zero corporate jargon or marketing fluff",
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


def recall_context(query: str, budget: str = "low") -> str:
    cache_key = (query.strip().lower(), budget)
    if cache_key in _recall_cache:
        return _recall_cache[cache_key]
    try:
        result = _memory_call("arecall", bank_id=BANK, query=query, budget=budget, max_tokens=1500)
        items = getattr(result, "results", result) or []
        formatted = "\n".join(f"- {_text(item)}" for item in items[:8])
        _recall_cache[cache_key] = formatted
        return formatted
    except Exception as error:
        return f"(memory unavailable: {error})"


def audience_insights(user_email: str = "default") -> str:
    """Analyze memory bank reflections, or synthesize insights via LLM tailored to the active brand."""
    brand = get_brand_profile(user_email)
    brand_name = (brand.get("brand_name") if brand else None) or "Your Brand"
    industry = (brand.get("industry") if brand else None) or "Social Media"
    tone = (brand.get("communication_tone") or brand.get("preferred_tone") if brand else None) or "Engaging and authentic"

    try:
        reflect_res = _memory_call(
            memory.areflect,
            bank_id=BANK,
            budget="high",
            query=f"""Analyze every post, engagement result, community comment, sentiment,
and manager correction stored in this memory bank for {brand_name}. Use the actual evidence in memory,
not generic social media advice.

Return exactly these seven numbered sections:
1. What Audience Likes Most
2. What Audience Dislikes / Ignores
3. Best Post Styles for this audience
4. Best Topics
5. Best Time to Post
6. Community Sentiment Summary
7. 3 Things to do better next time""",
        )
        text_out = _text(reflect_res)
        if text_out and not text_out.startswith("(") and len(text_out) > 40:
            return text_out
    except Exception:
        pass

    # Resilient fallback: synthesize strategic audience insights tailored to this brand's niche
    system = "You are SocialSpark's Audience Intelligence and Cognitive Reflection Engine. Provide actionable, structured audience insights."
    query = (
        f"Analyze audience engagement patterns, sentiment signals, and content preferences for '{brand_name}' ({industry}). "
        f"Brand communication tone: {tone}.\n\n"
        "Generate a structured audience reflection report with exactly these seven numbered sections:\n"
        "1. What Audience Likes Most\n"
        "2. What Audience Dislikes / Ignores\n"
        "3. Best Post Styles for this audience\n"
        "4. Best Topics\n"
        "5. Best Time to Post\n"
        "6. Community Sentiment Summary\n"
        "7. 3 Things to do better next time\n\n"
        "Be specific, insightful, and strategic. Avoid generic filler."
    )
    return chat(system, query)


def analyze_brand_voice(
    brand_name: str,
    brand_description: str,
    industry: str,
    preferred_tone: str,
    previous_posts: str,
    sample_content: str = "",
) -> dict:
    """Analyze writing style, vocabulary, sentence structure, tone, and personality using LLM."""
    if not (brand_name or "").strip():
        return {"error": "Brand name is required."}

    system = (
        "You are an expert brand identity strategist, linguist, and social media copy director. "
        "Analyze the user's brand details, communication tone, historical posts, and sample content "
        "to formulate a comprehensive Brand Voice Memory profile.\n\n"
        "You must analyze and extract:\n"
        "1. Brand Personality: 3 to 5 core persona traits (e.g. 'Warm, Witty, Confident, Empathetic').\n"
        "2. Frequently Used Vocabulary: Key terms, industry keywords, signature verbs, and vocabulary preferences.\n"
        "3. Sentence Structure: Pacing, typical sentence length, phrasing cadence, rhythm, formatting, and emoji/hashtag usage.\n"
        "4. Communication Tone: Emotional resonance, warmth, formality, humor, assertiveness, and audience relationship.\n"
        "5. Preferred Expressions: Signature phrases, opening hooks, transitions, call-to-actions, and sign-offs.\n"
        "6. Brand Voice Summary: A clear, actionable directive (2-3 paragraphs) that guides any AI or writer to speak authentically as this brand.\n\n"
        "Output strictly valid JSON with no markdown backticks, no code block wrapping, and no preamble:\n"
        "{\n"
        '  "personality": "...",\n'
        '  "vocabulary": "...",\n'
        '  "sentence_structure": "...",\n'
        '  "communication_tone": "...",\n'
        '  "preferred_expressions": "...",\n'
        '  "voice_summary": "..."\n'
        "}"
    )

    user_prompt = (
        f"Brand Name: {brand_name}\n"
        f"Industry / Category: {industry or 'General'}\n"
        f"Brand Description: {brand_description or 'Not specified'}\n"
        f"Target / Preferred Tone: {preferred_tone or 'Conversational'}\n\n"
        f"Previous High-Performing Social Media Posts:\n{previous_posts or 'None provided'}\n\n"
        f"Uploaded / Supplementary Sample Content:\n{sample_content or 'None provided'}\n\n"
        "Perform a rigorous linguistic and brand analysis and output the JSON Brand Voice Profile."
    )

    raw_response = chat(system, user_prompt)
    if raw_response.startswith("[LLM"):
        return {"error": raw_response}

    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_response.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        profile_analysis = json.loads(cleaned)
    except Exception:
        personality_match = re.search(r'"personality"\s*:\s*"([^"]+)"', raw_response)
        vocab_match = re.search(r'"vocabulary"\s*:\s*"([^"]+)"', raw_response)
        structure_match = re.search(r'"sentence_structure"\s*:\s*"([^"]+)"', raw_response)
        tone_match = re.search(r'"communication_tone"\s*:\s*"([^"]+)"', raw_response)
        expressions_match = re.search(r'"preferred_expressions"\s*:\s*"([^"]+)"', raw_response)
        summary_match = re.search(r'"voice_summary"\s*:\s*"([^"]+)"', raw_response)

        profile_analysis = {
            "personality": personality_match.group(1) if personality_match else f"{preferred_tone}, Engaging, Authentic",
            "vocabulary": vocab_match.group(1) if vocab_match else "Community-focused, value-driven, conversational",
            "sentence_structure": structure_match.group(1) if structure_match else "Punchy hooks, clear body, concise call-to-action",
            "communication_tone": tone_match.group(1) if tone_match else preferred_tone,
            "preferred_expressions": expressions_match.group(1) if expressions_match else "Friendly openings, actionable questions",
            "voice_summary": summary_match.group(1) if summary_match else raw_response[:300],
        }

    _try_memory_call(
        memory.aretain,
        bank_id=BANK,
        context="brand_voice",
        timestamp=now(),
        content=f'Brand Voice Profile for "{brand_name}" ({industry}): {profile_analysis.get("voice_summary")}. '
                f'Tone: {profile_analysis.get("communication_tone")}. '
                f'Personality: {profile_analysis.get("personality")}. '
                f'Key Vocabulary: {profile_analysis.get("vocabulary")}.'
    )

    return profile_analysis


def draft_post(platform: str, topic: str, use_memory: bool = True, user_email: str = "default") -> dict:
    topic = topic.strip()
    if not topic:
        return {"draft": "[Please enter a topic or subject]", "memory": ""}
    
    brand = get_brand_profile(user_email)
    brand_context = ""
    if brand and brand.get("brand_name"):
        brand_context = (
            f"\n\nACTIVE BRAND VOICE PROFILE FOR {brand['brand_name'].upper()}:\n"
            f"- Brand: {brand['brand_name']} ({brand.get('industry', 'General')})\n"
            f"- Personality Traits: {brand.get('personality', 'Engaging')}\n"
            f"- Communication Tone: {brand.get('communication_tone', brand.get('preferred_tone', 'Conversational'))}\n"
            f"- Sentence Structure & Style: {brand.get('sentence_structure', 'Punchy, engaging')}\n"
            f"- Signature Vocabulary & Keywords: {brand.get('vocabulary', '')}\n"
            f"- Preferred Expressions & Hooks: {brand.get('preferred_expressions', '')}\n"
            f"- Voice Directive: {brand.get('voice_summary', '')}\n"
            f"Always craft this post strictly embodying {brand['brand_name']}'s unique voice and tone."
        )

    if not use_memory:
        system = BASE_SYSTEM + brand_context + f"\n\nPlatform guidance for {platform}: {_platform_guidance(platform)}"
        request = (f"Create a {platform} social media post for this exact user topic:\n"
                   f"{topic}\n\nInclude an engaging caption, suitable hashtags, a call to "
                   "action, and a suggested tone. Output only the finished content.")
        draft = chat(system, request, max_tokens=650)
        if not (brand and "brewline" in brand.get("brand_name", "").lower()):
            draft = _enforce_brand_context(draft, topic, system, request)
        return {"draft": draft, "memory": ""}

    recalled = recall_context(f"Exact topic: {topic}; platform: {platform}; related manager feedback", budget="low")
    system = (BASE_SYSTEM + brand_context + "\n\nUse the memories below only when they directly relate to "
              "the user's exact topic or selected platform. Ignore unrelated memories, "
              "including memories from a different product category or industry. Do not "
              "copy an unrelated brand, product, or theme into this post.\n\n"
              "TOPIC-RELEVANT MEMORIES:\n" + recalled +
              "\n\nApply only relevant lessons and output only the post text in the specified brand voice.")
    request = (f"Create a {platform} social media post for this exact user topic:\n"
               f"{topic}\n\nAddress this topic directly. Include an engaging caption, suitable hashtags, a call to "
               "action, and a suggested tone. Output only the finished content.")
    draft = chat(system, request, max_tokens=650)
    if not (brand and "brewline" in brand.get("brand_name", "").lower()):
        draft = _enforce_brand_context(draft, topic, system, request)
    return {"draft": draft, "memory": recalled}


def draft_reply(platform: str, user: str, comment: str, use_memory: bool = True, user_email: str = "default") -> dict:
    brand = get_brand_profile(user_email)
    brand_context = ""
    if brand and brand.get("brand_name"):
        brand_context = (
            f"\n\nACTIVE BRAND VOICE PROFILE FOR {brand['brand_name'].upper()}:\n"
            f"- Brand Tone: {brand.get('communication_tone', brand.get('preferred_tone', 'Empathetic and conversational'))}\n"
            f"- Personality: {brand.get('personality', 'Friendly')}\n"
            f"- Style & Rhythm: {brand.get('sentence_structure', 'Concise, clear')}\n"
            f"- Signature Expressions: {brand.get('preferred_expressions', '')}\n"
            f"- Voice Directive: {brand.get('voice_summary', '')}\n"
            f"Reply representing {brand['brand_name']} in this authentic brand voice."
        )

    if not use_memory:
        system = BASE_SYSTEM + brand_context
        draft = chat(system, f"Reply to this {platform} comment: {comment}")
        if not (brand and "brewline" in brand.get("brand_name", "").lower()):
            draft = _enforce_brand_context(draft, comment, system, f"Reply to: {comment}")
        return {"draft": draft, "memory": ""}

    recalled = recall_context(f"{user} past interactions, sentiment, issues; {comment}")
    system = (BASE_SYSTEM + brand_context + "\n\nWhat we remember about this person/topic:\n" + recalled +
              "\n\nReference relevant history naturally, match the tone that worked "
              "before, and never repeat a mistake. Keep it under 50 words.")
    request = f'{user} wrote on {platform}: "{comment}". Write our reply.'
    draft = chat(system, request)
    if not (brand and "brewline" in brand.get("brand_name", "").lower()):
        draft = _enforce_brand_context(draft, comment, system, request)
    return {"draft": draft, "memory": recalled}


def analyze_comment(comment: str, platform: str = "Instagram") -> dict:
    """Analyze a social media comment to extract Emotion, Sentiment, Intent, Context, and Requirement."""
    comment = (comment or "").strip()
    if not comment:
        return {"error": "Please enter a comment to analyze."}

    platform_guideline = _platform_guidance(platform)
    system = (
        "You are an expert Social Media Emotional Intelligence and Sentiment Analyst. "
        "Analyze the provided social media comment and identify:\n"
        "1. Emotion: The primary emotional state (e.g., Frustrated, Excited, Skeptical, Delighted, Angry, Neutral, Grateful, Curious, Anxious, Disappointed).\n"
        "2. Sentiment: Exactly one of [Positive, Negative, Neutral, Mixed].\n"
        "3. User intent: Concise description of what the commenter is trying to accomplish.\n"
        "4. Conversation context: Brief situational overview.\n"
        "5. Communication requirement: What the responder needs to do to address this commenter effectively.\n\n"
        "Output strictly valid JSON with no markdown backticks, no code blocks, and no preamble:\n"
        "{\n"
        '  "emotion": "...",\n'
        '  "sentiment": "...",\n'
        '  "intent": "...",\n'
        '  "context": "...",\n'
        '  "requirement": "..."\n'
        "}"
    )

    user_prompt = f"Platform: {platform}\nPlatform Context: {platform_guideline}\nComment:\n\"{comment}\"\n\nIdentify the emotion, sentiment, intent, context, and requirement."
    raw = chat(system, user_prompt)
    if raw.startswith("[LLM"):
        return {"error": raw}

    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        data = json.loads(cleaned)
    except Exception:
        def _extract(key, default=""):
            m = re.search(rf'"{key}"\s*:\s*"((?:\\.|[^"\\])*)"', raw)
            if m:
                return m.group(1).replace(r'\"', '"').replace(r'\n', '\n')
            return default

        data = {
            "emotion": _extract("emotion", "Neutral"),
            "sentiment": _extract("sentiment", "Neutral"),
            "intent": _extract("intent", "General inquiry or feedback"),
            "context": _extract("context", "Social media interaction"),
            "requirement": _extract("requirement", "Polite, constructive reply"),
        }

    return data


def analyze_and_generate_replies(
    comment: str,
    platform: str = "Instagram",
    user_email: str = "default",
    commenter: str = "",
) -> dict:
    """Analyze comment emotion, intent, sentiment, context, and requirement, then generate 3 distinct responses."""
    comment = (comment or "").strip()
    if not comment:
        return {"error": "Please enter a social media comment to analyze and generate replies."}

    brand = get_brand_profile(user_email)
    brand_context = ""
    brand_name = ""
    if brand and brand.get("brand_name"):
        brand_name = brand["brand_name"]
        brand_context = (
            f"\n\nACTIVE BRAND IDENTITY ({brand['brand_name']}):\n"
            f"- Industry: {brand.get('industry', 'General')}\n"
            f"- Personality Traits: {brand.get('personality', 'Engaging, Authentic')}\n"
            f"- Preferred Communication Tone: {brand.get('communication_tone') or brand.get('preferred_tone', 'Warm and approachable')}\n"
            f"- Signature Expressions: {brand.get('preferred_expressions', '')}\n"
            f"- Vocabulary Style: {brand.get('vocabulary', '')}\n"
            f"- Sentence Cadence: {brand.get('sentence_structure', '')}\n"
            f"- Voice Directive: {brand.get('voice_summary', '')}\n"
            f"Represent {brand_name} authentically using this brand voice in all replies."
        )

    platform_guideline = _platform_guidance(platform)

    system = (
        "You are an advanced Cognitive Emotion & Social Engagement Intelligence AI. "
        "Your task is to analyze social media comments, decode underlying emotions, sentiments, "
        "intentions, and communication requirements, and craft three distinct, high-impact responses "
        "tailored to the specific platform and active brand voice.\n\n"
        "You must generate:\n"
        "1. Friendly Response: Warm, approachable, upbeat, conversational, natural emojis if suitable for platform.\n"
        "2. Professional Response: Polished, courteous, articulate, solution-driven, business-appropriate.\n"
        "3. Empathetic Response: Validating feelings, compassionate, high emotional intelligence, acknowledging their perspective before offering next steps.\n\n"
        "Output strictly valid JSON with no markdown code blocks, backticks, or preamble:\n"
        "{\n"
        '  "emotion": "Single dominant emotion (e.g. Frustrated, Excited, Skeptical, Delighted, Angry, Neutral, Grateful, Curious, Anxious)",\n'
        '  "sentiment": "Positive, Negative, Neutral, or Mixed",\n'
        '  "intent": "Concise summary of the commenter\'s underlying goal or intention",\n'
        '  "context": "Brief overview of the conversation context or user situation",\n'
        '  "requirement": "The core communication requirement needed to address this commenter",\n'
        '  "friendly_response": "...",\n'
        '  "professional_response": "...",\n'
        '  "empathetic_response": "..."\n'
        "}"
    )

    user_prompt = (
        f"Selected Platform: {platform}\n"
        f"Platform Style Guidance: {platform_guideline}\n"
        f"Commenter: {commenter or 'Audience Member'}\n"
        f"Comment to Analyze & Respond to:\n\"{comment}\""
        f"{brand_context}\n\n"
        "Perform cognitive analysis and generate the three responses strictly adhering to JSON format."
    )

    raw = chat(system, user_prompt)
    if raw.startswith("[LLM"):
        return {"error": raw}

    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        data = json.loads(cleaned)
    except Exception:
        def _extract(key, default=""):
            m = re.search(rf'"{key}"\s*:\s*"((?:\\.|[^"\\])*)"', raw)
            if m:
                return m.group(1).replace(r'\"', '"').replace(r'\n', '\n')
            return default

        data = {
            "emotion": _extract("emotion", "Neutral"),
            "sentiment": _extract("sentiment", "Neutral"),
            "intent": _extract("intent", "General inquiry or feedback"),
            "context": _extract("context", "Social media interaction"),
            "requirement": _extract("requirement", "Polite and constructive reply"),
            "friendly_response": _extract("friendly_response", ""),
            "professional_response": _extract("professional_response", ""),
            "empathetic_response": _extract("empathetic_response", ""),
        }

    if not data.get("friendly_response") and not data.get("professional_response"):
        return {"error": f"Failed to generate structured replies from LLM output: {raw[:200]}"}

    # Save to SQLite
    data["platform"] = platform
    data["commenter"] = commenter
    data["comment"] = comment
    data["brand_name"] = brand_name
    record_id = save_emotion_reply(data, user_email)
    data["saved_id"] = record_id

    # Log to Hindsight memory bank asynchronously / safely
    _try_memory_call(
        memory.aretain,
        bank_id=BANK,
        context="emotion_reply",
        timestamp=now(),
        content=f'On {platform}, comment: "{comment}" (Emotion: {data.get("emotion")}, Sentiment: {data.get("sentiment")}). '
                f'Generated responses: Friendly="{data.get("friendly_response")[:60]}...", Professional="{data.get("professional_response")[:60]}..."'
    )

    return data