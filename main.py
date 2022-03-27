import telebot
import traceback
import time
from telebot import types
import threading
import requests


TOKEN = '5220830717:AAHoxS5mT7ODuAAirBtJt59gC5EEuMBac8w'

print('''------------------restart------------------''')

bot = telebot.TeleBot(TOKEN)

mafia_games = {}
players = {}
mafia_registrations = {}
# Ключи - id групп, значения - [зарегистрированные игроки, id сообщения о начале регистрации, время окончания]


class Game:
    def __init__(self, group_id):
        self.group_id = group_id


        bot.send_message(chat_id=group_id,
                         text='*Игра начинается!*', parse_mode="Markdown")

        for i in mafia_registrations[group_id][1]:
            bot.delete_message(
                chat_id=group_id,
                message_id=i,
            )

        self.players = mafia_registrations[group_id][0]

    def iteration(self):
        return
        bot.send_message(chat_id=self.group_id,
                         text='Живые игроки:\n' + '\n'.join([i[1] for i in self.players]))


class Timer:
    def __init__(self):
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def start_registration(self, group_id, time_for_registration=60):
        return int(time.time()) + time_for_registration

    def loop(self):
        while True:
            now = int(time.time())
            for i in mafia_registrations.copy():
                if mafia_registrations[i][2] == now + 2:
                    keyboard = types.InlineKeyboardMarkup()
                    callback_button = types.InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")
                    keyboard.add(callback_button)

                    message = bot.send_message(chat_id=i,
                                               text='До окончания регистрации осталась 1 минута. Поторопитесь!',
                                               reply_to_message_id=mafia_registrations[i][1][0],
                                               reply_markup=keyboard)
                    mafia_registrations[i][1].append(message.id)

                elif mafia_registrations[i][2] == now + 1:
                    keyboard = types.InlineKeyboardMarkup()
                    callback_button = types.InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")
                    keyboard.add(callback_button)

                    message = bot.send_message(chat_id=i,
                                               text='До окончания регистрации осталось 30 секунд. Поторопитесь!',
                                               reply_to_message_id=mafia_registrations[i][1],
                                               reply_markup=keyboard)
                    mafia_registrations[i][1].append(message.id)

                elif mafia_registrations[i][2] <= now:
                    game = Game(i)
                    mafia_games[i] = game

                    del mafia_registrations[i]

            for i in mafia_games:
                mafia_games[i].iteration()

            time.sleep(1)



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
        'Привет! Я бот для игры в мафию! Напишите "/help" для получения дополнительной информации'
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        'Как работает этот бот, вы можете понять методом тыка!'
    )


@bot.message_handler(commands=['registration_mafia'])
def registration_command_mafia(message):
    if message.chat.type == 'group':
        start_registration_mafia(message.chat.id)



@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.from_user.id in players:
        bot.send_message(message.chat.id, 'Уже зареган')
    else:
        bot.send_message(message.from_user.id, 'Добро пожаловать')
        new_player = Player(message.from_user.id, message.from_user.first_name)
        players[message.from_user.id] = new_player


def start_registration_mafia(group_id):
    if group_id in mafia_registrations:
        bot.send_message(group_id, 'Регистрация уже началась')
        return

    if group_id in mafia_games:
        bot.send_message(group_id, 'Вы уже играете!')
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


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
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

