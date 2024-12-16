import asyncio
import json
from typing import Type

import aiohttp
import logging
import sys
from os import getenv

import sqlalchemy
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import PickleType

from aiogram import Bot, Dispatcher, html, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import keyboards
from keyboards import contentKeyboard

Base = sqlalchemy.orm.declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String)
    name = Column(String)
    age = Column(Integer)
    city = Column(String)
    cityApi = Column(String)
    content = Column(String)
    chat_id = Column(String)

engine = create_engine('sqlite:///party.db', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    cityApi = State()
    content = State()
    isFinalShown = State()
    isReady = State()
    isRegistered = State()
    feed = State()



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
bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\n Я помогу тебе найти где отпразнывать нг, или локальные тусовочки. Скажи как тебя зовут"
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

        await message.answer(f"Ебать целых, {age} годиков! Теперь напиши, пожалуйста, откуда ты?")

        await state.set_state(Form.city)

    except ValueError:
        await message.answer("Некорректный ввод. Пожалуйста, введите ваш возраст числом.")


@dp.message(Form.city)
async def process_dsd(message: Message, state: FSMContext) -> None:

    print(message.text)
    apiCity = await get_city_info(message.text)
    await state.update_data(cityApi = apiCity)
    await state.update_data(city=message.text)
    await state.update_data(content={'photo':[], 'video':[]})
    await state.update_data(isFinalShown=False)
    await state.set_state(Form.content)
    await message.answer(f"{apiCity} хороший городок. Ну теперь скинь свои фоточки")



async def finalqustion(message: types.Message, state: FSMContext)-> None:
    data = await state.get_data()
    if not data["isFinalShown"]:
        await state.update_data(isFinalShown=True)
        await state.set_state(Form.isReady)
        await message.answer("Так выглядит твоя анкета:")
        caption = f"{data['name']} - {data['age']} - {data['city']}"
        media_group = MediaGroupBuilder(caption=caption)
        for i in data["content"]['photo']:
            media_group.add_photo(i)

        await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())
        await message.answer("Всё хорошо выглядит?",
                             reply_markup=keyboards.final_keyboard.as_markup(resize_keyboard=True))



@dp.message(Form.content)
async def process_photo(message: types.Message, state: FSMContext)-> None:
    data = await state.get_data()
    photos = data['content']['photo']
    if len(photos) == 3 or message.text == "Да":
        await finalqustion(message, state)
        await state.update_data(content={'photo': photos})
    if len(photos) < 4:
        if message.photo:
            photos.append(message.photo[-1].file_id)
            print(photos)
            await message.answer(f"Получено {len(photos)} из 3 фото, это всё?",
                             reply_markup=contentKeyboard.as_markup(resize_keyboard=True))
        else:
            await message.answer("Не понимаю бро")



async def get_users(message, state, cityApi)-> list[Type[User]]:
    users = session.query(User).filter(User.cityApi == cityApi).all()
    #, age-2<age<age+2
    return users


@dp.message(Form.feed)
async def process_feed(message: types.Message, state: FSMContext)-> None:
    data = await state.get_data()
    users = await get_users(message, state, data['cityApi'])
    print(users)
    for user in users:
        caption = f"{user.name} - {user.age} - {user.city}"
        media_group = MediaGroupBuilder(caption=caption)
        for i in json.loads(user.content)['photo']:
            media_group.add_photo(i)
        await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())











@dp.message(Form.isReady)
async def isright(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.text == "Нравиться":
        json_content = json.dumps(data['content'])
        new_user = User(name=data['name'], age=data['age'], city=data['city'], cityApi=data['cityApi'],
                        content=json_content)
        session.add(new_user)
        session.commit()
        await state.set_state(Form.feed)
        await state.update_data(isRegistered=True)
        await message.answer("Сотреть анкеты?", reply_markup=keyboards.lookAnkets.as_markup(resize_keyboard=True))
    else:
        await message.answer("Ну минус вайб", reply_markup=ReplyKeyboardRemove())






async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())