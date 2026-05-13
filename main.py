import os
import requests
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
COINGECKO_API = "https://api.coingecko.com/api/v3"

CREATOR = "🧠 Bot yaratuvchisi: <b>Ozodbek Yusupov</b>\n📡 Barcha ma'lumotlar uning miyasidan uzatiladi."

# ─── Supported pairs ─────────────────────────────────────────────────────────
COINS = {
    "BTC/USDT": "bitcoin",
    "ETH/USDT": "ethereum",
    "BNB/USDT": "binancecoin",
    "SOL/USDT": "solana",
    "XRP/USDT": "ripple",
    "ADA/USDT": "cardano",
    "DOGE/USDT": "dogecoin",
    "TON/USDT": "the-open-network",
    "AVAX/USDT": "avalanche-2",
    "DOT/USDT": "polkadot",
}

COIN_EMOJIS = {
    "BTC/USDT": "₿",
    "ETH/USDT": "⟠",
    "BNB/USDT": "🔶",
    "SOL/USDT": "◎",
    "XRP/USDT": "✕",
    "ADA/USDT": "₳",
    "DOGE/USDT": "🐕",
    "TON/USDT": "💎",
    "AVAX/USDT": "🔺",
    "DOT/USDT": "⬤",
}

# ─── CoinGecko helpers ────────────────────────────────────────────────────────

def fetch_price_data(coin_id: str) -> dict | None:
    """Fetch current price + 24h stats from CoinGecko."""
    try:
        url = f"{COINGECKO_API}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        md = data["market_data"]
        return {
            "name": data["name"],
            "symbol": data["symbol"].upper(),
            "price": md["current_price"]["usd"],
            "change_24h": md["price_change_percentage_24h"],
            "change_7d": md["price_change_percentage_7d"],
            "high_24h": md["high_24h"]["usd"],
            "low_24h": md["low_24h"]["usd"],
            "market_cap": md["market_cap"]["usd"],
            "volume_24h": md["total_volume"]["usd"],
            "ath": md["ath"]["usd"],
            "ath_change": md["ath_change_percentage"]["usd"],
        }
    except Exception as e:
        logger.error(f"CoinGecko error for {coin_id}: {e}")
        return None


def generate_signal(data: dict) -> tuple[str, str, str]:
    """
    Simple rule-based signal generator.
    Returns: (signal, emoji, reason)
    """
    change_24h = data["change_24h"] or 0
    change_7d = data["change_7d"] or 0
    price = data["price"]
    high = data["high_24h"]
    low = data["low_24h"]

    # Price position in 24h range (0-100%)
    range_24h = high - low
    position = ((price - low) / range_24h * 100) if range_24h > 0 else 50

    score = 0
    reasons = []

    # 24h momentum
    if change_24h > 5:
        score += 2
        reasons.append("24s kuchli o'sish (+{:.1f}%)".format(change_24h))
    elif change_24h > 2:
        score += 1
        reasons.append("24s o'rtacha o'sish (+{:.1f}%)".format(change_24h))
    elif change_24h < -5:
        score -= 2
        reasons.append("24s kuchli tushish ({:.1f}%)".format(change_24h))
    elif change_24h < -2:
        score -= 1
        reasons.append("24s o'rtacha tushish ({:.1f}%)".format(change_24h))

    # 7d trend
    if change_7d > 10:
        score += 1
        reasons.append("7k yuqori trend (+{:.1f}%)".format(change_7d))
    elif change_7d < -10:
        score -= 1
        reasons.append("7k pastki trend ({:.1f}%)".format(change_7d))

    # Position in daily range
    if position < 25:
        score += 1
        reasons.append("Kunlik minimumga yaqin (oversold zona)")
    elif position > 75:
        score -= 1
        reasons.append("Kunlik maksimumga yaqin (overbought zona)")

    # ATH distance
    ath_change = data["ath_change"] or 0
    if ath_change < -70:
        score += 1
        reasons.append("ATH dan juda uzoq — potentsial past baho")

    # Final signal
    if score >= 2:
        return "SOTIB OL 🟢", "🟢", " | ".join(reasons)
    elif score == 1:
        return "EHTIYOTKORLIK BILAN SOTIB OL 🟡", "🟡", " | ".join(reasons)
    elif score == -1:
        return "KUTING ⚪", "⚪", " | ".join(reasons)
    elif score <= -2:
        return "SOT 🔴", "🔴", " | ".join(reasons)
    else:
        return "NEYTRAL ⚪", "⚪", "Aniq signal yo'q — bozor noaniq"


