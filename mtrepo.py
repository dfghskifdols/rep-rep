import nest_asyncio
import asyncio
import logging
import random
import re
import string
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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json

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
ALLOWED_USER_IDS = [5283100992, 5344318601, 5713511759]
LOG_CHAT_ID = -1002411396364
ALLOWED_USERS = [5283100992, 5713511759, 5344318601, 6340673182]
ADMINS_ALLOWED = [5283100992, 5713511759, 5344318601, 6340673182, 1385118926, 5222780613, 6139706645]
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

# Оновлення статусу репорту
async def update_report_status(report_key, status, accepted_by=None):
    conn = await connect_db()
    await conn.execute('''
        UPDATE user_reports
        SET status = $1, accepted_by = $2
        WHERE report_key = $3
    ''', status, accepted_by, report_key)
    await conn.close()

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
        await update.message.reply_text("❌ Нет доступа.")
        return

    # Перевірка, чи надано ключ репорту
    if len(context.args) == 0:
        await update.message.reply_text("❌ Пожалуйста введите правильно. Пример: /accept {ключ репорту}")
        return

    report_key = context.args[0]  # Ключ репорту з аргументів команди

    # Отримуємо репорт з бази даних за ключем
    report = await get_report_by_key(report_key)
    if not report:
        await update.message.reply_text(f"❌ Репорт с ключом {report_key} не найден!")
        return

    # Перевірка, чи репорт вже прийнятий
    if report['status'] == 'accepted':
        await update.message.reply_text(f"❌ Репорт с ключом {report_key} уже принят!")
        return

    # Оновлення статусу репорту в базі даних
    try:
        await update_report_status(report_key, 'accepted', str(user_id))
        await update.message.reply_text(f"✅ Репорт с ключом {report_key} успешно принят!")

    except Exception as e:
        await update.message.reply_text(f"❌ Случилась ошибка при обробке: {str(e)}")

