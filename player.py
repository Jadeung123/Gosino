import pygame

class Player:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 30
        self.speed = 4

        self.money = 100  # starting money

    def move(self, keys):
        moved = False

        if keys[pygame.K_w]:
            self.y -= self.speed
            moved = True
        if keys[pygame.K_s]:
            self.y += self.speed
            moved = True
        if keys[pygame.K_a]:
            self.x -= self.speed
            moved = True
        if keys[pygame.K_d]:
            self.x += self.speed
            moved = True

        return moved

    def draw(self, screen):
        pygame.draw.rect(screen, (120,70,15), (self.x,self.y,self.size,self.size))

    def get_rect(self):
        return pygame.Rect(self.x,self.y,self.size,self.size)