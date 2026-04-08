

import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import openai
from aroma_data import AROMA_OILS, AROMA_EFFECTS, USAGE_CONTEXT

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
    warning_confirm = State()


# ===================== КНОПКИ =====================
Q1_OPTIONS = [
    ("🍋 Цитрусовые", "citrus"),
    ("🌸 Цветочные", "floral"),
    ("🌲 Древесные", "woody"),
    ("🌿 Травяные", "herbal"),
    ("🌙 Восточные / пряные", "oriental"),
    ("🌊 Свежие / акватические", "fresh"),
    ("🍬 Сладкие / гурманские", "gourmand"),
    ("🌼 Пудровые", "powdery"),
    ("🍃 Зелёные", "green"),
    ("🤍 Без предпочтений", "any"),
]

def get_q1_kb(selected: list[str]) -> types.InlineKeyboardMarkup:
    buttons = []
    for text, key in Q1_OPTIONS:
        is_selected = key in selected
        btn_text = ("✅ " if is_selected else "") + text
        buttons.append(types.InlineKeyboardButton(text=btn_text, callback_data=f"q1_{key}"))
    # Arrange buttons in 2 per row
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    # No extra appending needed; this covers all cases
    # Add continue button
    rows.append([types.InlineKeyboardButton(text="➡️ Продолжить", callback_data="q1_done")])
    return types.InlineKeyboardMarkup(inline_keyboard=rows)

Q2_OPTIONS = [
    ("🧘 Спокойствия", "calm"),
    ("🔋 Энергии", "energy"),
    ("🎯 Концентрации", "focus"),
    ("😌 Радости", "joy"),
    ("💪 Уверенности", "confidence"),
    ("😴 Отдыха", "rest"),
    ("🤍 Просто приятного аромата", "pleasant")
]

def get_q2_kb(selected: str = None) -> types.InlineKeyboardMarkup:
    buttons = []
    for text, key in Q2_OPTIONS:
        btn_text = ("✅ " if selected == key else "") + text
        buttons.append(types.InlineKeyboardButton(text=btn_text, callback_data=f"q2_{key}"))
    # Arrange buttons in 2 per row
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return types.InlineKeyboardMarkup(inline_keyboard=rows)

Q3_OPTIONS = [
    ("💼 На работе", "work"),
    ("🏠 Дома", "home"),
    ("🌙 Перед сном", "sleep"),
    ("🚶 На прогулке", "walk"),
    ("💬 Встречи и общение", "social"),
    ("🧘 Во время отдыха", "rest"),
    ("✈️ В дороге", "travel"),
    ("❤️ На свидании", "date")
]

def get_q3_kb(selected: str = None) -> types.InlineKeyboardMarkup:
    buttons = []
    for text, key in Q3_OPTIONS:
        btn_text = ("✅ " if selected == key else "") + text
        buttons.append(types.InlineKeyboardButton(text=btn_text, callback_data=f"q3_{key}"))
    # Arrange buttons in 2 per row
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return types.InlineKeyboardMarkup(inline_keyboard=rows)
warning_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="✅ Продолжить", callback_data="confirm_warning")]
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
        f"Придумай креативное название для этого аромата (1 строка, ярко и красиво, с эмодзи).\n"
        f"Составь полноценный рецепт духов на 5 мл базового масла. "
        f"Укажи:\n"
        f"1. Количество капель каждого эфирного масла (3–5 масел).\n"
        f"2. Пошаговый способ приготовления: как смешать, настаивать, использовать.\n"
        f"3. Краткое объяснение, как аромат влияет на настроение и подходит для выбранного контекста.\n"
        f"Оформи красиво с эмодзи, чтобы было понятно и приятно читать.\n"
        f"Ограничь ответ 4000 символами, не превышай этот лимит."
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
        aroma_name = "🌿 Аромат мечты"
        recipe = (
            "Твой персональный аромат (на 5 мл базового масла):\n"
            + "\n".join([f"- {oil}" for oil in oils[:3]])
            + "\n✨ Используй и наслаждайся ароматом!"
        )
        text = f"{aroma_name}\n{recipe}"

    # Ограничиваем длину ответа 4000 символами
    if len(text) > 4000:
        text = text[:4000]
    return text

