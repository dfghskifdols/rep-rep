from telethon import TelegramClient, events
import asyncio

# Дані для авторизації
api_id = 20375319     # Візьми на my.telegram.org
api_hash = '4cb9df2254ee99282e0bd8b00ed1a636'
session_name = 'userbot'

# Ваш номер телефону
phone_number = '+380686782426'  # Замініть на свій номер телефону

client = TelegramClient(session_name, api_id, api_hash)

async def main():
    # Авторизація
    await client.start(phone_number)

    # Обробка команди /get_reward
    @client.on(events.NewMessage(pattern='/get_reward'))
    async def handle_reward(event):
        sender = await event.get_sender()
        user_id = sender.id

        # Відповідь "дать миф 1"
        sent = await event.respond("дать миф 1", reply_to=event.id)

        # Через 1 секунду видаляємо повідомлення
        await asyncio.sleep(1)
        await client.delete_messages(event.chat_id, sent.id)

    print("Userbot працює!")
    await client.run_until_disconnected()

# Запуск
asyncio.run(main())
