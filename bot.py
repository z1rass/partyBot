import asyncio
import json

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
    name = Column(String)
    age = Column(Integer)
    city = Column(String)
    cityApi = Column(String)
    content = Column(String)

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
    contentCounter = State()
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
    await state.update_data(contentCounter=0)
    await state.update_data(content={'photo':[], 'video':[]})
    await state.set_state(Form.content)
    await message.answer(f"Теперь скнь фо   точки свои")


@dp.message(Form.content)
async def process_photo(message: types.Message, state: FSMContext)-> None:
    data = await state.get_data()
    counter = data['contentCounter']
    content_ids = data['content']
    print(content_ids)
    if counter >= 3:
        await state.set_state(Form.isReady)
        await message.answer("Так выглядит твоя анкета:")
        caption = f"{data['name']} - {data['age']} - {data['city']}"
        media_group = MediaGroupBuilder(caption=caption)
        for i in data["content"]['photo']:
            media_group.add_photo(i)
        for i in data["content"]['video']:
            media_group.add_video(i)
        bot = Bot(TOKEN)
        await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())
        await message.answer("Всё хорошо выглядит?")
    elif counter > 0:
        await message.answer(f"Получено {counter} из 3 медиафайлов, это всё?",
                             reply_markup=contentKeyboard.as_markup(resize_keyboard=True))

    if message.photo:
        content_ids['photo'].append(message.photo[-2].file_id)
        counter += 1
        await state.update_data(contentCounter=counter, content=content_ids)
    elif message.video:
            content_ids['video'].append(message.video.file_id)
            counter += 1
            await state.update_data(contentCounter=counter, content=content_ids)
    else:
        if message.text.strip() == "Да":
            await message.answer("Так выглядит твоя анкета:")
            caption = f"{data['name']} - {data['age']} - {data['city']}"
            media_group = MediaGroupBuilder(caption=caption)
            for i in data["content"]['photo']:
                media_group.add_photo(i)
            for i in data["content"]['video']:
                media_group.add_video(i)
            bot = Bot(TOKEN)
            await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())
            await state.set_state(Form.isReady)
            await message.answer("Всё хорошо выглядит?")
        elif message.text.strip() == "Нет":
            print(content_ids)
            await message.answer("Тогда просто скинь мне 3 фото или видео для анкеты", reply_markup=ReplyKeyboardRemove())


        else:
            await message.answer("Бро ты плохо скинул, скинь норм фотки или видео")



@dp.message(Form.isReady)
async def finalAsk(message: types.Message, state: FSMContext)-> None:
    data = await state.get_data()
    if message.text == "Да":
        await message.answer("Ты прошёл регестрацию")
        json_content = json.dumps(data['content'])
        new_user = User(name=data['name'], age=data['age'], city=data['city'], cityApi=data['cityApi'],
                        content=json_content)
        session.add(new_user)
        session.commit()
        session.close()
    else:
        await message.answer("Затычка")

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())