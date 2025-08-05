import asyncio
import logging
import os
import random
import re
import tracemalloc
from functools import lru_cache

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage


class GameStates(StatesGroup):
    SELECTING_X = State()
    WAITING_ANSWER = State()


API_TOKEN = ''
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher()

BOOKS_DIR = 'data/txt'

tracemalloc.start()

MAX_CACHED_BOOKS = 15


def get_books_list():
    return [f for f in os.listdir(BOOKS_DIR) if f.endswith('.txt')]


@lru_cache(maxsize=MAX_CACHED_BOOKS)
def read_book(book_path):
    file_path = os.path.join(BOOKS_DIR, book_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().splitlines()

    # Пропускаем первую строку с количеством предложений
    sentences = content[1:]

    # Объединяем все строки в один текст
    text = ' '.join(sentences)

    # Разделяем на предложения по [.!?]
    pattern = r'(?<=[.!?])\s+'
    sentences = re.split(pattern, text)

    # Очищаем
    sentences = [s.strip() for s in sentences if s.strip()]

    print(f"Загружаю и кэширую: {book_path}")
    return sentences


@dp.message(Command("start"))
async def start_game(message: types.Message, state: FSMContext):
    await message.answer("Выберите количество предложений:")
    await state.set_state(GameStates.SELECTING_X)


@dp.message(GameStates.SELECTING_X)
async def select_x(message: types.Message, state: FSMContext):
    x = int(message.text)
    if x <= 0:
        await message.answer("Количество должно быть больше 0!")
        return

    books = get_books_list()
    if not books:
        await message.answer("Нет доступных книг!")
        return

    book_name = random.choice(books)
    sentences = read_book(book_name)

    monitor_alloc()

    total_sentences = len(sentences)

    if x > total_sentences:
        await message.answer(f"В книге {book_name} только {total_sentences} предложений. Выберите меньшее число.")
        return

    start_index = random.randint(0, len(sentences) - x)
    fragment = '\n'.join(sentences[start_index:start_index + x])

    await state.update_data(book_name=book_name, x=x, fragment=fragment)
    await message.answer(f"Угадайте книгу по {x} предложениям:\n\n{fragment}")
    await state.set_state(GameStates.WAITING_ANSWER)


@dp.message(GameStates.WAITING_ANSWER)
async def check_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    correct_book = data['book_name']
    user_answer = message.text.strip()

    if user_answer.lower() == correct_book.replace('.txt', '').lower():
        await message.answer("Правильно! Теперь следующая загадка.")
        await state.clear()
        await start_game(message, state)
    else:
        await message.answer(f"Не угадали. Правильный ответ: {correct_book.replace('.txt', '')}")
        await start_game(message, state)


@dp.message(Command("stop"))
async def stop_game(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Игра остановлена. Нажмите /start для новой игры.", reply_markup=types.ReplyKeyboardRemove())


def monitor_alloc():
    current, peak = tracemalloc.get_traced_memory()
    print(f"Текущее потребление памяти: {current / 1024 / 1024:.2f} МБ")
    print(f"Пиковое потребление памяти: {peak / 1024 / 1024:.2f} МБ")
    print(f"Кэш: {read_book.cache_info()}")


async def main() -> None:
    global bot
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Ну че народ погнали нах")
    try:
        asyncio.run(main())
        logging.info("Бот запущен.")
    except Exception as e:
        logging.error("Ошибка при запуске бота: %s", e)
        logging.exception(f"Произошла ошибка: {e}")
        print(f"Произошла ошибка: {e}")


