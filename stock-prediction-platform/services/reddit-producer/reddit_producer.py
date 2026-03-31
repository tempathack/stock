"""Reddit PRAW producer — polls r/wallstreetbets, r/stocks, r/investing every 60 seconds.

Extracts S&P 500 ticker mentions from post titles + bodies and publishes to
the reddit-raw Kafka topic as JSON: {post_id, title, body, subreddit, created_utc, tickers}.

Environment variables (from reddit-producer-configmap + reddit-secrets):
    KAFKA_BOOTSTRAP_SERVERS  - e.g. kafka-kafka-bootstrap.storage.svc.cluster.local:9092
    REDDIT_CLIENT_ID         - from reddit-secrets K8s Secret
    REDDIT_CLIENT_SECRET     - from reddit-secrets K8s Secret
    POLL_INTERVAL_SECONDS    - default 60
    POSTS_PER_POLL           - default 25
"""
from __future__ import annotations

import json
import logging
import os
import re
import time

import praw
from confluent_kafka import Producer

from sp500_tickers import BLOCKLIST, SP500_SET

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
TICKER_RE = re.compile(r'\$([A-Z]{1,5})\b')
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
POSTS_PER_POLL = int(os.environ.get("POSTS_PER_POLL", "25"))
REDDIT_TOPIC = "reddit-raw"


def extract_tickers(text: str) -> list[str]:
    """Extract S&P 500 ticker mentions from text using $TICKER and bare uppercase patterns."""
    found: set[str] = set()
    normalized = text or ""
    # Pattern 1: $AAPL style — explicit ticker signal
    for m in TICKER_RE.finditer(normalized):
        t = m.group(1)
        if t in SP500_SET and t not in BLOCKLIST:
            found.add(t)
    # Pattern 2: bare uppercase 1-5 letter words matching S&P 500
    for word in re.findall(r'\b([A-Z]{1,5})\b', normalized):
        if word in SP500_SET and word not in BLOCKLIST:
            found.add(word)
    return sorted(found)


def poll_subreddit(
    reddit: praw.Reddit,
    producer: Producer,
    subreddit_name: str,
    limit: int = POSTS_PER_POLL,
) -> int:
    """Poll subreddit new posts, extract tickers, produce to Kafka. Returns message count."""
    sub = reddit.subreddit(subreddit_name)
    count = 0
    for post in sub.new(limit=limit):
        text = f"{post.title} {post.selftext}"
        tickers = extract_tickers(text)
        if not tickers:
            continue
        record = {
            "post_id": post.id,
            "title": post.title[:500],           # cap at 500 chars
            "body": post.selftext[:2000],         # cap at 2000 chars
            "subreddit": subreddit_name,
            "created_utc": int(post.created_utc),
            "tickers": tickers,
        }
        producer.produce(
            topic=REDDIT_TOPIC,
            key=post.id.encode(),
            value=json.dumps(record).encode(),
        )
        count += 1
    producer.flush()
    return count


def main() -> None:
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.warning("REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set — producer sleeping indefinitely")
        while True:
            time.sleep(3600)

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="stock-sentiment-bot/1.0",
        read_only=True,
    )
    producer = Producer({"bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"]})
    logger.info("Reddit producer started — polling %s subreddits every %ds",
                SUBREDDITS, POLL_INTERVAL)

    while True:
        for sr in SUBREDDITS:
            try:
                n = poll_subreddit(reddit, producer, sr)
                logger.info("polled r/%s: %d messages produced", sr, n)
            except Exception as exc:  # noqa: BLE001
                logger.error("error polling r/%s: %s", sr, exc)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
