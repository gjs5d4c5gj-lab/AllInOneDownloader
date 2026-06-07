import telebot
from telebot import types
import requests
import os

# Bot tokeningizni shu yerga aniq qo'ying
BOT_TOKEN = '8997436001:AAG5p4zvAmGOHDViQAJkfsD1DAxGe9ojqqI'
bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 **Assalomu alaykum!**\n\n"
        "🎬 TikTok va YouTube videolarini hamda musiqalarini (MP3) yuklovchi botga xush kelibsiz!\n\n"
        "👉 Menga shunchaki video havolasini yuboring."
    )

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    
    if "tiktok.com" in url:
        user_data[chat_id] = url
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_video = types.InlineKeyboardButton("🎬 Original Video", callback_data="tt_video")
        btn_audio = types.InlineKeyboardButton("🎵 MP3 (Faqat Musiqa)", callback_data="tt_mp3")
        markup.add(btn_video, btn_audio)
        bot.send_message(chat_id, "✨ TikTok videosi aniqlandi! Formatni tanlang:", reply_markup=markup)

    elif "youtube.com" in url or "youtu.be" in url:
        user_data[chat_id] = url
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_video = types.InlineKeyboardButton("🎥 HD Video (MP4)", callback_data="yt_video")
        btn_mp3 = types.InlineKeyboardButton("🎵 MP3 (Faqat Musiqa)", callback_data="yt_mp3")
        markup.add(btn_video, btn_mp3)
        bot.send_message(chat_id, "✨ YouTube videosi aniqlandi! Formatni tanlang:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "⚠️ Iltimos, faqat TikTok yoki YouTube videosi havolasini yuboring!")

@bot.callback_query_handler(func=lambda call: True)
def callback_processing(call):
    chat_id = call.message.chat.id
    action = call.data
    url = user_data.get(chat_id)
    
    if not url:
        bot.answer_callback_query(call.id, "❌ Havola topilmadi. Qaytadan yuboring.", show_alert=True)
        return

    bot.edit_message_text("⏳ Yuklash jarayoni boshlandi, iltimos kuting...", chat_id, call.message.message_id, reply_markup=None)
    
    # Cobalt API ning eng barqaror manzili
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    is_audio = "mp3" in action or "tt_mp3" in action
    
    # API talablariga mos g'ırt sodda va toza sozlamalar
    payload = {
        "url": url,
        "filenamePattern": "basic"
    }
    
    if is_audio:
        payload["isAudioOnly"] = True

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        result = response.json()
        
        if result.get("status") == "error":
            bot.edit_message_text(f"❌ API Xatoligi: {result.get('text', 'Noma`lum xato')}", chat_id, call.message.message_id)
            return
            
        download_link = result.get("url")
        
        if download_link:
            bot.edit_message_text("🚀 Fayl Telegramga yuklanmoqda...", chat_id, call.message.message_id)
            
            file_response = requests.get(download_link, stream=True, timeout=120)
            file_name = f"download_{chat_id}.mp3" if is_audio else f"download_{chat_id}.mp4"
            
            with open(file_name, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            
            with open(file_name, 'rb') as f:
                if is_audio:
                    bot.send_audio(chat_id, f, caption=f"🎵 **Musiqa tayyor!**\n\n⚡ @{bot.get_me().username}")
                else:
                    bot.send_video(chat_id, f, caption=f"🎬 **Video tayyor!**\n\n⚡ @{bot.get_me().username}")
            
            if os.path.exists(file_name):
                os.remove(file_name)
                
            bot.delete_message(chat_id, call.message.message_id)
        else:
            bot.edit_message_text("❌ Yuklab olish havolasini shakllantirib bo'lmadi.", chat_id, call.message.message_id)
            
    except Exception as e:
        bot.edit_message_text("❌ Tizimda vaqtincha uzilish yuz berdi. Qaytadan urinib ko'ring.", chat_id, call.message.message_id)
        if 'file_name' in locals() and os.path.exists(file_name):
            os.remove(file_name)

    if chat_id in user_data:
        del user_data[chat_id]

print("Yangi tahrirlangan bot ishga tushdi...")
bot.infinity_polling()
