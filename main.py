import asyncio, telebot
import os
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv


load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
bot = AsyncTeleBot(TOKEN_BOT)


@bot.message_handler(commands=['start'])
async def start_handler(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "Start")













if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())
