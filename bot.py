import os
import re
import io
import json
import logging
import asyncio
from datetime import datetime
import edge_tts
import pypdf
import docx
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8940844890:AAHndP19m54Sa_JwHPcdbijEkuYG6sGrgGc")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "telegram_audio")
SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

os.makedirs(TEMP_DIR, exist_ok=True)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Available Voices
VOICES = {
    "neerja": {
        "id": "en-IN-NeerjaNeural",
        "name": "🇮🇳 Neerja (Indian English - Crisp Female)",
        "short": "🇮🇳 Neerja (Crisp)"
    },
    "prabhat": {
        "id": "en-IN-PrabhatNeural",
        "name": "🇮🇳 Prabhat (Indian English - Deep Male)",
        "short": "🇮🇳 Prabhat (Male)"
    },
    "sonia": {
        "id": "en-GB-SoniaNeural",
        "name": "🇬🇧 Sonia (British English - Calm Female)",
        "short": "🇬🇧 Sonia (Calm)"
    },
    "ryan": {
        "id": "en-GB-RyanNeural",
        "name": "🇬🇧 Ryan (British English - Narrative Male)",
        "short": "🇬🇧 Ryan (Male)"
    },
    "jenny": {
        "id": "en-US-JennyNeural",
        "name": "🇺🇸 Jenny (US English - Natural Female)",
        "short": "🇺🇸 Jenny (Natural)"
    },
    "guy": {
        "id": "en-US-GuyNeural",
        "name": "🇺🇸 Guy (US English - Deep Male)",
        "short": "🇺🇸 Guy (Deep)"
    }
}

