import asyncio
import nest_asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import random

nest_asyncio.apply()

API_TOKEN = '7705193251:AAG0pWFSQfcu-S-huST-PU-OsxezNC2u67g'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID групи адміністрації
USER_CHAT_ID = 5283100992  # Ваш ID для відправки повідомлень в ЛС
LOG_CHAT_ID = -1002411396364  # ID групи для логування всіх дій

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Хранимо вже підтверджені репорти
confirmed_reports = set()

# Можливі відповіді на "РаФа"
rafa_responses = [
    "Hymanoid ненавидить мене, за те що я його не завжди пінгую", "Blue_Nexus іноді стає ебланом", "Кирич неуважний", 
    "IDC... я не придумав що він робить", "РаФа - скорочено Рандом Факт", "Freeze похуїст по життю", "Humanoid постійно нить, що у нього немає твинка",
    "Blue_Nexus тримають у рабстві", "Кирич любить аніме-тянок... але в житті дівчат він не любить", "IDC - дуже зайнята людина... не питайте чим, навіщо і чому",
    "Freeze - успіх успішний", "Humanoid фанат пнг блю лок чекає 3 сезон зроблений в Microsoft Excel", "Blue_Nexus обожає чат GPT",
    "Ізначально Кирич створював канал про своє життя", "IDC любить скамити дітей на петов в адопт мі", "Freeze - антипацифіст☮️"
]

# Можливі відповіді для "РаФу"
rafu_responses = [
    "Цікавий факт! SsVladiSlaveSs не знає цей факт", 
    "чекаю", 
    "чекаю",  
    "Може ти хотів написати РаФа?", 
    "РаФу - скорочено РАндом Факт про Учасників"
]

