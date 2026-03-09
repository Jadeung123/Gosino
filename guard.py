import pygame
import random

class Guard:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.direction = random.choice(["up","down","left","right"])
        self.size = 30
        self.color = (0,0,255)
        self.move_timer = 0
        self.chasing = False
        self.chase_speed = 4
        self.sprite = pygame.image.load("sprites/guard.png")
        self.sprite = pygame.transform.scale(self.sprite,(32,32))

    def move(self):
        self.move_timer += 1

        if self.move_timer > 60:
            self.direction = random.choice(["up","down","left","right"])
            self.move_timer = 0

        if self.direction == "up":
            self.y -= self.speed

        if self.direction == "down":
            self.y += self.speed

        if self.direction == "left":
            self.x -= self.speed

        if self.direction == "right":
            self.x += self.speed

    def draw(self, screen):
        screen.blit(self.sprite,(self.x,self.y))

    def see_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y

        distance = (dx**2 + dy**2) ** 0.5

        if distance > 150:
            return False

        # Direction check
        if self.direction == "up" and dy < 0:
            return True

        if self.direction == "down" and dy > 0:
            return True

        if self.direction == "left" and dx < 0:
            return True

        if self.direction == "right" and dx > 0:
            return True

        return False
    
    def draw_vision(self, screen):
        vision_color = (255,255,0)

        if self.direction == "up":
            pygame.draw.polygon(screen, vision_color,
                [(self.x+15,self.y),
                (self.x-60,self.y-120),
                (self.x+90,self.y-120)])

        if self.direction == "down":
            pygame.draw.polygon(screen, vision_color,
                [(self.x+15,self.y+30),
                (self.x-60,self.y+150),
                (self.x+90,self.y+150)])

        if self.direction == "left":
            pygame.draw.polygon(screen, vision_color,
                [(self.x,self.y+15),
                (self.x-120,self.y-60),
                (self.x-120,self.y+90)])

        if self.direction == "right":
            pygame.draw.polygon(screen, vision_color,
                [(self.x+30,self.y+15),
                (self.x+150,self.y-60),
                (self.x+150,self.y+90)])
            
    def chase_player(self, player):
        if player.x > self.x:
            self.x += self.chase_speed
        if player.x < self.x:
            self.x -= self.chase_speed

        if player.y > self.y:
            self.y += self.chase_speed
        if player.y < self.y:
            self.y -= self.chase_speed