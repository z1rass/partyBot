import asyncio
import json
import random
from typing import Type

import aiohttp
import logging
import sys

import sqlalchemy
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker

from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from aiogram.fsm.context import FSMContext
import keyboards
from keyboards import contentKeyboard

from states import Form
import menu

Base = sqlalchemy.orm.declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
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

menu_text = """1. Смотреть анкеты
2. Изменить анкету
3. Донатик
4. Получить дикпик"""


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    print(message.text)

    if session.query(User).filter(User.telegram_id == message.from_user.id).all():
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        # await state.set_state(Form.feed)
        await state.update_data(name=user.name, age=user.age, cityApi=user.cityApi, city=user.city,
                                content=user.content)
        await state.set_state(Form.start)
        await message.answer("Смотрим дальше?", reply_markup=keyboards.contentKeyboard.as_markup(resize_keyboard=True))
    else:
        await state.set_state(Form.name)
        await message.answer(
            f"Привет, {html.bold(message.from_user.full_name)}!\n Я помогу тебе найти где отпразнывать нг, или локальные тусовочки. Скажи как тебя зовут"
        )


@dp.message(Form.start)
async def process_start(message: Message, state: FSMContext) -> None:
    if message.text == "Да":
        data = await state.get_data()
        await state.set_state(Form.feed)
        await message.answer("🚀", reply_markup=keyboards.feed_keyboard.as_markup(resize_keyboard=True))
        await get_users(message, state)
        await get_feed(message, state)
    elif message.text == "Нет":
        await state.set_state(Form.menu)
        await message.answer(menu_text, reply_markup=keyboards.menu_keyboard.as_markup(resize_keyboard=True))
    else:
        await message.answer("Такого варианта нету")


@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    if message.text == "None" or message.text is None:
        await message.answer("Некоректный ввод. Введите ваше имя текстом")
    else:
        await state.update_data(name=message.text)
        await state.set_state(Form.age)
        await message.answer(f"Приятно познакомиться {message.text}.  Теперь напиши пожалуйста сколько тебе годиков: ")


@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext) -> None:
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
async def process_city(message: Message, state: FSMContext) -> None:
    print(message.text)
    api_city = await get_city_info(message.text)
    print("ASdASDASDASD")
    print(type(api_city))
    if api_city == "None" or api_city is None:
        await message.answer("Нкоректные ввод")
    else:
        await state.update_data(cityApi=api_city)
        await state.update_data(city=message.text)
        await state.update_data(content={'photo': [], 'video': []})
        await state.update_data(isFinalShown=False)
        await state.update_data(isRegistered=False)
        if session.query(User).filter(User.telegram_id == message.from_user.id).first():
            await state.update_data(isRegistered=True)
        await state.set_state(Form.content)
        await message.answer(f"{api_city} хороший городок. Ну теперь скинь свои фоточки")


async def finalqustion(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data["isFinalShown"]:
        await state.update_data(isFinalShown=True)
        await state.set_state(Form.isReady)
        await message.answer("Так выглядит твоя анкета:")
        caption = f"{data['name']} - {data['age']} - {data['city']}"
        media_group = MediaGroupBuilder(caption=caption)
        for i in data["content"]['photo']:
            media_group.add_photo(i)
        for i in data["content"]['video']:
            media_group.add_video(i)

        await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())
        await message.answer("Всё хорошо выглядит?",
                             reply_markup=keyboards.final_keyboard.as_markup(resize_keyboard=True))


