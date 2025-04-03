import logging
import random
import re
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
from telegram import CopyTextButton

nest_asyncio.apply()

API_TOKEN = '7705193251:AAFrnXeNBgiFo3ZQsGNvEOa2lNzQPKo3XHM'
ADMIN_CHAT_ID = -1002651165474
USER_CHAT_ID = 5283100992
LOG_CHAT_ID = -1002411396364
ALLOWED_USERS = [5283100992, 6340673182, 5344318601, 1552417677, 1385118926, 6139706645, 5222780613]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Храним уже подтверждённые репорты
confirmed_reports = set()

# Возможные ответы на "РаФа"
rafa_responses = [
    "<b>Blue_Nexus иногда стает ебланом</b>", 
    "<b>Blue_Nexus держат в рабстве</b>",  
    "<b>Blue_Nexus абажает чат гпт</b>",
    "<b>Кирич любит аниме-тянок... но в жизни девушек он не любит</b>", 
    "<b>Изначально Кирич создавал канал про свою жизнь</b>", 
    "<b>Кирич невнимательный</b>",
    "<b>IDC - очень занятый человек... не спрашивайте чем, зачем и почему</b>", 
    "<b>IDC любит скамить детей на петов в адопт ми</b>", 
    "<b>IDC... я не придумал что он делает</b>",
    "<b>Freezee - успех успешный</b>", 
    "<b>Freezee - антипацифист☮</b>", 
    "<b>Freezee похуист по жизни</b>",
    "<b>Vipsii - долбаеб</b>", 
    "<b>Vipsii слишком глупый</b>", 
    "<b>Третий факт про себя Vipsii забыл</b>", 
    "<b>Exponnentik - повелитель чая</b>", 
    "<b>Exponnentik держит чери в заложниках</b>", 
    "<b>Exponnentik главный пупс кирича(кирич этого не знает)</b>",
    "<b>РаФа - сокращенно Рандом Факт про Андминов</b>"
]
  
# Возможные ответы для "РаФу"
rafu_responses = [
    "<b>Интересный факт! SsVladiSlaveSs не знает этот факт</b>", 
    "<b>На самом деле @khvtg не только отличный игрок, хороший администратор, щедрый согильдиец и крутой дизайнер – он еще и невероятно скромная личность</b>", 
    "<b>#Хаюш#Бой.#твикат#Not Хочет умереть от своей души</b>",
    "<b>Бомбабот на самом деле не бот🙈</b>",
    "<b>О пушочке: 11 лет, гей, ищет жену</b>",
    "<b>Ниндзя - майнкрафтер</b>",
    "<b>Тихий_Сон пытается найти мираж остров и на нем шестеренку для в4 рас в блокс фрукт</b>",
    "<b>Vloger про себя: я студент и очень тащус по аниме тянкам но в риле девушек боюсь</b>",
    "<b>StrazhTellOffichal Очень любит Юни, что он даже создал свой культ по своей любимой кошке Uni Cat</b>",
    "<b>Mapc - невероятный Python-айтишник с большим стажом валяния на кровати... накормите его пожалуйста</b>",
    "<b>Интересный факт: вся вселенная — это подвал, владелец которого — danyagreench.</b>",
    "<b>жду</b>",
    "<b>жду</b>",
    "<b>Просто чел - гей</b>",
    "<b>РаФу - сокращенно РАндом Факт про Участников</b>"
]

# Регулярное выражение для проверки формата причины репорта (например, "П1.3", "п1.3")
REPORT_REASON_REGEX = re.compile(r"^п\d+\.\d+$", re.IGNORECASE)

# Парсинг URL підключення до бази даних
DATABASE_URL = 'postgresql://neondb_owner:npg_PXgGyF7Z5MUJ@ep-shy-feather-a2zlgfcw-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require'
url = urlparse(DATABASE_URL)

# Параметри підключення з URL
DB_NAME = url.path[1:]  # Видаляємо перший символ '/' з шляху
DB_USER = url.username
DB_PASSWORD = url.password
DB_HOST = url.hostname
DB_PORT = url.port if url.port else 5432  # Встановлюємо порт, якщо він не вказаний в URL

