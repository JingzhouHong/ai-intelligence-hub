import os
import re
from datetime import datetime

import feedparser
import requests
import streamlit as st
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found. Please set it in your environment variables.")
    st.stop()

client = OpenAI(api_key=api_key)

feeds = {
    "Tech": "https://techcrunch.com/feed/",
    "Business": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Healthcare": "https://www.statnews.com/feed/",
    "World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
}

st.set_page_config(page_title="AI Intelligence Hub", layout="wide")

st.markdown("""
<style>
.typing-title {
    display: inline-block;
    font-size: 3rem;
    font-weight: 800;
    color: #111827;
    white-space: nowrap;
    overflow: hidden;
    border-right: 3px solid #111827;
    width: 0;
    animation:
        typing-cycle 8.5s steps(30, end) infinite,
        blink-caret 0.8s step-end infinite;
    margin-bottom: 0.25rem;
}

@keyframes typing-cycle {
    0%   { width: 0; }
    18%  { width: 29ch; }
    62%  { width: 29ch; }
    82%  { width: 0; }
    100% { width: 0; }
}

@keyframes blink-caret {
    50% { border-color: transparent; }
}

.section-title {
    margin-top: 1.4rem;
    margin-bottom: 0.8rem;
    font-size: 2rem;
    font-weight: 800;
    color: #111827;
}

.news-title {
    margin-top: 0.2rem;
    margin-bottom: 0.6rem;
    line-height: 1.4;
}

.news-title a {
    color: #1d4ed8 !important;
    text-decoration: none !important;
    font-weight: 800;
    font-size: 1.2rem;
}

.news-title a:hover {
    text-decoration: underline !important;
}

.news-meta {
    color: #6b7280;
    font-size: 0.95rem;
    margin-bottom: 0.45rem;
}

.summary-box {
    background: #f3f4f6;
    border-radius: 12px;
    padding: 12px 14px;
    color: #374151;
    font-size: 0.96rem;
    line-height: 1.6;
    margin-top: 10px;
    margin-bottom: 10px;
}

.link-line {
    margin-top: 0.35rem;
}

.link-line a {
    color: #2563eb !important;
    text-decoration: none !important;
    font-weight: 600;
}

.link-line a:hover {
    text-decoration: underline !important;
}

.stButton > button {
    border-radius: 12px !important;
    border: 1px solid #d1d5db !important;
    background: white !important;
    color: #111827 !important;
    font-weight: 600 !important;
}

.back-top-link {
    position: fixed;
    right: 18px;
    bottom: 18px;
    width: 42px;
    height: 42px;
    border-radius: 999px;
    background: rgba(255,255,255,0.96);
    color: #111827 !important;
    border: 1px solid #d1d5db;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none !important;
    font-size: 20px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    z-index: 9999;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def summarize_cached(title: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Summarize this news headline in 2 short, clear, professional sentences."
            },
            {
                "role": "user",
                "content": title
            }
        ]
    )
    return response.choices[0].message.content


def _extract_img_from_html(html: str) -> str | None:
    if not html:
        return None

    og_match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )
    if og_match:
        return og_match.group(1)

    og_match_2 = re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        html,
        re.IGNORECASE
    )
    if og_match_2:
        return og_match_2.group(1)

    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if img_match:
        return img_match.group(1)

    return None


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_og_image(article_url: str) -> str | None:
    if not article_url or article_url == "#":
        return None

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(article_url, headers=headers, timeout=8)
        if response.status_code == 200:
            return _extract_img_from_html(response.text)
    except Exception:
        return None

    return None


def extract_image(entry) -> str | None:
    if hasattr(entry, "media_content") and entry.media_content:
        for media in entry.media_content:
            url = media.get("url")
            if url:
                return url

    if hasattr(entry, "links") and entry.links:
        for link in entry.links:
            link_type = link.get("type", "")
            href = link.get("href")
            if href and link_type.startswith("image"):
                return href

    summary_html = getattr(entry, "summary", "") or getattr(entry, "description", "")
    image_from_summary = _extract_img_from_html(summary_html)
    if image_from_summary:
        return image_from_summary

    entry_link = getattr(entry, "link", "")
    og_image = fetch_og_image(entry_link)
    if og_image:
        return og_image

    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            url = media.get("url")
            if url:
                return url

    return None


def format_published(entry) -> str:
    published = getattr(entry, "published", "")
    if published:
        return published

    published_parsed = getattr(entry, "published_parsed", None)
    if published_parsed:
        try:
            return datetime(*published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "Latest update"

    updated = getattr(entry, "updated", "")
    if updated:
        return updated

    return "Latest update"


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_news():
    all_news = []

    for category, url in feeds.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            title = getattr(entry, "title", "No title")
            link = getattr(entry, "link", "#")
            published = format_published(entry)
            image = extract_image(entry)

            all_news.append({
                "category": category,
                "title": title,
                "link": link,
                "published": published,
                "image": image
            })

    return all_news


def answer_question(question: str, context: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI news research assistant. "
                    "Answer only based on the provided news context. "
                    "If the answer is not in the context, say you don't see enough information. "
                    "Be concise, structured, and professional."
                )
            },
            {
                "role": "user",
                "content": f"News context:\n{context}\n\nQuestion:\n{question}"
            }
        ]
    )
    return response.choices[0].message.content


def summary_state_key(item: dict) -> str:
    return f"summary_{item['category']}_{item['title']}"


def render_summary_block(item: dict, button_key: str):
    state_key = summary_state_key(item)

    if st.button("Generate Summary", key=button_key):
        with st.spinner("Generating summary..."):
            st.session_state[state_key] = summarize_cached(item["title"])

    if state_key in st.session_state:
        st.markdown(
            f"<div class='summary-box'>{st.session_state[state_key]}</div>",
            unsafe_allow_html=True
        )


def render_featured_card(item: dict, idx: int):
    with st.container(border=True):
        if item["image"]:
            st.image(item["image"], use_container_width=True)

        st.markdown(
            f"<div class='news-meta'>{item['category']} · {item['published']}</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div class='news-title'><a href='{item['link']}' target='_blank'>{item['title']}</a></div>",
            unsafe_allow_html=True
        )

        render_summary_block(item, button_key=f"featured_summary_{item['category']}_{idx}")

        st.markdown(
            f"<div class='link-line'><a href='{item['link']}' target='_blank'>Read full article ↗</a></div>",
            unsafe_allow_html=True
        )


def render_small_card(item: dict, idx: int):
    with st.container(border=True):
        if item["image"]:
            st.image(item["image"], use_container_width=True)

        st.markdown(
            f"<div class='news-meta'>{item['category']} · {item['published']}</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div class='news-title'><a href='{item['link']}' target='_blank'>{item['title']}</a></div>",
            unsafe_allow_html=True
        )

        render_summary_block(item, button_key=f"card_summary_{item['category']}_{idx}")

        st.markdown(
            f"<div class='link-line'><a href='{item['link']}' target='_blank'>Read full article ↗</a></div>",
            unsafe_allow_html=True
        )


if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.markdown("""
<div id="top-anchor"></div>
<a href="#top-anchor" class="back-top-link">↑</a>
""", unsafe_allow_html=True)

st.markdown("""
<div class="typing-title">Welcome to AI Intelligence Hub</div>
<div style="color:#6b7280; font-size:1rem; margin-bottom: 1.2rem;">
    A multi-industry AI-powered news briefing dashboard
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### About")
    st.write("This dashboard aggregates multi-industry news and uses AI to generate on-demand summaries.")
    st.write("Categories included:")
    st.markdown("""
    - Tech
    - Business
    - Healthcare
    - World
    """)

    if st.button("Refresh News"):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.rerun()

    st.write(f"Last refreshed: {st.session_state.last_refresh}")

with st.spinner("Loading latest news..."):
    news_items = fetch_news()

selected_category = st.selectbox(
    "Choose a category",
    ["All", "Tech", "Business", "Healthcare", "World"]
)

search_keyword = st.text_input("Search by keyword")

st.subheader("Ask AI")
user_question = st.text_input("Ask a question about today's news:")

filtered_news = news_items

if selected_category != "All":
    filtered_news = [item for item in filtered_news if item["category"] == selected_category]

if search_keyword:
    filtered_news = [
        item for item in filtered_news
        if search_keyword.lower() in item["title"].lower()
    ]

if user_question:
    full_context = "\n\n".join(
        [
            f"Category: {item['category']}\nTitle: {item['title']}\nLink: {item['link']}"
            for item in filtered_news
        ]
    )

    with st.spinner("Thinking..."):
        answer = answer_question(user_question, full_context)

    st.markdown("### AI Answer")
    st.write(answer)

categories_to_show = ["Tech", "Business", "Healthcare", "World"]

for category in categories_to_show:
    if selected_category != "All" and selected_category != category:
        continue

    category_news = [item for item in filtered_news if item["category"] == category]

    if not category_news:
        continue

    st.markdown(f"<div class='section-title'>{category}</div>", unsafe_allow_html=True)

    featured = category_news[0]
    render_featured_card(featured, 0)

    remaining = category_news[1:5]
    if remaining:
        cols = st.columns(2)
        for idx, item in enumerate(remaining):
            with cols[idx % 2]:
                render_small_card(item, idx + 1)