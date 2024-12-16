# from aiogram import Router, types, html
# from aiogram.fsm.context import FSMContext
# from aiogram.types import ReplyKeyboardRemove
#
# import keyboards
# from bot import get_feed
# from states import Form
#
#
# menu_router = Router()
#
#
# @menu_router.message(Form.menu)
# async def menu(message: types.Message, state: FSMContext):
#     match message.text:
#         case "1🚀":
#             await state.set_state(Form.feed)
#             await message.answer("🚀", reply_markup=keyboards.feed_keyboard.as_markup(resize_keyboard=True))
#             await get_feed(message, state)
#         case "2":
#             await state.set_state(Form.name)
#             await message.answer(
#                 f"Привет, {html.bold(message.from_user.full_name)}!\n Я помогу тебе найти где отпразнывать нг, или локальные тусовочки. Скажи как тебя зовут",
#                 reply_markup=ReplyKeyboardRemove(),
#             )
#         case "3":
#             await message.answer("пока что затычка")
#         case "4":
#             await message.answer("пока что затычка")
#         case _:
#             await message.answer("Не понимаю")

