import asyncio
import nest_asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram import CopyTextButton
import logging
import random

nest_asyncio.apply()

API_TOKEN = '7705193251:AAG0pWFSQfcu-S-huST-PU-OsxezNC2u67g'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
USER_CHAT_ID = 5283100992  # Ваш ID для отправки сообщений в ЛС
LOG_CHAT_ID = -1002411396364  # ID группы для логирования всех действий
ALLOWED_USERS = [5283100992, 6340673182, 5344318601, 1552417677, 1385118926, 6139706645]  # Список пользователей, которым разрешено отправлять сообщения

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Храним уже подтверждённые репорты
confirmed_reports = set()

# Возможные ответы на "РаФа"
rafa_responses = [
    "Hymanoid ненавидит меня, за то что я его не всегда пингую", "Blue_Nexus иногда стает ебланом", "Кирич невнимательный", 
    "IDC... я не придумал что он делает", "РаФа - сокращенно Рандом Факт", "Freezee похуист по жизни", "Humanoid постоянно ноет что у него нету твинка",
    "Blue_Nexus держат в рабстве", "Кирич любит аниме-тянок... но в жизни девушек он не любит", "IDC - очень занятый человек... не спрашивайте чем, зачем и почему",
    "Freezee - успех успешный", "Humanoid фанат пнг блю лок ждет 3 сезон сделанный в Microsoft Excel", "Blue_Nexus абажает чат гпт",
    "Изначально Кирич создавал канал про свою жизнь", "IDC любит скамить детей на петов в адопт ми", "Freezee - антипацифист☮️",
    "Vipsii - долбаеб", "Vipsii слишком глупый", "Третий факт про себя Vipsii забыл", 
    "Exponnentik - повелитель чая", "Exponnentik держит чери в заложниках", "Exponnentik главный пупс кирича(кирич этого не знает)"
]
  
# Возможные ответы для "РаФу"
rafu_responses = [
    "Интересный факт! SsVladiSlaveSs не знает этот факт", 
    "На самом деле @khvtg не только отличный игрок, хороший администратор, щедрый согильдиец и крутой дизайнер – он еще и невероятно скромная личность", 
    "Может ты хотел написать РаФа?", 
    "РаФу - сокращенно РАндом Факт про Участников"
]

# Функция отправки логов в группу
async def log_action(text: str):
    try:
        await bot.send_message(LOG_CHAT_ID, text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при отправке лога: {e}")

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /report в ответ на сообщение, чтобы отправить репорт.")

# Функция репорта
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Репорт можно отправить только ответом на сообщение!")
        return
    
    message_id = update.message.reply_to_message.message_id
    user_id = update.message.from_user.id
    report_key = f"{user_id}_{message_id}"

    if report_key in confirmed_reports:
        await update.message.reply_text("⚠️ Этот репорт уже был подтверждён!")
        return

    keyboard = [[
        InlineKeyboardButton("✅ Да", callback_data=f"confirm_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{user_id}_{message_id}")
    ]] 

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Вы уверены, что хотите отправить репорт?", reply_markup=reply_markup)
    await log_action(f"📌 Репорт отправил {update.message.from_user.full_name} ({user_id})")

# Функция обработки репорта
async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]
    try:
        user_id = int(data[1])
        message_id = int(data[2])
    except ValueError:
        await query.message.edit_text("❌ Ошибка: неверные данные для обработки репорта!")
        return

    if query.from_user.id != user_id:
        await query.answer(text="❌ Нельзя жмякать чужие репорты!", show_alert=True)
        return

    report_key = f"{user_id}_{message_id}"
    if report_key in confirmed_reports:
        await query.answer(text="⚠️ Этот репорт уже был обработан!", show_alert=True)
        return

    if action == "confirm":
        reported_message = query.message.reply_to_message
        reported_user = reported_message.from_user

        if query.message.chat.username:
            message_link = f"https://t.me/{query.message.chat.username}/{reported_message.message_id}"
            link_text = f"<a href='{message_link}'>Перейти к сообщению</a>"
        else:
            link_text = "Сообщение отправлено в приватном чате, ссылка недоступна."

        message_text = reported_message.text if reported_message.text else "(медиа-файл)"
        reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

        report_text = (
            f"⚠️ <b>Новый репорт!</b>\n\n"
            f"👤 Пользователь: {reported_user_mention}\n"
            f"💬 Сообщение:\n<blockquote>{message_text}</blockquote>\n"
            f"{link_text}"
        )

        await query.message.edit_text("⏳Отправка...")

        # Получаем администраторов
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
            await bot.send_message(ADMIN_CHAT_ID, "Первая часть админов: " + " ".join(admin_mentions[:half]))
            await asyncio.sleep(4)
            await bot.send_message(ADMIN_CHAT_ID, "Вторая часть админов: " + " ".join(admin_mentions[half:]))

        confirmed_reports.add(report_key)
        await query.message.edit_text("✅Репорт успешно отправлен!")
        await log_action(f"✅ Репорт подтверждён пользователем {query.from_user.full_name} ({query.from_user.id})")
    elif action == "cancel":
        await query.message.edit_text("❌ Репорт отменен.")
        await log_action(f"❌ Репорт отменён пользователем {query.from_user.full_name} ({query.from_user.id})")

