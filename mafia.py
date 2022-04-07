class MafiaPlayer:
    def __init__(self, player_id, player_name, game, bot):
        self.player_id = player_id
        self.player_name = player_name

        self.game = game
        self.bot = bot

        self.reset_parameters()

    def reset_parameters(self):
        self.doctor_visit = False  # True если этой ночью приходил доктор
        self.mafia_visit = False  # True если этой ночью приходила мафия (дон)
        self.komissar_visit = False  # True если этой ночью приходил комиссар
        self.maniak_visit = False  # True если этой ночью приходил маньяк
        self.woman_visit = False  # True если этой ночью приходила любовница
        self.advokat_visit = False  # True если этой ночью приходил адвокат


class Mafia(MafiaPlayer):
    def __init__(self, player_id, player_name, game, bot, is_don=False):
        super().__init__(self, player_id, player_name, game, bot)
        self.is_don = is_don



