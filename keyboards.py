from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

contentKeyboard = ReplyKeyboardBuilder()
contentKeyboard.row(
        types.KeyboardButton(text="Да"),
        types.KeyboardButton(text="Нет")
    )

