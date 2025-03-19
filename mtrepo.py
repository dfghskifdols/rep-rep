from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хэндлер для команды /report
@dp.message_handler(commands=['report'])
async def handle_report(message: types.Message):
    try:
        # Получаем текст отчета
        report_text = message.text

        # Если сообщение является репортом на конкретное сообщение, добавляем ссылку на это сообщение
        if message.reply_to_message:
            reported_message = message.reply_to_message
            message_link = f"https://t.me/{message.chat.username}/{reported_message.message_id}"  # Формируем ссылку на сообщение
            # Экранируем точку в ссылке
            message_link = message_link.replace('.', r'\.')  
            report_text += f"\n\nСсылка на сообщение: {message_link}"

        # Экранируем все специальные символы для MarkdownV2
        report_text = report_text.replace('*', r'\*').replace('_', r'\_').replace('[', r'\[').replace(']', r'\]')

        # Отправляем репорт в группу администрации
        await bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode=ParseMode.MARKDOWN_V2)

        # Подтверждаем пользователю, что репорт отправлен
        await message.reply("Репорт успешно отправлен!")

    except Exception as e:
        # Логируем и информируем пользователя о возможной ошибке
        await message.reply(f"Произошла ошибка при отправке репорта: {e}. Попробуйте позже.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
