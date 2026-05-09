import telebot
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
from io import BytesIO

TOKEN = '8568851239:AAGPcoTEWl0zdlU2grRqUE1cgl1Deckkqr4'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    text = (f"Xush kelibsiz Magnumga!\n\n"
            f"👤 **Bot yaratuvchisi:** Ozodbek Yusupov\n\n"
            f"Istalgan valyuta, kripto yoki aksiya nomini yozing.\n"
            f"Masalan: `BTC-USD`, `GC=F` (Oltin), `EURUSD=X`.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def send_analysis(message):
    user_input = message.text.upper().strip()
    
    # Avtomatik formatlash
    replacements = {"XAUUSD": "GC=F", "GOLD": "GC=F", "BTC": "BTC-USD", "ETH": "ETH-USD"}
    symbol = replacements.get(user_input, user_input)
    if len(symbol) == 6 and "=" not in symbol and "-" not in symbol:
        symbol = f"{symbol}=X"

    try:
        data = yf.download(symbol, interval='15m', period='1d', progress=False)
        
        if data.empty:
            bot.reply_to(message, "❌ Ma'lumot topilmadi. To'g'ri nom yozing.")
            return

        current_price = data['Close'].iloc[-1]
        
        # Real shamlar (candlestick) grafigini chizish
        buf = BytesIO()
        mpf.plot(data, type='candle', style='charles', title=f'\n{symbol} Jonli Grafik',
                 ylabel='Narx', savefig=buf)
        buf.seek(0)

        caption = (f"📊 **{symbol}**\n\n"
                   f"💰 **Joriy narx:** {current_price:.4f}\n\n"
                   f"👤 **Yaratuvchi:** Ozodbek Yusupov")
        
        bot.send_photo(message.chat.id, buf, caption=caption, parse_mode="Markdown")
        buf.close()

    except Exception as e:
        bot.send_message(message.chat.id, f"Xato: {str(e)}")

if __name__ == "__main__":
    bot.polling(none_stop=True)
