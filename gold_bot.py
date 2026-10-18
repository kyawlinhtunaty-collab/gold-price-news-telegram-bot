import os
import time
import requests
import feedparser
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

# 1. Combined Master RSS Feeds (Original Specialist Feeds + Google News Aggregator)
RSS_FEEDS = [
    # --- Original Specialist Feeds ---
    "https://www.kitco.com/rss/news",               # Kitco Gold & Metals
    "https://www.investing.com/rss/news_11.rss",    # Investing.com Commodities & Oil
    "https://www.investing.com/rss/news_25.rss",    # Investing.com Foreign Exchange (USD / DXY)
    "https://www.investing.com/rss/news_14.rss",    # Investing.com Bonds & Interest Rates
    "https://cnbc.com/id/10000664/device/rss/rss.html", # CNBC World Economy & Inflation
    
    # --- Google News Search Aggregators ---
    "https://news.google.com/rss/search?q=Gold+price+market+news&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Crude+Oil+price+market+news&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+Dollar+Index+DXY&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+Treasury+Bond+Yields&hl=en-US&gl=US&ceid=US:en"
]

def fetch_all_master_news():
    news_items = []
    seen_titles = set()  # Duplication preventer
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            # Fetch top 3 headlines from each feed to ensure ALL useful news is captured
            for entry in feed.entries[:3]:
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                pubDate = entry.get('published', '').strip()
                summary = entry.get('summary', '')[:250].strip()
                
                # Filter duplicates based on similar titles
                title_key = title.lower()[:30]
                if title_key not in seen_titles and title:
                    seen_titles.add(title_key)
                    news_items.append(
                        f"Headline: {title}\nPublished: {pubDate}\nSummary: {summary}\nLink: {link}"
                    )
        except Exception as e:
            print(f"Error fetching RSS from {url}: {e}")
            
    return "\n\n---\n\n".join(news_items)

def generate_macro_interconnected_report(news_data):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")

    client = genai.Client(api_key=api_key)

    # Prompt demanding ALL useful headlines to be processed without skipping
    prompt = f"""
    Below is a full master collection of recent market news from Kitco, Investing.com, CNBC, and Google News covering Gold, Crude Oil, US Dollar Index (DXY), and US Treasury Bond Yields:

    {news_data}

    YOUR INSTRUCTIONS:
    1. Extract and process ALL useful and meaningful news headlines provided above without leaving key market facts out.
    2. Translate and summarize them into clear, accurate, direct, and complete Burmese for Telegram.
    3. Clearly explain how Crude Oil, US Dollar, and Bond Yields directly connect to each other and drive Gold prices today.
    4. Keep the tone professional, news-oriented, natural, and easy to read.

    Format the output for Telegram using HTML formatting (<b>, <i>, <a>):

    <b>📰 ကမ္ဘာ့ရွှေ၊ ရေနံ၊ ဒေါ်လာနှင့် ဘွန်ဒ် ဈေးကွက် သတင်း အပြည့်အစုံ စုစည်းမှု</b>
    <b>🕒 ထုတ်ပြန်ချိန် - [Date and Time in ICT]</b>

    <b>🟡 ၁။ ရွှေဈေးကွက် အခြေအနေ သတင်းများ (Gold Market Updates)</b>
    • [Comprehensive bullet points covering ALL key gold headlines]

    <b>🛢️ ၂။ ရေနံစိမ်းနှင့် စွမ်းအင်ဈေးကွက် သတင်းများ (Crude Oil & Energy Updates)</b>
    • [Comprehensive bullet points covering ALL key oil headlines]

    <b>💵 ၃။ အမေရိကန်ဒေါ်လာနှင့် ဘွန်ဒ်အတိုးနှုန်း သတင်းများ (DXY & US Bond Yields)</b>
    • [Comprehensive bullet points covering DXY and US Treasury Bond headlines]

    <b>🌐 ၄။ ဈေးကွက်များ ပေါင်းစပ်သက်ရောက်မှု (Intermarket Impact & Summary)</b>
    • [A 2-3 sentence summary explaining how Oil + USD + Bond Yields combined are moving Gold today]

    <b>🔗 မူရင်း သတင်းလင့်ခ်များ:</b>
    • [List top official news source links provided in the data]
    """

    candidate_models = ["gemini-3.8-flash", "gemini-3.8-lite"]
    
    for model_name in candidate_models:
        max_retries = 15  # Up to 15 retries for 503 high demand handling
        
        print(f"--- Attempting execution with model: {model_name} ---")
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Attempt {attempt}/{max_retries} for {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2)
                )
                print(f"✅ Success on attempt {attempt} using {model_name}!")
                return response.text
            except (ServerError, APIError) as e:
                print(f"⚠️ 503 / API Error on {model_name} (Attempt {attempt}): {e}")
                if attempt < max_retries:
                    wait_time = min(5 + (attempt * 2), 15)
                    print(f"⏳ Waiting {wait_time} seconds before next retry...")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"Unexpected error on {model_name}: {e}")
                break

    raise RuntimeError("All candidate models failed after 15 retries due to heavy server demand.")

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
    news_data = fetch_all_master_news()
    report = generate_macro_interconnected_report(news_data)
    send_telegram_message(report)

if __name__ == "__main__":
    main()
