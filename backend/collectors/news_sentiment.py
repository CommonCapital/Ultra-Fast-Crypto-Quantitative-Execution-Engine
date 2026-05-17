import asyncio
import html
import json
import logging
import re
import xml.etree.ElementTree as ET
import httpx

logger = logging.getLogger(__name__)

# Institutional NLP Keyword Weights
BEARISH_KEYWORDS = {
    "hack": -40, "war": -50, "lawsuit": -35, "sec": -20, "rate hike": -40, "investigation": -35,
    "bankrupt": -50, "crash": -45, "dump": -30, "collapse": -50, "panic": -35, "liquidation": -30,
    "subpoena": -30, "sanctions": -45, "tension": -25, "missile": -50, "emergency": -40, "outage": -30,
    "lose": -20, "losing": -20, "bearish": -25, "fraud": -45, "prison": -40, "charge": -35
}

BULLISH_KEYWORDS = {
    "etf approval": 50, "rate cut": 45, "partnership": 30, "stimulus": 40, "integration": 25,
    "surge": 30, "breakout": 35, "all-time high": 40, "ath": 35, "adoption": 30, "milestone": 20,
    "bullish": 25, "inflow": 30, "accumulate": 25, "launch": 25, "upgrade": 20, "record high": 35,
    "win": 25, "recovers": 20, "gain": 25, "rally": 30, "soars": 35, "soar": 35, "pump": 25
}

# Flawless Google News RSS aggregators for Crypto and Macro Geopolitics (strictly limited to the last 24 hours)
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=cryptocurrency+bitcoin+ethereum+solana+when:24h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=geopolitics+global+economy+fed+interest+rates+when:24h&hl=en-US&gl=US&ceid=US:en"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def fetch_rss_feed(client: httpx.AsyncClient, url: str) -> list:
    headlines = []
    try:
        response = await client.get(url, headers=HEADERS, timeout=10.0, follow_redirects=True)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            for item in root.findall(".//item")[:10]: # Top 10 per feed
                title_elem = item.find("title")
                desc_elem = item.find("description")
                link_elem = item.find("link")
                pubdate_elem = item.find("pubDate")
                
                title = title_elem.text if title_elem is not None else ""
                desc = desc_elem.text if desc_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                pubdate = pubdate_elem.text if pubdate_elem is not None else ""
                
                # Clean html tags
                clean_title = html.unescape(re.sub(r'<[^>]+>', '', title))
                clean_desc = html.unescape(re.sub(r'<[^>]+>', '', desc))
                clean_pubdate = pubdate.replace(" GMT", "").replace(" +0000", "") if pubdate else "Just now"
                
                if clean_title:
                    headlines.append({"title": clean_title, "summary": clean_desc, "link": link, "pubdate": clean_pubdate})
    except Exception as e:
        logger.warning(f"Error fetching RSS {url}: {e}")
    return headlines

async def start_news_sentiment_collector(redis_client, pairs):
    """Periodically fetches macro/news RSS and calculates aggregate sentiment score."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                all_headlines = []
                for feed_url in RSS_FEEDS:
                    items = await fetch_rss_feed(client, feed_url)
                    all_headlines.extend(items)
                
                total_score = 0
                keyword_hits = []
                
                # Evaluate NLP Keywords across all fetched headlines with exact word boundaries
                for item in all_headlines:
                    text = (item["title"] + " " + item["summary"]).lower()
                    
                    for kw, weight in BEARISH_KEYWORDS.items():
                        if re.search(r'\b' + re.escape(kw) + r'\b', text):
                            total_score += weight
                            keyword_hits.append(f"🚨 {kw.upper()} ({weight})")
                            
                    for kw, weight in BULLISH_KEYWORDS.items():
                        if re.search(r'\b' + re.escape(kw) + r'\b', text):
                            total_score += weight
                            keyword_hits.append(f"🚀 {kw.upper()} (+{weight})")
                
                # Normalize total score between -100 (Severe Fear/Risk) and +100 (Extreme Greed/Bullish)
                normalized_score = min(100, max(-100, total_score))
                
                status_class = "Neutral"
                if normalized_score >= 50: status_class = "Strong Bullish"
                elif normalized_score >= 20: status_class = "Bullish"
                elif normalized_score <= -50: status_class = "Severe Risk"
                elif normalized_score <= -20: status_class = "Bearish"
                
                # Return top 10 unique articles with full metadata and links
                seen = set()
                top_articles = []
                for h in all_headlines:
                    if h["title"] not in seen:
                        seen.add(h["title"])
                        top_articles.append({
                            "title": h["title"],
                            "link": h["link"],
                            "summary": h["summary"][:140] + "..." if len(h["summary"]) > 140 else h["summary"],
                            "pubdate": h.get("pubdate", "Just now")
                        })
                        if len(top_articles) >= 10:
                            break
                
                payload = {
                    "score": round(normalized_score),
                    "status": status_class,
                    "keyword_hits": list(set(keyword_hits))[:8], # top 8 unique hits
                    "top_headlines": top_articles
                }
                
                redis_client.set("global:macro_sentiment", json.dumps(payload))
                logger.info(f"Macro Sentiment Updated: {normalized_score} ({status_class}) - {len(top_articles)} headlines cached")
                
            except Exception as e:
                logger.error(f"Macro news collector error: {e}")
                
            await asyncio.sleep(60) # Run every 60 seconds
