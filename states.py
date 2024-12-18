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
    lastUser = State()
    feed = State()
    likes = State()
    who_liked_message = State()
    menu = State()

class MyStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
