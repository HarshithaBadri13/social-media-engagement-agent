<<<<<<< HEAD
# ✨ SocialSpark Social Media Engagement Agent

An agent that learns YOUR audience: which post styles, topics and timings work, how the community
feels, and what the manager keeps correcting, then applies it to every draft.

## Hindsight usage
| Op | Where | Purpose |
|---|---|---|
| `retain` | post results, comment threads, approve/edit/reject feedback | build long-term memory |
| `recall` | `draft_post`, `draft_reply` | pull relevant history (customer, topic, platform) |
| `reflect` | `audience_insights` | synthesize patterns ("stories beat hard-sells 8x") |

UI shows **Without memory vs With memory** side by side, the demo money shot.

## Run
```bash
py -m pip install -r requirements.txt
cp .env.example .env      # add keys (promo MEMHACK99 for Hindsight Cloud credits)
py seed_data.py           # ~3 weeks of synthetic history (optional)
py -m streamlit run frontend/app.py
```

Set `GROQ_API_KEY` in `.env`. The Topic field accepts any user-entered subject; there is
no predefined topic list. The backend sends the selected platform and topic directly to
Groq, while Hindsight continues to provide the memory-powered comparison.

The Streamlit frontend lives in `frontend/app.py`; Hindsight and LLM integration lives in
`backend/agent.py`. The root `app.py` and `agent.py` files remain compatibility entry points.

## 60-second demo script
1. Generate any topic: the left draft is generic, while the right uses relevant memory.
2. Reply to `@arjun_k` ("late AGAIN"): agent recalls his previous late order + free replacement.
3. Edit a draft, Approve, regenerate: the correction shows up next time.
4. Insights tab: reflect summarizes the learning curve.
=======
# social-media-engagement-agent
>>>>>>> f3ce71940df95e888c73a4bcede02a834134f5bc
