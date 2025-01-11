import os
import logging
import requests
from typing import List
import telebot
from telebot import types
from telebot.callback_data import CallbackData
from bot_func_abc import AtomicBotFunctionABC

class AtomicExampleBotFunction(AtomicBotFunctionABC):
    """Пример реализации атомной функции бота с возможностью отправки случайных картинок собак"""

    commands: List[str] = ["example", "ebf"]
    authors: List[str] = ["IHVH"]
    about: str = "Пример функции бота с отправкой случайных картинок собак!"
    description: str = """Этот бот отправляет случайные картинки собак с сайта random.dog.
    Вы можете выбрать количество картинок (1, 3 или 5).
    Пример вызова функции - /ebf"""
    state: bool = True

    bot: telebot.TeleBot
    example_keyboard_factory: CallbackData

    def set_handlers(self, bot: telebot.TeleBot):
        """Настройка обработчиков для команд и клавиатуры"""
        self.bot = bot
        self.example_keyboard_factory = CallbackData('t_key_button', prefix=self.commands[0])

        @bot.message_handler(commands=self.commands)
        def example_message_handler(message: types.Message):
            chat_id_msg = f"\nCHAT ID = {message.chat.id}"
            msg = (
                f"Ваш запрос обработан в AtomicExampleBotFunction! {chat_id_msg}\n"
                f"USER ID = {message.from_user.id} \nEXAMPLETOKEN = {self.__get_example_token()}"
            )
            bot.send_message(text=msg, chat_id=message.chat.id, reply_markup=self.__gen_markup())

        @bot.callback_query_handler(func=lambda call: self.example_keyboard_factory.filter()(call.data))
        def example_keyboard_callback(call: types.CallbackQuery):
            callback_data: dict = self.example_keyboard_factory.parse(callback_data=call.data)
            t_key_button = callback_data['t_key_button']

            match t_key_button:
                case 'cb_yes':
                    bot.answer_callback_query(call.id, "Ответ ДА!")
                case 'cb_no':
                    bot.answer_callback_query(call.id, "Ответ НЕТ!")
                case 'force_reply':
                    force_reply = types.ForceReply(selective=False)
                    text = "Отправьте текст для обработки в process_next_step"
                    bot.send_message(call.message.chat.id, text, reply_markup=force_reply)
                    bot.register_next_step_handler(call.message, self.__process_next_step)
                case 'send_dog_images':
                    # Вызов функции для отправки изображений собак
                    self.send_dog_images(call.message)
                case _:
                    bot.answer_callback_query(call.id, call.data)

    def __get_example_token(self):
        token = os.environ.get("EXAMPLETOKEN")
        return token

    def __gen_markup(self):
        """Генерация inline клавиатуры"""
        markup = types.InlineKeyboardMarkup()
        markup.row_width = 2
        yes_callback_data = self.example_keyboard_factory.new(t_key_button="cb_yes")
        no_callback_data = self.example_keyboard_factory.new(t_key_button="cb_no")
        force_reply_callback_data = self.example_keyboard_factory.new(t_key_button="force_reply")
        send_dog_images_callback_data = self.example_keyboard_factory.new(t_key_button="send_dog_images")
        markup.add(
            types.InlineKeyboardButton("Да", callback_data=yes_callback_data),
            types.InlineKeyboardButton("Нет", callback_data=no_callback_data),
            types.InlineKeyboardButton("ForceReply", callback_data=force_reply_callback_data),
            types.InlineKeyboardButton("Собаки", callback_data=send_dog_images_callback_data)
        )
        return markup

    def __process_next_step(self, message: types.Message):
        try:
            chat_id = message.chat.id
            txt = message.text
            if txt != "exit":
                force_reply = types.ForceReply(selective=False)
                text = f"text = {txt}; chat.id = {chat_id}; \n Для выхода из диалога введите - exit"
                msg = self.bot.send_message(message.chat.id, text, reply_markup=force_reply)
                self.bot.register_next_step_handler(msg, self.__process_next_step)
        except Exception as ex:
            logging.exception(ex)
            self.bot.reply_to(message, f"Exception - {ex}")

    def send_dog_images(self, message: types.Message):
        """Функция для отправки случайных картинок собак"""
        # Вопрос о количестве картинок
        keyboard = [
            [types.InlineKeyboardButton("1 картинка", callback_data="1")],
            [types.InlineKeyboardButton("3 картинки", callback_data="3")],
            [types.InlineKeyboardButton("5 картинок", callback_data="5")]
        ]
        markup = types.InlineKeyboardMarkup(keyboard)
        self.bot.send_message(message.chat.id, "Сколько картинок собак вы хотите?", reply_markup=markup)

    def get_random_dog_image(self):
        """Получение случайной картинки собаки с random.dog"""
        response = requests.get("https://random.dog/woof.json")
        if response.status_code == 200:
            data = response.json()
            return data['url']
        return None

    def handle_dog_image_selection(self, call: types.CallbackQuery):
        """Обработка выбора количества картинок"""
        num_images = int(call.data)  # Получаем число из callback_data
        for _ in range(num_images):
            dog_image_url = self.get_random_dog_image()
            if dog_image_url:
                self.bot.send_photo(call.message.chat.id, dog_image_url)
            else:
                self.bot.send_message(call.message.chat.id, "Не удалось получить изображение собаки, попробуйте снова.")
