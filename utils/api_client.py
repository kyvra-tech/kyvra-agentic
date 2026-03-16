import logging
import httpx
import feedparser
from bs4 import BeautifulSoup
from modules.base import DataSource, RawItem
from utils.cache import cache

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KyvraBot/1.0; +https://kyvra.ai)"
}


async def fetch_rss(source: DataSource) -> list[RawItem]:
    cached = cache.get(f"rss:{source.url}")
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(source.url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

        items = []
        for entry in feed.entries[:10]:
            items.append(RawItem(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=source.name,
                published_at=entry.get("published", entry.get("updated", "")),
                summary=entry.get("summary", "")[:500],
                authority_score=source.authority_score,
            ))
        cache.set(f"rss:{source.url}", items)
        return items
    except Exception as e:
        logger.warning(f"RSS fetch failed for {source.name}: {e}")
        return []


async def fetch_hackernews(source: DataSource) -> list[RawItem]:
    cached = cache.get("hn:top")
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(source.url)
            story_ids = resp.json()[:source.params.get("limit", 30)]

            items = []
            for story_id in story_ids:
                try:
                    story_resp = await client.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    )
                    story = story_resp.json()
                    if not story or story.get("type") != "story":
                        continue
                    items.append(RawItem(
                        title=story.get("title", ""),
                        url=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        source=source.name,
                        published_at=str(story.get("time", "")),
                        summary="",
                        score=story.get("score", 0),
                        comments=story.get("descendants", 0),
                        authority_score=source.authority_score,
                    ))
                except Exception:
                    continue

        cache.set("hn:top", items)
        return items
    except Exception as e:
        logger.warning(f"HackerNews fetch failed: {e}")
        return []


async def fetch_github_trending(source: DataSource) -> list[RawItem]:
    cached = cache.get("github:trending")
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(source.url)
            soup = BeautifulSoup(resp.text, "lxml")

        items = []
        for repo in soup.select("article.Box-row")[:15]:
            name_tag = repo.select_one("h2 a")
            if not name_tag:
                continue
            repo_path = name_tag.get("href", "").lstrip("/")
            desc_tag = repo.select_one("p")
            stars_tag = repo.select_one("span.d-inline-block.float-sm-right")

            stars_today = 0
            if stars_tag:
                stars_text = stars_tag.get_text(strip=True).replace(",", "").split()[0]
                try:
                    stars_today = int(stars_text)
                except ValueError:
                    pass

            items.append(RawItem(
                title=repo_path,
                url=f"https://github.com/{repo_path}",
                source=source.name,
                published_at="",
                summary=desc_tag.get_text(strip=True) if desc_tag else "",
                score=stars_today,
                authority_score=source.authority_score,
            ))

        cache.set("github:trending", items)
        return items
    except Exception as e:
        logger.warning(f"GitHub trending fetch failed: {e}")
        return []


async def fetch_x_search(source: DataSource) -> list[RawItem]:
    from config import X_BEARER_TOKEN
    if not X_BEARER_TOKEN:
        logger.warning(f"X_BEARER_TOKEN not set, skipping {source.name}")
        return []

    query = source.params.get("query", "")
    max_results = source.params.get("max_results", 10)
    cache_key = f"x:{source.name}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        headers = {**HEADERS, "Authorization": f"Bearer {X_BEARER_TOKEN}"}
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,author_id,text",
            "expansions": "author_id",
            "user.fields": "username,name",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        tweets = data.get("data", [])
        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        items = []
        for tweet in tweets:
            author = users.get(tweet.get("author_id", ""), {})
            username = author.get("username", "unknown")
            metrics = tweet.get("public_metrics", {})
            text = tweet.get("text", "")
            tweet_id = tweet.get("id", "")
            items.append(RawItem(
                title=text[:280],
                url=f"https://x.com/{username}/status/{tweet_id}",
                source=source.name,
                published_at=tweet.get("created_at", ""),
                summary=text,
                score=metrics.get("like_count", 0),
                comments=metrics.get("reply_count", 0),
                authority_score=source.authority_score,
            ))

        cache.set(cache_key, items)
        logger.info(f"[X] {source.name}: fetched {len(items)} tweets")
        return items
    except Exception as e:
        logger.warning(f"X search failed for {source.name}: {e}")
        return []


async def fetch_source(source: DataSource) -> list[RawItem]:
    if source.source_type == "rss":
        return await fetch_rss(source)
    elif source.source_type == "rest" and source.name == "HackerNews":
        return await fetch_hackernews(source)
    elif source.source_type == "scrape" and source.name == "GitHub Trending":
        return await fetch_github_trending(source)
    elif source.source_type == "x":
        return await fetch_x_search(source)
    else:
        logger.warning(f"No fetcher for source: {source.name} ({source.source_type})")
        return []
