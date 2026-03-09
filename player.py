import pygame

class Player:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.speed = 4
        self.money = 100
        self.clothing = []

        self.sprite = pygame.image.load("sprites/gorilla.png")
        self.sprite = pygame.transform.scale(self.sprite,(32,32))

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
        screen.blit(self.sprite,(self.x,self.y))

    def get_rect(self):
        return pygame.Rect(self.x,self.y,32,32)
    
    def add_clothing(self, item):
        self.clothing.append(item)
        print("Bought:", item.name)

    def has_clothing(self, item):
        return item in self.clothing