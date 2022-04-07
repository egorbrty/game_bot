import sqlite3
from telebot import types


price = {0: 200,
         1: 100,
         2: 150,
         3: 50,
         4: 100,
         5: 170
}


class Player:
    def __init__(self, player_id, money=100,
                 mafia_role=0, mafia_shield=0, mafia_documents=0,
                 uno_skips=0, uno_change_color=0, uno_cards=0,
                 bot=None):

        self.id = player_id
        self.money = money

        self.bot = bot

        self.objects = [mafia_role, mafia_shield, mafia_documents,
                        uno_skips, uno_change_color, uno_cards]

    def print_info(self):
        """Пишет информацию о профиле игроку"""
        text = self.get_info()

        keyboard = types.InlineKeyboardMarkup()
        callback_button = types.InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")
        keyboard.add(callback_button)

        self.bot.send_message(chat_id=self.id, text=text, parse_mode="Markdown", reply_markup=keyboard)

    def get_info(self):
        text = f'''👤*Профиль*

💵 Деньги: {self.money}

🎎 Активная роль: {self.objects[0]}
🛡 Защита: {self.objects[1]}
📂 Документы: {self.objects[2]}

🔴 Пропуск хода: {self.objects[3]}
🔄 Смена цвета: {self.objects[4]}
➕ +2 карты любому противнику: {self.objects[5]}'''

        return text

    def use_object(self, obj_id):
        """Тратит объект. Возвращает 1 если объект потрачен и 0, если объекта нет"""
        if self.objects[obj_id]:
            self.objects[obj_id] -= 1
            self.load_info()
            return True
        return False

    def open_shop(self, call):
        # Кнопка
        text = '''Что ты хочешь купить? 
_Мафия_
🎎 *Активная роль*
Надоело скучать по ночам? Эта покупка увеличит шанс выпадения активной роли
🛡 *Защита*
Может спасти один раз, если кто-то ночью попытается тебя убить
📂 *Документы*
Пригодятся, когда комиссар захочет проверить твою роль

_Уно_
🔴 *Пропуск хода*
Позволит тебе пропустить ход в случае, если у тебя нет нужной карты
🔄 *Смена цвета*
Нет нужной карты? Не беда. Это усиление позволяет один раз сменить цвет
➕ *2 карты любому противнику*
Не повезло тому, кого ты выберешь... Ведь у этого игрока образуется 2 дополнительных карты
'''

        keyboard = types.InlineKeyboardMarkup()

        mas = [f'🎎 Активная роль - {price[0]}', f'🛡 Защита - {price[1]}', f'📂 Поддельные документы - {price[2]}',
                 f'🔴 Пропуск хода - {price[3]}', f'🔄 Смена цвета - {price[4]}',
               f'➕ 2 карты любому противнику - {price[5]}']

        for i in range(len(mas)):
            callback_button = types.InlineKeyboardButton(text=mas[i],
                                                         callback_data=str(i))
            keyboard.add(callback_button)

        callback_button = types.InlineKeyboardButton(text='⬅ Назад', callback_data='shop_back')
        keyboard.add(callback_button)

        # Кнопка
        self.bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.id,
                              text=text, reply_markup=keyboard, parse_mode="Markdown")

        self.bot.answer_callback_query(callback_query_id=call.id, show_alert=True,
                                  text="Что ты хочешь купить?")

    def buy(self, call):
        """Купить предмет"""
        if self.money < price[int(call.data)]:
            self.bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                                           text="Недостаточно средств. Нужно больше играть!")
            return

        # !!!!!!!!!!!!!!!!!!!!!!!!!!сохранение

        self.money -= price[int(call.data)]

        self.objects[int(call.data)] += 1

        name = call.message.json['reply_markup']['inline_keyboard'][int(call.data)][0]['text']

        name = name.split(' - ')[0]

        self.bot.answer_callback_query(callback_query_id=call.id, show_alert=True,
                                       text="Теперь у тебя есть: " + name)
        self.load_info()

    def back_shop(self, call):
        """Вернуться из магазина"""
        text = self.get_info()

        keyboard = types.InlineKeyboardMarkup()
        callback_button = types.InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")
        keyboard.add(callback_button)

        self.bot.edit_message_text(chat_id=self.id, text=text,
                                   parse_mode="Markdown", message_id=call.message.id,
                                   reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id=call.id, show_alert=True)

    def load_info(self):
        """Загрузка информации о пользователе в БД"""
        con = sqlite3.connect("files/players.sqlite")
        cur = con.cursor()

        cur.execute(f"""UPDATE players
SET money={self.money},
mafia_role={self.objects[0]},
mafia_shield={self.objects[1]},
mafia_documents={self.objects[2]},
uno_skips={self.objects[3]},
uno_change_color={self.objects[4]},
uno_cards={self.objects[5]}
WHERE ID={self.id}""")
        con.commit()

        con.close()

    def add_player(self):
        """Новый игрок"""
        con = sqlite3.connect("files/players.sqlite")
        cur = con.cursor()

        cur.execute(f"""INSERT INTO players
        VALUES ({self.id}, 100, 0, 0, 0, 0, 0, 0)""")

        con.commit()
        con.close()

def get_players(bot):
    """Возвращает массив экземпляров класса Player"""
    con = sqlite3.connect("files/players.sqlite")

    cur = con.cursor()

    try:
        result = {}
        mas_id = cur.execute("""SELECT id FROM players""").fetchall()

        for i in mas_id:
            mas = cur.execute(f"""SELECT * FROM players WHERE id={i[0]}""").fetchall()[0]

            result[i[0]] = Player(*mas, bot)

        con.close()

        return result

    except:
        cur.execute("""CREATE TABLE players (
            id int,
            money int,
            mafia_role int,
            mafia_shield int,
            mafia_documents int,
            uno_skips int,
            uno_change_color int,
            uno_cards int,
            PRIMARY KEY(id)
        )""")

        con.commit()

        con.close()

        return {}


