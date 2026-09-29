"""Seed ~3 weeks of realistic history so the agent has memory to learn from."""
from agent import remember_post, remember_interaction, remember_feedback

POSTS = [  # platform, text, likes, comments, shares, timestamp
 ("Instagram", "New Ethiopian Yirgacheffe is here. Notes of blueberry & jasmine. Link in bio.", 210, 8, 4, "2026-08-03T09:00:00Z"),
 ("Instagram", "Behind the scenes: Ravi roasting at 5am. Meet the person behind your morning cup", 1480, 96, 141, "2026-08-05T07:30:00Z"),
 ("Instagram", "20% off all beans this weekend only!!! Shop now", 190, 5, 2, "2026-08-07T14:00:00Z"),
 ("Twitter", "Poll: Oat milk or regular milk in your flat white? Fight in the replies.", 620, 210, 88, "2026-08-08T08:15:00Z"),
 ("Instagram", "Latte art fail compilation - we're not perfect and that's the fun part", 2350, 180, 260, "2026-08-10T07:45:00Z"),
 ("Twitter", "Our new subscription plan launches Monday. Details on our website.", 95, 3, 6, "2026-08-11T15:00:00Z"),
 ("LinkedIn", "How we source beans directly from 14 farms in Coorg & Chikmagalur", 340, 27, 45, "2026-08-12T10:00:00Z"),
 ("Instagram", "Customer story: Priya's 30-day filter coffee journey with us", 1720, 130, 95, "2026-08-14T08:00:00Z"),
 ("Twitter", "Monday mood: coffee first, opinions later.", 780, 64, 110, "2026-08-17T07:50:00Z"),
 ("Instagram", "Introducing our summer cold brew range. Buy now.", 240, 9, 3, "2026-08-18T18:30:00Z"),
]
INTERACTIONS = [
 ("Instagram", "@arjun_k", "My order arrived 4 days late and the beans were stale.", "Sorry Arjun, that's not okay. DM us your order ID and we'll ship a fresh bag free.", "angry"),
 ("Instagram", "@arjun_k", "Thanks, the replacement was great! Fast too.", "So glad it landed well, Arjun! Enjoy the roast.", "positive"),
 ("Twitter", "@meera.reads", "Do you have decaf options? Pregnant and missing coffee :(", "Congratulations Meera! Our Swiss Water decaf is 99.9% caffeine-free and tastes rich. Want a sample?", "neutral"),
 ("Instagram", "@coffeenerd_dev", "Is the Yirgacheffe washed or natural?", "Washed! Bright and tea-like. Happy to share brew ratios.", "curious"),
 ("Twitter", "@sam_brews", "Your subscription is overpriced vs competitors.", "Fair to raise it, Sam. Here's what's included in the price: fresh roast in 48h + free shipping.", "negative"),
]
FEEDBACK = [
 ("post", "Elevate your morning ritual with our artisanal, ethically-sourced small-batch blends!", "rejected", "Too corporate. Our voice is warm, playful, a little self-deprecating. No buzzwords like 'elevate' or 'artisanal'."),
 ("post", "Coffee is life. Buy our beans now! #coffee #buynow", "rejected", "Never hard-sell. Our best posts are stories about people. Max 3 hashtags."),
 ("reply", "We apologize for the inconvenience. Please contact support.", "edited", "Hey Arjun, that's on us. Send your order ID and we'll make it right today."),
 ("post", "Ravi burned his first batch today. We're keeping the smell, losing the beans. Lesson learned.", "approved", None),
]

if __name__ == "__main__":
    for p in POSTS: remember_post(*p[:5], posted_at=p[5])
    for i in INTERACTIONS: remember_interaction(*i)
    for f in FEEDBACK: remember_feedback(*f[:3], edited=f[3] if f[2] != "approved" else None)
    print("Seeded:", len(POSTS), "posts,", len(INTERACTIONS), "interactions,", len(FEEDBACK), "feedback items")
