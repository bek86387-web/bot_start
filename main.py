import telebot
import yfinance as yf
import pandas_ta as ta
import matplotlib.pyplot as plt
import time
from io import BytesIO
import threading

TOKEN = '8568851239:AAFt-9KMGOkncby0lnr1vG-D8lqJISdyZV0'
bot = telebot.TeleBot(TOKEN)
users = set()

SYMBOLS = ['EURUSD=X', 'GBPUSD=X', 'BTC-USD', 'GC=F', 'AAPL', 'TSLA', 'XAUUSD=X']

@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.chat.id)
    text = "Xush kelibsiz Magnumga!\n\nBot yaratuvchisi: **Yusupov Ozodbek**\n\nSignallar avtomatik ravishda yuboriladi."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def check_markets():
    while True:
        for symbol in SYMBOLS:
            try:
                df = yf.download(symbol, interval='15m', period='2d', progress=False)
                if df.empty: continue
                
                df['RSI'] = ta.rsi(df['Close'], length=14)
                macd = ta.macd(df['Close'])
                df = df.join(macd)
                
                last = df.iloc[-1]
                
                signal = None
                if last['RSI'] < 32 and last['MACD_12_26_9'] > last['MACDs_12_26_9']:
                    signal = 'BUY 🟢'
                elif last['RSI'] > 68 and last['MACD_12_26_9'] < last['MACDs_12_26_9']:
                    signal = 'SELL 🔴'
                
                if signal:
                    plt.figure(figsize=(10, 5))
                    plt.plot(df.index[-40:], df['Close'][-40:], color='blue', label='Price')
                    plt.title(f"{symbol} - {signal}")
                    plt.grid(True)
                    buf = BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plt.close()
                    
                    for user_id in users:
                        bot.send_photo(user_id, buf, caption=f"🚀 KUCHLI SIGNAL!\n\nInstrument: {symbol}\nYo'nalish: {signal}\n\nYaratuvchi: Yusupov Ozodbek")
                    buf.close()
            except:
                continue
        time.sleep(300)

if __name__ == "__main__":
    threading.Thread(target=check_markets, daemon=True).start()
    bot.polling(none_stop=True)
