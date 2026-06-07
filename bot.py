import telebot
from telebot import types
import os
import yt_dlp

# BotFather'dan olgan yangi bot tokeningizni shu yerga qo'ying
BOT_TOKEN = '8997436001:AAG5p4zvAmGOHDViQAJkfsD1DAxGe9ojqqI'
bot = telebot.TeleBot(BOT_TOKEN)

# Vaqtincha ma'lumotlarni saqlash uchun lug'at (User yuborgan linkni eslab qolish uchun)
user_data = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 **Assalomu alaykum!**\n\n"
        "🎬 Men TikTok va YouTube yuklovchi professional botman!\n\n"
        "👉 Menga shunchaki video havolasini (linkini) yuboring."
    )

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    
    # 1. TIKTOK LOGIKASI: Video yoki MP3 tanlash tugmasi chiqadi
    if "tiktok.com" in url:
        user_data[chat_id] = url # Havolani eslab qolamiz
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_video = types.InlineKeyboardButton("🎬 Original Video", callback_data="tt_video")
        btn_audio = types.InlineKeyboardButton("🎵 MP3 (Faqat Musiqa)", callback_data="tt_mp3")
        markup.add(btn_video, btn_audio)
        
        bot.send_message(chat_id, "✨ TikTok videosi aniqlandi! Yuklash formatini tanlang:", reply_markup=markup)
        return

    # 2. YOUTUBE LOGIKASI: Sifat va Musiqa tanlash tugmalari chiqadi
    elif "youtube.com" in url or "youtu.be" in url:
        user_data[chat_id] = url # Havolani eslab qolamiz
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_720 = types.InlineKeyboardButton("🎥 720p (HD Sifat)", callback_data="yt_720")
        btn_360 = types.InlineKeyboardButton("🎬 360p (Kam MB)", callback_data="yt_360")
        btn_mp3 = types.InlineKeyboardButton("🎵 MP3 (Faqat Musiqa)", callback_data="yt_mp3")
        
        markup.add(btn_720, btn_360)
        markup.add(btn_mp3)
        
        bot.send_message(chat_id, "✨ YouTube videosi aniqlandi! Yuklash formatini tanlang:", reply_markup=markup)
        return

    else:
        bot.send_message(chat_id, "⚠️ Iltimos, faqat TikTok yoki YouTube videosi havolasini yuboring!")

# Tugmalar bosilganda ishlaydigan qism (Callback query)
@bot.callback_query_handler(func=lambda call: True)
def callback_processing(call):
    chat_id = call.message.chat.id
    action = call.data
    
    # Foydalanuvchi yuborgan linkni olamiz
    url = user_data.get(chat_id)
    if not url:
        bot.answer_callback_query(call.id, "❌ Xatolik: Havola topilmadi. Qaytadan yuboring.", show_alert=True)
        return

    is_mp3 = False
    status_text = "⏳ Yuklash boshlanmoqda..."

    # TikTok uchun shartlar
    if action == "tt_video":
        status_text = "⏳ TikTok video original sifatda yuklanmoqda..."
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_tt_video_%(id)s.%(ext)s',
            'quiet': True
        }
    elif action == "tt_mp3":
        status_text = "🎵 TikTok'dan audio (MP3) ajratib olinmoqda..."
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_tt_audio_%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        is_mp3 = True

    # YouTube uchun shartlar
    elif action == "yt_720":
        status_text = "⏳ YouTube video 720p (HD) formatda yuklanmoqda..."
        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl': f'downloads/{chat_id}_yt_720_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True
        }
    elif action == "yt_360":
        status_text = "⏳ YouTube video 360p formatda yuklanmoqda..."
        ydl_opts = {
            'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'outtmpl': f'downloads/{chat_id}_yt_360_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True
        }
    elif action == "yt_mp3":
        status_text = "🎵 YouTubedan audio (MP3) ajratib olinmoqda..."
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_yt_audio_%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        is_mp3 = True

    # Ekrandagi yozuvni o'zgartiramiz
    bot.edit_message_text(status_text, chat_id, call.message.message_id, reply_markup=None)
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    file_path = download_process(url, ydl_opts)
    
    # MP3 format uchun fayl kengaytmasini to'g'rilash
    if is_mp3 and file_path:
        base, ext = os.path.splitext(file_path)
        if os.path.exists(base + ".mp3"):
            file_path = base + ".mp3"

    send_and_clean(chat_id, file_path, call.message, is_mp3)

# Yuklash jarayoni (yt-dlp kutubxonasi orqali)
def download_process(url, ydl_opts):
    ydl_opts['max_filesize'] = 48 * 1024 * 1024 # Telegram limiti (48MB)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                base = filename.rsplit('.', 1)[0]
                if os.path.exists(base + '.mp4'):
                    filename = base + '.mp4'
            return filename
    except Exception as e:
        print(f"Xatolik yuklashda: {e}")
        return None

# Yuborish va serverni tozalash funksiyasi
def send_and_clean(chat_id, file_path, msg_to_update, is_mp3=False):
    if file_path and os.path.exists(file_path):
        try:
            bot.edit_message_text("🚀 Fayl Telegram'ga yuborilmoqda...", chat_id, msg_to_update.message_id)
            with open(file_path, 'rb') as f:
                if is_mp3:
                    bot.send_audio(chat_id, f, caption=f"🎵 **Musiqa tayyor!**\n\n⚡ @{bot.get_me().username} orqali yuklandi.")
                else:
                    bot.send_video(chat_id, f, caption=f"🎬 **Video tayyor!**\n\n⚡ @{bot.get_me().username} orqali yuklandi.")
            
            os.remove(file_path)
            bot.delete_message(chat_id, msg_to_update.message_id)
        except Exception as e:
            bot.edit_message_text("❌ Faylni yuborishda xatolik yuz berdi.", chat_id, msg_to_update.message_id)
    else:
        bot.edit_message_text("❌ Yuklab bo'lmadi. Havola hato yoki video hajmi juda katta (Max: 48MB).", chat_id, msg_to_update.message_id)
        
    if chat_id in user_data:
        del user_data[chat_id]

print("TikTok va YouTube Downloader ishga tushdi...")
bot.infinity_polling()
