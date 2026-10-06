import html
import os
import re
from datetime import datetime, timezone

import feedparser
import requests

NEWS_RSS_URL = "https://news.google.com/rss/search?q=gold+price+news&hl=en-US&gl=US&ceid=US:en"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK_MODELS = ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash")
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _clean_text(value: str) -> str:
    """Remove markup and normalize whitespace from RSS text."""
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fetch_top_news(limit: int = 3) -> list[dict[str, str]]:
    """Fetch the top gold-price news items from Google News RSS."""
    response = requests.get(NEWS_RSS_URL, timeout=30)
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError("Google News RSS could not be parsed")

    articles = []
    for entry in feed.entries[:limit]:
        source = entry.get("source", {})
        source_name = source.get("title", "Google News") if hasattr(source, "get") else "Google News"
        articles.append(
            {
                "title": _clean_text(entry.get("title", "Untitled")),
                "summary": _clean_text(entry.get("summary", "")),
                "source": _clean_text(source_name),
                "published": _clean_text(entry.get("published", "")),
                "link": entry.get("link", ""),
            }
        )

    if not articles:
        raise RuntimeError("No gold-price news items were returned by Google News RSS")
    return articles


def summarize_in_burmese(articles: list[dict[str, str]]) -> str:
    """Use Gemini to produce a concise, professional Burmese market summary."""
    api_key = os.environ["GEMINI_API_KEY"]
    article_text = "\n\n".join(
        f"[{index}] {item['title']}\nSource: {item['source']}\n"
        f"Published: {item['published']}\nSummary: {item['summary']}"
        for index, item in enumerate(articles, start=1)
    )
    prompt = f"""You are a professional commodities-market editor.
Analyze the three latest global gold-price news items below and write a clean Burmese-language update.

Requirements:
- Write exactly 3 concise bullet points, one for each article.
- Each bullet must explain the main development, its likely effect on gold prices, and the key market factor (such as US dollar, interest rates, inflation, central-bank buying, geopolitics, or safe-haven demand) when supported by the source.
- Use natural, professional Myanmar Burmese. Keep commonly understood financial terms such as Gold, USD, Fed, and Treasury yields in English when clearer.
- Do not invent prices, causes, forecasts, or facts not present in the supplied items.
- Do not include Markdown headings, URLs, citations, or HTML tags. Start every line with a simple dash.

News items:
{article_text}
"""
    response_text = None
    last_error = None
    for model_name in (GEMINI_MODEL, *GEMINI_FALLBACK_MODELS):
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=60,
            )
            if response.status_code == 404:
                last_error = RuntimeError(f"Gemini model unavailable: {model_name}")
                continue
            response.raise_for_status()
            payload = response.json()
            parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            response_text = "".join(part.get("text", "") for part in parts).strip()
            if response_text:
                break
            last_error = RuntimeError(f"Gemini returned no text for model: {model_name}")
        except requests.RequestException as error:
            last_error = error
    if not response_text:
        raise RuntimeError("No configured Gemini model is available") from last_error
    text = response_text
    if not text:
        raise RuntimeError("Gemini returned an empty Burmese summary")

    # Normalize the model's bullets before embedding the content in Telegram HTML.
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
        if line:
            lines.append(f"• {html.escape(line)}")
    if not lines:
        raise RuntimeError("Gemini returned no usable summary lines")
    return "\n".join(lines[:3])


def build_message(articles: list[dict[str, str]], summary: str) -> str:
    """Build a Telegram-safe HTML message with the summary and source links."""
    date_text = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sources = "\n".join(
        f"• <a href=\"{html.escape(item['link'], quote=True)}\">"
        f"{html.escape(item['source'] or item['title'])}</a>"
        for item in articles
        if item.get("link")
    )
    return (
        "<b>🪙 နေ့စဉ် ရွှေဈေးကွက်သတင်း</b>\n"
        f"<i>{date_text}</i>\n\n"
        f"{summary}\n\n"
        "<b>သတင်းရင်းမြစ်များ</b>\n"
        f"{sources}"
    )


def send_to_telegram(message: str) -> None:
    """Send the formatted update to the configured Telegram chat."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    response = requests.post(
        TELEGRAM_API_URL.format(token=token),
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def main() -> None:
    articles = fetch_top_news(limit=3)
    summary = summarize_in_burmese(articles)
    message = build_message(articles, summary)
    send_to_telegram(message)
    print(f"Delivered a Burmese gold-price update based on {len(articles)} articles.")


if __name__ == "__main__":
    main()