@dp.message(Form.content)
async def process_content(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = data['content']['photo']
    videos = data['content']['video']

    if not message.photo and not message.video:
        await message.answer(f"Бро, не понимаю, скинь ещё {3 - (len(photos) + len(videos))} фото или видео")

    if (len(photos) + len(videos)) < 3:
        if message.photo:
            photos.append(message.photo[-1].file_id)
            if (len(photos) + len(videos)) == 3:
                await finalqustion(message, state)
                await state.update_data(content={'photo': photos, 'video': videos})
            else:
                print(photos)
                await message.answer(f"Получено {len(photos) + len(videos)} из 3 фото, это всё?",
                                     reply_markup=contentKeyboard.as_markup(resize_keyboard=True))
        elif message.video:
            videos.append(message.video.file_id)
            if (len(photos) + len(videos)) == 3:
                await finalqustion(message, state)
                await state.update_data(content={'photo': photos, 'video': videos})
            else:
                await message.answer(f"Получено {len(photos) + len(videos)} из 3 видео, это всё?",
                                     reply_markup=contentKeyboard.as_markup(resize_keyboard=True))
    elif (len(photos) + len(videos)) >= 2 or message.text == "Да":
        await finalqustion(message, state)
        await state.update_data(content={'photo': photos, 'video': videos})


@dp.message(Form.isReady)
async def is_right(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    print(data)
    if message.text == "Нравится":
        print("is ready")
        if data['isRegistered']:
            print("user is registered")
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()

            if user:
                user.name = data['name']
                user.age = data['age']
                user.city = data['city']
                user.cityApi = data['cityApi']
                user.content = json.dumps(data['content'])
                user.chat_id = message.chat.id

                session.commit()
                await state.update_data(isRegistered=True)
                await state.set_state(Form.start)
                await message.answer("Сотреть анкеты?",
                                     reply_markup=keyboards.contentKeyboard.as_markup(resize_keyboard=True))

        else:
            print("user is registered else")
            json_content = json.dumps(data['content'])
            new_user = User(telegram_id=message.from_user.id, name=data['name'], age=data['age'], city=data['city'],
                            cityApi=data['cityApi'],
                            content=json_content, chat_id=message.chat.id)
            session.add(new_user)
            session.commit()
            await state.set_state(Form.start)
            await state.update_data(isRegistered=True)
            await message.answer("Сотреть анкеты?",
                                 reply_markup=keyboards.contentKeyboard.as_markup(resize_keyboard=True))
    else:
        await state.set_state(Form.name)
        await message.answer("Ну минус вайб. Регайся заеново, как тебя зовут?", reply_markup=ReplyKeyboardRemove())


async def get_users(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    users = session.query(User).filter(User.cityApi == data["cityApi"]).all()
    await state.update_data(usersInFeed=[users])

async def get_feed(message, state):
    data = await state.get_data()
    users = data["usersInFeed"]
    print(not users[0])
    if users[0]:
        user = users[0].pop(random.randint(0, len(users[0]) - 1))
        await state.update_data(usersInFeed=users, lastUser = user)
        caption = f"{user.name} - {user.age} - {user.city}"
        media_group = MediaGroupBuilder(caption=caption)
        for i in json.loads(user.content)['photo']:
            media_group.add_photo(i)
        for i in json.loads(user.content)['video']:
            media_group.add_video(i)
        await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())
    else:
        await get_users(message, state)
        data = await state.get_data()
        users = data["usersInFeed"]
        user = users[0].pop(random.randint(0, len(users[0]) - 1))
        await state.update_data(usersInFeed=users, lastUser = user)
        caption = f"{user.name} - {user.age} - {user.city}"
        media_group = MediaGroupBuilder(caption=caption)
        for i in json.loads(user.content)['photo']:
            media_group.add_photo(i)
        for i in json.loads(user.content)['video']:
            media_group.add_video(i)
        await bot.send_media_group(chat_id=message.chat.id, media=media_group.build())



@dp.message(Form.feed)
async def process_feed(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.text == "Нет" or message.text == "⚙️":
        await state.set_state(Form.menu)
        await message.answer(menu_text, reply_markup=keyboards.menu_keyboard.as_markup(resize_keyboard=True))
    elif message.text == "👍":
        await bot.send_message(data['lastUser'].chat_id, "Ты кое кому понравилься!!!")
    else:
        await get_feed(message, state)




@dp.message(Form.menu)
async def menu(message: types.Message, state: FSMContext):
    match message.text:
        case "1🚀":
            data = await state.get_data()
            await state.set_state(Form.feed)
            await get_users(message, state)
            await message.answer("🚀", reply_markup=keyboards.feed_keyboard.as_markup(resize_keyboard=True))
            await get_feed(message, state)
        case "2":
            await state.set_state(Form.name)
            await message.answer(
                f"Привет, {html.bold(message.from_user.full_name)}!\n Я помогу тебе найти где отпразнывать нг, или локальные тусовочки. Скажи как тебя зовут",
                reply_markup=ReplyKeyboardRemove(),
            )
        case "3":
            await message.answer("пока что затычка")
        case "4":
            await message.answer("пока что затычка")
        case _:
            await message.answer("Не понимаю")


@dp.message()
async def allAnother(message: types.Message, state: FSMContext) -> None:
    print(message.text)
    if session.query(User).filter(User.telegram_id == message.from_user.id).all():
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        # await state.set_state(Form.feed)
        await state.update_data(name=user.name, age=user.age, cityApi=user.cityApi, city=user.city,
                                content=user.content)

        await message.answer("Смотрим дальше?", reply_markup=keyboards.contentKeyboard.as_markup(resize_keyboard=True))
        await state.set_state(Form.start)

    else:
        await state.set_state(Form.name)
        await message.answer(
            f"Привет, {html.bold(message.from_user.full_name)}!\n Я помогу тебе найти где отпразнывать нг, или локальные тусовочки. Скажи как тебя зовут"
        )


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    # dp.include_router(menu.menu_router)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
