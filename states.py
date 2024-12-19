from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    start = State()
    name = State()
    age = State()
    city = State()
    cityApi = State()
    content = State()
    isFinalShown = State()
    isReady = State()
    isRegistered = State()
    usersInFeed = State()
    askWantSeeLikes = State()
    lastUser = State()
    feed = State()
    likes = State()
    last_like = State()
    who_liked_message = State()
    menu = State()


