import os
import streamlit as st
import feedparser
from openai import OpenAI
from datetime import datetime

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found. Please set it in your environment variables.")
    st.stop()

client = OpenAI(api_key=api_key)

feeds = {
    "Tech": "https://techcrunch.com/feed/",
    "AI": "https://venturebeat.com/category/ai/feed/",
    "Business": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Healthcare": "https://www.statnews.com/feed/"
}

st.set_page_config(page_title="AI Intelligence Hub", layout="wide")

st.markdown("""
<style>
.typing-title {
    display: inline-block;
    font-size: 3rem;
    font-weight: 700;
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


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_news():
    all_news = []

    for category, url in feeds.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            title = getattr(entry, "title", "No title")
            link = getattr(entry, "link", "#")

            all_news.append({
                "category": category,
                "title": title,
                "link": link
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


if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.markdown('<div class="typing-title">Welcome to AI Intelligence Hub</div>', unsafe_allow_html=True)
st.caption("A multi-industry AI-powered news briefing dashboard")

with st.sidebar:
    st.header("About")
    st.write("This dashboard aggregates multi-industry news and uses AI to generate on-demand summaries.")
    st.write("Categories included:")
    st.write("- Tech")
    st.write("- AI")
    st.write("- Business")
    st.write("- Healthcare")

    if st.button("Refresh News"):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.rerun()

    st.write(f"Last refreshed: {st.session_state.last_refresh}")

with st.spinner("Loading latest news..."):
    news_items = fetch_news()

selected_category = st.selectbox(
    "Choose a category",
    ["All", "Tech", "AI", "Business", "Healthcare"]
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

categories_to_show = ["Tech", "AI", "Business", "Healthcare"]

for category in categories_to_show:
    if selected_category != "All" and selected_category != category:
        continue

    category_news = [item for item in filtered_news if item["category"] == category]

    if not category_news:
        continue

    st.header(category)

    for i, item in enumerate(category_news):
        expander_label = f"{item['title']}"
        with st.expander(expander_label, expanded=False):
            st.markdown(f"[Read full article]({item['link']})")

            button_key = f"summary_{category}_{i}"

            if st.button("Generate Summary", key=button_key):
                with st.spinner("Generating summary..."):
                    summary = summarize_cached(item["title"])
                st.write(summary)