import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ParseMode
from aiogram.utils.exceptions import TelegramAPIError

# Токен бота
API_TOKEN = '7705193251:AAFQPcT5iNqlu4bnlcjV_lYjjZ7GZWzZHj4'

# ID группы, куда будут отправляться репорты (получить с помощью getidsbot или из логов)
ADMIN_GROUP_CHAT_ID = '-1002651165474'  # Заменить на настоящий chat_id группы администраторов

# Создание экземпляра бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Приветственное сообщение и инструкция по использованию
@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    await message.reply("Привет! Для отправки репорта о нарушении напиши: `/report Причина нарушения`")

# Обработчик для команды /report
@dp.message_handler(commands=['report'])
async def handle_report(message: Message):
    # Извлекаем текст репорта (после команды /report)
    report_text = message.get_args()

    if not report_text:
        await message.reply("Пожалуйста, укажи причину нарушения после команды. Пример: `/report Спам`")
        return

    # Создание и отправка репорта в группу администраторов
    try:
        # Формирование сообщения для отправки в группу
        report_message = f"🚨 **Новый репорт о нарушении!** 🚨\n\n" \
                         f"**Пользователь:** {message.from_user.full_name}\n" \
                         f"**ID пользователя:** {message.from_user.id}\n" \
                         f"**Причина нарушения:** {report_text}\n" \
                         f"**Дата:** {message.date.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Отправка репорта в группу
        await bot.send_message(ADMIN_GROUP_CHAT_ID, report_message, parse_mode=ParseMode.MARKDOWN)

        # Подтверждение отправки репорта пользователю
        await message.reply("Ваш репорт был отправлен администраторам для рассмотрения. Спасибо за помощь!")
    except TelegramAPIError as e:
        print(f"Ошибка при отправке репорта: {e}")
        await message.reply("Произошла ошибка при отправке репорта. Попробуйте позже.")

# Обработчик обычных сообщений
@dp.message_handler()
async def echo_message(message: Message):
    # Эхо-бот: бот повторяет все сообщения
    await message.answer(message.text)

# Главная функция для запуска бота с обработкой ошибок
async def main():
    try:
        print("Бот запущен...")
        await dp.start_polling()
    except TelegramAPIError as e:
        print(f"Ошибка при получении обновлений: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Запуск асинхронной функции main
if __name__ == '__main__':
    asyncio.run(main())
