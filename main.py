import asyncio, telebot
import os, re
from datetime import datetime
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv
from telebot import types

load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
bot = AsyncTeleBot(TOKEN_BOT)


user_steps = {}   #user_id: step    #FSM-словари
user_data = {}    #user_id: {данные}


STEPS = [
    'fio', 'phone', 'address', 'animal_count', 'photo'
]    #Шаги


@bot.message_handler(commands=['start', 'help'])
async def start_handler(message):
    """Старт"""
    chat_id = message.chat.id
    await bot.send_message(chat_id, "🐾 Бот для помощи безнадзорным животным\n\nЧтобы сообщить о безнадзорном животном:\n1. Нажмите /report\n2. Заполните все обязательные поля\n3. Отправьте местоположение и фото животного\n\nВаша заявка будет передана в службу отлова.")

@bot.message_handler(commands=['report'])
async def report_handler(message):
    """Обработка команды report"""
    user_id = message.chat.id
    user_steps[user_id] = 'fio'
    user_data[user_id] = {}
    await bot.send_message(user_id, "📝 Введите ваше ФИО полностью:")

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'fio')
async def handle_fio(message):
    """Получение ФИО"""
    if len(message.text.split()) < 2:
        await bot.send_message(message.chat.id, "❌ Укажите ФИО полностью.")
        return
    user_data[message.chat.id]['fio'] = message.text
    user_steps[message.chat.id] = 'phone'
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Отправить мой номер", request_contact=True))
    await bot.send_message(message.chat.id, "📱 Отправьте номер телефона или нажмите кнопку:", reply_markup=keyboard)

@bot.message_handler(content_types=['contact'])
async def handle_contact(message):
    """Телефон — автоматическая отправка своего контакта"""
    if user_steps.get(message.chat.id) != 'phone':
        return
    user_data[message.chat.id]['phone'] = message.contact.phone_number
    user_steps[message.chat.id] = 'address'
    await bot.send_message(message.chat.id, "🏠 Укажите адрес:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'phone')
async def handle_phone(message):
    """Телефон — вручную"""
    phone = message.text.strip()
    if not re.match(r'^\+?\d{10,15}$', phone):
        await bot.send_message(message.chat.id, "❌ Неверный формат телефона.")
        return
    user_data[message.chat.id]['phone'] = phone
    user_steps[message.chat.id] = 'address'
    await bot.send_message(message.chat.id, "🏠 Укажите адрес(населенный пункт, улица, дом):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'address')
async def handle_address(message):
    """Адрес"""
    if len(message.text) < 5:
        await bot.send_message(message.chat.id, "❌ Адрес слишком короткий.")
        return
    user_data[message.chat.id]['address'] = message.text
    user_steps[message.chat.id] = 'animal_count'
    await bot.send_message(message.chat.id, "🔢 Укажите количество животных:")

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'animal_count')
async def handle_count(message):
    """Обработка количества животных"""
    if not message.text.isdigit():
        await bot.send_message(message.chat.id, "❌ Введите число.")
        return
    user_data[message.chat.id]['animal_count'] = int(message.text)
    user_steps[message.chat.id] = 'photo'
    await bot.send_message(message.chat.id,
                           "📷 Прикрепите фото животного (или отправьте 'пропустить'):",
                           reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=['photo'])
async def handle_photo(message):
    """Фото"""
    if user_steps.get(message.chat.id) != 'photo':
        return
    user_data[message.chat.id]['photo'] = message.photo[-1].file_id

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'photo' and m.text.lower() == 'пропустить')
async def skip_photo(message):
    """Пропуск фото"""
    user_data[message.chat.id]['photo'] = None
    user_steps[message.chat.id] = 'description'
    await bot.send_message(message.chat.id, "✍️ Оставьте комментарий:")

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'description')
async def handle_description(message):
    """Описание и принятие заявки"""
    chat_id = message.chat.id
    user_data[chat_id]['description'] = message.text
    await bot.send_message(chat_id,
                           f"✅ Заявка принята!\n\n"
                           f"📌 Адрес: {user_data[chat_id]['address']}\n"
                           f"🔢 Кол-во животных: {user_data[chat_id]['animal_count']}\n"
                           f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                           "Спасибо за оставленное обращение! Информация будет передана сотрудникам!")


if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())
