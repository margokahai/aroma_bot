import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aroma_data import AROMA_OILS, AROMA_EFFECTS, USAGE_CONTEXT

import openai

# ===================== Загрузка токенов =====================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
openai.api_key = OPENAI_KEY

# ===================== FSM =====================
class AromaForm(StatesGroup):
    aroma_type = State()
    need = State()
    context = State()

# ===================== КНОПКИ =====================
q1_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [
        types.InlineKeyboardButton(text="🍋 Цитрусовые", callback_data="q1_citrus"),
        types.InlineKeyboardButton(text="🌲 Древесные", callback_data="q1_woody")
    ],
    [
        types.InlineKeyboardButton(text="🌿 Травяные", callback_data="q1_herbal"),
        types.InlineKeyboardButton(text="🌸 Цветочные", callback_data="q1_floral")
    ],
    [
        types.InlineKeyboardButton(text="🌙 Восточные", callback_data="q1_oriental"),
        types.InlineKeyboardButton(text="🌊 Свежие", callback_data="q1_fresh")
    ],
    [
        types.InlineKeyboardButton(text="🤍 Хочу что-то новое", callback_data="q1_any")
    ]
])

q2_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [
        types.InlineKeyboardButton(text="🧘 Спокойствия", callback_data="q2_calm"),
        types.InlineKeyboardButton(text="🔋 Энергии", callback_data="q2_energy")
    ],
    [
        types.InlineKeyboardButton(text="🌞 Радости", callback_data="q2_joy"),
        types.InlineKeyboardButton(text="💪 Уверенности", callback_data="q2_confidence")
    ],
    [
        types.InlineKeyboardButton(text="🎯 Концентрации", callback_data="q2_focus"),
        types.InlineKeyboardButton(text="🤗 Уюта", callback_data="q2_safety")
    ],
    [
        types.InlineKeyboardButton(text="💖 Нежности", callback_data="q2_selflove")
    ]
])

q3_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [
        types.InlineKeyboardButton(text="💼 Работа", callback_data="q3_work"),
        types.InlineKeyboardButton(text="🏃 Активный день", callback_data="q3_active")
    ],
    [
        types.InlineKeyboardButton(text="🧘 Отдых", callback_data="q3_relax"),
        types.InlineKeyboardButton(text="🌙 Перед сном", callback_data="q3_sleep")
    ],
    [
        types.InlineKeyboardButton(text="💬 Общение", callback_data="q3_social"),
        types.InlineKeyboardButton(text="🏠 Дом", callback_data="q3_home")
    ],
    [
        types.InlineKeyboardButton(text="🚗 В дороге", callback_data="q3_travel")
    ]
])

again_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="🌿 Сделать ещё один аромат", callback_data="again")]
])

# ===================== ФУНКЦИЯ AI =====================
async def generate_aroma(data: dict) -> str:
    """
    Генерирует персональный рецепт духов через OpenAI API v1.x.
    Используется asyncio.to_thread, чтобы не блокировать event loop.
    Включает рецепт на 5 мл базового масла с пошаговым способом приготовления.
    """
    prompt = (
        f"Ты эксперт по ароматерапии и созданию духов. "
        f"Пользователь выбрал:\n"
        f"- Тип аромата: {data.get('aroma_type')}\n"
        f"- Эмоция/нужда: {data.get('need')}\n"
        f"- Контекст использования: {data.get('context')}\n\n"
        f"Составь полноценный рецепт духов на 5 мл базового масла. "
        f"Укажи:\n"
        f"1. Количество капель каждого эфирного масла (3–5 масел).\n"
        f"2. Пошаговый способ приготовления: как смешать, настаивать, использовать.\n"
        f"3. Краткое объяснение, как аромат влияет на настроение и подходит для выбранного контекста.\n"
        f"Оформи красиво с эмодзи, чтобы было понятно и приятно читать."
    )

    try:
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.8
        )
        text = response.choices[0].message.content.strip()
    except Exception:
        # fallback на случай ошибки API
        oils = AROMA_OILS.get(data.get("aroma_type", "any"), [])
        text = (
            "🌿 Твой персональный аромат (на 5 мл базового масла):\n"
            + "\n".join([f"- {oil}" for oil in oils[:3]])
            + "\n✨ Используй и наслаждайся ароматом!"
        )

    return text

# ===================== СТАРТ =====================
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(AromaForm.aroma_type)
    await message.answer(
        "Привет 🌿 Я бот по созданию ароматов!\n"
        "Выбери любимый тип аромата:",
        reply_markup=q1_kb
    )

# ===================== Q1 =====================
@dp.callback_query(AromaForm.aroma_type)
async def q1_handler(callback: types.CallbackQuery, state: FSMContext):
    aroma_type = callback.data.replace("q1_", "")
    await state.update_data(aroma_type=aroma_type)
    await state.set_state(AromaForm.need)
    await callback.message.answer(
        "Отлично! А теперь выбери, чего тебе сейчас не хватает:",
        reply_markup=q2_kb
    )
    await callback.answer()

# ===================== Q2 =====================
@dp.callback_query(AromaForm.need)
async def q2_handler(callback: types.CallbackQuery, state: FSMContext):
    need = callback.data.replace("q2_", "")
    await state.update_data(need=need)
    await state.set_state(AromaForm.context)
    await callback.message.answer(
        "Понимаю! И где или когда ты будешь использовать этот аромат?",
        reply_markup=q3_kb
    )
    await callback.answer()

# ===================== Q3 =====================
@dp.callback_query(AromaForm.context)
async def q3_handler(callback: types.CallbackQuery, state: FSMContext):
    context = callback.data.replace("q3_", "")
    await state.update_data(context=context)
    data = await state.get_data()

    # Отправляем сообщение о том, что бот думает
    thinking_msg = await callback.message.answer("🌿 Подождите немного, я создаю ваш аромат...")

    # Вызов AI через OpenAI API
    aroma_recommendation = await generate_aroma(data)

    # Удаляем сообщение о "думаю"
    await thinking_msg.delete()

    # Отправляем результат с кнопкой "Сделать ещё один аромат"
    await callback.message.answer(aroma_recommendation, reply_markup=again_kb)

    await state.clear()
    await callback.answer()

# ===================== КНОПКА "СДЕЛАТЬ ЕЩЁ ОДИН АРОМАТ" =====================
@dp.callback_query(lambda c: c.data == "again")
async def again_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()  # очищаем предыдущие ответы
    await state.set_state(AromaForm.aroma_type)
    await callback.message.answer(
        "Отлично! Давай создадим новый аромат 🌿\nВыбери любимый тип аромата:",
        reply_markup=q1_kb
    )
    await callback.answer()

# ===================== ЭХО =====================
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer("Нажми /start чтобы подобрать аромат 🌿")

# ===================== MAIN =====================
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
