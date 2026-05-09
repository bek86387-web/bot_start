import telebot
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
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
    text = "Xush kelibsiz Magnumga!\n\nBot yaratuvchisi: **Yusupov Ozodbek**\n\nSignallar tahlil qilinmoqda..."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def check_markets():
    while True:
        for symbol in SYMBOLS:
            try:
                df = yf.download(symbol, interval='15m', period='2d', progress=False)
                if df.empty or len(df) < 30: continue
                
                # RSI va MACD hisoblash
                rsi_series = RSIIndicator(close=df['Close'], window=14).rsi()
                macd_obj = MACD(close=df['Close'])
                macd_line = macd_obj.macd()
                macd_signal_line = macd_obj.macd_signal()
                
                last_rsi = rsi_series.iloc[-1]
                last_macd = macd_line.iloc[-1]
                last_signal = macd_signal_line.iloc[-1]
                
                signal = None
                if last_rsi < 32 and last_macd > last_signal:
                    signal = 'BUY 🟢'
                elif last_rsi > 68 and last_macd < last_signal:
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
                    
                    for user_id in list(users):
                        try:
                            bot.send_photo(user_id, buf, caption=f"🚀 KUCHLI SIGNAL!\n\nInstrument: {symbol}\nYo'nalish: {signal}\n\nYaratuvchi: Yusupov Ozodbek")
                        except: pass
                    buf.close()
            except Exception as e:
                print(f"Xato: {e}")
                continue
        time.sleep(300)

if __name__ == "__main__":
    threading.Thread(target=check_markets, daemon=True).start()
    bot.polling(none_stop=True)
