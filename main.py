import threading
import time
import traceback

import requests
import telebot

from players import *
from mafia import *

TOKEN = '5220830717:AAHoxS5mT7ODuAAirBtJt59gC5EEuMBac8w'

print('''------------------restart------------------''')


class MyBot(telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)

    def send_message(self, *args, **args2):
        try:
            a = super().send_message(*args, **args2)
            return a
        except Exception as error:
            print(error)


bot = MyBot(TOKEN)

mafia_games = {}
mafia_registrations = {}
players = get_players(bot)

# Ключи - id групп, значения - [зарегистрированные игроки, id сообщения о начале регистрации, время окончания]


class GameMafia:
    def __init__(self, group_id):
        self.group_id = group_id


        bot.send_message(chat_id=group_id,
                         text='*Игра начинается!*', parse_mode="Markdown")

        for i in mafia_registrations[group_id][1]:
            bot.delete_message(
                chat_id=group_id,
                message_id=i,
            )

        # Распределение ролей
        for i in mafia_registrations[group_id][0]:
            pass

        self.players = mafia_registrations[group_id][0]
        print(self.players)

    def iteration(self):
        return
        bot.send_message(chat_id=self.group_id,
                         text='Живые игроки:\n' + '\n'.join([i[1] for i in self.players]))


class Timer:
    def __init__(self):
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def start_registration(self, group_id, time_for_registration=90):
        return int(time.time()) + time_for_registration

    def loop(self):
        while True:
            now = int(time.time())

            for i in mafia_registrations.copy(): 
                try:
                    if not isBotAdmin(i):
                        del mafia_registrations[i]

                    if mafia_registrations[i][2] == now + 60:
                        keyboard = types.InlineKeyboardMarkup()
                        callback_button = types.InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")
                        keyboard.add(callback_button)

                        message = bot.send_message(chat_id=i,
                                                   text='До окончания регистрации осталась 1 минута. Поторопитесь!',
                                                   reply_to_message_id=mafia_registrations[i][1][0],
                                                   reply_markup=keyboard)
                        mafia_registrations[i][1].append(message.id)

                    elif mafia_registrations[i][2] == now + 30:
                        keyboard = types.InlineKeyboardMarkup()
                        callback_button = types.InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")
                        keyboard.add(callback_button)

                        message = bot.send_message(chat_id=i,
                                                   text='До окончания регистрации осталось 30 секунд. Поторопитесь!',
                                                   reply_to_message_id=mafia_registrations[i][1],
                                                   reply_markup=keyboard)
                        mafia_registrations[i][1].append(message.id)

                    elif mafia_registrations[i][2] <= now:

                        game = GameMafia(i)
                        mafia_games[i] = game

                        del mafia_registrations[i]
                except Exception:
                    "В случае, если регистрация закончится в другом потоке"
                    print('Thread error registration')
                    pass

            for i in mafia_games.copy():
                try:
                    if not isBotAdmin(i):
                        del mafia_games[i]

                    mafia_games[i].iteration()
                except Exception:
                    # В случае, если игра закончится в другом потоке
                    print('Thread error game')

            time.sleep(1)


timer = Timer()


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


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

    bot.send_message(
        message.chat.id,
        'Привет! Я бот для игры в мафию! Напишите "/help" для получения дополнительной информации'
    )

    if message.chat.type == 'private' and message.from_user.id not in players:
        players[message.from_user.id] = Player(message.from_user.id, bot=bot)
        players[message.from_user.id].add_player()

    players[message.from_user.id].print_info()


@bot.message_handler(commands=['profile'])
def stop_registration(message):
    if message.chat.type == 'private':
        players[message.from_user.id].print_info()

@bot.message_handler(commands=['cancel_registration'])
def stop_registration(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.send_message(message.chat.id, 'Это действие возможно только в группе')
        return

    group_id = message.chat.id

    if group_id in mafia_games:
        bot.send_message(group_id, 'Вы уже играете!')
        return

    if group_id not in mafia_registrations:
        bot.send_message(group_id, 'Вы не начали набор в игру')
        return

    for i in mafia_registrations[group_id][1]:
        bot.delete_message(
            chat_id=group_id,
            message_id=i,
        )

    del mafia_registrations[group_id]

    bot.send_message(group_id, 'Регистрация отменена')


@bot.message_handler(commands=['continue_registration'])
def registration_command_mafia(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

    if message.chat.id in mafia_registrations:
        time_continue = message.text.split('@')[0]
        ch = 30
        massiv = time_continue.split()

        if len(massiv) == 1:
            pass

        elif len(massiv) > 2 or not massiv[1].isdigit:
            bot.send_message(
                message.chat.id,
                'Параметр задан некорректно!'
            )

        else:
            ch = int(massiv[1])

        mafia_registrations[message.chat.id][2] += ch

        now = int(time.time())
        left = mafia_registrations[message.chat.id][2] - now

        bot.send_message(
            message.chat.id,
            f'Регистрация продлена на {ch} сек. До её окончания осталось {left} сек.'
        )


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

    bot.send_message(
        message.chat.id,
        'Как работает этот бот, вы можете понять методом тыка!'
    )


@bot.message_handler(commands=['registration_mafia'])
def registration_command_mafia(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        start_registration_mafia(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Это действие доступно только для групп')


@bot.message_handler(commands=['start_game'])
def registration_command_mafia(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

    if message.chat.id not in mafia_registrations:
        bot.send_message(message.chat.id, 'Регистрация не ведется')
    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        game = GameMafia(message.chat.id)
        mafia_games[message.chat.id] = game

        del mafia_registrations[message.chat.id]
    else:
        bot.send_message(message.chat.id, 'Это действие доступно только для групп')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    return


def start_registration_mafia(group_id):
    if group_id in mafia_registrations:
        bot.send_message(group_id, 'Регистрация уже началась')
        return

    if group_id in mafia_games:
        bot.send_message(group_id, 'Вы уже играете!')
        return
    if not isBotAdmin(group_id):
        return

    # Проверка на то, ведутся ли еще игры

    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")
    keyboard.add(callback_button)

    message_id = bot.send_message(group_id,
                                  "Открыт набор для игры в мафию",
                                  reply_markup=keyboard,
                                  parse_mode='Markdown').id

    mafia_registrations[group_id] = [[], [message_id], timer.start_registration(group_id)]


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:  # Если вызов из чата с ботом
        if call.data == "register":
            if call.message.chat.id in mafia_registrations:
                registered_players = mafia_registrations[call.message.chat.id][0]

                if call.from_user.id not in [i[0] for i in registered_players]:

                    registered_players.append((call.from_user.id, call.from_user.first_name))
                    text = f"""Открыт набор для игры в мафию\n
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
                                          message_id=mafia_registrations[call.message.chat.id][1][0],
                                          text=text, reply_markup=keyboard)

                    bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                              text="Вы зарегистрировались")
        elif call.data == "shop":
            players[call.from_user.id].open_shop(call)

        elif call.data.isdigit() and 0 <= int(call.data) <= 5:
            players[call.from_user.id].buy(call)

        elif call.data == 'shop_back':
            players[call.from_user.id].back_shop(call)


@bot.message_handler(content_types=['photo'])
def delete_photo(message):
    if message.chat.id in mafia_games:
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

