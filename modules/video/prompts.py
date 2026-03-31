def build_twitter_caption_prompt(title: str, description: str, transcript: str, url: str) -> str:
    description_section = f"\nDescription: {description[:500]}" if description.strip() else ""
    transcript_section = f"\nTranscript: {transcript[:2000]}" if transcript.strip() else ""

    return f"""You are a viral Twitter/X content writer.

Media info:
Title: {title}{description_section}{transcript_section}
URL: {url}

Write exactly 1 tweet (max 280 characters total including the URL) that:
- Opens with a bold claim, surprising fact, or FOMO trigger
- Makes someone stop scrolling and want to watch
- Ends with the URL on its own line
- Includes 2-3 relevant hashtags inline

Output ONLY the tweet text. No explanation, no label, no quotes.
"""
