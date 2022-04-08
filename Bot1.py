import telebot
import traceback
import time
from telebot import types
import threading
import requests
import sqlite3
import random


TOKEN = '5203652236:AAFjvDB4uyP7n0cWmnli-CaEJE4t7_zKvwo'
bot = telebot.TeleBot(TOKEN)

uno_games = {}
players = {}
uno_registrations = {}
move = {}


# Ключи - id групп, значения - [зарегистрированные игроки, id сообщения о начале регистрации, время окончания]


class Game:
    def __init__(self, group_id):
        con = sqlite3.connect("uno_bot.db")
        cur = con.cursor()
        self.result = cur.execute("""SELECT * FROM cards""").fetchall()
        con.close()

        self.group_id = group_id

        bot.send_message(chat_id=group_id,
                         text='Игра начинается!', parse_mode="Markdown")

        for i in uno_registrations[group_id][1]:
            bot.delete_message(
                chat_id=group_id,
                message_id=i,
            )

        self.players = uno_registrations[group_id][0]
        self.move()

    def move(self):
        inf = []
        for i in uno_registrations[self.group_id][0]:
            c = random.sample(self.result, 7)
            inf.append([i, c])
            for j in c:
                del self.result[self.result.index(j)]
        uno_games[self.group_id] = inf
        print(uno_games)
        while True:
            for i in self.players:
                keyboard = types.InlineKeyboardMarkup()
                callback_button = types.InlineKeyboardButton(text="Выбрать карту",
                                                             switch_inline_query_current_chat='')
                keyboard.add(callback_button)
                bot.send_message(chat_id=self.group_id,
                                 text=f'Ход игрока: {i[1]}', reply_markup=keyboard)
                move[self.group_id] = i[0]

                while True:
                    if move[self.group_id] == 'YES':
                        break



class Timer:
    def __init__(self):
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def start_registration(self, group_id, time_for_registration=60):
        return int(time.time()) + time_for_registration

    def loop(self):
        global uno_games
        while True:
            now = int(time.time())

            for i in uno_registrations.copy():
                try:
                    if not isBotAdmin(i):
                        del uno_registrations[i]

                    if uno_registrations[i][2] == now + 60:
                        keyboard = types.InlineKeyboardMarkup()
                        callback_button = types.InlineKeyboardButton(text="Зарегистрироваться",
                                                                     callback_data="register")
                        keyboard.add(callback_button)

                        message = bot.send_message(chat_id=i,
                                                   text='До окончания регистрации осталась 1 минута. Поторопитесь!',
                                                   reply_to_message_id=uno_registrations[i][1][0],
                                                   reply_markup=keyboard)
                        uno_registrations[i][1].append(message.id)

                    elif uno_registrations[i][2] == now + 30:
                        keyboard = types.InlineKeyboardMarkup()
                        callback_button = types.InlineKeyboardButton(text="Зарегистрироваться",
                                                                     callback_data="register")
                        keyboard.add(callback_button)

                        message = bot.send_message(chat_id=i,
                                                   text='До окончания регистрации осталось 30 секунд. Поторопитесь!',
                                                   reply_to_message_id=uno_registrations[i][1],
                                                   reply_markup=keyboard)
                        uno_registrations[i][1].append(message.id)

                    elif uno_registrations[i][2] <= now and i not in uno_games:
                        Game(i)
                        del uno_registrations[i]
                        del uno_games[i]

                except Exception:
                    "В случае, если регистрация закончится в другом потоке"
                    print('Thread error registration')
                    print(Exception)
                    pass

            time.sleep(1)


def isBotAdmin(chat_id):
    mas = bot.get_chat_administrators(chat_id)

    for i in mas:
        if i.user.id == bot.get_me().id:
            mas = []

            mas.append(i.can_edit_messages is None)
            mas.append(i.can_edit_messages is None)
            mas.append(i.can_pin_messages)
            mas.append(i.can_delete_messages)

            if all(mas):
                return True

            bot.send_message(
                chat_id,
                f'''Для работы бота нужны следующие права:
{'✅' if mas[0] else '❌'} Отправлять сообщения
{'✅' if mas[1] else '❌'} Изменять сообщения
{'✅' if mas[2] else '❌'} Прикреплять сообщения
{'✅' if mas[3] else '❌'} Удалять сообщения'''
            )

            return False

    return False
timer = Timer()


