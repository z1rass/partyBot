from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

contentKeyboard = ReplyKeyboardBuilder()
contentKeyboard.row(
        types.KeyboardButton(text="Да"),
        types.KeyboardButton(text="Нет")
    )


final_keyboard = ReplyKeyboardBuilder()
final_keyboard.row(
        types.KeyboardButton(text="Нравится")
    )
final_keyboard.row(
        types.KeyboardButton(text="Не нравиться")
    )


lookAnkets = ReplyKeyboardBuilder()
lookAnkets.row(
        types.KeyboardButton(text="Смотреть")
    )
lookAnkets.row(
        types.KeyboardButton(text="Меню")
    )



menu_keyboard = ReplyKeyboardBuilder()
menu_keyboard.row(
    types.KeyboardButton(text="1🚀"),
    types.KeyboardButton(text="2"),
    types.KeyboardButton(text="3"),
    types.KeyboardButton(text="4"),
)


feed_keyboard = ReplyKeyboardBuilder()
feed_keyboard.row(
    types.KeyboardButton(text="👍"),
    types.KeyboardButton(text="👎"),
    types.KeyboardButton(text="⚙️")
)



