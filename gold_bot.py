import os
import requests
import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

# Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def fetch_gold_news():
    query = (
        "gold price OR XAUUSD OR World Gold Council OR LBMA OR COMEX gold "
        "OR Kitco gold OR Gold Traders Association Thailand OR YGEA"
    )
    rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss_url)
    
    articles = feed.entries[:10]
    news_text = ""
    
    for idx, entry in enumerate(articles, 1):
        title = entry.get('title', '')
        source = entry.get('source', {}).get('title', 'Financial Source')
        published = entry.get('published', '')
        news_text += f"{idx}. [{source}] {title}\nPublished: {published}\n\n"
        
    return news_text

def generate_report(raw_news, patong_time_str):
    # Google GenAI Official Client အသစ်
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are a senior global commodities analyst. Generate an in-depth daily gold market report in Burmese for a user based in Patong, Phuket, Thailand.
    
    Current Patong Time: {patong_time_str}

    Structure the report strictly with clean HTML formatting for Telegram:

    <b>🪙 နေ့စဉ် ကမ္ဘာ့နှင့် ဒေသတွင်း ရွှေဈေးကွက် အသေးစိတ် အစီရင်ခံစာ</b>
    <b>🕒 ထုတ်ပြန်ချိန် - {patong_time_str}</b>

    <b>🌐 ၁။ ကမ္ဘာ့ Macro ဈေးကွက် သုံးသပ်ချက် (WGC, LBMA, CME/COMEX, Reuters, Bloomberg)</b>
    - (Analyze global interest rates, US Dollar Index, Central Bank Reserves, Inflation, and Spot Gold trends).

    <b>📊 ၂။ Technical & Chart Analysis (Kitco, TradingView, Investing.com)</b>
    - (Detail support & resistance levels, bullish/bearish price targets, and market sentiment).

    <b>🇹🇭 ၃။ ထိုင်းနိုင်ငံ ရွှေဈေးကွက် အခြေအနေ (Gold Traders Association Thailand - GTA)</b>
    - (Analyze Thai Baht gold benchmark trends and Thailand local market demand/price impact).

    <b>🇲🇲 ၄။ မြန်မာ့ရွှေဈေးကွက် အခြေအနေ (YGEA Context)</b>
    - (Brief overview of Myanmar local gold market context and foreign exchange spillover effects).

    <b>💡 ၅။ ရင်းနှီးမြှုပ်နှံသူများအတွက် အနှစ်ချုပ် သတိပြုရန် (Key Takeaways)</b>
    - (Provide 2 critical takeaways for investors).

    <b>🔗 တရားဝင် သတင်းရင်းမြစ်များနှင့် မူရင်း Link များ:</b>
    • <a href="https://www.gold.org">1. World Gold Council (WGC)</a>
    • <a href="https://www.lbma.org.uk">2. LBMA (London Spot)</a>
    • <a href="https://www.cmegroup.com">3. CME / COMEX Futures</a>
    • <a href="https://www.kitco.com">4. Kitco News</a>
    • <a href="https://www.tradingview.com">5. TradingView Charts</a>
    • <a href="https://www.investing.com/commodities/gold">6. Investing.com Gold</a>
    • <a href="https://www.reuters.com/markets/commodities/">7. Reuters Commodities</a>
    • <a href="https://www.bloomberg.com/markets">8. Bloomberg Markets</a>
    • <a href="https://www.goldtraders.or.th">9. GTA Thailand (Thai Baht Benchmark)</a>
    • <a href="https://www.ygea.org.mm">10. YGEA (Myanmar Gold)</a>

    Translate and structure into natural, professional, analytical Burmese. Avoid overly basic summaries.
    Max length: 3500 characters.

    News Data:
    {raw_news}
    """
    
    # Model စစ်ဆေးပြီး အဆင်ပြေရာ Model ဖြင့် အလိုအလျောက် ရွေးချယ်အသုံးပြုပေးမည့် စနစ်
    models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}. Trying next...")
            continue
            
    raise Exception("Failed to generate content with available Gemini models.")

def send_telegram(message_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload)
    return res.json()

if __name__ == "__main__":
    patong_tz = ZoneInfo("Asia/Bangkok")
    patong_time_str = datetime.now(patong_tz).strftime("%Y-%m-%d %H:%M ICT (Patong Time)")
    
    print(f"Generating detailed report for Patong time: {patong_time_str}...")
    news_data = fetch_gold_news()
    report = generate_report(news_data, patong_time_str)
    result = send_telegram(report)
    print("Completed:", result)