class Player:
    def __init__(self, player_id, money):
        self.id = player_id

    def equal(self, other):
        if type(other) == str:
            if self.id == other:
                return True

        else:
            if self.id == other.id:
                return True

        return False


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        'Привет! Я бот для игры в UNO! Напишите "/help" для получения дополнительной информации'
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        'Как работает этот бот, вы можете понять методом тыка!'
    )


@bot.message_handler(commands=['registration_uno'])
def registration_command_uno(message):
    if message.chat.type == 'group':
        start_registration_uno(message.chat.id)


@bot.inline_handler(lambda query: len(query.query) >= 0)
def query(inline_query):
    try:
        result = []
        user_id = inline_query.from_user.id
        print(user_id)
        for i in uno_games:
            for j in uno_games[i]:
                print(j[0][0], user_id, move[i])
                if j[0][0] == user_id and move[i] == user_id:
                    result.append(types.InlineQueryResultCachedSticker('take', sticker_file_id=
                    'CAACAgQAAxkBAAEEWjxiSDuIzyI_nqpFwb9ClCksHx3UPwAC-AIAAl9XmQAB_k3V0pbxGtsjBA'))
                    for cards in j[1]:
                        result.append(types.InlineQueryResultCachedSticker(cards[0], sticker_file_id=cards[1]))
                    result.append(types.InlineQueryResultCachedSticker('pass', sticker_file_id=
                    'CAACAgQAAxkBAAEEWj5iSDuu9LeZ5InRK8xySOe2XYrBUAACzgIAAl9XmQAB3nO8ol7EhmMjBA'))

        bot.answer_inline_query(inline_query.id, result, cache_time=0)
    except Exception as e:
        print(e)


@bot.chosen_inline_handler(lambda chosen_inline_handler: True)
def chosen_handler(chosen_inline_handler):
    for i in move:
        if move[i] == chosen_inline_handler.from_user.id:
            move[i] = 'YES'
            break
    for i in uno_games:
        for j in uno_games[i]:
            if j[0][0] == chosen_inline_handler.from_user.id:
                for g in j[1]:
                    if g[0] == chosen_inline_handler.result_id:
                        cards = j[1]
                        del cards[j[1].index(g)]
                        print(cards)

    print([chosen_inline_handler.from_user.id, chosen_inline_handler.result_id])


@bot.message_handler(commands=['start_game'])
def registration_command_mafia(message):
    if message.chat.id not in uno_registrations:
        bot.send_message(message.chat.id, 'Регистрация не ведется')
    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        Game(message.chat.id)

        del uno_registrations[message.chat.id]
        del uno_games[message.chat.id]
    else:
        bot.send_message(message.chat.id, 'Это действие доступно только для групп')


def start_registration_uno(group_id):
    if group_id in uno_registrations:
        bot.send_message(group_id, 'Регистрация уже началась')
        return

    if group_id in uno_games:
        bot.send_message(group_id, 'Вы уже играете!')
        return

    # Проверка на то, ведутся ли еще игры

    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")
    keyboard.add(callback_button)

    message_id = bot.send_message(group_id,
                                  "Открыт набор для игры в UNO",
                                  reply_markup=keyboard,
                                  parse_mode='Markdown').id

    uno_registrations[group_id] = [[], [message_id], timer.start_registration(group_id)]


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:  # Если вызов из чата с ботом
        if call.data == "register":
            if call.message.chat.id in uno_registrations:
                registered_players = uno_registrations[call.message.chat.id][0]

                if call.from_user.id not in [i[0] for i in registered_players]:

                    registered_players.append((call.from_user.id, call.from_user.first_name))
                    text = f"""Открыт набор для игры в UNO\n
Зарегистрировались:\n"""

                    for i in range(len(registered_players)):
                        text += f'{i + 1}) {registered_players[i][1]} \n'

                    text += f'\nИтого {len(registered_players)} чел.'

                    # Кнопка
                    keyboard = types.InlineKeyboardMarkup()
                    callback_button = types.InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")
                    keyboard.add(callback_button)

                    # Кнопка
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=uno_registrations[call.message.chat.id][1][0],
                                          text=text, reply_markup=keyboard)

                    bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                              text="Вы зарегистрировались")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.id in uno_games:
        bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.id,
        )


while True:
    try:
        bot.polling(none_stop=True)

    except requests.exceptions.ReadTimeout:
        print('ReadTimeout error')
        time.sleep(10)

    except Exception as e:
        print(traceback.format_exc())
