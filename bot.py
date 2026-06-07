import telebot
from telebot import types
import os
import yt_dlp

# BotFather'dan olgan yangi bot tokeningizni shu yerga qo'ying
BOT_TOKEN = '8997436001:AAG5p4zvAmGOHDViQAJkfsD1DAxGe9ojqqI'
bot = telebot.TeleBot(BOT_TOKEN)

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
    
    # Havolani tozalash va tekshirish
    if "tiktok.com" in url:
        user_data[chat_id] = url
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_video = types.InlineKeyboardButton("🎬 Original Video", callback_data="tt_video")
        btn_audio = types.InlineKeyboardButton("🎵 MP3 (Faqat Musiqa)", callback_data="tt_mp3")
        markup.add(btn_video, btn_audio)
        bot.send_message(chat_id, "✨ TikTok videosi aniqlandi! Formatni tanlang:", reply_markup=markup)
        return

    elif "youtube.com" in url or "youtu.be" in url:
        user_data[chat_id] = url
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_720 = types.InlineKeyboardButton("🎥 720p (HD Sifat)", callback_data="yt_720")
        btn_360 = types.InlineKeyboardButton("🎬 360p (Kam MB)", callback_data="yt_360")
        btn_mp3 = types.InlineKeyboardButton("🎵 MP3 (Faqat Musiqa)", callback_data="yt_mp3")
        markup.add(btn_720, btn_360)
        markup.add(btn_mp3)
        bot.send_message(chat_id, "✨ YouTube videosi aniqlandi! Formatni tanlang:", reply_markup=markup)
        return
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

    is_mp3 = False
    status_text = "⏳ Yuklash boshlanmoqda..."

    # YouTube va TikTok sozlamalarini xavfsiz formatga keltiramiz
    if action == "tt_video":
        status_text = "⏳ TikTok video yuklanmoqda..."
        ydl_opts = {'format': 'best', 'outtmpl': f'downloads/{chat_id}_tt_v.%(ext)s'}
    elif action == "tt_mp3":
        status_text = "🎵 TikTok'dan audio ajratilmoqda..."
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_tt_a.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        }
        is_mp3 = True
    elif action == "yt_720":
        status_text = "⏳ YouTube video 720p formatda yuklanmoqda..."
        ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f'downloads/{chat_id}_yt_720.%(ext)s', 'merge_output_format': 'mp4'}
    elif action == "yt_360":
        status_text = "⏳ YouTube video 360p formatda yuklanmoqda..."
        ydl_opts = {'format': 'best[height<=360]', 'outtmpl': f'downloads/{chat_id}_yt_360.%(ext)s', 'merge_output_format': 'mp4'}
    elif action == "yt_mp3":
        status_text = "🎵 YouTubedan audio ajratilmoqda..."
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_yt_a.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        }
        is_mp3 = True

    bot.edit_message_text(status_text, chat_id, call.message.message_id, reply_markup=None)
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    file_path = download_process(url, ydl_opts)
    
    if is_mp3 and file_path:
        base, ext = os.path.splitext(file_path)
        if os.path.exists(base + ".mp3"):
            file_path = base + ".mp3"

    send_and_clean(chat_id, file_path, call.message, is_mp3)

def download_process(url, ydl_opts):
    # Eng muhim qismi: Brauzer kabi ko'rinish beramiz (Blokga tushmaslik uchun)
    ydl_opts['http_headers'] = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    ydl_opts['quiet'] = True
    ydl_opts['no_warnings'] = True
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                base = filename.rsplit('.', 1)[0]
                for ext in ['.mp4', '.mkv', '.webm', '.mp3']:
                    if os.path.exists(base + ext):
                        return base + ext
            return filename
    except Exception as e:
        print(f"Yuklash xatosi: {e}")
        return None

def send_and_clean(chat_id, file_path, msg_to_update, is_mp3=False):
    if file_path and os.path.exists(file_path):
        try:
            bot.edit_message_text("🚀 Telegram serveriga yuklanmoqda...", chat_id, msg_to_update.message_id)
            with open(file_path, 'rb') as f:
                if is_mp3:
                    bot.send_audio(chat_id, f, caption=f"🎵 **Musiqa tayyor!**\n\n⚡ @{bot.get_me().username}")
                else:
                    bot.send_video(chat_id, f, caption=f"🎬 **Video tayyor!**\n\n⚡ @{bot.get_me().username}")
            os.remove(file_path)
            bot.delete_message(chat_id, msg_to_update.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Faylni yuborishda xatolik: {str(e)[:50]}", chat_id, msg_to_update.message_id)
    else:
        bot.edit_message_text("❌ Yuklab bo'lmadi. Video juda katta yoki YouTube cheklov qo'ygan.", chat_id, msg_to_update.message_id)
        
    if chat_id in user_data:
        del user_data[chat_id]

print("Yangilangan downloader ishga tushdi...")
bot.infinity_polling()
