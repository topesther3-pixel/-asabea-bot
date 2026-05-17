"""
AsabeaCreates Campaign Bot
Built with python-telegram-bot 20.7 (stable, synchronous polling pattern).
"""

import logging
import os
import schedule
import threading
import time

from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

TIPS: list[str] = [
    (
        "🤖 *ChatGPT Tip of the Week*\n\n"
        "Use ChatGPT to draft your campaign captions in seconds! "
        "Try prompts like:\n"
        "_\"Write a catchy Instagram caption for a back-to-school sale "
        "targeting teens.\"_\n\n"
        "Refine the output by adding your brand voice and emojis. 🎯"
    ),
    (
        "🧠 *Grok Tip of the Week*\n\n"
        "Grok can help you analyse trending topics in real time. "
        "Ask it what's buzzing in your niche and use those insights "
        "to shape your next campaign angle. 📈"
    ),
    (
        "🎬 *CapCut Tip of the Week*\n\n"
        "Speed up your video editing with CapCut's auto-captions feature. "
        "Upload your clip, enable captions, then customise the font and "
        "colour to match your brand. Perfect for Reels & TikToks! ✂️"
    ),
    (
        "🎵 *Suno Tip of the Week*\n\n"
        "Need a jingle for your ad? Use Suno to generate royalty-free "
        "background music in seconds. Describe the mood and genre, "
        "download the track, and drop it straight into your video. 🎶"
    ),
]

TOOLS_MESSAGE: str = (
    "🛠 *Digital Campaign Tools We Cover*\n\n"
    "• 🤖 [ChatGPT](https://chat.openai.com) — AI copywriting & content ideation\n"
    "• 🧠 [Grok](https://grok.x.ai) — Real-time trend analysis & research\n"
    "• 🎬 [CapCut](https://www.capcut.com) — Fast, professional video editing\n"
    "• 🎵 [Suno](https://suno.com) — AI-generated music & jingles\n\n"
    "Use /tip to get the latest weekly tip!"
)

FRIDAY_REMINDER: str = (
    "🔔 *Friday Reminder*\n\n"
    "The week is almost done — have you scheduled your weekend content? "
    "Use your AI tools to batch-create posts and stay ahead! 💪"
)

MONDAY_MOTIVATION: str = (
    "🌟 *Monday Motivation*\n\n"
    "New week, new campaign opportunities! Here's your tip to kick things off:\n\n"
)

WELCOME_TEMPLATE: str = (
    "👋 Welcome to the group, {name}!\n\n"
    "This is your hub for weekly digital campaign tips covering "
    "ChatGPT, Grok, CapCut, Suno, and more. 🚀\n\n"
    "Type /help to see what I can do."
)

# ---------------------------------------------------------------------------
# State — chat IDs collected as the bot receives updates
# ---------------------------------------------------------------------------

_active_chats: set[int] = set()
_tip_index: int = 0


def _next_tip() -> str:
    """Return the next tip in rotation."""
    global _tip_index
    tip = TIPS[_tip_index % len(TIPS)]
    _tip_index += 1
    return tip


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_chat(update)
    await update.message.reply_text(
        "👋 Hey! I'm your digital campaign assistant bot.\n\n"
        "I share weekly tips on tools like ChatGPT, Grok, CapCut & Suno "
        "to help you run better campaigns.\n\n"
        "Type /help to see all available commands.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_chat(update)
    await update.message.reply_text(
        "📋 *Available Commands*\n\n"
        "/start — Introduction to the bot\n"
        "/help — Show this help message\n"
        "/tip — Get the latest weekly digital campaign tip\n"
        "/tools — List all tools we cover with links\n"
        "/remind — Get a posting reminder right now",
        parse_mode="Markdown",
    )


async def cmd_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_chat(update)
    await update.message.reply_text(_next_tip(), parse_mode="Markdown")


async def cmd_tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_chat(update)
    await update.message.reply_text(
        TOOLS_MESSAGE,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_chat(update)
    await update.message.reply_text(FRIDAY_REMINDER, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# New member welcome
# ---------------------------------------------------------------------------

async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_chat(update)
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        name = member.full_name or member.username or "there"
        await update.message.reply_text(
            WELCOME_TEMPLATE.format(name=name),
            parse_mode="Markdown",
        )


# ---------------------------------------------------------------------------
# Chat tracking helper
# ---------------------------------------------------------------------------

def _register_chat(update: Update) -> None:
    """Add the chat to the active set so scheduled messages reach it."""
    if update.effective_chat:
        _active_chats.add(update.effective_chat.id)


async def _track_all_chats(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Catch-all handler that registers every chat the bot hears from."""
    _register_chat(update)


# ---------------------------------------------------------------------------
# Scheduled broadcasts
# ---------------------------------------------------------------------------

def _broadcast(bot: Bot, text: str) -> None:
    """Send *text* to every known active chat."""
    for chat_id in list(_active_chats):
        try:
            bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as exc:
            logger.warning("Failed to send scheduled message to %s: %s", chat_id, exc)


def _start_scheduler(bot: Bot) -> None:
    """Configure and launch the background scheduler thread."""

    def monday_tip() -> None:
        logger.info("Sending Monday motivation tip to %d chats", len(_active_chats))
        _broadcast(bot, MONDAY_MOTIVATION + _next_tip())

    def friday_reminder() -> None:
        logger.info("Sending Friday reminder to %d chats", len(_active_chats))
        _broadcast(bot, FRIDAY_REMINDER)

    schedule.every().monday.at("09:00").do(monday_tip)
    schedule.every().friday.at("16:00").do(friday_reminder)

    def _run_loop() -> None:
        while True:
            schedule.run_pending()
            time.sleep(30)

    thread = threading.Thread(target=_run_loop, daemon=True, name="scheduler")
    thread.start()
    logger.info("Background scheduler started.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    # Catch-all handler (group -1 runs before everything else) to track chats
    app.add_handler(MessageHandler(filters.ALL, _track_all_chats), group=-1)

    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("tip", cmd_tip))
    app.add_handler(CommandHandler("tools", cmd_tools))
    app.add_handler(CommandHandler("remind", cmd_remind))

    # New member welcome
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member)
    )

    # Start the background scheduler (needs the Bot object, available after build)
    _start_scheduler(app.bot)

    logger.info("AsabeaCreates bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

