import asyncio
import os
import schedule
import time
import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Weekly tips content
TIPS = {
    "chatgpt": (
        "🤖 *ChatGPT Tip of the Week*\n\n"
        "Use ChatGPT to draft your campaign captions in seconds! "
        "Try prompts like:\n"
        "_\"Write a catchy Instagram caption for a back-to-school sale "
        "targeting teens.\"_\n\n"
        "Refine the output by adding your brand voice and emojis. 🎯"
    ),
    "grok": (
        "🧠 *Grok Tip of the Week*\n\n"
        "Grok can help you analyse trending topics in real time. "
        "Ask it what's buzzing in your niche and use those insights "
        "to shape your next campaign angle. 📈"
    ),
    "capcut": (
        "🎬 *CapCut Tip of the Week*\n\n"
        "Speed up your video editing with CapCut's auto-captions feature. "
        "Upload your clip, enable captions, then customise the font and "
        "colour to match your brand. Perfect for Reels & TikToks! ✂️"
    ),
    "suno": (
        "🎵 *Suno Tip of the Week*\n\n"
        "Need a jingle for your ad? Use Suno to generate royalty-free "
        "background music in seconds. Describe the mood and genre, "
        "download the track, and drop it straight into your video. 🎶"
    ),
}

TOOLS_LIST = (
    "🛠 *Digital Campaign Tools We Cover*\n\n"
    "• 🤖 *ChatGPT* — AI copywriting & content ideation\n"
    "• 🧠 *Grok* — Real-time trend analysis & research\n"
    "• 🎬 *CapCut* — Fast, professional video editing\n"
    "• 🎵 *Suno* — AI-generated music & jingles\n\n"
    "Use /tip to get the latest weekly tip!"
)

WELCOME_MESSAGE = (
    "👋 Welcome to the group, {name}!\n\n"
    "This is your hub for weekly digital campaign tips covering "
    "ChatGPT, Grok, CapCut, Suno, and more. 🚀\n\n"
    "Type /help to see what I can do."
)

# Rotating tip index (cycles through tools each week)
_tip_keys = list(TIPS.keys())
_tip_index = 0


def _next_tip() -> str:
    global _tip_index
    tip = TIPS[_tip_keys[_tip_index % len(_tip_keys)]]
    _tip_index += 1
    return tip


# ---------- Command handlers ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hey! I'm your digital campaign assistant bot.\n\n"
        "I share weekly tips on tools like ChatGPT, Grok, CapCut & Suno "
        "to help you run better campaigns.\n\n"
        "Type /help to see all available commands.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 *Available Commands*\n\n"
        "/start — Introduction to the bot\n"
        "/help — Show this help message\n"
        "/tip — Get the latest weekly tip\n"
        "/tools — List all tools we cover\n"
        "/remind — Get a Friday motivation reminder",
        parse_mode="Markdown",
    )


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_next_tip(), parse_mode="Markdown")


async def tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(TOOLS_LIST, parse_mode="Markdown")


async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔔 *Friday Reminder*\n\n"
        "The week is almost done — have you scheduled your weekend content? "
        "Use your AI tools to batch-create posts and stay ahead! 💪",
        parse_mode="Markdown",
    )


# ---------- New member welcome ----------

async def welcome_new_member(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    for member in update.message.new_chat_members:
        name = member.full_name or member.username or "there"
        await update.message.reply_text(
            WELCOME_MESSAGE.format(name=name),
            parse_mode="Markdown",
        )


# ---------- Scheduled broadcasts ----------

def _start_scheduler(app) -> None:
    """Run schedule in a background thread so it doesn't block the bot."""

    def send_monday_tip():
        tip_text = _next_tip()
        for chat_id in _get_chat_ids():
            app.bot.send_message(
                chat_id=chat_id, text=tip_text, parse_mode="Markdown"
            )

    def send_friday_reminder():
        reminder = (
            "🔔 *Friday Reminder*\n\n"
            "The week is almost done — have you scheduled your weekend content? "
            "Use your AI tools to batch-create posts and stay ahead! 💪"
        )
        for chat_id in _get_chat_ids():
            app.bot.send_message(
                chat_id=chat_id, text=reminder, parse_mode="Markdown"
            )

    schedule.every().monday.at("09:00").do(send_monday_tip)
    schedule.every().friday.at("16:00").do(send_friday_reminder)

    def run():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


# Chat ID registry — populated as the bot receives messages
_active_chats: set[int] = set()


def _get_chat_ids() -> set[int]:
    return _active_chats


async def _track_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Track every chat the bot is active in for scheduled broadcasts."""
    if update.effective_chat:
        _active_chats.add(update.effective_chat.id)


# ---------- Main ----------

async def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Track chats for scheduled messages
    app.add_handler(MessageHandler(filters.ALL, _track_chat), group=-1)

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("tools", tools))
    app.add_handler(CommandHandler("remind", remind))

    # New member welcome
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member)
    )

    # Start background scheduler
    _start_scheduler(app)

    print("Bot is running...")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await app.updater.idle()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
