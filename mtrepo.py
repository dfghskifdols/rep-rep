import logging
import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import Message
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# Токен твоего бота (замени на свой)
BOT_TOKEN = '7705193251:AAH_ourDVEerK6BIPZQTd_oZuFz7EingxrQ'

# chat_id группы администратора (замени на свой chat_id)
ADMIN_GROUP_CHAT_ID = 2651165474

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Обработчик команды /report
@dp.message_handler(commands=['report'])
async def handle_report(message: Message):
    report_text = message.get_args()

    if not report_text:
        await message.reply("Пожалуйста, напиши, кого и за что нужно заблокировать. Пример: `/report Спам`")
        return

    try:
        report_message = f"🚨 **Новый репорт о нарушении!** 🚨\n\n" \
                         f"**Пользователь:** {message.from_user.full_name}\n" \
                         f"**ID пользователя:** {message.from_user.id}\n" \
                         f"**Причина нарушения:** {report_text}\n" \
                         f"**Дата:** {message.date.strftime('%Y-%m-%d %H:%M:%S')}"

        # Логирование попытки отправки сообщения
        print(f"Попытка отправить сообщение в группу с chat_id: {ADMIN_GROUP_CHAT_ID}")

        # Отправка сообщения в группу администраторов
        await bot.send_message(ADMIN_GROUP_CHAT_ID, report_message, parse_mode=ParseMode.MARKDOWN)

        # Ответ пользователю
        await message.reply("Ваш репорт был отправлен администраторам для рассмотрения. Спасибо за помощь!")

    except Exception as e:
        # Логирование ошибки
        print(f"Ошибка при отправке репорта: {e}")
        traceback.print_exc()  # Показывает более подробную информацию об ошибке
        await message.reply(f"Произошла ошибка при отправке репорта: {e}. Попробуйте позже.")

# Получение chat_id группы при отправке сообщения
@dp.message_handler(content_types=['text'])
async def get_chat_id(message: Message):
    print(f"Chat ID: {message.chat.id}")  # Выведет chat_id группы, в которую отправлено сообщение

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
