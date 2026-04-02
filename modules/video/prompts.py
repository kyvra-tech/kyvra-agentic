def build_twitter_caption_prompt(title: str, description: str, transcript: str, url: str) -> str:
    description_section = f"\nDescription:\n{description[:3000]}" if description.strip() else ""
    transcript_section = f"\nTranscript:\n{transcript[:3000]}" if transcript.strip() else ""

    return f"""You are a viral Twitter/X content writer.

Media info:
Title: {title}{description_section}{transcript_section}
URL: {url}

Read all the context above carefully. Use the most compelling detail, stat, or insight from the description/transcript — not just the title.

Write exactly 1 tweet (max 280 characters total including the URL) that:
- Opens with a bold claim, surprising fact, or FOMO trigger drawn from the content
- Makes someone stop scrolling and want to watch/read
- Ends with the URL on its own line
- Includes 2-3 relevant hashtags inline

Output ONLY the tweet text. No explanation, no label, no quotes.
"""
