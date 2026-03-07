import os
import feedparser
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found")

client = OpenAI(api_key=api_key)

feeds = {
    "Tech": "https://techcrunch.com/feed/",
    "AI": "https://venturebeat.com/category/ai/feed/",
    "Business": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Healthcare": "https://www.statnews.com/feed/"
}

def summarize(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize this news headline in 2 short sentences."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

for category, url in feeds.items():
    print(f"\n===== {category} News =====\n")

    feed = feedparser.parse(url)

    for entry in feed.entries[:3]:
        title = entry.title
        link = entry.link
        summary = summarize(title)

        print("Title:", title)
        print("Summary:", summary)
        print("Link:", link)
        print("------")