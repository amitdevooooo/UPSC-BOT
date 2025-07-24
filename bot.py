import logging
import os
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import google.generativeai as genai

# === Load .env ===
load_dotenv()

BOT_TOKEN = "7992369115:AAHClwij4Y1fjdTlHByn1_dwsQ5yhdsgh-4"
GOOGLE_API_KEY = "AIzaSyAaq1cziEhGEYbhWl64zuykOROSiWFyRXQ"
GROUP_ID = -1002131345978

# === Configure Gemini ===
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-pro")

logging.basicConfig(level=logging.INFO)

# === GK Questions ===
questions = [
    {
        "question": "Who was the first President of India?",
        "options": ["Dr. Rajendra Prasad", "Jawaharlal Nehru", "B. R. Ambedkar", "Mahatma Gandhi"],
        "answer": "Dr. Rajendra Prasad"
    },
    {
        "question": "Which river is known as the 'Sorrow of Bengal'?",
        "options": ["Ganga", "Damodar", "Yamuna", "Sutlej"],
        "answer": "Damodar"
    }
]

user_scores = {}

# === Gemini AI Answer ===
async def ai_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await update.message.reply_text("Thinking... 🤖")
    try:
        response = gemini_model.generate_content(question)
        answer = response.text.strip()
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"Gemini error: {e}")

# === Auto Quiz Function ===
async def send_quiz(context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(questions)
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"{opt}|{q['answer']}|{context.job.chat_id}")] for opt in q["options"]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🧠 *Quiz Time!*\n\n*{q['question']}*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# === Answer Handler ===
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected, correct, chat_id = query.data.split("|")
    user = query.from_user
    if selected == correct:
        response = f"✅ Correct! Answer: *{correct}*"
        user_scores[user.id] = user_scores.get(user.id, 0) + 1
    else:
        response = f"❌ Wrong! Correct answer: *{correct}*"
    await query.edit_message_text(text=response, parse_mode="Markdown")

# === Leaderboard ===
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_scores:
        await update.message.reply_text("No scores yet!")
        return
    top = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 *Leaderboard:*\n"
    for i, (uid, score) in enumerate(top, 1):
        user = await context.bot.get_chat_member(GROUP_ID, uid)
        text += f"{i}. {user.user.full_name} - {score} points\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# === Start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Welcome to Static GK Bot! Daily UPSC quizzes will be posted automatically. Type /leaderboard to check scores. You can also ask any question to AI.")

# === Setup ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(handle_answer))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_answer))

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_quiz, 'interval', minutes=1, args=[app])
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()
