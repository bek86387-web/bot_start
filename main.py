import telebot
import yfinance as yf
import matplotlib.pyplot as plt
import time
from io import BytesIO

TOKEN = '8568851239:AAFt-9KMGOkncby0lnr1vG-D8lqJISdyZV0'
bot = telebot.TeleBot(TOKEN)

# Kuzatiladigan bozorlar
SYMBOLS = {'Oltin': 'GC=F', 'Bitcoin': 'BTC-USD', 'EUR/USD': 'EURUSD=X', 'Tesla': 'TSLA'}

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in SYMBOLS.keys():
        markup.add(telebot.types.KeyboardButton(name))
    bot.send_message(message.chat.id, "Xush kelibsiz Magnumga!\nInstrumentni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in SYMBOLS.keys())
def send_analysis(message):
    symbol = SYMBOLS[message.text]
    df = yf.download(symbol, interval='15m', period='2d', progress=False)
    
    if df.empty:
        bot.reply_to(message, "Ma'lumot topilmadi.")
        return

    current_price = df['Close'].iloc[-1]
    support = df['Low'].tail(20).min()   # Oxirgi 20 sham ichidagi eng past nuqta
    resistance = df['High'].tail(20).max() # Oxirgi 20 sham ichidagi eng yuqori nuqta

    # Grafik chizish
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Close'], color='blue', label='Narx')
    plt.axhline(y=support, color='green', linestyle='--', label='Support (Pastki daraja)')
    plt.axhline(y=resistance, color='red', linestyle='--', label='Resistance (Yuqori daraja)')
    plt.title(f"{message.text} Jonli Grafik")
    plt.legend()
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    caption = (f"📊 **{message.text}**\n\n"
               f"💰 Joriy narx: {current_price:.2f}\n"
               f"📉 Kuchli pastki daraja: {support:.2f}\n"
               f"📈 Kuchli yuqori daraja: {resistance:.2f}\n\n"
               f"Yaratuvchi: Yusupov Ozodbek")
    
    bot.send_photo(message.chat.id, buf, caption=caption, parse_mode="Markdown")

if __name__ == "__main__":
    bot.polling(none_stop=True)