# Команда для видалення репорту за ключем
async def delete_report(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ALLOWED_USER_IDS:
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
        await update.message.reply_text(f"❇️ Репорт с ключом <code>{report_key}</code> успешно удален.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"⚠️ Репорт с ключом <code>{report_key}</code> не найден.", parse_mode=ParseMode.HTML)

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
        status = report.get('status', 'not accepted')
        accepted_by = report.get('accepted_by')

        message_text += f"🔑Ключ репорта: <code>{report['report_key']}</code>\n"
        message_text += f"🆔ID юзера: {report['user_id']}\n"
        message_text += f"📩ID сообщения: {report['message_id']}\n"
        message_text += f"🔨Кто отправил: {report['reporter_name']}\n"
        message_text += f"🤕На кого: {report['reported_name']}\n"
        message_text += f"🔗Ссылка: {report['message_link']}\n"
        message_text += f"⌚️Время: {report['report_time']}\n"
        message_text += f"💭Текст: {report['reported_text']}\n"

        if status == "accepted":
            message_text += f"✅ Статус: принят (админ: {accepted_by})\n\n"
        else:
            message_text += f"🕐 Статус: не принят\n\n"

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
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML  # додаємо параметр для обробки HTML
        )
    else:
        print(f"Editing message: {message_text}")  # Логування
        await update.callback_query.message.edit_text(
            message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML  # додаємо параметр для обробки HTML
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

# Вставляємо новий репорт з усіма даними в таблицю, додаємо статус
    await conn.execute(''' 
        INSERT INTO user_reports (report_key, user_id, message_id, reporter_name, reported_name, message_link, report_time, reported_text, report_date, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'pending')  -- статус за замовчуванням
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
        f"🔊Вы уверены, что хотите отправить репорт?",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    # Логування
    if reason != "п1.0":
         await save_report(user_id, message_id, reason, reporter_name, reported_name, message_link, reported_text, report_date)
    await log_action(f"📌 Репорт отправил {update.message.from_user.full_name} ({user_id}) с причиной {reason}")

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
            f"🔑 <b>Ключ репорту:</b> <code>{report_key}</code>" 
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

        # Додаємо квиток користувачу в БД з урахуванням преміуму
        conn = await connect_db()
        is_banned = await conn.fetchval("SELECT banned FROM banned_users WHERE user_id = $1", reported_user.id)

        if is_banned is None or not is_banned:
            user = await conn.fetchrow("SELECT premium_until FROM user_tickets WHERE user_id = $1", reported_user.id)
            now = datetime.utcnow()
            is_premium = user and user["premium_until"] and user["premium_until"] > now
            multiplier = 2 if is_premium else 1

            await conn.execute("""
                INSERT INTO user_tickets (user_id, tickets)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET tickets = user_tickets.tickets + $2
            """, reported_user.id, multiplier)

        await conn.close()

    if admin_mentions:
        # Ділимо на 3 частини
        third = len(admin_mentions) // 3
        part1 = admin_mentions[:third]
        part2 = admin_mentions[third:third*2]
        part3 = admin_mentions[third*2:]

        await asyncio.sleep(4)
        await bot.send_message(ADMIN_CHAT_ID, "🔔 1: " + " ".join(part1))
        await asyncio.sleep(4)
        await bot.send_message(ADMIN_CHAT_ID, "🔔 2: " + " ".join(part2))
        await asyncio.sleep(4)
        await bot.send_message(ADMIN_CHAT_ID, "🔔 3: " + " ".join(part3))

        confirmed_reports.add(report_key)
        await query.message.edit_text("✅Репорт успешно отправлен!")
        await log_action(f"✅ Репорт подтверждён пользователем {query.from_user.full_name} ({query.from_user.id})")
    elif action == "cancel":
        await query.message.edit_text("❌ Репорт отменен.")
        await log_action(f"❌ Репорт отменён пользователем {query.from_user.full_name} ({query.from_user.id})")

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

    elif message.lower() == "топ прп":
        conn = await connect_db()  # Підключення до БД

        rows = await conn.fetch(""" 
            SELECT accepted_by, COUNT(*) AS count
            FROM user_reports
            WHERE status = 'accepted'
            GROUP BY accepted_by
            ORDER BY count DESC
            LIMIT 10
        """)

        all_rows = await conn.fetch(""" 
            SELECT accepted_by, COUNT(*) AS count
            FROM user_reports
            WHERE status = 'accepted'
            GROUP BY accepted_by
            ORDER BY count DESC
        """)

        current_user_id = update.message.from_user.id
        leaderboard = "<b>🏆 Топ 10 админов по кол-ву принятых репортов:</b>\n"

        for idx in range(10):
            if idx < len(rows):
                user_id = int(rows[idx]["accepted_by"])
                count = rows[idx]["count"]

                # Перевірка, чи має користувач преміум статус
                premium_until_row = await conn.fetchrow("""
                    SELECT premium_until FROM user_tickets WHERE user_id = $1
                """, user_id)

                # Якщо поле premium_until є і дата більше поточної
                if premium_until_row and premium_until_row["premium_until"] > datetime.now():
                    premium_icon = "💎"  # Додаємо значок для користувачів з преміум
                else:
                    premium_icon = ""  # Якщо преміум не активний

                try:
                    user = await bot.get_chat(user_id)
                    name = user.full_name
                    link = f"<a href='tg://user?id={user_id}'>{premium_icon} {name}</a>"
                except:
                    link = f"<code>{user_id}</code>"

                if user_id == current_user_id:
                    leaderboard += f"<b>{idx + 1} - {link} — {count} 📍</b>\n"
                else:
                    leaderboard += f"{idx + 1} - {link} — {count} 📍\n"
            else:
                leaderboard += f"{idx + 1} - \n"

        if current_user_id not in ADMINS_ALLOWED:
            leaderboard += "\n🙅‍♂️ Ты не админ, и тебя здесь нет."
        else:
            position = next((i + 1 for i, row in enumerate(all_rows) if int(row["accepted_by"]) == current_user_id), None)
            count = next((row["count"] for row in all_rows if int(row["accepted_by"]) == current_user_id), 0)

            if position:
                leaderboard += f"\n<b>Твое место: {position} - {count}📍</b>"
            else:
                leaderboard += f"\n<b>Твое место: {len(all_rows) + 1} - 0📍</b>"

        await conn.close()  # Закриваємо з'єднання з базою після всіх операцій

        await update.message.reply_text(leaderboard, parse_mode=ParseMode.HTML)
        return

    elif message == "рбаланс":
        conn = await connect_db()
        row = await conn.fetchrow("SELECT tickets, neko_coins, drops FROM user_tickets WHERE user_id = $1", user_id)
        await conn.close()

        if not row:
            await update.message.reply_text(
                "ℹ️ Для начала зарегестрируйтесь написав мне в лс /start."
            )
        else:
            await update.message.reply_text(
                f"Билеты: {row['tickets']}🎫\nNeko коины: {row['neko_coins']}🍥\nКапли: {row['drops']}💧"
            )
        return

    elif message == "топ билеты":
        conn = await connect_db()

        # Отримуємо топ-10
        top_users = await conn.fetch(""" 
            SELECT user_id, tickets, premium_until
            FROM user_tickets
            ORDER BY tickets DESC
            LIMIT 10
        """)

        # Отримуємо місце користувача
        user_rank_row = await conn.fetchrow(""" 
            SELECT row_number FROM (
                SELECT user_id, tickets, ROW_NUMBER() OVER (ORDER BY tickets DESC) AS row_number
                FROM user_tickets
            ) sub
            WHERE user_id = $1
        """, user_id)

        user_tickets_row = await conn.fetchrow(""" 
            SELECT tickets FROM user_tickets WHERE user_id = $1
        """, user_id)

        await conn.close()

        text = "🎫 Топ 10 пользователей по кол-ву билетов:\n"

        for i in range(10):
            if i < len(top_users):
                uid = top_users[i]["user_id"]
                tickets = top_users[i]["tickets"]
                premium_until = top_users[i]["premium_until"]

                # Додаємо значок 💎 якщо у користувача є преміум
                premium_icon = "💎" if premium_until and premium_until > datetime.now() else ""

                try:
                    user = await bot.get_chat_member(update.effective_chat.id, uid)
                    name = user.user.full_name
                except:
                    name = f"Пользователь {uid}"
                text += f"{i+1} - {premium_icon}{name} — {tickets} 🎟\n"
            else:
                text += f"{i+1} -\n"

        if user_rank_row and user_tickets_row:
            text += f"\nТвое место: {user_rank_row['row_number']} - {user_tickets_row['tickets']} 🎟"

        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    elif message.lower().startswith("рпромо"):
        parts = message.split()
        if len(parts) != 2:
            conn = await connect_db()
            rows = await conn.fetch("""
                SELECT code, max_uses, array_length(used_by, 1) AS used, created_by_bot
                FROM promo_codes
                WHERE (array_length(used_by, 1) IS NULL OR array_length(used_by, 1) < max_uses)
            """)
            await conn.close()

            if rows:
                active_promos = "\n".join([
                    f"{'🔅' if row['created_by_bot'] else '🔆'}<code>{row['code']}</code>" for row in rows
                ])
            else:
                active_promos = "🔸Нет активных промокодов."

            await update.message.reply_text(
                f"🤪 Использование: рпромо {{промокод}}\n"
                f"🥠список действующих промокодов:\n{active_promos}",
                parse_mode="HTML"
            )
            return

        promo_code = parts[1].lower()
        user_id = update.message.from_user.id

        conn = await connect_db()

        # Перевірка на бан
        banned = await conn.fetchval("SELECT banned FROM banned_users WHERE user_id = $1", user_id)
        if banned:
            await update.message.reply_text("🚫 Вы забанены!")
            await conn.close()
            return

        user = await conn.fetchrow("SELECT * FROM user_tickets WHERE user_id = $1", user_id)

        if not user:
            await update.message.reply_text("❌ Вы не зарегистрированы! Пожалуйста, используйте команду /start.")
            await conn.close()
            return

        promo = await conn.fetchrow("SELECT * FROM promo_codes WHERE code = $1", promo_code)

        if not promo:
            await update.message.reply_text("❌ Промокод не найден.")
            await conn.close()
            return

        if user_id in promo["used_by"]:
            await update.message.reply_text("⚠️ Вы уже использовали этот промокод.")
            await conn.close()
            return

        if promo["max_uses"] != 0 and len(promo["used_by"]) >= promo["max_uses"]:
            await update.message.reply_text("🚫 Промокод уже ввели макс кол-во пользователей.")
            await conn.close()
            return

        # Визначаємо множники
        in_clan = bool(user["clans"])
        premium_until = user.get("premium_until")
        now = datetime.now()
        is_premium = premium_until and premium_until > now

        if in_clan and is_premium:
            mult_tickets = 4
            mult_neko = 3.5
            mult_drops = 4
        elif not in_clan and is_premium:
            mult_tickets = 2
            mult_neko = 1.5
            mult_drops = 2
        elif in_clan and not is_premium:
            mult_tickets = 2
            mult_neko = 2
            mult_drops = 2
        else:
            mult_tickets = 1
            mult_neko = 1
            mult_drops = 1

        tickets_reward = promo.get("reward_tickets", 0) * mult_tickets
        neko_reward = promo.get("reward_neko_coins", 0) * mult_neko
        drops_reward = promo.get("reward_drops", 0) * mult_drops

        await conn.execute("""
            UPDATE user_tickets
            SET tickets = tickets + $1,
                neko_coins = neko_coins + $2,
                drops = drops + $3
            WHERE user_id = $4
        """, int(tickets_reward), int(neko_reward), int(drops_reward), user_id)

        await conn.execute("""
            UPDATE promo_codes
            SET used_by = array_append(used_by, $1)
            WHERE code = $2
        """, user_id, promo_code)

        await conn.close()

        rewards = []
        if tickets_reward:
            rewards.append(f"{int(tickets_reward)} 🎟️")
        if neko_reward:
            rewards.append(f"{int(neko_reward)} 🍥")
        if drops_reward:
            rewards.append(f"{int(drops_reward)} 💧")

        reward_msg = " и ".join(rewards)
        await update.message.reply_text(f"✅ Промокод активирован! Вы получили {reward_msg}")
        return

    elif message.lower().startswith("обмен "):
        parts = message.split()
        if len(parts) != 3 or not parts[2].isdigit():
            await update.message.reply_text("❌ Неправильный формат. Напишите, например: обмен н 2500, обмен к 1, обмен б 100")
            return

        typ = parts[1].lower()
        amount = int(parts[2])

        conn = await connect_db()
        user = await conn.fetchrow("SELECT * FROM user_tickets WHERE user_id = $1", user_id)

        if not user:
            await update.message.reply_text("❌ Вы не зарегистрированы! Пожалуйста, используйте команду /start.")
            await conn.close()
            return

        # Перевірка на преміум
        is_premium = user.get("premium_until") and user["premium_until"] > datetime.utcnow()

        # Курси
        ticket_to_coin = 200 if is_premium else 100
        drop_to_coin = 1000 if is_premium else 750
        coin_to_drop_cost = 2000 if is_premium else 2500

        if typ == "к":
            if user["drops"] < amount:
                await update.message.reply_text("❌ Недостаточно капель 💧.")
                await conn.close()
                return
            neko_add = amount * drop_to_coin
            await conn.execute("""
                UPDATE user_tickets
                SET drops = drops - $1,
                    neko_coins = neko_coins + $2
                WHERE user_id = $3
            """, amount, neko_add, user_id)
            await conn.close()
            await update.message.reply_text(f"✅ Обмен успешно! Вы обменяли {amount} 💧 на {neko_add} 🍥")
            return

        elif typ == "б":
            if user["tickets"] < amount:
                await update.message.reply_text("❌ Недостаточно билетов 🎟️.")
                await conn.close()
                return
            neko_add = amount * ticket_to_coin
            await conn.execute("""
                UPDATE user_tickets
                SET tickets = tickets - $1,
                    neko_coins = neko_coins + $2
                WHERE user_id = $3
            """, amount, neko_add, user_id)
            await conn.close()
            await update.message.reply_text(f"✅ Обмен успешно! Вы обменяли {amount} 🎟️ на {neko_add} 🍥")
            return

        elif typ == "н":
            if user["neko_coins"] < amount:
                await update.message.reply_text("❌ Недостаточно Neko коинов 🍥.")
                await conn.close()
                return
            drops_add = amount // coin_to_drop_cost
            if drops_add == 0:
                await update.message.reply_text("❌ Недостаточно Neko коинов для обмена на капли.")
                await conn.close()
                return
            await conn.execute("""
                UPDATE user_tickets
                SET neko_coins = neko_coins - $1,
                    drops = drops + $2
                WHERE user_id = $3
            """, amount, drops_add, user_id)
            await conn.close()
            await update.message.reply_text(f"✅ Обмен успешно! Вы обменяли {amount} 🍥 на {drops_add} 💧")
            return

        else:
            await update.message.reply_text("❌ Неизвестный тип обмена. Используйте к (капли), б (билеты) или н (неко коины).")
            await conn.close()
            return

    elif message == "топ капли":
        conn = await connect_db()

        top_users = await conn.fetch(""" 
            SELECT user_id, drops, premium_until
            FROM user_tickets
            ORDER BY drops DESC
            LIMIT 10
        """)

        user_rank_row = await conn.fetchrow(""" 
            SELECT row_number FROM (
                SELECT user_id, drops, ROW_NUMBER() OVER (ORDER BY drops DESC) AS row_number
                FROM user_tickets
            ) sub
            WHERE user_id = $1
        """, user_id)

        user_row = await conn.fetchrow(""" 
            SELECT drops FROM user_tickets WHERE user_id = $1
        """, user_id)

        await conn.close()

        text = "💧 Топ 10 пользователей по каплям:\n"

        for i in range(10):
            if i < len(top_users):
                uid = top_users[i]["user_id"]
                drops = top_users[i]["drops"]
                premium_until = top_users[i]["premium_until"]

                # Додаємо значок 💎 якщо у користувача є преміум
                premium_icon = "💎" if premium_until and premium_until > datetime.now() else ""

                try:
                    user = await bot.get_chat_member(update.effective_chat.id, uid)
                    name = user.user.full_name
                except:
                    name = f"Пользователь {uid}"
                text += f"{i+1} - {premium_icon}{name} — {drops} 💧\n"
            else:
                text += f"{i+1} -\n"

        if user_rank_row and user_row:
            text += f"\nТвое место: {user_rank_row['row_number']} - {user_row['drops']} 💧"

        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    elif message == "топ неко":
        conn = await connect_db()

        top_users = await conn.fetch(""" 
            SELECT user_id, neko_coins, premium_until
            FROM user_tickets
            ORDER BY neko_coins DESC
            LIMIT 10
        """)

        user_rank_row = await conn.fetchrow(""" 
            SELECT row_number FROM (
                SELECT user_id, neko_coins, ROW_NUMBER() OVER (ORDER BY neko_coins DESC) AS row_number
                FROM user_tickets
            ) sub
            WHERE user_id = $1
        """, user_id)

        user_row = await conn.fetchrow(""" 
            SELECT neko_coins FROM user_tickets WHERE user_id = $1
        """, user_id)

        await conn.close()

        text = "🍥 Топ 10 пользователей по Neko коинам:\n"

        for i in range(10):
            if i < len(top_users):
                uid = top_users[i]["user_id"]
                neko = top_users[i]["neko_coins"]
                premium_until = top_users[i]["premium_until"]

                # Додаємо значок 💎 якщо у користувача є преміум
                premium_icon = "💎" if premium_until and premium_until > datetime.now() else ""

                try:
                    user = await bot.get_chat_member(update.effective_chat.id, uid)
                    name = user.user.full_name
                except:
                    name = f"Пользователь {uid}"
                text += f"{i+1} - {premium_icon}{name} — {neko} 🍥\n"
            else:
                text += f"{i+1} -\n"

        if user_rank_row and user_row:
            text += f"\nТвое место: {user_rank_row['row_number']} - {user_row['neko_coins']} 🍥"

        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    elif message.lower() == "премиум купить":
        conn = await connect_db()
        row = await conn.fetchrow("SELECT drops, premium_until FROM user_tickets WHERE user_id = $1", user_id)

        if not row:
            await update.message.reply_text("ℹ️ Для начала зарегестрируйтесь написав мне в лс /start.")
            await conn.close()
            return

        now = datetime.utcnow()
        if row["premium_until"] and row["premium_until"] > now:
            await update.message.reply_text("⚠️ У вас уже есть активный Премиум.")
            await conn.close()
            return

        if row["drops"] < 15:
            await update.message.reply_text("❌ У вас недостаточно 💧 Капель для покупки Премиума (нужно 15).")
            await conn.close()
            return

        new_until = now + timedelta(days=60)

        await conn.execute("""
            UPDATE user_tickets
            SET drops = drops - 15,
                premium_until = $1
            WHERE user_id = $2
        """, new_until, user_id)

        await conn.close()

        await update.message.reply_text("✅ Вы успешно приобрели Премиум на 2 месяца за 15 💧 Капель!")
        return

    elif message.lower() == "мой премиум":
        conn = await connect_db()
        user = await conn.fetchrow("SELECT premium_until FROM user_tickets WHERE user_id = $1", user_id)
        await conn.close()

        if not user or not user["premium_until"]:
            await update.message.reply_text("❌ У вас нет активного премиума.")
            return

        now = datetime.utcnow()
        premium_until = user["premium_until"]

        if premium_until < now:
            await update.message.reply_text("❌ Ваш премиум истёк.")
            return

        formatted_date = premium_until.strftime("%d.%m.%Y %H:%M")
        await update.message.reply_text(f"💎 Премиум: активен\n📅 До: {formatted_date}")
        return

    # Создание клана
    elif message.startswith("создать клан "):
        clan_name = message[13:].strip()  # Получаем название клана

        if not clan_name:
            await update.message.reply_text("Пожалуйста, введите название клана.")
            return

        conn = await connect_db()

        lower_clan_name = clan_name.lower()

        existing_clan = await conn.fetchval("""
            SELECT COUNT(*) FROM user_tickets WHERE LOWER(clans) = $1
        """, lower_clan_name)

        if existing_clan and existing_clan > 0:
            await conn.close()
            await update.message.reply_text("Клан с таким названием уже существует. Пожалуйста, выберите другое имя.")
            return

        # Получаем информацию о пользователе
        user_row = await conn.fetchrow("""
            SELECT tickets, drops, neko_coins, premium_until, clans
            FROM user_tickets WHERE user_id = $1
        """, user_id)

        await conn.close()

        if user_row:
            if user_row["clans"]:
                await update.message.reply_text("Вы уже состоите в клане.")
                return

            tickets = user_row["tickets"]
            drops = user_row["drops"]
            neko_coins = user_row["neko_coins"]
            premium_until = user_row["premium_until"]
            current_time = datetime.now()

            if premium_until and premium_until > current_time and tickets >= 100 and drops >= 75 and neko_coins >= 100000:
                text = (
                    f"Вы уверены, что хотите создать клан с названием '{clan_name}'? Для этого будут списаны:\n"
                    "100 квитков, 75 капель, 100000 неко коинов.\n\n"
                    "Введите 'да' чтобы подтвердить или 'нет' чтобы отменить."
                )
                context.user_data['clan_create'] = {'name': clan_name}
                await update.message.reply_text(text)
            else:
                await update.message.reply_text("У вас недостаточно ресурсов или нет премиума для создания клана.")
        else:
            await update.message.reply_text("Информация о вашем аккаунте не найдена.")
        return

    elif message == "да":
        clan_info = context.user_data.get('clan_create')
        if not clan_info:
            return

        clan_name = clan_info['name']

        conn = await connect_db()
        user_row = await conn.fetchrow("""
            SELECT tickets, drops, neko_coins, premium_until, clans
            FROM user_tickets WHERE user_id = $1
        """, user_id)

        if user_row:
            if user_row["clans"]:
                await conn.close()
                await update.message.reply_text("Вы уже состоите в клане.")
                return

            tickets = user_row["tickets"]
            drops = user_row["drops"]
            neko_coins = user_row["neko_coins"]
            premium_until = user_row["premium_until"]
            current_time = datetime.now()

            if premium_until and premium_until > current_time and tickets >= 100 and drops >= 75 and neko_coins >= 100000:
                # Оновлюємо дані користувача
                await conn.execute("""
                    UPDATE user_tickets
                    SET clans = $1, tickets = tickets - 100, drops = drops - 75, neko_coins = neko_coins - 100000, rank = 'creator'
                    WHERE user_id = $2
                """, clan_name, user_id)

                # Додаємо новий клан у таблицю clans
                await conn.execute("""
                    INSERT INTO clans (name, members, leader)
                    VALUES ($1, ARRAY[$2]::BIGINT[], $2)
                """, clan_name, user_id)

                await conn.close()

                del context.user_data['clan_create']
                await update.message.reply_text(f"Клан '{clan_name}' успешно создан! Вы стали создателем этого клана.")
            else:
                await conn.close()
                await update.message.reply_text("У вас недостаточно ресурсов или нет премиума для создания клана.")
        else:
            await conn.close()
            await update.message.reply_text("Информация о вашем аккаунте не найдена.")
        return

    elif message == "нет":
        if context.user_data.get('clan_create'):
            del context.user_data['clan_create']
            await update.message.reply_text("Создание клана отменено.")
        return

    # Обработка команды "мой клан"
    elif message == "мой клан":
        conn = await connect_db()

        # Получаем информацию о пользователе
        user_row = await conn.fetchrow(""" 
            SELECT clans, rank FROM user_tickets WHERE user_id = $1
        """, user_id)

        await conn.close()

        if user_row:
            clan_name = user_row["clans"]
            user_rank = user_row["rank"]

            if clan_name and clan_name != "NULL":
                # Если пользователь состоит в клане
                conn = await connect_db()

                # Получаем список всех участников клана
                clan_members = await conn.fetch(""" 
                    SELECT user_id, rank FROM user_tickets WHERE clans = $1
                """, clan_name)

                await conn.close()

                if clan_members:
                    text = f"Ваш клан: {clan_name}\n\n"

                    # Выводим участников клана с их рангами
                    for member in clan_members:
                        member_user_id = member["user_id"]
                        rank = member["rank"]
                        try:
                            user = await bot.get_chat_member(update.effective_chat.id, member_user_id)
                            name = user.user.full_name
                        except:
                            name = f"Пользователь {member_user_id}"

                        if rank == "creator":
                            text += f"{name} - создатель\n"
                        else:
                            text += f"{name} - участник\n"

                    await update.message.reply_text(text)
                else:
                    await update.message.reply_text(f"В вашем клане нет участников кроме вас.")
            else:
                await update.message.reply_text("Вы не состоите в клане.")
        else:
            await update.message.reply_text("Информация о вашем аккаунте не найдена.")
        return

    elif message.startswith("клан вступить "):
        clan_name = message[14:].strip()  # Получаем название клана

        if not clan_name:
            await update.message.reply_text("Пожалуйста, введите название клана.")
            return

        conn = await connect_db()

        # Получаем информацию о пользователе
        user_row = await conn.fetchrow("""
            SELECT clans, rank FROM user_tickets WHERE user_id = $1
        """, user_id)

        if user_row:
            user_clan = user_row["clans"]

            if user_clan and user_clan != "NULL":
                # Если пользователь уже в клане
                await conn.close()
                await update.message.reply_text("Вы уже состоите в другом клане.")
                return

            # Проверяем, существует ли клан с таким названием
            clan_row = await conn.fetchrow("""
                SELECT members FROM clans WHERE name = $1
            """, clan_name)

            if clan_row:
                members = clan_row["members"]
                if user_id in members:
                    await conn.close()
                    await update.message.reply_text("Вы уже состоите в этом клане.")
                    return

                # Присоединяем пользователя
                await conn.execute("""
                    UPDATE clans SET members = array_append(members, $1) WHERE name = $2
                """, user_id, clan_name)

                # Обновляем данные пользователя
                await conn.execute("""
                    UPDATE user_tickets SET clans = $1, rank = 'member' WHERE user_id = $2
                """, clan_name, user_id)

                await conn.close()
                await update.message.reply_text(f"Вы успешно вступили в клан '{clan_name}'!")
            else:
                await conn.close()
                await update.message.reply_text(f"Клан с названием '{clan_name}' не существует.")
        else:
            await conn.close()
            await update.message.reply_text("Информация о вашем аккаунте не найдена.")
        return

    elif message.lower() == "кланы":
        conn = await connect_db()
        clans = await conn.fetch("""
            SELECT name, array_length(members, 1) AS count
            FROM clans
            ORDER BY count DESC NULLS LAST
        """)
        await conn.close()

        if not clans:
            await update.message.reply_text("❌ Кланы пока не созданы.")
            return

        clan_list = "\n".join([
            f"🏰 <b>{clan['name']}</b> — {clan['count'] or 0} участников"
            for clan in clans
        ])

        await update.message.reply_text(
            f"📜 Список всех кланов:\n\n{clan_list}",
            parse_mode="HTML"
        )

    elif message == "клан брать разрешить":
        conn = await connect_db()

        user_data = await conn.fetchrow("SELECT clans, rank FROM user_tickets WHERE user_id = $1", user_id)
        if not user_data or not user_data["clans"]:
            await conn.close()
            await update.message.reply_text("❗ Вы не состоите в клане.")
            return

        if user_data["rank"] != "creator":
            await conn.close()
            await update.message.reply_text("❗ Только лидер клана может разрешить доступ.")
            return

        await conn.execute("UPDATE clans SET allow_take = TRUE WHERE name = $1", user_data["clans"])
        await conn.close()
        await update.message.reply_text("✅ Теперь участники клана могут брать ресурсы из хранилища.")

    elif message == "клан брать запретить":
        conn = await connect_db()

        user_data = await conn.fetchrow("SELECT clans, rank FROM user_tickets WHERE user_id = $1", user_id)
        if not user_data or not user_data["clans"]:
            await conn.close()
            await update.message.reply_text("❗ Вы не состоите в клане.")
            return

        if user_data["rank"] != "creator":
            await conn.close()
            await update.message.reply_text("❗ Только лидер клана может запретить доступ.")
            return

        await conn.execute("UPDATE clans SET allow_take = FALSE WHERE name = $1", user_data["clans"])
        await conn.close()
        await update.message.reply_text("🚫 Теперь только лидер может брать ресурсы из хранилища.")

    elif message.startswith("клан взять ") or message.startswith("клан положить ") or message.startswith("клан брать "):
        parts = message.split()

        if message.startswith("клан брать "):
            if len(parts) < 4:
                await update.message.reply_text("❗ Формат: клан брать [ресурс] [количество]")
                return

            resource_input = parts[2].lower()
            quantity_input = parts[3].strip()

            resource_map = {
                "билет": "tickets",
                "билеты": "tickets",
                "нека": "neko_coins",
                "неко": "neko_coins",
                "койны": "neko_coins",
                "капля": "drops",
                "капли": "drops",
                "кап": "drops"
            }

            if not quantity_input.isdigit():
                await update.message.reply_text("❗ Количество должно быть целым числом.")
                return

            if resource_input not in resource_map:
                await update.message.reply_text("❗ Ресурс должен быть один из: билет, нека, капли.")
                return

            resource = resource_map[resource_input]
            quantity = int(quantity_input)

            conn = await connect_db()
            user_data = await conn.fetchrow("SELECT clans, rank FROM user_tickets WHERE user_id = $1", user_id)

            if not user_data or not user_data["clans"]:
                await conn.close()
                await update.message.reply_text("❗ Вы не входите в клан.")
                return

            if user_data["rank"] != "creator":
                await conn.close()
                await update.message.reply_text("❗ Только лидер клана может устанавливать лимиты.")
                return

            clan_name = user_data["clans"]

            clan_data = await conn.fetchrow("SELECT limits FROM clans WHERE name = $1", clan_name)
            limits = {}

            if clan_data and clan_data["limits"]:
                try:
                    limits = json.loads(clan_data["limits"])
                except Exception:
                    limits = {}

            limits[resource] = quantity

            await conn.execute("UPDATE clans SET limits = $1 WHERE name = $2", json.dumps(limits), clan_name)
            await conn.close()
            await update.message.reply_text(f"✅ Лимит на {resource_input} установлен: {quantity}")
            return

        if len(parts) < 4:
            await update.message.reply_text("❗ Формат: клан [взять/положить] [ресурс] [количество]")
            return

        action = parts[1].lower()
        resource_input = parts[2].lower()
        quantity_input = parts[3].strip()

        resource_map = {
            "билет": "tickets",
            "билеты": "tickets",
            "нека": "neko_coins",
            "неко": "neko_coins",
            "койны": "neko_coins",
            "капля": "drops",
            "капли": "drops",
            "кап": "drops"
        }

        if not quantity_input.isdigit():
            await update.message.reply_text("❗ Количество должно быть целым числом.")
            return

        if resource_input not in resource_map:
            await update.message.reply_text("❗ Ресурс должен быть один из: билет, нека, капли.")
            return

        quantity = int(quantity_input)
        resource = resource_map[resource_input]

        conn = await connect_db()
        user_data = await conn.fetchrow("SELECT clans, rank, neko_coins, tickets, drops FROM user_tickets WHERE user_id = $1", user_id)

        if not user_data or not user_data["clans"]:
            await conn.close()
            await update.message.reply_text("❗ Вы не входите в клан.")
            return

        clan_name = user_data["clans"]
        user_rank = user_data["rank"]

        clan_data = await conn.fetchrow("SELECT storage, limits, allow_take FROM clans WHERE name = $1", clan_name)

        if not clan_data:
            await conn.close()
            await update.message.reply_text("❗ Клан не найден.")
            return

        try:
            storage = json.loads(clan_data["storage"])
        except Exception:
            storage = {"tickets": 0, "neko_coins": 0, "drops": 0}

        try:
            limits = json.loads(clan_data["limits"]) if clan_data["limits"] else {}
        except Exception:
            limits = {}

        allow_take = clan_data["allow_take"]

        if action == "взять":
            if user_rank != "creator" and not allow_take:
                await conn.close()
                await update.message.reply_text("❗ Только лидер клана может забирать ресурсы из хранилища.")
                return

            # Проверка лимита
            if user_rank != "creator" and resource in limits:
                daily_taken = await conn.fetchval("""
                    SELECT SUM(amount) FROM clan_take_log
                    WHERE user_id = $1 AND clan = $2 AND resource = $3 AND DATE(date) = CURRENT_DATE
                """, user_id, clan_name, resource)

                daily_taken = daily_taken or 0
                if daily_taken + quantity > limits[resource]:
                    await conn.close()
                    await update.message.reply_text(f"❗ Превышен дневной лимит на {resource_input}. Осталось: {limits[resource] - daily_taken}")
                    return

            if storage.get(resource, 0) >= quantity:
                storage[resource] -= quantity
            else:
                await conn.close()
                await update.message.reply_text(f"❗ Недостаточно {resource_input} в хранилище клана.")
                return

            await conn.execute("UPDATE clans SET storage = $1 WHERE name = $2", json.dumps(storage), clan_name)

            await conn.execute(f"""
                UPDATE user_tickets SET {resource} = {resource} + $1 WHERE user_id = $2
            """, quantity, user_id)

            # Логируем выдачу
            await conn.execute("""
                INSERT INTO clan_take_log (user_id, clan, resource, amount, date)
                VALUES ($1, $2, $3, $4, NOW())
            """, user_id, clan_name, resource, quantity)

            await conn.close()
            await update.message.reply_text(f"✅ Вы успешно забрали {quantity} {resource_input} из хранилища клана.")

        elif action == "положить":
            # Проверка хватает ли у пользователя ресурса
            if user_data[resource] < quantity:
                await conn.close()
                await update.message.reply_text("❗ У вас недостаточно ресурсов.")
                return

            storage[resource] = storage.get(resource, 0) + quantity

            await conn.execute(f"""
                UPDATE user_tickets SET {resource} = {resource} - $1 WHERE user_id = $2
            """, quantity, user_id)

            await conn.execute("UPDATE clans SET storage = $1 WHERE name = $2", json.dumps(storage), clan_name)
            await conn.close()
            await update.message.reply_text(f"✅ Вы положили {quantity} {resource_input} в хранилище клана.")

    elif message == "клан хранилище":
        conn = await connect_db()

        user_data = await conn.fetchrow("SELECT clans FROM user_tickets WHERE user_id = $1", user_id)
        if not user_data or not user_data["clans"]:
            await conn.close()
            await update.message.reply_text("❗ Вы не состоите в клане.")
            return

        clan_name = user_data["clans"]

        clan_data = await conn.fetchrow("SELECT storage FROM clans WHERE name = $1", clan_name)
        await conn.close()

        if not clan_data:
            await update.message.reply_text("❗ Клан не найден.")
            return

        # Преобразуем JSON-строку в словарь
        try:
            storage = json.loads(clan_data["storage"])
        except Exception:
            storage = {"tickets": 0, "neko_coins": 0, "drops": 0}

        tickets = storage.get("tickets", 0)
        neko_coins = storage.get("neko_coins", 0)
        drops = storage.get("drops", 0)

        text = (
            f"📦 Хранилище клана <b>{clan_name}</b>:\n\n"
            f"🎫 Билеты: <b>{tickets}</b>\n"
            f"🐾 Неко коины: <b>{neko_coins}</b>\n"
            f"💧 Капли: <b>{drops}</b>"
        )

        await update.message.reply_text(text, parse_mode="HTML")

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    conn = await connect_db()
    await conn.execute("""
        INSERT INTO user_tickets (user_id, username)
        VALUES ($1, $2)
        ON CONFLICT (user_id) DO NOTHING
    """, user.id, user.username)
    await conn.close()

    await update.message.reply_text("Привет! Я Неко бот! Бот для репортов(наверное).")

def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

async def get_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else f"ID: {user_id}"

    conn = await connect_db()
    row = await conn.fetchrow("SELECT tickets FROM user_tickets WHERE user_id = $1", user_id)

    if not row or row['tickets'] < 15:
        await update.message.reply_text("❌ У вас недостаточно билетов (надо 15).")
        await conn.close()
        return

    await conn.execute("UPDATE user_tickets SET tickets = tickets - 15 WHERE user_id = $1", user_id)
    await conn.close()

    # Повідомлення користувачу
    await update.message.reply_text("Ваш запрос на получение награды отправлен!")

    # Посилання на повідомлення
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    chat_link = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"

    # Екранування юзернейму для Markdown
    escaped_username = escape_markdown(username)

    # Повідомлення адміну
    admin_text = f"📥 Запит: {escaped_username}\n🔗 [Перейти до повідомлення]({chat_link})"

    await context.bot.send_message(
        chat_id=USER_CHAT_ID,
        text=admin_text,
        parse_mode="MarkdownV2"
    )

async def rban_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Перевірка, чи є ви адміністратором
    if user_id != 5283100992:  # Ваш Telegram ID
        await update.message.reply_text("⛔️ У вас нету прав на эту команду.")
        return

    # Перевірка, чи є відповідь на повідомлення
    if not update.message.reply_to_message:
        await update.message.reply_text("💮 Используйте в ответ на сообщение.")
        return

    # Отримуємо айді користувача, якого банимо
    banned_user_id = update.message.reply_to_message.from_user.id

    # З'єднання з базою даних
    conn = await connect_db()
    
    # Додаємо користувача до таблиці забанених
    await conn.execute("INSERT INTO banned_users (user_id, banned) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET banned = $2", banned_user_id, True)
    
    # Очищаємо квитки цього користувача
    await conn.execute("UPDATE user_tickets SET tickets = 0 WHERE user_id = $1", banned_user_id)
    
    # Закриваємо з'єднання
    await conn.close()

    await update.message.reply_text(f"🚷 Пользователь {banned_user_id} забанен и все его билеты убраны.")

async def runban_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Перевірка, чи є ви адміністратором
    if user_id != 5283100992:  # Ваш Telegram ID
        await update.message.reply_text("⛔️ У вас нету прав на эту команду.")
        return

    # Перевірка, чи є відповідь на повідомлення
    if not update.message.reply_to_message:
        await update.message.reply_text("💮 Используйте в ответ на сообщение.")
        return

    # Отримуємо айді користувача, якого розбанюємо
    unbanned_user_id = update.message.reply_to_message.from_user.id

    # З'єднання з базою даних
    conn = await connect_db()

    # Знімаємо бан з користувача
    await conn.execute("UPDATE banned_users SET banned = FALSE WHERE user_id = $1", unbanned_user_id)
    
    # Закриваємо з'єднання
    await conn.close()

    await update.message.reply_text(f"✳️ Пользователь {unbanned_user_id} разбанен.")

# Функція для генерування випадкового промокоду
def generate_promo_code():
    return ''.join(random.choices(string.ascii_lowercase, k=8))

# Функція для визначення капель (тільки по неділях)
def get_drops():
    if datetime.now().weekday() == 6:  # Якщо сьогодні неділя
        return random.randint(1, 2)
    return 0

# Функція для генерації нагород
def generate_rewards():
    neko_coins = random.randint(10, 150)  # Випадкова кількість Neko коїнів
    drops = get_drops()  # Отримуємо каплі, якщо сьогодні неділя
    tickets = 0  # Квитки завжди 0
    return neko_coins, drops, tickets

# Функція для збереження промокоду в базі даних
async def insert_promo_code(promo_code, max_users, neko_coins, drops, tickets):
    conn = await connect_db()

    await conn.execute("""
        INSERT INTO promo_codes (code, reward_tickets, reward_neko_coins, reward_drops, max_uses, created_by_bot)
        VALUES ($1, $2, $3, $4, $5, TRUE)
    """, promo_code, tickets, neko_coins, drops, max_users)

    await conn.close()

# Основна функція для створення промокоду
async def create_promo_code():
    promo_code = generate_promo_code()  # Генерація промокоду
    neko_coins, drops, tickets = generate_rewards()  # Генерація нагород

    max_users = random.choice([30, 40, 50])  # Випадковий вибір з 30, 40 або 50

    await insert_promo_code(promo_code, max_users, neko_coins, drops, tickets)

    chat_id = -1002268486160  # Потрібно вказати chat_id

    message = f"😝Новый промо!\n🎁<code>рпромо {promo_code}</code>\n😮кол-во активаций: {max_users}"

    # Надсилаємо повідомлення
    sent_message = await bot.send_message(chat_id, message, parse_mode='HTML')

    # Прикріплюємо відправлене повідомлення
    await sent_message.pin()

# Функція для запуску задачі кожного дня
def start_daily_promo_code_task():
    scheduler = AsyncIOScheduler()
    # Запускаємо задачу о 9:00 по МСК кожного дня
    scheduler.add_job(create_promo_code, 'cron', hour=9, minute=30, timezone='Europe/Moscow')
    scheduler.start()

# Додаємо обробники для команд /ban та /unban, так само як і для /send
app.add_handler(CommandHandler("rban", rban_user))
app.add_handler(CommandHandler("runban", runban_user))

# Добавляем команду /send
app.add_handler(CommandHandler("send", send_message))

app.add_handler(CommandHandler("delete_report", delete_report))

app.add_handler(CommandHandler('accept', accept_report))

# Добавляем команду /id
app.add_handler(CommandHandler("id", get_chat_id))

app.add_handler(CommandHandler("show_reports", show_reports))
app.add_handler(CallbackQueryHandler(button, pattern="^page_\d+$"))

app.add_handler(CommandHandler("bot_stop", bot_stop))

app.add_handler(CommandHandler("get_reward", get_reward))

# Основной цикл программы
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report_command))
app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_\d+_\d+$"))
app.add_handler(MessageHandler(filters.Chat(GROUP_ID) & filters.TEXT, handle_message))
app.add_handler(CallbackQueryHandler(handle_copy_id, pattern="^copy_"))

# Основна функція для запуску бота
async def main():
    print("🚀 Бот запущений!")

    # Запускаємо планувальник для генерації промокодів
    start_daily_promo_code_task()

    # Запуск polling і фонової перевірки одночасно
    await asyncio.gather(app.run_polling())  # Це має бути твій Telegram бот

if __name__ == "__main__":
    asyncio.run(main())