async def log_action(text: str):
    try:
        await bot.send_message(LOG_CHAT_ID, text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Помилка при відправці лога: {e}")

# Функція відправки повідомлення "Добре утро, мій господин!"
async def send_welcome_message():
    await bot.send_message(chat_id=USER_CHAT_ID, text="Добре утро, мій господин!")

# Функція старту
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Напиши /report в відповідь на повідомлення, щоб відправити репорт.")
    await log_action(f"✅ Команда /start від {update.message.from_user.full_name} ({update.message.from_user.id})")

# Функція репорту
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Репорт можна відправити тільки відповіддю на повідомлення!")
        return
    
    message_id = update.message.reply_to_message.message_id
    user_id = update.message.from_user.id
    report_key = f"{user_id}_{message_id}"

    if report_key in confirmed_reports:
        await update.message.reply_text("⚠️ Цей репорт вже був підтверджений!")
        return

    keyboard = [[
        InlineKeyboardButton("✅ Так", callback_data=f"confirm_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Ні", callback_data=f"cancel_{user_id}_{message_id}")
    ]]  

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Ви впевнені, що хочете відправити репорт?", reply_markup=reply_markup)
    await log_action(f"📌 Репорт від {update.message.from_user.full_name} ({user_id})")

# Функція обробки репорту
async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    if len(data) < 3:
        await query.message.edit_text("❌ Помилка: неправильний формат даних!")
        return

    action = data[0]
    try:
        user_id = int(data[1])
        message_id = int(data[2])
    except ValueError:
        await query.message.edit_text("❌ Помилка: невірні дані для обробки репорту!")
        return

    if query.from_user.id != user_id:
        await query.answer(text="❌ Нельзя натискати чужі репорти!", show_alert=True)
        return

    report_key = f"{user_id}_{message_id}"
    if report_key in confirmed_reports:
        await query.answer(text="⚠️ Цей репорт вже був оброблений!", show_alert=True)
        return

    if action == "confirm":
        reported_message = query.message.reply_to_message
        reported_user = reported_message.from_user

        if query.message.chat.username:
            message_link = f"https://t.me/{query.message.chat.username}/{reported_message.message_id}"
            link_text = f"<a href='{message_link}'>Перейти до повідомлення</a>"
        else:
            link_text = "Повідомлення надіслано в приватному чаті, посилання недоступне."

        message_text = reported_message.text if reported_message.text else "(медіа-файл)"
        reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

        report_text = (
            f"⚠️ <b>Новий репорт!</b>\n\n"
            f"👤 Користувач: {reported_user_mention}\n"
            f"💬 Повідомлення:\n<blockquote>{message_text}</blockquote>\n"
            f"{link_text}"
        )

        await query.message.edit_text("⏳Відправка...")

        # Отримуємо адміністраторів
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

        await bot.send_message(
            ADMIN_CHAT_ID, report_text,
            parse_mode=ParseMode.HTML,
            protect_content=True,
            disable_web_page_preview=True
        )

        if admin_mentions:
            half = len(admin_mentions) // 2
            await asyncio.sleep(4)
            await bot.send_message(ADMIN_CHAT_ID, "Перша частина адмінів: " + " ".join(admin_mentions[:half]))
            await asyncio.sleep(4)
            await bot.send_message(ADMIN_CHAT_ID, "Друга частина адмінів: " + " ".join(admin_mentions[half:]))

        confirmed_reports.add(report_key)
        await query.message.edit_text("✅Репорт успішно відправлений!")
        await log_action(f"✅ Репорт підтверджений користувачем {query.from_user.full_name} ({query.from_user.id})")
    elif action == "cancel":
        await query.message.edit_text("❌ Репорт скасовано.")
        await log_action(f"❌ Репорт скасовано користувачем {query.from_user.full_name} ({query.from_user.id})")

# Функція обробки пінгу адміністраторів
async def handle_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    
    if len(data) < 3:
        await query.message.edit_text("❌ Помилка: неправильний формат даних!")
        return

    action = data[0]  # Дія: ping

    if len(data) == 3:
        ping_answer = data[2]
        
        if ping_answer == "yes":
            await query.message.edit_text("⏳ Відправка репорту...")

            # Отримуємо адміністраторів
            admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
            admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

            # Відправляємо репорт і пінг
            await bot.send_message(ADMIN_CHAT_ID, "Репорт від користувача", parse_mode=ParseMode.HTML)

            if admin_mentions:
                half = len(admin_mentions) // 2
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Перша частина адмінів: " + " ".join(admin_mentions[:half]))
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Друга частина адмінів: " + " ".join(admin_mentions[half:]))

            await query.message.edit_text("✅ Репорт і пінг відправлені!")
        elif ping_answer == "no":
            await query.message.edit_text("❌ Репорт відправлений без пінгу.")
        else:
            await query.message.edit_text("❌ Помилка: невірна відповідь на питання про пінг.")
    else:
        await query.message.edit_text("❌ Помилка: неправильний формат даних для пінгу.")

# Функція отримання ID чату
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    await update.message.reply_text(f"🆔 ID цього чату: `{chat_id}`", parse_mode=ParseMode.MARKDOWN)

# Функція обробки повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Фільтрація простих повідомлень від учасників, не записуючи їх в лог
    if message.startswith('/'):
        # Якщо повідомлення — це команда, додаємо його в лог
        await log_action(f"💬 Команда: {update.message.text} від {update.message.from_user.full_name} ({update.message.from_user.id})")
    elif "рафа" in message:
        response = random.choice(rafa_responses)
        await update.message.reply_text(response)
        await log_action(f"💬 РаФа коментар від {update.message.from_user.full_name} ({update.message.from_user.id})")
    elif "рафу" in message:
        response = random.choice(rafu_responses)
        await update.message.reply_text(response)
        await log_action(f"💬 РаФу коментар від {update.message.from_user.full_name} ({update.message.from_user.id})")
    elif "пинг" in message:
        await update.message.reply_text("А нахуя він тобі?")
    elif "неко" in message:
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        if admins:
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            sent_message = await update.message.reply_text("Визначення кошко-девочки за айпі💻")
            await asyncio.sleep(5)
            await sent_message.edit_text(f"Кошко-девочка визначена! Вона знаходиться у @{random_username}")
            await log_action(f"😺 Неко-команда від {update.message.from_user.full_name} ({update.message.from_user.id})")
        else:
            await update.message.reply_text("❌ Не вдалося отримати адміністраторів для обчислень!")
    else:
        # Якщо це звичайне повідомлення, не додаємо його в лог
        return

# Функція для відправки повідомлень через бота
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Перевірка на доступ
    if update.message.from_user.id != USER_CHAT_ID:
        await update.message.reply_text("❌ У вас немає доступу до цієї команди.")
        return

    # Перевірка на наявність параметрів
    if len(context.args) < 2:
        await update.message.reply_text("❌ Використання: /send [chat_id] [текст повідомлення]")
        return

    chat_id = context.args[0]
    text = ' '.join(context.args[1:])

    try:
        await bot.send_message(chat_id=chat_id, text=text)
        await update.message.reply_text(f"✅ Повідомлення відправлене {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Сталася помилка: {e}")

# Додаємо команду /send
app.add_handler(CommandHandler("send", send_message))

# Додаємо команду /id
app.add_handler(CommandHandler("id", get_chat_id))

# Основна функція
async def main():
    await send_welcome_message()

    app.add_handler(CommandHandler("id", get_chat_id))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
