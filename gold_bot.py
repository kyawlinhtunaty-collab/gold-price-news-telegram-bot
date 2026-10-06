import os
import time
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
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are an elite global macro hedge fund strategist and economic historian in the style of Ray Dalio. 
    Analyze the provided daily gold market data and news to generate an institutional-grade, deep Macroeconomic Strategy Report in Burmese for a high-net-worth gold investor based in Patong, Phuket, Thailand.
    
    Current Patong Time: {patong_time_str}

    CRITICAL INSTRUCTION:
    Do NOT just provide simple news summaries. Analyze the underlying economic mechanics through Ray Dalio's macro principles:
    - Monetary policy & Debt cycles (Long-term debt cycle, central bank printing)
    - Currency Debasement & Real Yields (Nominal interest rates minus inflation)
    - Central Bank Reserve Allocation (Geopolitical diversification out of fiat into hard assets)
    - Portfolio Risk Management & Capital Preservation

    Structure the report strictly with clean HTML formatting for Telegram:

    <b>🏛️ Ray Dalio Style Global Macro & Gold Strategy Report</b>
    <b>🕒 ထုတ်ပြန်ချိန် - {patong_time_str}</b>

    <b>🌐 ၁။ ကမ္ဘာ့ မက်ခရို စီးပွားရေးနှင့် ငွေကြေးစနစ် သုံးသပ်ချက် (Macro & Monetary Framework)</b>
    - (Deeply analyze US Fed Policy, Debt Cycles, Currency Debasement, Real Yields vs Inflation, and Sovereign Reserve Diversification using WGC, LBMA, COMEX, Reuters, Bloomberg data).

    <b>📈 ၂။ ဈေးကွက် လျှောက်လှမ်းမှုနှင့် နည်းပညာပိုင်းဆိုင်ရာ သမိုင်းဝင် သဘောသဘာဝ (Market Dynamics & Technical Positioning)</b>
    - (Analyze institutional order flow, key structural support/resistance zones, RSI/MACD indicators, and systemic risk premiums via Kitco, TradingView, Investing.com).

    <b>🇹🇭 ၃။ ဒေသတွင်း ဂေဟစနစ်နှင့် ထိုင်းဘတ်ငွေ သက်ရောက်မှု (Thailand Regional Dynamics & Baht Hedging)</b>
    - (Detail local liquidity in Phuket/Patong, Thai Baht currency movement relative to USD, and GTA benchmark impact on real purchasing power).

    <b>🇲🇲 ၄။ မြန်မာ့ရွှေနှင့် ပြည်တွင်း ငွေကြေးဆိုင်ရာ အန္တရာယ် ကာကွယ်မှု (Myanmar Context & Asset Protection)</b>
    - (Analyze FX volatility, physical gold as a wealth preservation tool against local currency debasement, and YGEA market mechanics).

    <b>💡 ၅။ Ray Dalio မူဘောင်အပေါ် အခြေခံသော ရင်းနှီးမြှုပ်နှံမှု မဟာဗျူဟာ (Strategic Takeaways & Portfolio Allocation)</b>
    - (Provide 2-3 high-level, actionable macroeconomic strategies focusing on capital preservation, downside risk management, and long-term positioning).

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

    Tone: Sophisticated, institutional, authoritative, deep, and strategic Burmese. Avoid basic headline reporting. Focus on structural macro economics and risk management.
    Max length: 3800 characters.

    News Data:
    {raw_news}
    """
    
    candidate_models = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "") if hasattr(m, 'name') else str(m)
            if "flash" in name and "gemini" in name:
                candidate_models.append(name)
    except Exception as e:
        print(f"Could not list models dynamically: {e}")
        
    if not candidate_models:
        candidate_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']

    candidate_models = list(dict.fromkeys(candidate_models))

    for model_name in candidate_models:
        for attempt in range(1, 4):
            try:
                print(f"Attempting model '{model_name}' (Try {attempt})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_str = str(e)
                print(f"Failed '{model_name}' (Try {attempt}): {err_str}")
                if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                    time.sleep(5 * attempt)
                else:
                    break

    raise Exception("All Gemini model attempts failed. Please try again later.")

def send_telegram(message_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload)
    res_json = res.json()
    
    if not res_json.get("ok") and "parse" in res_json.get("description", "").lower():
        print("HTML format issue detected. Retrying without HTML mode...")
        payload.pop("parse_mode", None)
        res = requests.post(url, json=payload)
        res_json = res.json()
        
    return res_json

if __name__ == "__main__":
    patong_tz = ZoneInfo("Asia/Bangkok")
    patong_time_str = datetime.now(patong_tz).strftime("%Y-%m-%d %H:%M ICT (Patong Time)")
    
    print(f"Generating detailed report for Patong time: {patong_time_str}...")
    news_data = fetch_gold_news()
    report = generate_report(news_data, patong_time_str)
    result = send_telegram(report)
    print("Completed:", result)
