import asyncio, telebot
import os
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv


load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
bot = AsyncTeleBot(TOKEN_BOT)
user_data = {}

@bot.message_handler(commands=['start', 'help'])
async def start_handler(message):
    """Старт"""
    chat_id = message.chat.id
    await bot.send_message(chat_id, "🐾 Бот для помощи безнадзорным животным\n\nЧтобы сообщить о безнадзорном животном:\n1. Нажмите /report\n2. Заполните все обязательные поля\n3. Отправьте местоположение и фото животного\n\nВаша заявка будет передана в службу отлова.")

@bot.message_handler(commands=['report'])
async def report_handler(message):
    """Обработка команды report"""
    user_data[message.chat.id] = {}
    await bot.send_message(message.chat.id, "📝 Введите ваше ФИО (полностью):")




if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())