DEFAULT_SETTINGS = {
    "voice_key": "neerja",
    "speed": "+0%",
    "active_recall": False,
    "pause_duration": 3
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

def get_user_settings(chat_id: int):
    settings = load_settings()
    cid = str(chat_id)
    if cid not in settings:
        settings[cid] = DEFAULT_SETTINGS.copy()
        save_settings(settings)
    return settings[cid]

def update_user_setting(chat_id: int, key: str, value):
    settings = load_settings()
    cid = str(chat_id)
    if cid not in settings:
        settings[cid] = DEFAULT_SETTINGS.copy()
    settings[cid][key] = value
    save_settings(settings)

def process_text_for_active_recall(text: str, pause_sec: int = 3) -> str:
    lines = text.split("\n")
    processed_lines = []
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.endswith("?") or re.match(r'^(Q|Question|\d+[\.\)])\s*:', line_str, re.IGNORECASE):
            processed_lines.append(line_str)
            dots = ". " * (pause_sec * 2)
            processed_lines.append(f"{dots} Next, the answer: {dots}")
        else:
            processed_lines.append(line_str)
    return "\n".join(processed_lines)

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings = get_user_settings(update.effective_chat.id)
    voice_info = VOICES.get(user_settings.get("voice_key", "neerja"), VOICES["neerja"])
    
    welcome_text = (
        "🎧 *Welcome to your Commute Audio Study Studio!*\n\n"
        "You can send me:\n"
        "• 📝 *Pasted text / AI summaries*\n"
        "• 📄 *Documents: .txt, .md, .pdf, or .docx files!*\n\n"
        "I will instantly convert it into clear, natural MP3 audio for your bike ride.\n\n"
        "✨ *Features for Bike Rides:*\n"
        "• 📱 *Screen-off lockscreen playback*\n"
        "• 🎧 *Bluetooth earbud controls (play/pause)*\n"
        "• 📶 *100% offline playback on the road*\n\n"
        f"⚙️ *Current Settings:*\n"
        f"• Voice: `{voice_info['name']}`\n"
        f"• Speed: `{user_settings.get('speed', '+0%')}`\n"
        f"• Active Recall: `{'ON (with pauses)' if user_settings.get('active_recall') else 'OFF'}`\n\n"
        "📌 *Commands:*\n"
        "/voice - Change speaker voice & accent\n"
        "/speed - Adjust speaking pace\n"
        "/recall - Toggle active recall silence gaps\n"
        "/prompt - Get AI prompts for 10-min commute scripts\n\n"
        "👉 *Go ahead! Send text or upload a document now.*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for k, v in VOICES.items():
        keyboard.append([InlineKeyboardButton(v["name"], callback_data=f"setvoice_{k}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎙 *Select your preferred voice:*", reply_markup=reply_markup, parse_mode="Markdown")

async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("0.9x (Slow)", callback_data="setspeed_-10%"),
            InlineKeyboardButton("1.0x (Normal)", callback_data="setspeed_+0%"),
            InlineKeyboardButton("1.1x (Snappy)", callback_data="setspeed_+10%")
        ],
        [
            InlineKeyboardButton("1.2x (Fast)", callback_data="setspeed_+20%"),
            InlineKeyboardButton("1.3x (Turbo)", callback_data="setspeed_+30%")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚡ *Select speech rate:*", reply_markup=reply_markup, parse_mode="Markdown")

async def recall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings = get_user_settings(update.effective_chat.id)
    current_status = user_settings.get("active_recall", False)
    new_status = not current_status
    update_user_setting(update.effective_chat.id, "active_recall", new_status)
    
    status_text = "✅ *Active Recall is now ON!*" if new_status else "⏸ *Active Recall is now OFF.*"
    desc_text = "\n\nThe bot will now insert a 3-second reflection pause after every question so you can test yourself while riding." if new_status else "\n\nThe bot will read text smoothly in standard lecture style."
    await update.message.reply_text(f"{status_text}{desc_text}", parse_mode="Markdown")

async def prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt_text = (
        "💡 *AI Commute Prompt (Copy & paste into ChatGPT/Gemini):*\n\n"
        "```text\n"
        "Act as an expert study coach. Convert the following material into a crisp 10-minute audio learning script (approx 1,200 words) formatted for active listening on a bike ride:\n\n"
        "1. CORE CONCEPT (2 mins): Break down the main principle using 1 simple real-world analogy.\n"
        "2. ACTIVE RECALL Q&A (6 mins): 8-10 rapid-fire questions with punchy answers. Put each question on its own line ending with '?'.\n"
        "3. MNEMONIC RECAP (2 mins): Summary of key formulas and definitions.\n\n"
        "Material:\n[PASTE YOUR TOPIC HERE]\n"
        "```"
    )
    await update.message.reply_text(prompt_text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id

    if data.startswith("setvoice_"):
        v_key = data.split("_", 1)[1]
        if v_key in VOICES:
            update_user_setting(chat_id, "voice_key", v_key)
            await query.edit_message_text(
                f"✅ Voice updated to: *{VOICES[v_key]['name']}*",
                parse_mode="Markdown"
            )
    elif data.startswith("setspeed_"):
        speed_val = data.split("_", 1)[1]
        update_user_setting(chat_id, "speed", speed_val)
        await query.edit_message_text(
            f"✅ Speech speed updated to: *{speed_val}*",
            parse_mode="Markdown"
        )

# --- Core Audio Synthesis Generator ---
async def generate_and_send_audio(chat_id: int, text_content: str, default_title: str, context: ContextTypes.DEFAULT_TYPE, status_msg=None):
    if not text_content or not text_content.strip():
        if status_msg:
            await status_msg.edit_text("❌ Text content was empty.")
        return

    user_settings = get_user_settings(chat_id)
    voice_info = VOICES.get(user_settings.get("voice_key", "neerja"), VOICES["neerja"])
    voice_id = voice_info["id"]
    speed_rate = user_settings.get("speed", "+0%")
    active_recall = user_settings.get("active_recall", False)

    if not status_msg:
        status_msg = await context.bot.send_message(chat_id=chat_id, text="⏳ *Generating clear audio for your bike ride...*", parse_mode="Markdown")
    else:
        await status_msg.edit_text("⏳ *Generating clear audio for your bike ride...*", parse_mode="Markdown")

    await context.bot.send_chat_action(chat_id=chat_id, action="record_voice")

    # Extract title
    lines = [l.strip() for l in text_content.split("\n") if l.strip()]
    first_line = lines[0] if lines else default_title
    first_line = re.sub(r'^[#*_\-\s]+', '', first_line).strip()
    title = first_line[:40] if len(first_line) > 40 else first_line
    if not title:
        title = default_title or "Commute Lesson"

    # Process Active recall if on
    text_to_synthesize = text_content
    if active_recall:
        text_to_synthesize = process_text_for_active_recall(text_content, user_settings.get("pause_duration", 3))

    word_count = len(text_content.split())
    estimated_mins = round(word_count / 150, 1)

    safe_filename = f"commute_{chat_id}_{int(asyncio.get_event_loop().time() * 1000)}.mp3"
    filepath = os.path.join(TEMP_DIR, safe_filename)

    try:
        communicate = edge_tts.Communicate(
            text=text_to_synthesize,
            voice=voice_id,
            rate=speed_rate
        )
        await communicate.save(filepath)

        caption = (
            f"🚴 *{title}*\n"
            f"🎙 Voice: {voice_info['short']} | {speed_rate}\n"
            f"⏱ ~{estimated_mins} mins ({word_count} words)"
            f"{' | 🧠 Active Recall' if active_recall else ''}"
        )

        with open(filepath, "rb") as audio_file:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio_file,
                title=title,
                performer="Commute Study Studio",
                caption=caption,
                parse_mode="Markdown",
                read_timeout=120,
                write_timeout=120
            )

        await status_msg.delete()
        if os.path.exists(filepath):
            os.remove(filepath)

    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        await status_msg.edit_text(f"❌ *Failed to create audio:* {str(e)}", parse_mode="Markdown")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

# --- Text Handler ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    await generate_and_send_audio(
        chat_id=update.effective_chat.id,
        text_content=raw_text,
        default_title="Commute Lesson",
        context=context
    )

# --- Document Handler (.txt, .md, .pdf, .docx) ---
async def handle_document_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    filename = doc.file_name or "document"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ['.txt', '.md', '.pdf', '.docx']:
        await update.message.reply_text("📄 Supported document formats:\n• `.txt` (Text)\n• `.md` (Markdown)\n• `.pdf` (PDF Notes)\n• `.docx` (Word Documents)")
        return

    status_msg = await update.message.reply_text(f"📥 *Reading {filename}...*", parse_mode="Markdown")

    try:
        new_file = await context.bot.get_file(doc.file_id)
        doc_bytes = await new_file.download_as_bytearray()
        text_content = ""

        if ext in ['.txt', '.md']:
            text_content = doc_bytes.decode("utf-8", errors="ignore")
        elif ext == '.pdf':
            pdf_reader = pypdf.PdfReader(io.BytesIO(doc_bytes))
            pages_text = []
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted)
            text_content = "\n\n".join(pages_text)
        elif ext == '.docx':
            doc_obj = docx.Document(io.BytesIO(doc_bytes))
            paragraphs = [p.text for p in doc_obj.paragraphs if p.text.strip()]
            text_content = "\n\n".join(paragraphs)

        if not text_content.strip():
            await status_msg.edit_text(f"⚠️ Could not extract readable text from `{filename}`. Ensure it contains selectable text, not scanned images.")
            return

        clean_doc_title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
        await generate_and_send_audio(
            chat_id=update.effective_chat.id,
            text_content=text_content,
            default_title=clean_doc_title,
            context=context,
            status_msg=status_msg
        )
    except Exception as e:
        logger.error(f"Document error: {e}")
        await status_msg.edit_text(f"❌ Error reading `{filename}`: {str(e)}")

# --- Health Check Web Server for Cloud (Render/HF) ---
async def health_check_handler(request):
    return web.Response(text="Bot is healthy and running 24/7!")

async def start_health_server():
    port = int(os.getenv("PORT", 8080))
    server = web.Application()
    server.router.add_get("/", health_check_handler)
    server.router.add_get("/health", health_check_handler)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f">> Health check server listening on port {port}")

def main():
    print(">> Initializing Telegram Commute Audio Bot...")
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(120)
        .write_timeout(120)
        .connect_timeout(60)
        .pool_timeout(60)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("voice", voice_command))
    app.add_handler(CommandHandler("speed", speed_command))
    app.add_handler(CommandHandler("recall", recall_command))
    app.add_handler(CommandHandler("prompt", prompt_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document_message))

    async def post_init(application):
        await start_health_server()

    app.post_init = post_init

    print(">> Telegram Bot is live and listening for messages!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
