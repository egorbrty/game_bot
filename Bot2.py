import telebot
import traceback
import time
import threading
import requests
import random
from players import *


TOKEN = '5312049767:AAGQlrrbIcWrF8esJBwOkwadwvoW6Ro2d3Y'


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

uno_games = {}
uno_registrations = {}
move = {}
uno_cards = {}
players = get_players(bot)
print('start')


# Ключи - id групп, значения - [зарегистрированные игроки, id сообщения о начале регистрации, время окончания]


class Game:
    def __init__(self, group_id):
        con = sqlite3.connect("uno_bot.db")
        cur = con.cursor()
        self.result = cur.execute("""SELECT * FROM cards""").fetchall()
        con.close()

        self.group_id = group_id
        print(self.group_id)

        move[self.group_id] = ['', 'n']
        bot.send_message(chat_id=group_id,
                         text='Игра начинается!', parse_mode="Markdown")

        for i in uno_registrations[group_id][1]:
            bot.delete_message(
                chat_id=group_id,
                message_id=i,
            )

        inf = []
        for i in uno_registrations[self.group_id][0]:
            c = random.sample(self.result, 7)
            inf.append([i, c])
            for j in c:
                del self.result[self.result.index(j)]
        del uno_registrations[self.group_id]
        uno_games[self.group_id] = inf
        uno_cards[self.group_id] = [self.result, []]

        self.move(self.group_id)


    def move(self, id_gruop):
        running = True
        while running:
            id = id_gruop
            for i in uno_games[id]:
                if len(i[1]) == 0:
                    bot.send_message(chat_id=id,
                                     text=f'{i[0][1]} выиграл!')
                    running = False
                    break

                if len(uno_cards[id][0]) == 0:
                    print(uno_cards)
                    uno_cards[id][0] = uno_cards[id][1]
                    print()
                    print()
                    print(uno_cards)

                if move[id][0] == 'con':
                    move[id][0] = 'YES'
                    continue

                elif move[id][0] == 'rev':
                    move[id][0] = ''
                    break

                keyboard = types.InlineKeyboardMarkup()
                callback_button = types.InlineKeyboardButton(text="Выбрать карту",
                                                             switch_inline_query_current_chat='')
                keyboard.add(callback_button)
                bot.send_message(chat_id=id,
                                 text=f'Ход игрока: {i[0][1]}', reply_markup=keyboard)
                move[id][0] = i[0][0]

                while True:
                    if move[id][0] == 'YES' or move[id][0] == 'con' or move[id][0] == 'rev':
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



def take(user_id, amount, chat_id):
    card = random.sample(uno_cards[chat_id][0], amount)
    for i in uno_games[chat_id]:
        if i[0][0] == user_id:
            for n in card:
                i[1].append(n)
                car = uno_cards[chat_id][0].pop(uno_cards[chat_id][0].index(n))
                uno_cards[chat_id][1].append(car)
            break


def choise_color(chat_id):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("🔵", callback_data='b')
    item2 = types.InlineKeyboardButton("🟢", callback_data='g')
    item3 = types.InlineKeyboardButton("🔴", callback_data='r')
    item4 = types.InlineKeyboardButton("🟡", callback_data='y')

    markup.add(item1, item2, item3, item4)
    bot.send_message(chat_id, text='Выберете цвет!', reply_markup=markup)


def get_text(i, j):
    player = []
    color = move[i][1][0]

    if color == 'r':
        card = '🔴' + move[i][1].split('_')[-1]

    elif color == 'y':
        card = '🟡' + move[i][1].split('_')[-1]

    elif color == 'b':
        card = '🔵' + move[i][1].split('_')[-1]

    elif color == 'g':
        card = '🟢' + move[i][1].split('_')[-1]

    else:
        if len(move[i][1].split('_')) == 1:
            card = 'Первый игрок не сходил'

        else:
            card = move[i][1].split('_')[-1]

    for name in uno_games[i]:
        player.append(name[0][1])

    text = f"""Ход игрока: {j[0][1]}\n
Последняя карта: {card}\n
Игроки: {', '.join(player)}"""

    return text


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

    bot.send_message(
        message.chat.id,
        'Привет! Я бот для игры в UNO! Напишите "/help" для получения дополнительной информации'
    )

    if message.chat.type == 'private' and message.from_user.id not in players:
        players[message.from_user.id] = Player(message.from_user.id, bot=bot)
        players[message.from_user.id].add_player()

    players[message.from_user.id].print_info()


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        'Как работает этот бот, вы можете понять методом тыка!'
    )


