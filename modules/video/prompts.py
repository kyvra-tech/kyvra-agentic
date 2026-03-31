def build_caption_prompt(title: str, description: str, transcript: str, platform: str = "tiktok") -> str:
    platform_note = {
        "tiktok": "TikTok (max 2200 chars, lots of hashtags)",
        "reels": "Instagram Reels (max 2200 chars, moderate hashtags)",
        "shorts": "YouTube Shorts (max 5000 chars, more detailed description)",
    }.get(platform, "TikTok/Reels")

    transcript_section = f"\nVideo transcript/content:\n{transcript[:3000]}" if transcript.strip() else ""
    description_section = f"\nOriginal description:\n{description[:500]}" if description.strip() else ""

    return f"""You are a viral social media caption expert writing for an English-speaking audience.

Video info:
Title: {title}{description_section}{transcript_section}

Platform: {platform_note}

Write an English caption in this format:

🪝 **HOOK** (1-2 opening lines that stop the scroll — curiosity, shock, or FOMO)

📖 **BODY** (2-4 lines of storytelling that deliver the core value of the video)

💡 **INSIGHT** (1-2 lines of a takeaway or lesson)

🔥 **CTA** (call to action: like, comment, follow, save)

**HASHTAGS** (10-15 hashtags, mix of trending + niche, English only)

Rules:
- Write entirely in English
- Hook must be punchy and create curiosity or urgency
- Sound like a real person, not a robot
- Optimized for {platform_note.split('(')[0].strip()} algorithm
"""


def build_multi_caption_prompt(title: str, description: str, transcript: str) -> str:
    transcript_section = f"\nVideo transcript/content:\n{transcript[:3000]}" if transcript.strip() else ""
    description_section = f"\nOriginal description:\n{description[:500]}" if description.strip() else ""

    return f"""You are a viral social media caption expert writing for an English-speaking audience.

Video info:
Title: {title}{description_section}{transcript_section}

Write 3 caption versions for different platforms:

---
📱 **TIKTOK / REELS** (short, strong hook, lots of hashtags)

🪝 Hook:
[1-2 lines of powerful curiosity/shock]

📖 Body:
[2-3 lines of storytelling]

🔥 CTA:
[call to action]

#hashtag1 #hashtag2 ... (15 hashtags)

---
📺 **YOUTUBE SHORTS** (more detailed, explains value clearly)

[150-200 word caption, SEO keywords, hashtags]

---
🐦 **TWITTER/X HOOK** (1 compelling tweet to drive to the video)

[1 tweet <= 280 chars, extremely compelling]

---

Write everything in English. Sound natural like a real creator, not AI-generated.
"""