def fmt_price(p: float) -> str:
    if p >= 1:
        return f"${p:,.2f}"
    return f"${p:.6f}"


def fmt_large(n: float) -> str:
    if n >= 1_000_000_000:
        return f"${n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n/1_000_000:.2f}M"
    return f"${n:,.0f}"


def build_pair_message(pair: str, data: dict) -> str:
    signal, sig_emoji, reason = generate_signal(data)
    change_24h = data["change_24h"] or 0
    change_7d = data["change_7d"] or 0
    arrow_24 = "📈" if change_24h >= 0 else "📉"
    arrow_7d = "📈" if change_7d >= 0 else "📉"

    return (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{COIN_EMOJIS.get(pair, '🪙')} <b>{pair}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Narx: <b>{fmt_price(data['price'])}</b>\n"
        f"{arrow_24} 24s o'zgarish: <b>{change_24h:+.2f}%</b>\n"
        f"{arrow_7d} 7k o'zgarish: <b>{change_7d:+.2f}%</b>\n"
        f"🔼 24s Yuqori: {fmt_price(data['high_24h'])}\n"
        f"🔽 24s Past: {fmt_price(data['low_24h'])}\n"
        f"📊 Bozor kapitali: {fmt_large(data['market_cap'])}\n"
        f"🔄 24s Hajm: {fmt_large(data['volume_24h'])}\n"
        f"🏆 ATH: {fmt_price(data['ath'])} ({data['ath_change']:+.1f}%)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 Signal: <b>{signal}</b>\n"
        f"📝 Sabab: <i>{reason}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{CREATOR}"
    )


# ─── Keyboards ────────────────────────────────────────────────────────────────

def main_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    pairs = list(COINS.keys())
    for i in range(0, len(pairs), 2):
        row = [InlineKeyboardButton(f"{COIN_EMOJIS.get(p,'🪙')} {p}", callback_data=f"pair:{p}") for p in pairs[i:i+2]]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("📊 Barcha paralar", callback_data="all_pairs")])
    buttons.append([InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")])
    return InlineKeyboardMarkup(buttons)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back_main")]])


# ─── Handlers ────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 <b>Kripto Trading Bot</b>\n\n"
        "Assalomu alaykum! Men sizga kripto bozorida\n"
        "paralar haqida ma'lumot va savdo maslahatlarini beraman.\n\n"
        "Quyidan kerakli parani tanlang 👇\n\n"
        f"{CREATOR}"
    )
    await update.message.reply_html(text, reply_markup=main_keyboard())


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>Buyruqlar ro'yxati</b>\n\n"
        "/start — Bosh menyu\n"
        "/price BTC — BTC narxini ko'rish\n"
        "/signal BTC — BTC uchun signal\n"
        "/all — Barcha paralar\n"
        "/help — Yordam\n\n"
        "⚠️ <b>Ogohlantirish:</b> Bu bot faqat ma'lumot berish maqsadida ishlaydi. "
        "Moliyaviy maslahat emas. Har doim o'z tadqiqotingizni qiling (DYOR).\n\n"
        f"{CREATOR}"
    )
    await update.message.reply_html(text)


async def price_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_html("❌ Foydalanish: /price BTC yoki /price ETH")
        return
    symbol = ctx.args[0].upper()
    pair = f"{symbol}/USDT"
    coin_id = COINS.get(pair)
    if not coin_id:
        await update.message.reply_html(f"❌ <b>{pair}</b> topilmadi. Mavjud paralar: {', '.join(COINS.keys())}")
        return
    msg = await update.message.reply_html("⏳ Ma'lumot yuklanmoqda...")
    data = fetch_price_data(coin_id)
    if not data:
        await msg.edit_text("❌ Ma'lumot olishda xatolik. Qayta urinib ko'ring.")
        return
    await msg.edit_text(build_pair_message(pair, data), parse_mode="HTML", reply_markup=back_keyboard())


