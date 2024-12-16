from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

contentKeyboard = ReplyKeyboardBuilder()
contentKeyboard.row(
        types.KeyboardButton(text="Да"),
        types.KeyboardButton(text="Нет")
    )


final_keyboard = ReplyKeyboardBuilder()
final_keyboard.row(
        types.KeyboardButton(text="Нравиться")
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
