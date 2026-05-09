import telebot
import yfinance as yf
import pandas as pd
import time

TOKEN = '8568851239:AAGocCorWsn-qR1aSxMHuYd3X9f0PPGj2O8'
bot = telebot.TeleBot(TOKEN)

def get_trading_signal(symbol):
    try:
        # Ma'lumotlarni yuklash (15 minutlik va 1 kunlik)
        df = yf.download(symbol, interval='15m', period='h1', progress=False)
        if df.empty: return None

        curr_price = df['Close'].iloc[-1]
        high = df['High'].iloc[-20:].max()
        low = df['Low'].iloc[-20:].min()
        atr = (df['High'] - df['Low']).tail(10).mean() # O'rtacha o'zgaruvchanlik

        signal_type = None
        entry = curr_price
        sl = 0
        tp = 0
        zone = ""

        # Strategiya: Pivot va Support/Resistance asosida
        if curr_price >= high * 0.998: # Narx qarshilik zonasiga yaqinlashsa
            signal_type = "SELL 🔴"
            zone = f"{high:.2f} - {high + atr*0.5:.2f}"
            sl = high + atr
            tp = curr_price - (atr * 2)
        elif curr_price <= low * 1.002: # Narx qo'llab-quvvatlash zonasiga yaqinlashsa
            signal_type = "BUY 🟢"
            zone = f"{low - atr*0.5:.2f} - {low:.2f}"
            sl = low - atr
            tp = curr_price + (atr * 2)

        if signal_type:
            return {
                "symbol": symbol,
                "type": signal_type,
                "entry": entry,
                "zone": zone,
                "sl": sl,
                "tp": tp
            }
        return None
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    text = (f"🚀 **Magnum Signal Bot ishga tushdi!**\n\n"
            f"👤 **Yaratuvchi:** Ozodbek Yusupov\n\n"
            f"Bot avtomatik ravishda Index, FX va Kripto bozorlarini tahlil qiladi "
            f"va kuchli zonalardan signal beradi.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def manual_analyze(message):
    user_input = message.text.upper().strip()
    replacements = {"GOLD": "GC=F", "XAUUSD": "GC=F", "BTC": "BTC-USD"}
    symbol = replacements.get(user_input, user_input)
    if len(symbol) == 6 and "=" not in symbol and "-" not in symbol:
        symbol = f"{symbol}=X"

    bot.reply_to(message, f"🔎 {symbol} bo'yicha kuchli zonalar qidirilmoqda...")
    res = get_trading_signal(symbol)
    
    if res:
        msg = (f"🚀 **YANGI SIGNAL: {res['symbol']}**\n\n"
               f"📉 **Yo'nalish:** {res['type']}\n"
               f"🎯 **Kirish zonasi:** {res['zone']}\n"
               f"💰 **Hozirgi narx:** {res['entry']:.2f}\n\n"
               f"🛑 **Stop Loss:** {res['sl']:.2f}\n"
               f"✅ **Take Profit:** {res['tp']:.2f}\n\n"
               f"👤 **Yaratuvchi:** Ozodbek Yusupov")
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ Hozircha bu parada kuchli qaytish zonasi aniqlanmadi.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
    import feedparser # pip install feedparser

def get_economic_calendar():
    """ForexFactory yoki shunga o'xshash manbadan muhim yangiliklarni oladi"""
    try:
        # ForexFactory iqtisodiy taqvimi (RSS formatida)
        url = "https://forexfactory.com"
        feed = feedparser.parse(url)
        
        news_list = []
        for entry in feed.entries[:5]: # Eng yaqin 5 ta yangilik
            news_list.append(f"📅 {entry.title} ({entry.updated})")
            
        if not news_list:
            return "Bugun muhim iqtisodiy yangiliklar topilmadi."
        
        return "\n".join(news_list)
    except:
        return "Yangiliklarni yuklab olishda xatolik yuz berdi."

# Start yoki Signal xabariga qo'shish uchun namuna:
@bot.message_handler(commands=['news'])
def show_news(message):
    bot.send_message(message.chat.id, "🔍 Yaqin soatlardagi muhim yangiliklar tahlil qilinmoqda...")
    news = get_economic_calendar()
    text = (f"📢 **IQTISODIY TAQVIM**\n\n{news}\n\n"
            f"⚠️ *Eslatma:* Yangiliklar paytida bozor keskin o'zgarishi mumkin!\n\n"
            f"👤 **Yaratuvchi:** Ozodbek Yusupov")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
@bot.message_handler(commands=['stats'])
def market_stats(message):
    """Bozorning umumiy texnik holati"""
    bot.send_message(message.chat.id, "📊 Global bozor ko'rsatkichlari hisoblanmoqda...")
    try:
        # Bitcoin Dominansini hisoblash (taxminiy)
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        
        text = (f"📈 **BOZOR STATISTIKASI**\n\n"
                f"🪙 **BTC Narxi:** ${btc:,.2f}\n"
                f"🕒 **Vaqt:** {time.strftime('%H:%M:%S')}\n"
                f"💹 **Bozor holati:** Tahliliy ma'lumotlar yangilanmoqda...\n\n"
                f"💡 *Maslahat:* `/top` komandasi orqali eng faol harakatlarni ko'rishingiz mumkin.\n\n"
                f"👤 **Yaratuvchi:** Ozodbek Yusupov")
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "⚠️ Ma'lumot olishda xatolik.")

@bot.message_handler(commands=['info'])
def get_detailed_info(message):
    """Foydalanuvchidan para nomini so'raydi va to'liq ma'lumot beradi"""
    msg = bot.reply_to(message, "Qaysi para haqida ma'lumot kerak? (Masalan: `AAPL` yoki `BTC-USD`)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_info_step)

def process_info_step(message):
    symbol = message.text.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        
        detail_text = (f"ℹ️ **{symbol} BATAFSIL MA'LUMOT**\n\n"
                       f"💰 **Oxirgi narx:** {info['last_price']:.2f}\n"
                       f"📏 **Kunlik diapazon:** {info['day_low']:.2f} - {info['day_high']:.2f}\n"
                       f"📊 **Hajm (Volume):** {info['last_volume']:,.0f}\n"
                       f"📅 **52 haftalik max:** {info['year_high']:.2f}\n"
                       f"📅 **52 haftalik min:** {info['year_low']:.2f}\n\n"
                       f"👤 **Yaratuvchi:** Ozodbek Yusupov")
        bot.send_message(message.chat.id, detail_text, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Ma'lumot topilmadi. Tiker to'g'ri ekanligini tekshiring.")

