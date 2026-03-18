# score_system.py
# Score is earned only by winning gambles.
# No passive time-based scoring.

import pygame

class ScoreSystem:

    def __init__(self):
        self.score = 0
        self.font  = pygame.font.SysFont(None, 30)

    def add_money_score(self, amount):
        """Called by gambling games when the player wins."""
        self.score += amount

    def draw(self, screen):
        text = self.font.render(f"Score: {int(self.score)}", True, (255, 255, 255))
        screen.blit(text, (10, 100))