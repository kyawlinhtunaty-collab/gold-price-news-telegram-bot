import os
import requests
import feedparser
from google import genai
from google.genai import types

# 1. Broad Financial & Macro RSS Feeds
RSS_FEEDS = [
    "https://www.kitco.com/rss/news",               # Gold & Metals News
    "https://www.investing.com/rss/news_11.rss",    # Commodities & Oil
    "https://www.investing.com/rss/news_25.rss",    # Foreign Exchange (USD / DXY)
    "https://www.investing.com/rss/news_14.rss",    # Bonds & Interest Rates
    "https://cnbc.com/id/10000664/device/rss/rss.html" # World Economy & Inflation
]

def fetch_rss_news():
    news_items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]: # Extract top 2 articles per feed
                news_items.append(f"Title: {entry.title}\nLink: {entry.link}\nSummary: {entry.get('summary', '')[:200]}")
        except Exception as e:
            print(f"Error fetching RSS from {url}: {e}")
    return "\n\n".join(news_items)

def generate_macro_interconnected_report(news_data):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")

    client = genai.Client(api_key=api_key)

    # Directly connected Macro & Intermarket Prompt
    prompt = f"""
    Below is recent market news covering Gold, Oil, US Dollar Index (DXY), US Treasury Bond Yields, and Central Bank Interest Rates:

    {news_data}

    Please synthesize and translate this into a simple, clear, and direct Burmese report for Telegram. 
    Explain how these markets directly connect to each other and impact Gold, without using heavy academic jargon or Ray Dalio persona. Keep the tone natural, news-based, and easy to understand.

    Use standard Telegram HTML tags (<b>, <i>, <a>):

    <b>📰 ယနေ့ ကမ္ဘာ့ရွှေ၊ ရေနံ၊ ဒေါ်လာနှင့် ဘွန်ဒ် ဈေးကွက် ဆက်စပ်မှု သတင်းများ</b>
    <b>🕒 ထုတ်ပြန်ချိန် - [Date and Time in ICT]</b>

    <b>🟡 ၁။ ရွှေဈေးကွက် အခြေအနေ (Gold Market)</b>
    • [Direct summary of current Gold movements and drivers]

    <b>🛢️ ၂။ ရေနံစိမ်းနှင့် စွမ်းအင်ဈေးကွက် (Crude Oil & Energy)</b>
    • [Summary of Oil prices and how energy costs impact overall market/inflation]

    <b>💵 ၃။ အမေရိကန်ဒေါ်လာနှင့် ဘွန်ဒ်အတိုးနှုန်းများ (DXY & US Bond Yields)</b>
    • [Summary of USD Index (DXY) and US 10-Year Bond Yields, and their direct inverse/direct relationship with Gold]

    <b>🌐 ၄။ ဈေးကွက်များ၏ ပေါင်းစပ်သက်ရောက်မှု (Intermarket Impact & Summary)</b>
    • [A brief 2-sentence summary explaining how Oil + USD + Bond Yields combined are moving Gold today]

    <b>🔗 မူရင်း သတင်းလင့်ခ်များ:</b>
    • [Include key news source links provided]
    """

    # Explicit Target Model Setup with Clean Formatting
    target_model = "gemini-3.8-flash"
    
    try:
        available_models = [
            m.name.replace("models/", "") 
            for m in client.models.list() 
            if "2.5" not in m.name and "flash" in m.name.lower()
        ]
        if available_models:
            target_model = available_models[0]
    except Exception as e:
        print(f"Model dynamic listing failed, defaulting to {target_model}: {e}")

    print(f"Using Model: {target_model}")

    response = client.models.generate_content(
        model=target_model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3)
    )

    return response.text

def send_telegram_message(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    res = requests.post(url, json=payload)
    if not res.ok:
        # Fallback to plain text if Telegram HTML parsing fails
        payload["parse_mode"] = None
        requests.post(url, json=payload)

def main():
    news_data = fetch_rss_news()
    report = generate_macro_interconnected_report(news_data)
    send_telegram_message(report)

if __name__ == "__main__":
    main()
