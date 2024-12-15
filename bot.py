import asyncio
import aiohttp
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    cityApi = State()
    content = State()
    isReady = State()


async def get_city_info(city_name: str):
    url = f"http://api.geonames.org/searchJSON?q={city_name}&maxRows=1&username=moxikl"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data['geonames'][0]['toponymName'] if data['geonames'] else None
            else:
                return None



# Bot token can be obtained via https://t.me/BotFather
TOKEN = "7660337058:AAHHugNM5JDLCMXtlkVpOzkEbtuycg1IUmU"

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        f"Привет мой сладенький маленький друг, {html.bold(message.from_user.full_name)}!\nДавай скажи как тебя зовут"
    )

@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer(f"Приятно познакомиться {message.text}.  Теперь напиши пожалуйста сколько тебе годиков: ")

@dp.message(Form.age)
async def process_dsf(message: Message, state: FSMContext) -> None:
    try:
        age = int(message.text)
        if not (10 <= age <= 99):
            await message.answer("Некорректный ввод")
            return

        await state.update_data(age=age)

        await message.answer(f"Приятно познакомиться, {age}. Теперь напиши, пожалуйста, откуда ты?")

        await state.set_state(Form.city)

    except ValueError:
        await message.answer("Некорректный ввод. Пожалуйста, введите ваш возраст числом.")


@dp.message(Form.city)
async def process_dsd(message: Message, state: FSMContext) -> None:
    print(message.text)
    apiCity = await get_city_info(message.text)
    await state.update_data(cityApi = apiCity)
    await state.update_data(city=message.text)
    await state.set_state(Form.content)
    await message.answer(f"Теперь скнь фоточки свои")


@dp.message(Form.content)
async def process_photo(message: types.Message, state: FSMContext)-> None:
    content_ids = {'video':[], 'photo':[]}
    if message.photo:
        content_ids['photo'].append(message.photo[-2].file_id)
    elif message.video:
            content_ids['video'].append(message.video.file_id)
    else:
        await message.answer("Бро ты хуйню скинул, скинь норм фотки или видео")

    for i in content_ids['photo']:
        await message.answer_photo(i)
    for i in content_ids['video']:
        await message.answer_video(i)
    await state.update_data(content=content_ids)
    data = await state.get_data()
    await message.answer(str(data))


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())