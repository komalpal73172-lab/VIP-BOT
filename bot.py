import re
import os
import io
import html
import telebot
from telebot.types import ReplyKeyboardRemove
import requests
import yt_dlp
import phonenumbers
import qrcode
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from phonenumbers import geocoder, carrier, number_type, PhoneNumberType

# --- CONFIGURATION ---
BOT_TOKEN = "7002494152:AAFaAJUxqV0Ah5KX39YrLYn4R8BeufncIUg"
DARKX_API_URL = "https://darkxapi.onrender.com/api/v1/info"
DARKX_KEY = "Lifetime"
IFSC_API_URL = "https://ifsc.razorpay.com/"

bot = telebot.TeleBot(BOT_TOKEN)

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

def clean_extracted_value(val):
    if not val:
        return None
    val_str = str(val).strip()
    if val_str.lower() in ["none", "null", "n/a", "not available", "nil", ""]:
        return None
    val_str = re.sub(r'[!]+', ', ', val_str).strip(', ')
    val_str = re.sub(r'\s+', ' ', val_str)
    return val_str

def find_deep_value(data, target_keys):
    if isinstance(data, dict):
        for k, v in data.items():
            clean_k = str(k).lower().replace("_", "").replace(" ", "").replace("-", "").strip()
            for tk in target_keys:
                clean_tk = tk.lower().replace("_", "").replace(" ", "").replace("-", "").strip()
                if clean_k == clean_tk or clean_k.startswith(clean_tk):
                    cleaned = clean_extracted_value(v)
                    if cleaned:
                        return cleaned
            res = find_deep_value(v, target_keys)
            if res:
                return res
    elif isinstance(data, list):
        for item in data:
            res = find_deep_value(item, target_keys)
            if res:
                return res
    return None

def fetch_ifsc_details(ifsc_code: str) -> str:
    try:
        r = requests.get(f"{IFSC_API_URL}{ifsc_code.upper()}", timeout=15)
        if r.status_code == 200:
            d = r.json()
            fields = [
                ("🏛️", "Bank", d.get("BANK", "Not Available")),
                ("🏷️", "IFSC", ifsc_code.upper()),
                ("🏢", "Branch", d.get("BRANCH", "Not Available")),
                ("🔢", "MICR", d.get("MICR") or "Not Available"),
                ("🏙️", "City", d.get("CITY", "Not Available")),
                ("📍", "District", d.get("DISTRICT", "Not Available")),
                ("🗺️", "State", d.get("STATE", "Not Available")),
                ("🏠", "Address", d.get("ADDRESS", "Not Available"))
            ]
            lines = [
                "╔══════════════════════════════════╗",
                "       🏦  <b>BANK IFSC DETAILS</b>  🏦",
                "╠══════════════════════════════════╣"
            ]
            for icon, label, val in fields:
                lines.append(f" {icon} <b>{label.ljust(9)}</b> : <code>{html.escape(str(val))}</code>")
            lines.append("╚══════════════════════════════════╝")
            return "\n".join(lines)
        return "❌ <b>Galat IFSC Code!</b>"
    except Exception as e:
        return f"⚠️ <b>Error:</b> {e}"

def format_darkx_card(raw_json: dict, query_num: str, sim_carrier: str, sim_circle: str) -> str:
    name = find_deep_value(raw_json, ["fullname", "full_name", "customername", "name", "owner", "user_name"]) or "Not Available"
    fname = find_deep_value(raw_json, ["father_name", "fathername", "fname", "father", "fh_name", "f_name", "careof", "parent"]) or "Not Available"
    circle = find_deep_value(raw_json, ["circle", "state", "location", "region", "zone"]) or sim_circle
    op = find_deep_value(raw_json, ["operator", "carrier", "telecom", "sim", "network", "service_provider"]) or sim_carrier
    address = find_deep_value(raw_json, ["address", "addr", "permanent_address", "local_address", "city", "village"]) or "Not Available"
    alt_no = find_deep_value(raw_json, ["altmobile", "altphone", "alternate_number", "alt_no", "alternatenumber", "alternate", "alt"]) or "Not Available"

    raw_aadhaar = find_deep_value(raw_json, ["aadhar_number", "aadhaar_no", "aadhar", "aadhaar", "adhar", "uid", "id_number", "id"])
    aadhaar_display = "[Aadhaar Redacted]" if raw_aadhaar else "Not Available"

    fields = [
        ("📞", "Number", query_num),
        ("🪪", "Aadhaar", aadhaar_display),
        ("👤", "Name", name),
        ("👨‍👦", "Father", fname),
        ("📱", "Alt No", alt_no),
        ("📶", "Operator", op),
        ("📍", "Circle", circle),
        ("🏠", "Address", address),
    ]

    lines = [
        "╔══════════════════════════════════╗",
        "       👑  <b>CALLER PROFILE</b>  👑",
        "╠══════════════════════════════════╣"
    ]
    for icon, label, val in fields:
        lines.append(f" {icon} <b>{label.ljust(9)}</b> : <code>{html.escape(val)}</code>")
    lines.append("╚══════════════════════════════════╝")
    return "\n".join(lines)

