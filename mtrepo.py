import nest_asyncio
import asyncio
import logging
import random
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from urllib.parse import urlparse
from telegram import CopyTextButton
import sqlite3
import pytz
import time
import aiopg
import asyncpg
import math
from pytz import timezone

moscow_tz = timezone('Europe/Moscow')
current_time = datetime.now(moscow_tz)
hour = current_time.hour

bot_paused_until = None

# Глобальна змінна для зберігання ID користувачів, які написали "Репорт-бот-вопрос"
waiting_for_question = set()

nest_asyncio.apply()

REPORTS_PER_PAGE = 3
API_TOKEN = '7705193251:AAFrnXeNBgiFo3ZQsGNvEOa2lNzQPKo3XHM'
ADMIN_CHAT_ID = -1002651165474
USER_CHAT_ID = 5283100992
ALLOWED_USER_IDS = [5283100992, 5344318601]
LOG_CHAT_ID = -1002411396364
ALLOWED_USERS = [5283100992, 5713511759, 5344318601, 6340673182]
ADMINS_ALLOWED = [5283100992, 5713511759, 5344318601, 6340673182, 1385118926, 5222780613]
GROUP_ID = -1002268486160
LOG_CHATDEL_ID = -4665694960

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Возможные ответы на "РаФа"
rafa_responses = [
    "<b>Blue_Nexus иногда стает ебланом</b>", 
    "<b>Blue_Nexus держат в рабстве</b>",  
    "<b>Blue_Nexus абажает чат гпт</b>",
    "<b>Кирич любит аниме-тянок... но в жизни девушек он не любит</b>", 
    "<b>Изначально Кирич создавал канал про свою жизнь</b>", 
    "<b>Кирич невнимательный</b>",
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
    "<b>Интересный факт, SsVladiSlaveSs это SsVladiSlaveSs</b>",
    "<b>Александр любит котиков</b>",
    "<b>Просто чел - гей</b>",
    "<b>Кот ананас стал ананасом когда на его голову свалился ананас</b>",
    "<b>🐍ɥɥƎ очень боится собак</b>",
    "<b>У Люцика сегодня экзамен</b>",
    "<b>РаФу - сокращенно РАндом Факт про Участников</b>"
]

# Регулярное выражение для проверки формата причины репорта (например, "П1.3", "п1.3")
REPORT_REASON_REGEX = re.compile(r"^п\d+\.\d+$", re.IGNORECASE)

# Отримання репорту за ключем
async def get_report_by_key(report_key):
    conn = await connect_db()
    report = await conn.fetchrow('''
        SELECT * FROM user_reports WHERE report_key = $1
    ''', report_key)
    await conn.close()
    return report

# Функция отправки логов в группу
async def log_action(text: str):
    try:
        # Отправляем текст в лог-группу или канал
        await bot.send_message(LOG_CHAT_ID, text, parse_mode=ParseMode.HTML)
    except Exception as e:
        # Логируем ошибку, если что-то пошло не так
        logger.error(f"Ошибка при отправке лога: {e}")

async def accept_report(update, context):
    user_id = update.message.from_user.id

    # Перевірка чи користувач є адміністратором
    if user_id not in ADMINS_ALLOWED:
        await update.message.reply_text("❌ У вас немає прав для використання цієї команди.")
        return

    # Перевірка, чи надано ключ репорту
    if len(context.args) == 0:
        await update.message.reply_text("❌ Будь ласка, надайте ключ репорту після команди. Наприклад: /accept {ключ репорту}")
        return

    report_key = context.args[0]  # Ключ репорту з аргументів команди

    # Отримуємо репорт з бази даних за ключем
    report = await get_report_by_key(report_key)
    if not report:
        await update.message.reply_text(f"❌ Репорт з ключем {report_key} не знайдений!")
        return

    # Перевірка, чи репорт вже прийнятий
    if report['status'] == 'accepted':
        await update.message.reply_text(f"❌ Репорт з ключем {report_key} вже був прийнятий!")
        return

    # Оновлення статусу репорту в базі даних
    try:
        await update_report_status(report_key, "accepted", user_id)  # Оновлюємо статус репорту в базі
        await update.message.reply_text(f"✅ Репорт з ключем {report_key} був успішно прийнятий!")

    except Exception as e:
        await update.message.reply_text(f"❌ Сталася помилка при обробці репорту: {str(e)}")

