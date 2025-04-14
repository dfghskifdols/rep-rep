from pyrogram import Client
import ntplib
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

def sync_time():
    try:
        c = ntplib.NTPClient()
        response = c.request('pool.ntp.org', version=3)
        print(f"Time synchronized: {ctime(response.tx_time)}")
    except Exception as e:
        print(f"Error synchronizing time: {e}")

# Виклик функції
sync_time()

# Головна функція
async def main():
    sync_time()

    app = Client("userbot", api_id=api_id, api_hash=api_hash)

    await app.start()
    logging.info("✅ Userbot запущено!")

    # Тримаємо бота живим
    try:
        while True:
            await asyncio.sleep(60)
    finally:
        await app.stop()
        logging.info("🛑 Userbot зупинено.")

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