def format_telecom_card(parsed, formatted_num: str) -> str:
    sim_carrier = carrier.name_for_number(parsed, "en") or "Not Available"
    sim_circle = geocoder.description_for_number(parsed, "en") or "India"
    ntype = number_type(parsed)
    type_map = {PhoneNumberType.MOBILE: "Mobile", PhoneNumberType.FIXED_LINE: "Landline"}
    line_type = type_map.get(ntype, "Other")

    items = [
        ("📞", "Format", formatted_num),
        ("📶", "Carrier", sim_carrier),
        ("📍", "Circle", sim_circle),
        ("📱", "Type", line_type),
        ("⚡", "Status", "Valid Active")
    ]
    lines = [
        "╔══════════════════════════════════╗",
        "       📡  <b>TELECOM INFO</b>  📡",
        "╠══════════════════════════════════╣"
    ]
    for icon, label, val in items:
        lines.append(f" {icon} <b>{label.ljust(8)}</b> : <code>{html.escape(val)}</code>")
    lines.append("╚══════════════════════════════════╝")
    return "\n".join(lines)

def fetch_darkx_task(query_num: str, sim_carrier: str, sim_circle: str):
    try:
        url = f"{DARKX_API_URL}?key={DARKX_KEY}&query={query_num}"
        r = requests.get(url, headers=API_HEADERS, timeout=25)
        if r.status_code == 200:
            data = r.json()
            card = format_darkx_card(data, query_num, sim_carrier, sim_circle)
            if card:
                return [card]
    except Exception:
        pass
    return []

def fetch_all_info(raw_text: str):
    cleaned = re.sub(r"[^0-9+]", "", raw_text)
    if not cleaned.startswith("+"):
        if len(cleaned) == 10:
            cleaned = "+91" + cleaned
        elif len(cleaned) == 12 and cleaned.startswith("91"):
            cleaned = "+" + cleaned
        else:
            cleaned = "+91" + cleaned

    try:
        parsed = phonenumbers.parse(cleaned, None)
        if not phonenumbers.is_valid_number(parsed):
            return "⚠️ <b>Invalid Number:</b> Sahi number enter karein."
    except Exception:
        return "⚠️ Galat number format."

    formatted_num = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    query_num = re.sub(r"[^0-9]", "", cleaned)[-10:]
    sim_carrier = carrier.name_for_number(parsed, "en") or "Not Available"
    sim_circle = geocoder.description_for_number(parsed, "en") or "India"

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_darkx = executor.submit(fetch_darkx_task, query_num, sim_carrier, sim_circle)
        darkx_cards = future_darkx.result()

    final_cards = []
    if darkx_cards:
        final_cards.extend(darkx_cards)
    final_cards.append(format_telecom_card(parsed, formatted_num))
    return "\n\n".join(final_cards)

def execute_lookup_and_send(chat_id, target_number):
    status = bot.send_message(chat_id, "⚡ <i>Searching records...</i>", parse_mode="HTML")
    res = fetch_all_info(target_number)
    bot.edit_message_text(res, chat_id, status.message_id, parse_mode="HTML")

