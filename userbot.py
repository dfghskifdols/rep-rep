from pyrogram import Client
import pyrogram.utils  # ← окремо імпортуємо
import time
import logging
logging.basicConfig(level=logging.DEBUG)

api_id = 20375319  # Твій api_id, отриманий на my.telegram.org
api_hash = '4cb9df2254ee99282e0bd8b00ed1a636'  # Твій api_hash
phone_number = '+380 68 678 24 26'  # Твій номер телефону

# Створюємо об'єкт клієнта
app = Client("userbot", api_id=api_id, api_hash=api_hash)

# Функція авторизації
async def main():
    await app.start()

    print("Userbot успішно авторизувався!")

    # Після авторизації збережеться файл session
    await app.stop()

# Запускаємо авторизацію
app.run(main())
