import pygame
import random
import math

class Guard:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.speed = 1.2
        self.chase_speed = 2.2

        self.direction = random.choice(["up","down","left","right"])

        self.move_timer = 0
        self.notice_timer = 0

        self.chasing = False

        self.vision_distance = 110

        self.sprite = pygame.image.load("sprites/guard.png")
        self.sprite = pygame.transform.scale(self.sprite,(32,32))


    # PATROL MOVEMENT
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


    # PLAYER DETECTION
    def see_player(self, player):

        dx = player.x - self.x
        dy = player.y - self.y

        distance = math.sqrt(dx**2 + dy**2)

        if distance > self.vision_distance:
            return False

        if self.direction == "up" and dy < 0:
            return True

        if self.direction == "down" and dy > 0:
            return True

        if self.direction == "left" and dx < 0:
            return True

        if self.direction == "right" and dx > 0:
            return True

        return False


    # VISION CONE
    def draw_vision(self, screen):

        vision_color = (255,255,0)

        if self.direction == "up":
            pygame.draw.polygon(screen, vision_color,
                [(self.x+16,self.y),
                 (self.x-40,self.y-80),
                 (self.x+72,self.y-80)])

        if self.direction == "down":
            pygame.draw.polygon(screen, vision_color,
                [(self.x+16,self.y+32),
                 (self.x-40,self.y+110),
                 (self.x+72,self.y+110)])

        if self.direction == "left":
            pygame.draw.polygon(screen, vision_color,
                [(self.x,self.y+16),
                 (self.x-90,self.y-40),
                 (self.x-90,self.y+72)])

        if self.direction == "right":
            pygame.draw.polygon(screen, vision_color,
                [(self.x+32,self.y+16),
                 (self.x+110,self.y-40),
                 (self.x+110,self.y+72)])


    # CHASE PLAYER
    def chase_player(self, player):

        dx = player.x - self.x
        dy = player.y - self.y

        distance = math.sqrt(dx**2 + dy**2)

        if distance != 0:

            self.x += (dx / distance) * self.chase_speed
            self.y += (dy / distance) * self.chase_speed