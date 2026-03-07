import feedparser

feeds = {
    "Tech": "https://techcrunch.com/feed/",
    "AI": "https://venturebeat.com/category/ai/feed/",
    "Business": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Startup": "https://www.ycombinator.com/blog/feed",
    "Healthcare": "https://www.statnews.com/feed/",
    "World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
}

for category, url in feeds.items():
    print(f"\n===== {category} News =====\n")

    feed = feedparser.parse(url)

    for entry in feed.entries[:3]:
        print("Title:", entry.title)
        print("Link:", entry.link)
        print("------")