from telethon import TelegramClient, events
import asyncio

# Дані для авторизації
api_id = 20375319     # Візьми на my.telegram.org
api_hash = '4cb9df2254ee99282e0bd8b00ed1a636'
session_name = 'userbot'

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(pattern='/get_reward'))
async def handle_reward(event):
    sender = await event.get_sender()
    user_id = sender.id

    # Відповідь "дать миф 1"
    sent = await event.respond("дать миф 1", reply_to=event.id)

    # Через 1 секунду видаляємо повідомлення
    await asyncio.sleep(1)
    await client.delete_messages(event.chat_id, sent.id)

client.start()
print("Userbot працює!")
client.run_until_disconnected()
