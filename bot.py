import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
import requests
import yt_dlp
import phonenumbers
from phonenumbers import geocoder, carrier
import qrcode
from PIL import Image
import io

# ================= Render Port Binding Server =================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

    def log_message(self, format, *args):
        return  # Keep console logs clean

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ================= Bot Configuration =================
BOT_TOKEN = "APNA_BOT_TOKEN_YAHAN_RAKHEIN"
DARKX_KEY = "Lifetime"
IFSC_API_URL = "https://ifsc.razorpay.com/"

bot = telebot.TeleBot(BOT_TOKEN)

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ================= Bot Handlers =================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 **Namaste! Main aapka All-in-One Bot hoon.**\n\n"
        "Aap mujhe ye sab bhej sakte hain:\n"
        "🔹 **Mobile Number** (Caller info check karne ke liye)\n"
        "🔹 **IFSC Code** (Bank details nikalne ke liye)\n"
        "🔹 **Video Link** (Download karne ke liye)\n"
        "🔹 **Text** (QR code generate karne ke liye)"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text.strip()

    # 1. Video Download Check (Links)
    if text.startswith("http://") or text.startswith("https://"):
        bot.reply_to(message, "⏳ Video download shuru ho raha hai...")
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'max_filesize': 50 * 1024 * 1024  # 50MB Telegram limit
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                file_path = ydl.prepare_filename(info)
                with open(file_path, 'rb') as video:
                    bot.send_video(message.chat.id, video)
                if os.path.exists(file_path):
                    os.remove(file_path)
            return
        except Exception as e:
            bot.reply_to(message, f"❌ Download error: {str(e)[:100]}")
            return

    # 2. IFSC Code Check (11 characters)
    if len(text) == 11 and text[:4].isalpha():
        try:
            res = requests.get(f"{IFSC_API_URL}{text}", headers=API_HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                reply = (
                    f"🏦 **Bank Details**\n\n"
                    f"🏛 **Bank:** {data.get('BANK')}\n"
                    f"📍 **Branch:** {data.get('BRANCH')}\n"
                    f"🏙 **City:** {data.get('CITY')}\n"
                    f"📌 **State:** {data.get('STATE')}\n"
                    f"🔢 **IFSC:** {data.get('IFSC')}"
                )
                bot.reply_to(message, reply, parse_mode="Markdown")
                return
        except Exception:
            pass

    # 3. Phone Number Check
    try:
        parsed_number = phonenumbers.parse(text, "IN")
        if phonenumbers.is_valid_number(parsed_number):
            operator = carrier.name_for_number(parsed_number, "en")
            region = geocoder.description_for_number(parsed_number, "en")
            reply = (
                f"📞 **Number Details**\n\n"
                f"🌍 **Circle:** {region or 'Unknown'}\n"
                f"📡 **Operator:** {operator or 'Unknown'}\n"
                f"🔢 **Number:** +{parsed_number.country_code} {parsed_number.national_number}"
            )
            bot.reply_to(message, reply, parse_mode="Markdown")
            return
    except Exception:
        pass

    # 4. QR Code Generator (Default fallback for text)
    try:
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        bio = io.BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        bot.send_photo(message.chat.id, photo=bio, caption="✅ QR Code Generated!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)
    
