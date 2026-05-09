import google.generativeai as genai

# Gemini sozlamalari
genai.configure(api_key="SIZNING_GEMINI_API_KALITINGIZ")
model = genai.GenerativeModel('gemini-pro')

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    try:
        # AIga uning kimligini va yaratuvchisi kimligini o'rgatamiz
        prompt = (f"Sen Ozodbek Yusupov tomonidan yaratilgan 'Magnum' treyding botisan. "
                  f"Foydalanuvchiga samimiy va professional javob ber. "
                  f"Foydalanuvchi so'rovi: {message.text}")
        
        response = model.generate_content(prompt)
        
        # AI javobining oxiriga har doim sizning ismingizni qo'shib qo'yamiz
        final_response = f"{response.text}\n\n👤 **Yaratuvchi:** Ozodbek Yusupov"
        
        bot.reply_to(message, final_response, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "Hozircha javob bera olmayman, birozdan so'ng urinib ko'ring.")
