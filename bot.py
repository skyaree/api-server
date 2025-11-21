import requests
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') 
API_BASE_URL = os.getenv('API_BASE_URL')

if not TOKEN or not API_BASE_URL:
    exit()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎰 Крутить (20 💰)", callback_data='roll'),
        InlineKeyboardButton("💼 Инвентарь", callback_data='inventory'),
        InlineKeyboardButton("❓ Помощь", callback_data='help')
    )
    return keyboard

def api_get_player_status(user_id: int):
    try:
        response = requests.get(f"{API_BASE_URL}/player/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def api_roll(user_id: int):
    try:
        response = requests.post(f"{API_BASE_URL}/game/roll/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return e.response.json()
        return None
    except requests.RequestException:
        return None

def api_get_inventory(user_id: int):
    try:
        response = requests.get(f"{API_BASE_URL}/inventory/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    
    data = api_get_player_status(user_id)
    
    if data and data.get('status') == 'success':
        text = (
            f"Добро пожаловать в RNG-Bot, **{message.from_user.first_name}**!\n"
            f"Ваш баланс: {data['money']} 💰.\n"
            f"Нажмите 'Крутить', чтобы начать игру!"
        )
    else:
        text = "Произошла ошибка при подключении к игровому серверу. Попробуйте позже."

    await message.reply(text, reply_markup=get_main_keyboard(), parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data == 'roll')
async def process_roll(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    
    data = api_roll(user_id)
    
    if not data:
        message_text = "Произошла критическая ошибка при обращении к API."
    
    elif data.get('status') == 'success':
        message_text = (
            f"🎉 **ПОЗДРАВЛЯЮ!** 🎉\n"
            f"Вы выкрутили: **{data['item']}**!\n"
            f"Ваш новый баланс: {data['new_money']} 💰."
        )
    elif data.get('detail') == 'Недостаточно средств.':
        player_status = api_get_player_status(user_id)
        current_money = player_status.get('money', '???') if player_status else '???'
        message_text = (
            f"⚠️ **Недостаточно средств.**\n"
            f"Для крутки нужно 20 💰. Ваш баланс: {current_money} 💰."
        )
    else:
        message_text = f"Неизвестная ошибка: {data.get('detail', 'N/A')}"
        
    await bot.send_message(
        user_id,
        message_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


@dp.callback_query_handler(lambda c: c.data == 'inventory')
async def show_inventory(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    
    data = api_get_inventory(user_id)
    
    if not data or data.get('status') != 'success':
        inv_text = "Произошла ошибка при получении данных инвентаря."
    else:
        inventory = data.get('inventory', [])
        
        if inventory:
            inv_text = "💼 **Ваш Инвентарь:**\n"
            for item in inventory:
                inv_text += f"- {item['name']}: x{item['count']}\n"
        else:
            inv_text = "💼 **Ваш Инвентарь пуст.** Попробуйте 'Крутить'!"
            
        inv_text += f"\n💰 Ваш текущий баланс: {data['money']} 💰"

    await bot.send_message(
        user_id,
        inv_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
