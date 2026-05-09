import telebot
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

TOKEN = '8568851239:AAFt-9KMGOkncby0lnr1vG-D8lqJISdyZV0'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    text = (f"Xush kelibsiz Magnumga!\n\n"
            f"👤 **Bot yaratuvchisi:** Ozodbek Yusupov\n\n"
            f"Istalgan valyuta, aksiya yoki kriptovalyuta nomini yozing.\n"
            f"Masalan: `BTC-USD`, `EURUSD=X`, `GC=F` (Oltin), `AAPL`.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def analyze_market(message):
    symbol = message.text.upper()
    # Yahoo Finance formatiga moslash (agar foydalanuvchi oddiy yozsa)
    if len(symbol) == 6 and "=" not in symbol:
        symbol = f"{symbol}=X"
    
    try:
        sent_msg = bot.reply_to(message, "📊 Ma'lumotlar tahlil qilinmoqda...")
        df = yf.download(symbol, interval='15m', period='5d', progress=False)
        
        if df.empty:
            bot.edit_message_text("❌ Bunday belgi topilmadi. To'g'ri yozganingizga ishonch hosil qiling.", message.chat.id, sent_msg.message_id)
            return

        # 1. Narx va darajalar
        current_price = df['Close'].iloc[-1]
        high_max = df['High'].max()
        low_min = df['Low'].min()
        
        # 2. Narx qaytish zonalari (Supply & Demand)
        demand_zone = df['Low'].tail(50).min()
        supply_zone = df['High'].tail(50).max()

        # 3. Gann burchaklari (Soddalashtirilgan matematik model)
        # Gann nazariyasi bo'yicha narx o'zgarishi vaqtga nisbatan olinadi
        x = np.arange(len(df))
        y = df['Close'].values
        start_price = df['Low'].min()
        gann_1x1 = start_price + (x * (df['Close'].std() / 100)) # 45 daraja

        # Grafik chizish
        plt.figure(figsize=(12, 7))
        plt.plot(df.index, df['Close'], color='#1f77b4', label='Joriy Narx', linewidth=2)
        
        # Darajalar
        plt.axhline(y=supply_zone, color='red', linestyle='--', alpha=0.6, label='Supply Zone (Qarshilik)')
        plt.axhline(y=demand_zone, color='green', linestyle='--', alpha=0.6, label='Demand Zone (Qo\'llab-quvvatlash)')
        
        # Gann Line
        plt.plot(df.index, gann_1x1, color='orange', linestyle=':', label='Gann 1x1 burchagi')
        
        plt.title(f"{symbol} - Professional Tahlil", fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        plt.close()

        caption = (f"💎 **{symbol} ANALIZI**\n\n"
                   f"💰 **Joriy narx:** {current_price:.4f}\n"
                   f"📈 **Maksimal (5 kunlik):** {high_max:.4f}\n"
                   f"📉 **Minimal (5 kunlik):** {low_min:.4f}\n\n"
                   f"🎯 **Qaytish zonalari:**\n"
                   f"🔴 Supply: {supply_zone:.4f}\n"
                   f"🟢 Demand: {demand_zone:.4f}\n\n"
                   f"📐 **Gann 1x1:** Narx burchakdan {('tepada' if current_price > gann_1x1[-1] else 'pastda')}\n\n"
                   f"👤 **Yaratuvchi:** Ozodbek Yusupov")
        
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_photo(message.chat.id, buf, caption=caption, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(message.chat.id, f"Xato yuz berdi: {str(e)}")

if __name__ == "__main__":
    bot.polling(none_stop=True)
