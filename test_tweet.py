import asyncio
from agents.graph_runner import GraphRunner

async def test():
    runner = GraphRunner("tech")
    try:
        res = await runner.generate_tweet_hook(rank=1, lang="en")
        print("TWEET RESULT:", res)
    except Exception as e:
        print("TWEET EXCEPTION:", repr(e))

if __name__ == "__main__":
    asyncio.run(test())
