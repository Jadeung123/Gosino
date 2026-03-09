import pygame

class SuspicionSystem:

    def __init__(self):

        self.level = 0
        self.max_level = 100
        self.font = pygame.font.SysFont(None,30)

    def increase(self, amount):

        self.level += amount

        if self.level > self.max_level:
            self.level = self.max_level

    def decrease(self, amount):

        self.level -= amount

        if self.level < 0:
            self.level = 0

    def is_caught(self):

        return self.level >= self.max_level

    def draw(self, screen):

        text = self.font.render(f"Suspicion: {self.level}", True, (255,80,80))
        screen.blit(text,(10,70))