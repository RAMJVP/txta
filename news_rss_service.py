import feedparser

RSS_URL = "https://news.google.com/rss/search?q=business+india"

def get_google_business_news(max_results=20):
    feed = feedparser.parse(RSS_URL)

    news_list = []

    for entry in feed.entries[:max_results]:
        news_list.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": entry.get("summary", "")
        })

    return news_list