@bot.message_handler(commands=['registration_uno'])
def registration_command_uno(message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        start_registration_uno(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Это действие доступно только для групп')


@bot.inline_handler(lambda query: len(query.query) == 0)
def query(inline_query):
    result = []
    user_id = inline_query.from_user.id
    for i in uno_games:
        for j in uno_games[i]:
            if j[0][0] == user_id and move[i][0] == user_id:
                result.append(types.InlineQueryResultCachedSticker('take', sticker_file_id=
                'CAACAgQAAxkBAAEEWjxiSDuIzyI_nqpFwb9ClCksHx3UPwAC-AIAAl9XmQAB_k3V0pbxGtsjBA'))
                for cards in j[1]:
                    if ((move[i][1][0] == cards[0][0] or move[i][1][0] == 'n')
                        or cards[0][0] == 'n' or move[i][1].split('_')[-1] == cards[0].split('_')[-1]) \
                            and (move[i][1].split('_')[-1] not in ['color', '+4']):
                        result.append(types.InlineQueryResultCachedSticker(cards[0],
                                                                           sticker_file_id=cards[1]))
                    else:
                        result.append(types.InlineQueryResultCachedSticker
                                      (cards[0], sticker_file_id=cards[1],
                                      input_message_content=types.InputTextMessageContent(get_text(i, j))))

                result.append(types.InlineQueryResultCachedSticker
                              ('inf',
                               sticker_file_id='CAACAgQAAxkBAAEEbvdiUyX84VWmnoMOxJFENg3k_ThtcwACxAIAAl9XmQABotkMvdyCEMIjBA',
                               input_message_content=types.InputTextMessageContent(get_text(i, j))))

                bot.answer_inline_query(inline_query.id, result, cache_time=0)



@bot.chosen_inline_handler(lambda chosen_inline_handler: True)
def chosen_handler(chosen_inline_handler):
    result_id = chosen_inline_handler.result_id
    running = True

    for i in move:
        if (move[i][1][0] == result_id[0] or move[i][1][0] == 'n'
                or result_id[0] == 'n' or result_id.split('_')[-1] == move[i][1].split('_')[-1]) \
                and (result_id not in ['inf', 'take']) and (move[i][1].split('_')[-1] not in ['color', '+4']):
            if result_id.split('_')[-1] == '+2':
                move[i][0] = 'YES'

                while True:
                    if move[i][0] != 'YES':
                        break
                take(move[i][0], 2, i)

            elif result_id.split('_')[-1] == '+4':
                choise_color(i)

            elif result_id.split('_')[-1] == 'color':
                choise_color(i)

            elif result_id.split('_')[-1] == 'reverse':
                for j in uno_games[i]:
                    if j[0][0] == move[i][0]:
                        ind = uno_games[i].index(j)

                player = uno_games[i][:ind][::-1] + uno_games[i][ind + 1:][::-1] + [uno_games[i][ind]]
                move[i][0] = 'rev'
                uno_games[i] = player

            elif result_id.split('_')[-1] == 'skipping':
                move[i][0] = 'con'

            else:
                move[i][0] = 'YES'

        elif result_id == 'take':
            take(chosen_inline_handler.from_user.id, 1, i)

        else:
            running = False

    if running:
        for i in uno_games:
            for j in uno_games[i]:
                if j[0][0] == chosen_inline_handler.from_user.id:
                    for g in j[1]:
                        if g[0] == chosen_inline_handler.result_id:
                            move[i][1] = chosen_inline_handler.result_id
                            cards = j[1]
                            del cards[j[1].index(g)]


@bot.message_handler(commands=['start_game'])
def registration_command_uno(message):
    if message.chat.id not in uno_registrations:
        bot.send_message(message.chat.id, 'Регистрация не ведется')
    elif message.chat.type == 'group' or message.chat.type == 'supergroup':
        Game(message.chat.id)
        del uno_games[message.chat.id]
    else:
        bot.send_message(message.chat.id, 'Это действие доступно только для групп')


@bot.message_handler(commands=['profile'])
def stop_registration(message):
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.id,
    )

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

    if group_id in uno_games:
        bot.send_message(group_id, 'Вы уже играете!')
        return

    if group_id not in uno_registrations:
        bot.send_message(group_id, 'Вы не начали набор в игру')
        return

    for i in uno_registrations[group_id][1]:
        bot.delete_message(
            chat_id=group_id,
            message_id=i,
        )

    del uno_registrations[group_id]

    bot.send_message(group_id, 'Регистрация отменена')


def start_registration_uno(group_id):
    if group_id in uno_registrations:
        bot.send_message(group_id, 'Регистрация уже началась')
        return

    if group_id in uno_games:
        bot.send_message(group_id, 'Вы уже играете!')
        return
    if not isBotAdmin(group_id):
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

        elif call.data in ['r', 'y', 'g', 'b']:
            if call.from_user.id == move[call.message.chat.id][0]:
                if call.data == 'r':
                    text = '🔴'

                elif call.data == 'y':
                    text = '🟡'

                elif call.data == 'b':
                    text = '🔵'

                elif call.data == 'g':
                    text = '🟢'
                bot.send_message(chat_id=call.message.chat.id,
                                 text=f'Цвет: {text}')
                if move[call.message.chat.id][1].split('_')[-1] == '+4':
                    move[call.message.chat.id][1] = call.data + '_'
                    move[call.message.chat.id][0] = 'YES'
                    while True:
                        if move[call.message.chat.id][0] != 'YES':
                            break
                    take(move[call.message.chat.id][0], 4, call.message.chat.id)
                else:
                    move[call.message.chat.id][0] = 'YES'

        elif call.data == "shop":
            players[call.from_user.id].open_shop(call)

        elif call.data.isdigit() and 0 <= int(call.data) <= 5:
            players[call.from_user.id].buy(call)

        elif call.data == 'shop_back':
            players[call.from_user.id].back_shop(call)





while True:
    try:
        bot.polling(none_stop=True)

    except requests.exceptions.ReadTimeout:
        print('ReadTimeout error')
        time.sleep(10)

    except Exception as e:
        print(traceback.format_exc())