# Функция обработки пинга администраторов
async def handle_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    
    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]  # Действие: ping

    if len(data) == 3:
        ping_answer = data[2]
        
        if ping_answer == "yes":
            await query.message.edit_text("⏳ Отправка репорта...")

            # Получаем администраторов
            admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
            admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

            # Отправляем репорт и пинг
            await bot.send_message(ADMIN_CHAT_ID, "Репорт от пользователя", parse_mode=ParseMode.HTML)

            if admin_mentions:
                half = len(admin_mentions) // 2
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Первая часть админов: " + " ".join(admin_mentions[:half]))
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Вторая часть админов: " + " ".join(admin_mentions[half:]))

            await query.message.edit_text("✅ Репорт и пинг отправлены!")
        elif ping_answer == "no":
            await query.message.edit_text("❌ Репорт отправлен без пинга.")
        else:
            await query.message.edit_text("❌ Ошибка: неверный ответ на вопрос о пинге.")
    else:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных для пинга.")

# Функция получения ID чата
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    # ID оброботка
    copy_button = InlineKeyboardButton("📋 Copy ID", callback_data=f"copy_{chat_id}")
    keyboard = [[copy_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"🆔 ID цього чату: `{chat_id}`", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

# Обработка кнопки Copy ID
async def handle_copy_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ ID скопировано!")

# Функция оброботки 
async def handle_message(update: Update, context):
    message = update.message.text.lower()
    
# Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    if message == "Неко":
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        if admins:
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            sent_message = await update.message.reply_text("вычисления кошко-девочки по айпи💻")
            await asyncio.sleep(5)
            await sent_message.edit_text(f"Кошко-девочка вычислена! Она находится у @{random_username}")
        else:
            await update.message.reply_text("❌ Не удалось получить администраторов для вычислений!")

    elif message == "Пинг":
        await update.message.reply_text("А нахуя он тебе?")

    elif message == "РаФа":
        response = random.choice(rafa_responses)
        await update.message.reply_text(response)
    
    elif message == "РаФу":
        response = random.choice(rafu_responses)
        await update.message.reply_text(response)

# Функция для отправки сообщений через бота
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка доступа
    if update.message.from_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    # Проверка на параметры
    if len(context.args) < 2:
        await update.message.reply_text("❌ Использование: /send [chat_id] [текст сообщения]")
        return

    chat_id = context.args[0]
    text = ' '.join(context.args[1:])

    try:
        sent_message = await bot.send_message(chat_id=chat_id, text=text)
        message_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{sent_message.message_id}"
        log_text = (f"📩 Сообщение отправлено через бота\n"
                    f"👤 Отправитель: {update.message.from_user.full_name} ({update.message.from_user.id})\n"
                    f"📍 В чат: {chat_id}\n"
                    f"💬 Текст: {text}\n"
                    f"🔗 <a href='{message_link}'>Ссылка на сообщение</a>")
        await log_action(log_text)
        await update.message.reply_text(f"✅ Сообщение отправлено {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Случилась ошибка: {e}")

# Добавляем команду /send
app.add_handler(CommandHandler("send", send_message))

# Добавляем команду /id
app.add_handler(CommandHandler("id", get_chat_id))

# Основной цикл программы
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report_command))
app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_"))
app.add_handler(CallbackQueryHandler(handle_ping, pattern="^(ping)_"))
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.add_handler(CallbackQueryHandler(handle_copy_id, pattern="^copy_"))

# Запускаем бота
if __name__ == "__main__":
    app.run_polling()
