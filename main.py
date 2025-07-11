import asyncio, os, re
from datetime import datetime
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv

from ggl_api import save_to_google_sheet    #Функция сохранения в Google Sheets


load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
bot = AsyncTeleBot(TOKEN_BOT)

user_steps = {}    #user_id: step
user_data = {}    #user_id: dict с данными

STEPS = ['fio', 'phone', 'address', 'animal_count', 'photo', 'description']    #Шаги

@bot.message_handler(commands=['start', 'help'])
async def start_handler(message):
    """Старт"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🆕 Новая заявка", callback_data="new_report"))
    await bot.send_message(
        message.chat.id,
        "🐾 Бот для помощи безнадзорным животным\n\n"
        "Чтобы сообщить о безнадзорном животном — нажмите кнопку ниже.",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda c: c.data == 'new_report')
async def start_report_callback(call):
    """Обработка команды report"""
    user_id = call.message.chat.id
    user_steps[user_id] = 'fio'
    user_data[user_id] = {}
    await bot.answer_callback_query(call.id)
    await bot.send_message(user_id, "📝 Введите ваше ФИО полностью:")

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'fio')
async def handle_fio(message):
    """Получение ФИО"""
    if len(message.text.split()) < 2:
        await bot.send_message(message.chat.id, "❌ Укажите ФИО полностью.")
        return
    user_data[message.chat.id]['fio'] = message.text
    user_steps[message.chat.id] = 'phone'
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("Отправить мой номер", request_contact=True))
    await bot.send_message(message.chat.id, "📱 Отправьте номер телефона или введите вручную:", reply_markup=keyboard)

@bot.message_handler(content_types=['contact'])
async def handle_contact(message):
    """Получение номера телефона"""
    if user_steps.get(message.chat.id) != 'phone':
        return
    user_data[message.chat.id]['phone'] = message.contact.phone_number
    user_steps[message.chat.id] = 'address'
    await bot.send_message(message.chat.id, "🏠 Укажите адрес (населённый пункт, улица, дом):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'phone')
async def handle_phone(message):
    """Получение номера телефона"""
    phone = message.text.strip()
    if not re.match(r'^\+?\d{10,15}$', phone):
        await bot.send_message(message.chat.id, "❌ Неверный формат телефона. Пример: +79161234567")
        return
    user_data[message.chat.id]['phone'] = phone
    user_steps[message.chat.id] = 'address'
    await bot.send_message(message.chat.id, "🏠 Укажите адрес (населённый пункт, улица, дом):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'address')
async def handle_address(message):
    """Получение адреса"""
    if len(message.text) < 5:
        await bot.send_message(message.chat.id, "❌ Адрес слишком короткий. Укажите подробнее.")
        return
    user_data[message.chat.id]['address'] = message.text
    user_steps[message.chat.id] = 'animal_count'
    await bot.send_message(message.chat.id, "🔢 Укажите количество безнадзорных животных:")

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'animal_count')
async def handle_count(message):
    """Обработка количества животных"""
    if not message.text.isdigit():
        await bot.send_message(message.chat.id, "❌ Введите число.")
        return
    user_data[message.chat.id]['animal_count'] = int(message.text)
    user_steps[message.chat.id] = 'photo'
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📷 Пропустить фото", callback_data='skip_photo'))
    await bot.send_message(message.chat.id, "📷 Прикрепите фото животного или нажмите кнопку ниже:",
                           reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == 'skip_photo')
async def skip_photo(call):
    """Обработка пропуска фото"""
    user_data[call.message.chat.id]['photo'] = None
    user_steps[call.message.chat.id] = 'description'
    await bot.send_message(call.message.chat.id, "✍️ Оставьте комментарий:")

@bot.message_handler(content_types=['photo'])
async def handle_photo(message):
    """Обработка фото"""
    if user_steps.get(message.chat.id) != 'photo':
        return
    file_id = message.photo[-1].file_id
    user_data[message.chat.id]['photo_id'] = file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    photo_url = f"https://api.telegram.org/file/bot{TOKEN_BOT}/{file_path}"    #Получаем ссылку на фото
    user_data[message.chat.id]['photo_url'] = photo_url
    user_steps[message.chat.id] = 'description'
    await bot.send_message(message.chat.id, "✍️ Оставьте комментарий:")

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'photo' and m.text and m.text.lower() == 'пропустить')
async def skip_photo(message):
    """Обработка пропуска фото"""
    user_data[message.chat.id]['photo_id'] = None
    user_data[message.chat.id]['photo_url'] = None
    user_steps[message.chat.id] = 'description'
    await bot.send_message(message.chat.id, "✍️ Оставьте комментарий / описание животного:")

@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'description')
async def handle_description(message):
    """Обработка комментария"""
    chat_id = message.chat.id
    user_data[chat_id]['description'] = message.text
    try:
        save_to_google_sheet(user_data[chat_id])    #Сохраняем в Google Sheets
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка при сохранении заявки: {e}")
        return
    await bot.send_message(
        chat_id,
        f"✅ Заявка принята!\n\n"
        f"📌 Адрес: {user_data[chat_id]['address']}\n"
        f"🔢 Количество животных: {user_data[chat_id]['animal_count']}\n"
        f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        "Спасибо за оставленное обращение! Информация будет передана сотрудникам!",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🆕 Создать новую заявку", callback_data="new_report")
        )
    )
    del user_steps[chat_id]    #Очистка данных
    del user_data[chat_id]


if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())