# Підключення до бази даних
def create_reports_table():
    conn = psycopg2.connect(
        dbname=DB_NAME, 
        user=DB_USER, 
        password=DB_PASSWORD, 
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS reports')
    cur.execute('''
        CREATE TABLE reports (
            id SERIAL PRIMARY KEY,
            report_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("Таблиця створена успішно!")

# Функція для отримання всіх репортів
def get_reports():
    conn = psycopg2.connect(
        dbname=DB_NAME, 
        user=DB_USER, 
        password=DB_PASSWORD, 
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute('SELECT * FROM reports ORDER BY created_at DESC')
    reports = cur.fetchall()
    cur.close()
    conn.close()
    return reports

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
        await update.message.reply_text(
            "⚠️ <b>Репорт можно отправить только <i>ответом на сообщение</i>!</b>\n\n"
            "Пример репорта: <code>/report П1.3</code>",
            parse_mode=ParseMode.HTML
        )
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ <b>Не указана причина репорта!</b>\n\n"
            "Пример репорта: <code>/report П1.3</code>",
            parse_mode=ParseMode.HTML
        )
        return

    reason = context.args[0]
    if not REPORT_REASON_REGEX.match(reason):
        await update.message.reply_text(
            "⚠️ <b>Неверный формат причины!</b>\n\n"
            "Пример правильного формата: <code>/report П1.3</code>",
            parse_mode=ParseMode.HTML
        )
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
    
    await update.message.reply_text(
        f"Вы уверены, что хотите отправить репорт с причиной <b>{reason}</b>?",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    await log_action(f"📌 Репорт отправил {update.message.from_user.full_name} ({user_id}) с причиной {reason}")

# Функция обработки репорта
async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

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
            f"<blockquote>⚠️ <b>Новый репорт!</b>\n\n"
            f"👤 <b>Пользователь:</b> {reported_user_mention}\n"
            f"💬 <b>Сообщение:</b>\n<blockquote>{message_text}</blockquote>\n</blockquote>"
            f"🔗 <b>Ссылка:</b> {link_text}"
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

# Функция одержания ID чату
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    # Юзаем InlineKeyboardButton для кнопки копирования ID
    button = InlineKeyboardButton(text="Скопировать", copy_text=CopyTextButton(text=chat_id))
    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"🆔 ID этого чата: `{chat_id}`", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

# Оброботка кнопки Copy ID
async def handle_copy_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.data.split('_')[1]
    await query.answer()  # Отвечаем на запрос

# Кидаем сообщение, что ID скопировано
    await query.edit_message_text(f"✅ ID чата: `{chat_id}` скопировано!")

# Функция оброботки 
async def handle_message(update: Update, context):
    message = update.message.text.lower()
    
# Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    if message.lower() == "Неко".lower():
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        if admins:
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            sent_message = await update.message.reply_text("вычисления кошко-девочки по айпи💻")
            await asyncio.sleep(5)
            await sent_message.edit_text(f"Кошко-девочка вычислена! Она находится у @{random_username}")
        else:
            await update.message.reply_text("❌ Не удалось получить администраторов для вычислений!")

    elif message.lower() == "Пинг".lower():
        await update.message.reply_text("А нахуя он тебе?")

    elif message.lower() == "РаФа".lower():
        response = random.choice(rafa_responses)
        await update.message.reply_text(f"<b>{response}</b>", parse_mode=ParseMode.HTML)
    
    elif message.lower() == "РаФу".lower():
        response = random.choice(rafu_responses)
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)

    elif message.lower() == "привет".lower():  # Добавляем проверку на "привет" без учета регистра
        current_time = datetime.now(timezone.utc) + timedelta(hours=3)
        hour = current_time.hour

        if 5 <= hour < 7:
            response = "А ты спать не хочешь?"
        elif 7 <= hour < 13:
            response = "Доброго утра!"
        elif 13 <= hour < 17:
            response = "Хорошего дня!"
        elif 17 <= hour < 22:
            response = "Доброго вечера!"
        else:
            response = "А ну ка спать!"

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

async def main():
    print("Бот запущений!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
