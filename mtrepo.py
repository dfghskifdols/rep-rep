from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хэндлер для команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот!")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