# ===================== СТАРТ =====================

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(AromaForm.aroma_type)
    await state.update_data(aroma_types=[])
    await message.answer(
        "Привет 🌿 Я бот по созданию ароматов!\n"
        "Выбери любимые типы аромата (можно несколько):",
        reply_markup=get_q1_kb([])
    )


# ===================== Q1 =====================
@dp.callback_query(AromaForm.aroma_type)
async def q1_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    aroma_types = data.get("aroma_types", [])
    cb = callback.data
    if cb == "q1_done":
        if not aroma_types:
            await callback.answer("Выберите хотя бы один вариант", show_alert=True)
            return
        await state.update_data(aroma_types=aroma_types)
        await state.set_state(AromaForm.need)
        await callback.message.answer(
            "Какой эффект ты хочешь получить?",
            reply_markup=get_q2_kb()
        )
        await callback.answer()
        return
    # Toggle selection
    key = cb.replace("q1_", "")
    if key in aroma_types:
        aroma_types.remove(key)
    else:
        aroma_types.append(key)
    await state.update_data(aroma_types=aroma_types)
    await callback.message.edit_reply_markup(reply_markup=get_q1_kb(aroma_types))
    await callback.answer()

# ===================== Q2 =====================
@dp.callback_query(AromaForm.need)
async def q2_handler(callback: types.CallbackQuery, state: FSMContext):
    need = callback.data.replace("q2_", "")
    await state.update_data(need=need)
    await state.set_state(AromaForm.context)
    await callback.message.answer(
        "Где будешь использовать аромат?",
        reply_markup=get_q3_kb()
    )
    await callback.answer()

# ===================== Q3 =====================
@dp.callback_query(AromaForm.context)
async def q3_handler(callback: types.CallbackQuery, state: FSMContext):
    context = callback.data.replace("q3_", "")
    await state.update_data(context=context)
    data = await state.get_data()

    # Show summary block before warning
    aroma_types = data.get("aroma_types", [])
    need = data.get("need", "")
    context_val = context

    # Find readable text for each selection
    def get_text(options, key):
        for text, k in options:
            if k == key:
                return text
        return key
    aroma_types_text = ", ".join([get_text(Q1_OPTIONS, t) for t in aroma_types]) if aroma_types else "—"
    need_text = get_text(Q2_OPTIONS, need)
    context_text = get_text(Q3_OPTIONS, context_val)

    summary = (
        "🌿 Твои выборы:\n"
        f"Тип аромата: {aroma_types_text}\n"
        f"Чего тебе сейчас не хватает: {need_text}\n"
        f"Где будешь использовать аромат: {context_text}\n"
    )
    await callback.message.answer(summary)

    # Proceed to warning
    await state.set_state(AromaForm.warning_confirm)
    warning_text = (
        "⚠️ Важно перед использованием\n\n"
        "Эфирные масла могут вызывать индивидуальную реакцию.\n"
        "Сделай тест на чувствительность на коже перед применением.\n\n"
        "Если есть аллергии, беременность или хронические состояния — проконсультируйся со специалистом.\n\n"
        "Нажми «Продолжить», чтобы получить рецепт 🌿"
    )
    await callback.message.answer(warning_text, reply_markup=warning_kb)
    await callback.answer()
@dp.callback_query(lambda c: c.data == "confirm_warning")
async def confirm_warning_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    thinking_msg = await callback.message.answer("🌿 Подождите немного, я создаю ваш аромат...")
    aroma_recommendation = await generate_aroma(data)
    try:
        await thinking_msg.delete()
    except Exception as e:
        # Ignore if message was already deleted or not found
        pass
    await callback.message.answer(aroma_recommendation, reply_markup=again_kb)
    await state.clear()
    await callback.answer()

    # Вызов AI через OpenAI API
    aroma_recommendation = await generate_aroma(data)

    # Удаляем сообщение о "думаю"
    try:
        await thinking_msg.delete()
    except Exception as e:
        # Ignore if message was already deleted or not found
        pass

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
        reply_markup=get_q1_kb([])
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