def download_and_send_reel(chat_id, reel_url):
    status = bot.send_message(chat_id, "⏳ <i>Media fetch ho raha hai... Kripya intezaar karein.</i>", parse_mode="HTML")
    out_dir = "downloads"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"media_{chat_id}.mp4")

    if os.path.exists(out_file):
        try:
            os.remove(out_file)
        except Exception:
            pass

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': out_file,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 50 * 1024 * 1024
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])

        if os.path.exists(out_file):
            bot.edit_message_text("📤 <i>Uploading to Telegram...</i>", chat_id, status.message_id, parse_mode="HTML")
            with open(out_file, 'rb') as video_fp:
                bot.send_video(chat_id, video_fp, caption="🎬 <b>Downloaded successfully!</b>", parse_mode="HTML")
            bot.delete_message(chat_id, status.message_id)
            try:
                os.remove(out_file)
            except Exception:
                pass
        else:
            bot.edit_message_text("❌ Download nahi ho paya. Link check karein ya private reel ho sakti hai.", chat_id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ <b>Download Error:</b> {e}", chat_id, status.message_id, parse_mode="HTML")

def generate_cute_qr(data_text: str):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=3)
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#4A148C", back_color="#FFF8E1")
    out = io.BytesIO()
    img.save(out, format="PNG")
    out.name = "cute_qr.png"
    out.seek(0)
    return out

@bot.message_handler(commands=['start'])
def start_cmd(message):
    welcome_msg = (
        "╔══════════════════════════════╗\n"
        "      ⚡ <b>VIP DASHBOARD</b> ⚡\n"
        "╚══════════════════════════════╝\n\n"
        "┏━━━ 💳 <b>ACCOUNT STATUS</b> ━━━┓\n"
        "  ▫️ <b>Service Mode :</b> <code>100% Free Access 🟢</code>\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "📌 <b>AVAILABLE SERVICES:</b>\n\n"
        "<b>[01] 📞 Phone Search</b>\n"
        "     ├── 🎁 Unlimited Free Search\n"
        "     └── ⚡ Complete Caller & Telecom Info\n\n"
        "<b>[02] 🏦 Bank IFSC Details</b>\n"
        "     ├── 🆓 100% Free Lifetime\n"
        "     └── 🏢 Complete Branch Address\n\n"
        "<b>[03] 🎨 Aesthetic QR Studio</b>\n"
        "     ├── 🌈 Cute Multi-Color Palette\n"
        "     └── 💬 Direct Photo / Text To QR\n\n"
        "<b>[04] 📸 Video Downloader</b>\n"
        "     ├── ⚡ High Quality Video\n"
        "     └── 📥 Insta Reels / YouTube Shorts\n\n"
        "══════════════════════════════\n"
        "👉 <i>Direct koi bhi Photo, Number, IFSC, text ya link chat me bhejein!</i>"
    )
    bot.reply_to(message, welcome_msg, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(content_types=['photo'])
def handle_photo_direct_qr(m):
    status = bot.reply_to(m, "🎨 <i>Generating Cute QR for your photo...</i>", parse_mode="HTML")
    try:
        photo_id = m.photo[-1].file_id
        file_info = bot.get_file(photo_id)
        photo_direct_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        qr_io = generate_cute_qr(photo_direct_url)
        bot.delete_message(m.chat.id, status.message_id)
        bot.send_photo(
            m.chat.id,
            qr_io,
            caption="🎨 <b>Aapka Cute Multi-Color Photo QR Code Ready Hai!</b>\n<i>(Scan karte hi aapki photo khul jayegi)</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        bot.edit_message_text(f"⚠️ <b>Error:</b> {e}", m.chat.id, status.message_id, parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(m):
    text = m.text.strip()
    chat_id = m.chat.id

    if "instagram.com" in text.lower() or "youtu.be" in text.lower() or "youtube.com" in text.lower():
        download_and_send_reel(chat_id, text)
        return

    clean_text = text.replace(" ", "").upper()
    if re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', clean_text):
        status_msg = bot.reply_to(m, "⚡ <i>Searching bank details...</i>", parse_mode="HTML")
        res = fetch_ifsc_details(clean_text)
        bot.edit_message_text(res, m.chat.id, status_msg.message_id, parse_mode="HTML")
        return

    raw_num = re.sub(r"[^0-9]", "", text)
    if len(raw_num) in [10, 11, 12]:
        execute_lookup_and_send(chat_id, text)
        return

    if len(text) >= 1 and not text.startswith("/"):
        qr_img = generate_cute_qr(text)
        bot.send_photo(chat_id, qr_img, caption="🎨 <b>Aapka Cute Multi-Color QR Code Ready Hai!</b>", parse_mode="HTML")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)
      