# Команда для видалення репорту за ключем
async def delete_report(update: Update, context: CallbackContext):
    if update.message.from_user.id != ALLOWED_USER_IDS:
        await update.message.reply_text("🚫 У вас нету доступа к команде!.")
        return

    if not context.args:
        await update.message.reply_text("〽️ Укажите ключ репорта. Пример: /delete_report 12345_67890")
        return

    report_key = context.args[0]
    conn = await connect_db()
    result = await conn.execute("DELETE FROM user_reports WHERE report_key = $1", report_key)
    await conn.close()

    if result == "DELETE 1":
        await update.message.reply_text(f"❇️ Репорт з ключом <code>{report_key}</code> успешно удален.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"⚠️ Репорт з ключом <code>{report_key}</code> не найден.", parse_mode=ParseMode.HTML)

# Функция для остановки бота
async def bot_stop(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id  # Получаем ID пользователя

    # Проверяем, есть ли пользователь в списке разрешённых
    if user_id in ALLOWED_USER_IDS:
        try:
            minutes = int(context.args[0])  # Получаем количество минут из аргументов команды
            stop_time = time.time() + minutes * 60  # Бот останавливается на указанное время

            # Отправляем сообщение, что бот остановлен
            await update.message.reply_text(f"💤 Бот остановлен на {minutes} минут.")
            
            # Ждём указанное количество минут
            await asyncio.sleep(minutes * 60)

            # Возвращаем бота в рабочее состояние после завершения времени
            await update.message.reply_text("🛜 Бот снова запущен.")
        except (IndexError, ValueError):
            await update.message.reply_text("⚠️ Пожалуйста, введите время (в минутах). Пример: /bot_stop 5")
    else:
        await update.message.reply_text("⛔️ У вас нет доступа к этой команде.")

# Підключення до бази даних PostgreSQL
async def connect_db():
    return await asyncpg.connect(
        dsn='postgresql://neondb_owner:npg_PXgGyF7Z5MUJ@ep-shy-feather-a2zlgfcw-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require'
    )

# Отримання репортів з бази даних для сторінки
async def get_reports(page=1, reports_per_page=3):
    conn = await connect_db()
    offset = (page - 1) * reports_per_page
    rows = await conn.fetch(''' 
        SELECT * FROM user_reports
        ORDER BY report_date DESC
        LIMIT $1 OFFSET $2
    ''', reports_per_page, offset)
    await conn.close()
    return rows

# Отримуємо загальну кількість репортів
async def get_total_reports():
    conn = await connect_db()
    total_reports = await conn.fetchval('SELECT COUNT(*) FROM user_reports')
    await conn.close()
    return total_reports

# Показати репорти
async def show_reports(update, context, page=1):
    user_id = (
        update.effective_user.id if update.effective_user else None
    )

    if user_id not in ALLOWED_USERS:
        if update.message:
            await update.message.reply_text("⛔ У вас нету доступа к команде.")
        else:
            await update.callback_query.answer("⛔ Тебе нельзя", show_alert=True)
        return

    reports = await get_reports(page)
    total_reports = await get_total_reports()
    total_pages = math.ceil(total_reports / 3)

    if not reports:
        if update.message:
            await update.message.reply_text("🌐 Нету репортов.")
        else:
            await update.callback_query.message.reply_text("🌐 Нету репортов")
        return

    # Формуємо текст для показу
    message_text = "Список репортов:\n\n"
    for report in reports:
        message_text += f"🔑Ключ репорта: {report['report_key']}\n"
        message_text += f"🆔ID юзера: {report['user_id']}\n"
        message_text += f"🆔📩ID сообщения: {report['message_id']}\n"
        message_text += f"🔨Тот кто кинул репорт: {report['reporter_name']}\n"
        message_text += f"🤕Тот на кого кинули репорт: {report['reported_name']}\n"
        message_text += f"🔗Ссылка: {report['message_link']}\n"
        message_text += f"⌚️Время: {report['report_time']}\n"
        message_text += f"💭Текст: {report['reported_text']}\n\n"

    # Створюємо клавіатуру
    keyboard = []
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("←", callback_data=f"page_{page - 1}"))

    buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))

    if page < total_pages:
        buttons.append(InlineKeyboardButton("→", callback_data=f"page_{page + 1}"))

    keyboard.append(buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Відповідь (оновлення або нове повідомлення)
    if update.message:
        print(f"Replying with message: {message_text}")  # Логування
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        print(f"Editing message: {message_text}")  # Логування
        await update.callback_query.message.edit_text(
            message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

async def button(update, context):
    query = update.callback_query
    data = query.data

    if data.startswith("page_"):
        page = int(data.split("_")[1])
        await show_reports(update, context, page=page)
        await query.answer()

    print("test")

# Функція збереження репорту в базі даних
async def save_report(user_id, message_id, reason, reporter_name, reported_name, message_link, reported_text, report_date):
    conn = await connect_db()
    # Отримуємо поточний час у МСК
    report_time = datetime.now(moscow_tz).replace(tzinfo=None)

    # Генерація report_key на основі user_id та message_id
    report_key = f"{user_id}_{message_id}"

    # Вставляємо новий репорт з усіма даними в таблицю
    await conn.execute('''
        INSERT INTO user_reports (report_key, user_id, message_id, reporter_name, reported_name, message_link, report_time, reported_text, report_date)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    ''', report_key, user_id, message_id, reporter_name, reported_name, message_link, report_time, reported_text, report_date)

    await conn.close()

confirmed_reports = set()

# Функція обробки репорту
async def report_command(update: Update, context: CallbackContext):
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

    reason = context.args[0].lower()  # <- приводимо до нижнього регістру
    message = update.message  # отримуємо об'єкт повідомлення з update
    message_id = update.message.reply_to_message.message_id
    user_id = update.message.from_user.id
    report_key = f"{user_id}_{message_id}"
    reporter_name = update.message.from_user.full_name
    reported_name = update.message.reply_to_message.from_user.full_name
    message_link = f"https://t.me/{update.message.chat.username}/{message_id}"
    report_time = update.message.date
    reported_text = update.message.reply_to_message.text

    # Перевіряємо, чи є forward_date у повідомленні, якщо немає - використовуємо date
    report_date = message.forward_date if hasattr(message, 'forward_date') else message.date
    report_date = report_date.replace(tzinfo=None)

    if report_key in confirmed_reports:
        await update.message.reply_text("⚠️ Этот репорт уже был подтверждён!")
        return

    keyboard = [[
        InlineKeyboardButton("✅ Да", callback_data=f"confirm_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{user_id}_{message_id}")
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔊Вы уверены, что хотите отправить репорт с причиной <b>{reason}</b>?",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    # Логування
    await log_action(f"📌 Репорт отправил {update.message.from_user.full_name} ({user_id}) с причиной {reason}")

    # Не зберігати в БД, якщо причина п1.0 (в будь-якому регістрі)
    if reason != "п1.0":
        await save_report(user_id, message_id, reason, reporter_name, reported_name, message_link, reported_text, report_date)

# Обробка підтвердження або відхилення репорту
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
            f"🔗 <b>Ссылка:</b> {link_text}\n"
            f"🔑 <b>Ключ репорту:</b> {report_key}"
        )

        await query.message.edit_text("⏳ Отправка...")

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

async def command_handler(update: Update, context):
    global stop_time
    if stop_time is not None and time.time() < stop_time:
        await update.message.reply_text("Бот тимчасово зупинений. Спробуйте пізніше.")
        return 

# Функция одержания ID чату
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    # Юзаем InlineKeyboardButton для кнопки копирования ID
    button = InlineKeyboardButton(text="Скопировать", copy_text=CopyTextButton(text=chat_id))
    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"🆔 ID этого чата: {chat_id}", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

# Оброботка кнопки Copy ID
async def handle_copy_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.data.split('_')[1]
    await query.answer()  # Отвечаем на запрос

# Кидаем сообщение, что ID скопировано
    await query.edit_message_text(f"✅ ID чата: {chat_id} скопировано!")

# Основна функція обробки повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip().lower()  # Перетворюємо на малий регістр
    user_id = update.message.from_user.id

    # Обробка обох команд
    if message in ["рбв", "репорт бот вопрос"]:
        if user_id not in waiting_for_question:
            waiting_for_question.add(user_id)
            await update.message.reply_text("Слушаю! Напишите ваш вопрос.")
            asyncio.create_task(wait_for_response(user_id, update.message.chat_id, context))
        else:
            await update.message.reply_text("⏳ Я уже жду на твой вопрос! Напиши свой вопрос или подожди немного!")
        return

    elif user_id in waiting_for_question:
        waiting_for_question.remove(user_id)
        admin_id = 5283100992  # Твій Telegram ID
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"📩 Новый вопрос @{update.message.from_user.username or update.message.from_user.first_name}:\n\n{message}")
            await update.message.reply_text("✅ Ваш вопрос отправлен!")
        except Exception as e:
            await update.message.reply_text("❌ Случилась ошибка при отправке вопроса.")
            print(f"Ошибка отправки вопроса: {e}")
        return

    elif message in ["неко", "где неко"]:
        admins = await context.bot.get_chat_administrators(ADMIN_CHAT_ID)
        if admins:
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            sent_message = await update.message.reply_text("вычисления кошко-девочки по айпи💻")
            await asyncio.sleep(2)
            await sent_message.edit_text(f"Кошко-девочка вычислена! Она находится у @{random_username}")
        else:
            await update.message.reply_text("❌ Не удалось получить администраторов для вычислений!")

    elif message == "пинг":
        await update.message.reply_text("А нахуя он тебе?")

    elif message in ["рафа", "рандом факт админ"]:
        response = random.choice(rafa_responses)
        await update.message.reply_text(f"<b>{response}</b>", parse_mode=ParseMode.HTML)
    
    elif message in ["рафу", "рандом факт участники"]:
        response = random.choice(rafu_responses)  # Відповідь для РаФу
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)

    elif message in ["привет", "сап", "ку"]:  # Перевірка привітань
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

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напишите /report в ответ на сообщение, чтобы отправить репорт.")

# Добавляем команду /send
app.add_handler(CommandHandler("send", send_message))

app.add_handler(CommandHandler("delete_report", delete_report))

app.add_handler(CommandHandler('accept', accept_report))

# Добавляем команду /id
app.add_handler(CommandHandler("id", get_chat_id))

app.add_handler(CommandHandler("show_reports", show_reports))
app.add_handler(CallbackQueryHandler(button, pattern="^page_\d+$"))

app.add_handler(CommandHandler("bot_stop", bot_stop))

# Основной цикл программы
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report_command))
app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_\d+_\d+$"))
app.add_handler(MessageHandler(filters.Chat(GROUP_ID) & filters.TEXT, handle_message))
app.add_handler(CallbackQueryHandler(handle_copy_id, pattern="^copy_"))

async def main():
    print("🚀 Бот запущений!")

    # Запуск polling і фонової перевірки одночасно
    await asyncio.gather(app.run_polling())

if __name__ == "__main__":
    asyncio.run(main())
