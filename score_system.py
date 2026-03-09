import pygame

class ScoreSystem:

    def __init__(self):

        self.score = 0
        self.font = pygame.font.SysFont(None, 30)

    def add_money_score(self, amount):
        self.score += amount * 2

    def add_survival_score(self):
        self.score += 1

    def add_risk_bonus(self, suspicion):
        if suspicion > 70:
            self.score += 5

    def draw(self, screen):
        text = self.font.render(f"Score: {int(self.score)}", True, (255,255,255))
        screen.blit(text, (10,100))