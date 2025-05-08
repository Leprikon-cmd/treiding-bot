
class GuardError(Exception):
    pass

class EntryGuards:
    def __init__(self, account, positions, settings):
        self.account = account
        self.positions = positions
        self.settings = settings

    def check_interval(self):
        # Заглушка — здесь должна быть логика проверки времени между входами
        pass

    def check_margin_free(self):
        if self.account.margin_free < self.settings["min_free_margin"]:
            raise GuardError("Недостаточно свободной маржи")

    def check_max_positions(self):
        if len(self.positions) >= self.settings["max_positions"]:
            raise GuardError("Превышено количество открытых позиций")

    def check_tf_trend(self):
        # Заглушка — логика тренда по таймфреймам
        pass

    def check_all(self):
        self.check_interval()
        self.check_margin_free()
        self.check_max_positions()
        self.check_tf_trend()
