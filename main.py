import telebot
import yfinance as yf
import pandas as pd
import time
import feedparser
from io import BytesIO

# --- BOT SOZLAMALARI ---
TOKEN = '8568851239:AAHSva3qh2eo59ltfGVGaBSb4t8gLK-XgVI'
bot = telebot.TeleBot(TOKEN)
CREATOR = "Ozodbek Yusupov"

# --- YORDAMCHI FUNKSIYALAR ---

def get_trading_signal(symbol):
    """Texnik tahlil va signal yaratish"""
    try:
        df = yf.download(symbol, interval='15m', period='2d', progress=False)
        if df.empty: return None

        curr_price = df['Close'].iloc[-1]
        high = df['High'].iloc[-20:].max()
        low = df['Low'].iloc[-20:].min()
        atr = (df['High'] - df['Low']).tail(10).mean()

        signal_type = None
        sl, tp, zone = 0, 0, ""

        if curr_price >= high * 0.998:
            signal_type = "SELL 🔴"
            zone = f"{high:.2f} - {high + atr*0.5:.2f}"
            sl = high + atr
            tp = curr_price - (atr * 2)
        elif curr_price <= low * 1.002:
            signal_type = "BUY 🟢"
            zone = f"{low - atr*0.5:.2f} - {low:.2f}"
            sl = low - atr
            tp = curr_price + (atr * 2)

        if signal_type:
            return {"symbol": symbol, "type": signal_type, "entry": curr_price, "zone": zone, "sl": sl, "tp": tp}
        return None
    except:
        return None

def get_economic_calendar():
    """Iqtisodiy yangiliklarni olish"""
    try:
        url = "https://forexfactory.com"
        feed = feedparser.parse(url)
        if not feed.entries: return "Bugun muhim yangiliklar topilmadi."
        
        news_list = []
        for entry in feed.entries[:5]:
            news_list.append(f"📅 **{entry.title}**\n⏰ {entry.updated}")
        return "\n\n".join(news_list)
    except:
        return "Yangiliklarni yuklab olishda xatolik."

# --- KOMANDALAR (MESSAGE HANDLERS) ---

@bot.message_handler(commands=['start'])
def start(message):
    text = (f"🚀 **Magnum Signal Bot ishga tushdi!**\n\n"
            f"👤 **Yaratuvchi:** {CREATOR}\n\n"
            f"Bot bozorlarni tahlil qiladi va kuchli zonalardan signal beradi.\n"
            f"Istalgan parani yozing (masalan: `BTC`, `GOLD`).")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['news'])
def show_news(message):
    bot.send_message(message.chat.id, "🔍 Yaqin soatlardagi yangiliklar tahlil qilinmoqda...")
    news = get_economic_calendar()
    text = f"📢 **IQTISODIY TAQVIM**\n\n{news}\n\n👤 {CREATOR}"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def market_stats(message):
    bot.send_message(message.chat.id, "📊 Global bozor ko'rsatkichlari...")
    try:
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        text = (f"📈 **BOZOR STATISTIKASI**\n\n"
                f"🪙 **BTC Narxi:** ${btc:,.2f}\n"
                f"🕒 **Vaqt:** {time.strftime('%H:%M:%S')}\n\n"
                f"👤 {CREATOR}")
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "⚠️ Ma'lumot olishda xatolik.")

@bot.message_handler(commands=['info'])
def get_detailed_info(message):
    msg = bot.reply_to(message, "Qaysi para haqida ma'lumot kerak? (Masalan: `AAPL` yoki `BTC-USD`)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_info_step)

def process_info_step(message):
    symbol = message.text.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        detail_text = (f"ℹ️ **{symbol} BATAFSIL MA'LUMOT**\n\n"
                       f"💰 **Narx:** {info['last_price']:.2f}\n"
                       f"📏 **Kunlik diapazon:** {info['day_low']:.2f} - {info['day_high']:.2f}\n"
                       f"📊 **Hajm:** {info['last_volume']:,.0f}\n\n"
                       f"👤 {CREATOR}")
        bot.send_message(message.chat.id, detail_text, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Ma'lumot topilmadi.")

@bot.message_handler(func=lambda message: True)
def manual_analyze(message):
    user_input = message.text.upper().strip()
    replacements = {"GOLD": "GC=F", "XAUUSD": "GC=F", "BTC": "BTC-USD"}
    symbol = replacements.get(user_input, user_input)
    if len(symbol) == 6 and "=" not in symbol and "-" not in symbol: symbol += "=X"

    bot.reply_to(message, f"🔎 {symbol} bo'yicha kuchli zonalar qidirilmoqda...")
    res = get_trading_signal(symbol)
    
    if res:
        msg = (f"🚀 **YANGI SIGNAL: {res['symbol']}**\n\n"
               f"📉 **Yo'nalish:** {res['type']}\n"
               f"🎯 **Kirish zonasi:** {res['zone']}\n"
               f"💰 **Hozirgi narx:** {res['entry']:.2f}\n\n"
               f"🛑 **Stop Loss:** {res['sl']:.2f}\n"
               f"✅ **Take Profit:** {res['tp']:.2f}\n\n"
               f"👤 {CREATOR}")
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ Hozircha bu parada kuchli qaytish zonasi aniqlanmadi.")

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.polling(none_stop=True)
