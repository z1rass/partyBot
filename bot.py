import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup




class Form(StatesGroup):
    name = State()  
    age = State()
    city = State()
    photos = State()



# Bot token can be obtained via https://t.me/BotFather
TOKEN = ""

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        f"Привет мой сладенький маленький друг, {html.bold(message.from_user.full_name)}!\nНапиши пожалуйста как тебя зовут?"
    )

@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer(f"Приятно познакомиться {message.text}.  Теперь напиши пожалуйста сколько тебе годиков: ")

@dp.message(Form.age)
async def process_dsf(message: Message, state: FSMContext) -> None:
    await state.update_data(age=message.text)
    await state.set_state(Form.city)
    await message.answer(f"Приятно познакомиться {message.text}.  Теперь напиши пожалуйста от куда ты?")


@dp.message(Form.city)
async def process_dsd(message: Message, state: FSMContext) -> None:
    await state.update_data(city=message.text)
    await state.set_state(Form.photos)
    await message.answer(f"Приятно познакомиться {message.text}.  Теперь скнь фоточки свои")

@dp.message(StateFilter(Form.photos))
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    
    current_state = await state.get_state()

    await message.answer(f"Текущее состояние: {current_state}", photo=photo_id)
    await message.answer_photo(photo_id)
    # Отправляем ID фотографии
    await message.answer(f"Полученный ID фото: {photo_id}")
    


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())