class DaySystem:

    def __init__(self):
        self.day = 1
        self.time_limit = 90 * 60   # 90 seconds (in frames)
        self.timer = self.time_limit
        self.debt = 100
        self.closing = False

    def update(self):
        if not self.closing:
            self.timer -= 1

            if self.timer <= 0:
                self.closing = True

    def next_day(self):
        self.day += 1
        self.time_limit = max(30 * 60, self.time_limit - 5 * 60)
        self.timer = self.time_limit
        self.debt += 60
        self.closing = False

    def reset_timer(self):
        self.timer = self.time_limit

    def get_time_seconds(self):
        return self.timer // 60