def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """Split a long message into Telegram-safe chunks (≤4096 chars)."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        # Split at last newline before limit
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks
