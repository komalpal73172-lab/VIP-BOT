import os
import io
import sys
import glob
import re
import urllib.parse
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw
import requests
from yt_dlp import YoutubeDL

BOT_TOKEN = "7002494152:AAFj97fLHYtbO6WYx0PaEzVtwMQjJbCF1o0"
INSTA_USER = "kartikraja09"
INSTA_URL = f"https://instagram.com/{INSTA_USER}"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

DARKX_API_URL = "https://darkxapi.onrender.com/api/v1/info?key=Lifetime&query="

PINK_HEX = "f45f90"
PINK_RGB = (244, 95, 144)

# ----------------- ROYAL STYLISH FONT ENGINE ----------------- #

def to_royal_font(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    fancy  = " Name: 𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖤𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"[7:]
    tr = str.maketrans(normal, fancy)
    return str(text).translate(tr)

FIELD_MAP = {
    "name": ("Full Name", "👤"),
    "fname": ("Father Name", "👨‍👦"),
    "father": ("Father Name", "👨‍👦"),
    "fathername": ("Father Name", "👨‍👦"),
    "farther": ("Father Name", "👨‍👦"),
    "farthername": ("Father Name", "👨‍👦"),
    "father_name": ("Father Name", "👨‍👦"),
    "farther_name": ("Father Name", "👨‍👦"),
    "phonenumber": ("Mobile No", "📱"),
    "phone": ("Mobile No", "📱"),
    "mobile": ("Mobile No", "📱"),
    "othernumber": ("Other No", "📞"),
    "alt": ("Alternate No", "📞"),
    "address": ("Address", "🏠"),
    "town": ("Town / City", "🏙️"),
    "city": ("City", "🏙️"),
    "state": ("State Circle", "📍"),
    "circle": ("Circle", "📍"),
    "pincode": ("Area Pin", "📮"),
    "operator": ("SIM Operator", "📡"),
    "carrier": ("Telecom Carrier", "📡"),
    "gender": ("Gender", "⚧️"),
    "dob": ("Date of Birth", "🎂"),
    "email": ("Email ID", "📧"),
    "aadhar": ("Aadhaar No", "🆔"),
    "uid": ("UID", "🆔")
}

BLOCKED_KEYS = {
    "buyapi", "apiname", "apiversion", "count", "developedby", "executiontime",
    "developer", "credit", "status", "success", "msg", "key", "query",
    "servertime", "server_time", "telegram", "tg", "channel", "source"
}

# ----------------- 1. PHOTO TO QR ENGINE ----------------- #

def round_corners(image, radius=24):
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
    output = Image.new('RGBA', image.size, (255, 255, 255, 0))
    output.paste(image, (0, 0))
    output.putalpha(mask)
    return output

def generate_cute_qr_from_url(photo_url):
    encoded = urllib.parse.quote(photo_url)
    qr_api_url = (
        f"https://api.qrserver.com/v1/create-qr-code/"
        f"?size=500x500"
        f"&data={encoded}"
        f"&color={PINK_HEX}"
        f"&bgcolor=ffffff"
        f"&ecc=H"
        f"&margin=4"
    )
    res = requests.get(qr_api_url, timeout=15)
    base_qr = Image.open(io.BytesIO(res.content)).convert("RGBA")

    bordered_qr = Image.new("RGBA", (530, 530), (255, 255, 255, 0))
    draw_b = ImageDraw.Draw(bordered_qr)
    draw_b.rounded_rectangle([6, 6, 524, 524], radius=38, outline=PINK_RGB, width=7, fill=(255, 255, 255, 255))
    
    inner_qr = base_qr.resize((480, 480), Image.Resampling.LANCZOS)
    inner_qr_rounded = round_corners(inner_qr, radius=24)
    bordered_qr.paste(inner_qr_rounded, (25, 25), inner_qr_rounded)

    canvas = Image.new("RGB", (700, 700), (255, 255, 255))
    cw, ch = canvas.size
    qw, qh = 530, 530
    canvas.paste(bordered_qr, ((cw - qw) // 2, (ch - qh) // 2), bordered_qr)

    out_bytes = io.BytesIO()
    canvas.save(out_bytes, format='PNG')
    out_bytes.seek(0)
    return out_bytes

# ----------------- 2. INSTAGRAM REEL DOWNLOADER ----------------- #

def download_instagram_media(message, url):
    status_msg = bot.reply_to(message, "⚡ *Extracting Reel Stream...*", parse_mode="Markdown")
    out_template = f"reel_{message.chat.id}_{message.message_id}.%(ext)s"
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 50 * 1024 * 1024
    }

    file_path = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        matched = glob.glob(f"reel_{message.chat.id}_{message.message_id}.*")
        if matched:
            file_path = matched[0]
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📸 Follow Owner (@kartikraja09)", url=INSTA_URL))
            
            with open(file_path, 'rb') as vf:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=vf,
                    caption="🎬 *Reel Downloaded Successfully!*",
                    reply_to_message_id=message.message_id,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="❌ Reel download nahi ho saki.")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ Error: `{str(e)[:80]}`")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# ----------------- 3. RECONSTRUCTED DATA PARSER ----------------- #

def format_darkx_response(raw_text, query_num):
    pairs = re.findall(r"['\"]?([a-zA-Z0-9_]+)['\"]?\s*:\s*['\"]?([^'\",}{]+)['\"]?", raw_text)
    
    has_field_val_structure = any(k.strip().lower() in ("field", "fieldname") for k, _ in pairs)
    resolved_dict = {}
    
    if has_field_val_structure:
        current_field = None
        for k, v in pairs:
            k_lower = k.strip().lower()
            val = v.strip()
            if k_lower in ("field", "fieldname"):
                current_field = val
            elif k_lower in ("value", "val") and current_field:
                resolved_dict[current_field] = val
                current_field = None
            else:
                if k_lower not in ("field", "value", "fieldname", "val"):
                    resolved_dict[k.strip()] = val
    else:
        for k, v in pairs:
            k_clean = k.strip()
            if k_clean.lower() not in ("field", "value"):
                resolved_dict[k_clean] = v.strip()

    lines = [
        "╭────────────────────────────╮",
        "│    🔍  *I N T E L  D O S S I E R*   │",
        "╰────────────────────────────╯\n",
        f"🎯 *TARGET NUMBER:* `{query_num}`\n",
        "┌─── 📋 [ " + to_royal_font("Verified Record") + " ] ───"
    ]

    items_added = 0
    for raw_k, raw_v in resolved_dict.items():
        k_clean = raw_k.lower().replace("_", "").replace(" ", "")
        
        if k_clean in BLOCKED_KEYS or any(b in k_clean for b in BLOCKED_KEYS):
            continue

        val_str = raw_v.strip()
        if val_str.lower() in ("none", "null", "n/a", "not available", ""):
            continue

        label_text = raw_k.replace("_", " ").title()
        icon = "🔸"

        if "farth" in k_clean or "fath" in k_clean:
            label_text = "Father Name"
            icon = "👨‍👦"
        else:
            for key_pattern, (mapped_label, mapped_icon) in FIELD_MAP.items():
                if key_pattern in k_clean:
                    label_text = mapped_label
                    icon = mapped_icon
                    break

        styled_label = to_royal_font(label_text)
        lines.append(f"│  {icon}  *{styled_label}:*  `{val_str}`")
        items_added += 1

    if items_added == 0:
        lines.append("│  ⚠️  *Koi detail verify nahi ho saki.*")

    lines.append("└────────────────────────────")
    lines.append("⚡ *Database:* `Encrypted Archive`")
    return "\n".join(lines)

def fetch_telecom_and_darkx_info(message, raw_number):
    clean_num = raw_number.strip().replace(" ", "").replace("-", "")
    pure_10 = clean_num[-10:] if len(clean_num) >= 10 and clean_num[-10:].isdigit() else clean_num
    
    status_msg = bot.reply_to(message, f"⚡ *Searching Database:* `{pure_10}`...", parse_mode="Markdown")

    try:
        api_url = f"{DARKX_API_URL}{pure_10}"
        res = requests.get(api_url, headers=REQ_HEADERS, timeout=16)
        
        report = format_darkx_response(res.text, pure_10)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📸 Developer (@kartikraja09)", url=INSTA_URL))

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=report,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ Error: `{str(e)}`")

# ----------------- 4. BANK IFSC ROUTINE ----------------- #

def fetch_ifsc_details(message, raw_code):
    clean_ifsc = raw_code.strip().upper().replace(" ", "")
    status_msg = bot.reply_to(message, f"⏳ *Checking Banking Network:* `{clean_ifsc}`...", parse_mode="Markdown")
    try:
        res = requests.get(f"https://ifsc.razorpay.com/{clean_ifsc}", headers=REQ_HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json()
            report = (
                "╭────────────────────────────╮\n"
                "│    🏦  *B A N K  D E T A I L S*   │\n"
                "╰────────────────────────────╯\n\n"
                f"│  🏛️  *{to_royal_font('Bank Name')}:* `{data.get('BANK')}`\n"
                f"│  🏢  *{to_royal_font('Branch')}:* `{data.get('BRANCH')}`\n"
                f"│  🔑  *{to_royal_font('IFSC Code')}:* `{clean_ifsc}`\n"
                f"│  🏙️  *{to_royal_font('City')}:* `{data.get('CITY')}`\n"
                f"│  📍  *{to_royal_font('State')}:* `{data.get('STATE')}`\n"
                f"│  📬  *{to_royal_font('Address')}:* `{data.get('ADDRESS')[:50]}...`\n"
                "└────────────────────────────"
            )
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=report, parse_mode="Markdown")
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ IFSC `{clean_ifsc}` records me nahi mila.")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ Error: `{str(e)}`")

# ----------------- 5. SAJA HUA START WELCOME HANDLER ----------------- #

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "╔══════════════════════════════╗\n"
        "   👑  *M U L T I  -  U T I L I T Y*  👑\n"
        "╚══════════════════════════════╝\n\n"
        "┌── 🌸 〖 *" + to_royal_font("Photo to QR") + "* 〗\n"
        "│  └─ 📸 *Action:* Send any image\n"
        "│  └─ ✨ *Output:* Cute floral scannable QR\n"
        "│\n"
        "├── 🎬 〖 *" + to_royal_font("Reel Downloader") + "* 〗\n"
        "│  └─ 🔗 *Action:* Send Instagram link\n"
        "│  └─ ⚡ *Output:* Fast HD MP4 stream\n"
        "│\n"
        "├── ⚡ 〖 *" + to_royal_font("Number Intelligence") + "* 〗\n"
        "│  └─ 📱 *Action:* Send 10-digit number\n"
        "│  └─ 🔍 *Output:* Live database recon dossier\n"
        "│\n"
        "└── 🏦 〖 *" + to_royal_font("IFSC Lookup") + "* 〗\n"
        "   └─ 🔑 *Action:* Send 11-digit bank IFSC\n"
        "   └─ 🏛️ *Output:* Branch & city mapping\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Developer:* [@{INSTA_USER}]({INSTA_URL})\n"
        "🌟 *Status:* `System Online & Ready`"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📸 Instagram (@kartikraja09)", url=INSTA_URL))

    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    status_msg = bot.reply_to(message, "⏳ *Rendering Floral QR Frame...*", parse_mode="Markdown")
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        qr_bytes = generate_cute_qr_from_url(photo_url)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📸 Follow (@kartikraja09)", url=INSTA_URL))

        caption = "🌸 *Floral QR Ready! Direct scan se photo open hogi.*"
        bot.send_photo(
            chat_id=message.chat.id,
            photo=qr_bytes,
            caption=caption,
            reply_to_message_id=message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ QR Error: `{str(e)}`")

@bot.message_handler(func=lambda msg: True)
def handle_text_messages(message):
    text = message.text.strip()

    if "instagram.com" in text or "instagr.am" in text:
        download_instagram_media(message, text)
        return

    clean_code = text.replace(" ", "").upper()
    if len(clean_code) == 11 and clean_code[4] == '0' and not clean_code.isdigit():
        fetch_ifsc_details(message, clean_code)
        return

    clean_digits = text.replace(" ", "").replace("-", "")
    is_phone = (
        (clean_digits.startswith("+") and clean_digits[1:].isdigit() and len(clean_digits) >= 11) or
        (clean_digits.isdigit() and len(clean_digits) == 10)
    )

    if is_phone:
        fetch_telecom_and_darkx_info(message, text)
        return

    bot.reply_to(message, "⚠️ Mobile number, Instagram link, IFSC code, ya Photo bhejein.")

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass

    bot_info = bot.get_me()
    print(f"✅ Bot connected: @{bot_info.username}")
    print("🚀 Bot running with @kartikraja09 branding!")

    try:
        bot.infinity_polling(skip_pending=True)
    except KeyboardInterrupt:
        print("\nBot stopped.")
        sys.exit(0)
