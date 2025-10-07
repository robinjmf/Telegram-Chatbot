import asyncio
from typing import Dict, Any

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import settings
from memory import JsonMemory
from planner import generate_plan

# Conversation states
ASK_NAME, ASK_ROLE, ASK_AVAILABILITY = range(3)

memory = JsonMemory(settings.memory_path)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Hi! I'm your planning bot. What's your name?")
    return ASK_NAME


async def ask_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = (update.message.text or "").strip()
    await update.message.reply_text("Nice to meet you! What do you do or study?")
    return ASK_ROLE


async def ask_availability(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["role"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "How much time can you dedicate? (e.g., '2h/day', '10h/week', or both)"
    )
    return ASK_AVAILABILITY


def _parse_availability(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    hours_per_day = None
    hours_per_week = None

    # Very lightweight parsing
    import re
    day_match = re.search(r"(\d+(?:\.\d+)?)\s*h\s*/\s*day", text_lower)
    week_match = re.search(r"(\d+(?:\.\d+)?)\s*h\s*/\s*week", text_lower)
    if day_match:
        hours_per_day = float(day_match.group(1))
    if week_match:
        hours_per_week = float(week_match.group(1))

    # If user says just a number, assume hours per week
    if not day_match and not week_match:
        num = re.search(r"(\d+(?:\.\d+)?)", text_lower)
        if num:
            hours_per_week = float(num.group(1))

    return {
        "hours_per_day": hours_per_day,
        "hours_per_week": hours_per_week,
    }


async def finish_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    availability_text = (update.message.text or "").strip()
    availability = _parse_availability(availability_text)

    user = update.effective_user
    profile = {
        "name": context.user_data.get("name", ""),
        "role": context.user_data.get("role", ""),
        **availability,
    }
    memory.set_profile(user.id, profile)

    await update.message.reply_text(
        "Thanks! You can now send your goals or use /plan. Try sending a message like:\n"
        "'I can spend 2 hours during the week; thesis on SSL for MIR; follow up DB course; guitar tutorials. Give me a plan.'"
    )
    return ConversationHandler.END


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = memory.get_profile(user.id)
    if not profile:
        await update.message.reply_text("No profile saved yet. Use /start to set it up.")
        return

    hours_day = profile.get("hours_per_day")
    hours_week = profile.get("hours_per_week")

    lines = [
        f"Name: {profile.get('name','')}",
        f"Role: {profile.get('role','')}",
        f"Availability: "
        + ", ".join(
            s
            for s in [
                f"~{hours_day}h/day" if hours_day else None,
                f"~{hours_week}h/week" if hours_week else None,
            ]
            if s
        ),
    ]
    await update.message.reply_text("\n".join(lines))


async def reset_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    memory.reset(user.id)
    await update.message.reply_text("Your data has been cleared. Use /start to onboard again.")


async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = memory.get_profile(user.id)
    if not profile:
        await update.message.reply_text("No profile found. Use /start to set it up.")
        return

    goals_text = memory.get_last_goals(user.id)
    plan_text = generate_plan(profile, goals_text)
    await update.message.reply_text(plan_text)


async def free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text or ""
    user = update.effective_user
    memory.set_last_goals(user.id, user_text)

    profile = memory.get_profile(user.id)
    if not profile:
        await update.message.reply_text("I saved your message. Use /start to set your profile first.")
        return

    plan_text = generate_plan(profile, user_text)
    await update.message.reply_text(plan_text)


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_role)],
            ASK_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_availability)],
            ASK_AVAILABILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_onboarding)],
        },
        fallbacks=[],
    )

    application.add_handler(conv)
    application.add_handler(CommandHandler("profile", show_profile))
    application.add_handler(CommandHandler("reset", reset_profile))
    application.add_handler(CommandHandler("plan", plan_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_text))

    application.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
