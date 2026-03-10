import pygame

class MessageSystem:

    def __init__(self):
        self.messages = []
        self.queue = []

        self.spawn_delay = 25   # frames between messages
        self.spawn_timer = 0

        self.font = pygame.font.SysFont(None, 30)

    def add(self, text, x, y):
        # add message to queue instead of showing immediately
        self.queue.append([text, x, y])

    def update(self):
        # spawn queued messages slowly
        self.spawn_timer += 1

        if self.queue and self.spawn_timer >= self.spawn_delay:

            text, x, y = self.queue.pop(0)

            self.messages.append([text, x, y, 120])

            self.spawn_timer = 0

        # update active messages
        for m in self.messages:
            m[2] -= 0.3   # slower upward movement
            m[3] -= 1

        # remove expired messages
        self.messages = [m for m in self.messages if m[3] > 0]

    def draw(self, screen):
        for text, x, y, timer in self.messages:
            img = self.font.render(text, True, (255,255,0))
            screen.blit(img, (x, y))