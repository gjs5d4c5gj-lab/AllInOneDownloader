import telebot
from telebot import types
import requests
import os

# Tokenlarni Railway Environment Variables (O'zgaruvchilar) qismidan xavfsiz olamiz
BOT_TOKEN = os.getenv('8997436001:AAG5p4zvAmGOHDViQAJkfsD1DAxGe9ojqqI')
RAPIDAPI_KEY = os.getenv('curl --request POST \
	--url https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink \
	--header 'Content-Type: application/json' \
	--header 'x-rapidapi-host: auto-download-all-in-one.p.rapidapi.com' \
	--data '{"url":"https://www.tiktok.com/@yeuphimzz/video/7237370304337628442"}'')

if not BOT_TOKEN or not RAPIDAPI_KEY:
    print("Xatolik: BOT_TOKEN yoki RAPIDAPI_KEY tizimga kiritilmagan!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 **Assalomu alaykum!**\n\n🎬 TikTok va YouTube platformalaridan fayllarni yuklovchi botga xush kelibsiz!\n\n👉 Havola yuboring:"
    )

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    
    if "tiktok.com" in url or "youtube.com" in url or "youtu.be" in url:
        user_data[chat_id] = url
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_video = types.InlineKeyboardButton("🎬 Original Video", callback_data="get_video")
        btn_audio = types.InlineKeyboardButton("🎵 MP3 Audio", callback_data="get_audio")
        markup.add(btn_video, btn_audio)
        bot.send_message(chat_id, "✨ Havola aniqlandi! Formatni tanlang:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "⚠️ Iltimos, faqat YouTube yoki TikTok havolasini yuboring!")

@bot.callback_query_handler(func=lambda call: True)
def callback_processing(call):
    chat_id = call.message.chat.id
    action = call.data
    url = user_data.get(chat_id)
    
    if not url:
        bot.answer_callback_query(call.id, "❌ Havola topilmadi.", show_alert=True)
        return

    bot.edit_message_text("⏳ Yuklash boshlandi...", chat_id, call.message.message_id, reply_markup=None)
    
    api_url = "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "auto-download-all-in-one.p.rapidapi.com"
    }
    payload = {"url": url}

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        result = response.json()
        
        if result.get("success") and result.get("links"):
            links = result.get("links")
            download_link = None
            is_audio = (action == "get_audio")
            
            if is_audio:
                for item in links:
                    if item.get("type") == "audio" or "mp3" in item.get("quality", "").lower():
                        download_link = item.get("url")
                        break
                if not download_link:
                    download_link = links[0].get("url")
            else:
                download_link = links[0].get("url")

            if download_link:
                bot.edit_message_text("🚀 Fayl Telegram serveriga uzatilyapti...", chat_id, call.message.message_id)
                
                file_response = requests.get(download_link, stream=True, timeout=120)
                file_name = f"file_{chat_id}.mp3" if is_audio else f"file_{chat_id}.mp4"
                
                with open(file_name, 'wb') as f:
                    for chunk in file_response.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                
                with open(file_name, 'rb') as f:
                    if is_audio:
                        bot.send_audio(chat_id, f, caption=f"🎵 Musiqa tayyor! @{bot.get_me().username}")
                    else:
                        bot.send_video(chat_id, f, caption=f"🎬 Video tayyor! @{bot.get_me().username}")
                
                if os.path.exists(file_name):
                    os.remove(file_name)
                bot.delete_message(chat_id, call.message.message_id)
            else:
                bot.edit_message_text("❌ Yuklab olish havolasi topilmadi.", chat_id, call.message.message_id)
        else:
            bot.edit_message_text("❌ Tizim videoni o'qiy olmadi.", chat_id, call.message.message_id)
            
    except Exception as e:
        bot.edit_message_text("❌ Xatolik yuz berdi. Birozdan so'ng qayta urining.", chat_id, call.message.message_id)
        if 'file_name' in locals() and os.path.exists(file_name):
            os.remove(file_name)

    if chat_id in user_data:
        del user_data[chat_id]

print("Bot muvaffaqiyatli yurgizildi...")
bot.infinity_polling()
