import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

API_TOKEN = '7705193251:AAFQPcT5iNqlu4bnlcjV_lYjjZ7GZWzZHj4'  # Замени на токен твоего бота
ADMIN_CHAT_ID = '-1002651165474'  # Замени на ID твоей группы

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для репортов. Напиши мне /report для отправки жалобы.")

# Команда /report
@dp.message_handler(commands=['report'])
async def handle_report(message: types.Message):
    await message.reply("Пожалуйста, напиши, кого и за что нужно заблокировать.")
    # Сохраняем команду и ждём следующего сообщения для отчёта
    await dp.register_message_handler(save_report, state='report', content_types=types.ContentTypes.TEXT)

async def save_report(message: types.Message):
    report = message.text
    await bot.send_message(ADMIN_CHAT_ID, f"Новый репорт: {report}")
    await message.reply("Ваш репорт был отправлен администратору.")
    await dp.unregister_message_handler(save_report)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
