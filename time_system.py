import pygame

class TimeSystem:

    def __init__(self):
        self.time = 0
        self.font = pygame.font.SysFont(None,30)

    def add_time(self, amount):
        self.time += amount

    def draw(self, screen, player):

        time_text = self.font.render(f"Time: {self.time}", True, (255,255,255))
        money_text = self.font.render(f"Money: ${player.money}", True, (255,255,0))

        screen.blit(time_text,(10,10))
        screen.blit(money_text,(10,40))