async def signal_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await price_cmd(update, ctx)  # same output includes signal


async def all_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_html("⏳ Barcha paralar yuklanmoqda...")
    lines = ["📊 <b>Barcha paralar — Tezkor ko'rinish</b>\n"]
    for pair, coin_id in COINS.items():
        data = fetch_price_data(coin_id)
        if data:
            change = data["change_24h"] or 0
            sig, sig_emoji, _ = generate_signal(data)
            arrow = "📈" if change >= 0 else "📉"
            lines.append(
                f"{COIN_EMOJIS.get(pair,'🪙')} <b>{pair}</b>: {fmt_price(data['price'])} "
                f"({arrow} {change:+.2f}%) {sig_emoji}"
            )
        else:
            lines.append(f"🪙 <b>{pair}</b>: ❌ xatolik")

    lines.append(f"\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append(f"\n{CREATOR}")
    await msg.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_keyboard())


# ─── Callback handlers ────────────────────────────────────────────────────────

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        text = (
            "🤖 <b>Kripto Trading Bot</b>\n\n"
            "Quyidan kerakli parani tanlang 👇\n\n"
            f"{CREATOR}"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=main_keyboard())

    elif data.startswith("pair:"):
        pair = data.split("pair:")[1]
        coin_id = COINS.get(pair)
        if not coin_id:
            await query.edit_message_text("❌ Para topilmadi.", reply_markup=back_keyboard())
            return
        await query.edit_message_text("⏳ Ma'lumot yuklanmoqda...", parse_mode="HTML")
        price_data = fetch_price_data(coin_id)
        if not price_data:
            await query.edit_message_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.", reply_markup=back_keyboard())
            return
        await query.edit_message_text(
            build_pair_message(pair, price_data),
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

    elif data == "all_pairs":
        await query.edit_message_text("⏳ Barcha paralar yuklanmoqda...", parse_mode="HTML")
        lines = ["📊 <b>Barcha paralar — Tezkor ko'rinish</b>\n"]
        for pair, coin_id in COINS.items():
            pd = fetch_price_data(coin_id)
            if pd:
                change = pd["change_24h"] or 0
                sig, sig_emoji, _ = generate_signal(pd)
                arrow = "📈" if change >= 0 else "📉"
                lines.append(
                    f"{COIN_EMOJIS.get(pair,'🪙')} <b>{pair}</b>: {fmt_price(pd['price'])} "
                    f"({arrow} {change:+.2f}%) {sig_emoji}"
                )
            else:
                lines.append(f"🪙 <b>{pair}</b>: ❌ xatolik")
        lines.append(f"\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
        lines.append(f"\n{CREATOR}")
        await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=back_keyboard())

    elif data == "about":
        text = (
            "🤖 <b>Kripto Trading Bot</b>\n\n"
            "📌 Versiya: 1.0\n"
            "📡 Ma'lumot manba'i: CoinGecko API\n"
            "🔄 Real vaqtda narxlar\n"
            "📊 10+ kripto para\n"
            "🎯 Avtomatik signal generatsiya\n\n"
            "⚙️ <b>Signal hisoblash:</b>\n"
            "• 24s va 7k narx o'zgarishi\n"
            "• Kunlik diapazon pozitsiyasi\n"
            "• ATH masofasi analizi\n\n"
            "⚠️ <b>Muhim:</b> Bu bot faqat ma'lumot berish maqsadida. "
            "Har doim o'z tadqiqotingizni qiling.\n\n"
            f"{CREATOR}"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_keyboard())


async def unknown_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper().strip()
    # Check if user typed a coin symbol directly
    pair = f"{text}/USDT"
    if pair in COINS:
        coin_id = COINS[pair]
        msg = await update.message.reply_html("⏳ Ma'lumot yuklanmoqda...")
        data = fetch_price_data(coin_id)
        if data:
            await msg.edit_text(build_pair_message(pair, data), parse_mode="HTML", reply_markup=back_keyboard())
        else:
            await msg.edit_text("❌ Xatolik yuz berdi.")
    else:
        await update.message.reply_html(
            "❓ Tushunmadim. /start buyrug'ini bosing yoki BTC, ETH kabi belgi yozing.",
            reply_markup=main_keyboard(),
        )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()