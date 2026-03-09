import pygame

class CasinoMap:

    def __init__(self):

        self.areas = [
            {"rect": pygame.Rect(100,100,100,100), "type":"slots"},
            {"rect": pygame.Rect(600,100,100,100), "type":"dice"},
            {"rect": pygame.Rect(350,400,100,100), "type":"roulette"},
            {"rect": pygame.Rect(50,450,100,100), "type":"shop"}
        ]

    def draw(self, screen):

        for area in self.areas:

            if area["type"] == "slots":
                color = (200,0,0)

            elif area["type"] == "dice":
                color = (0,0,200)

            elif area["type"] == "roulette":
                color = (200,200,0)

            elif area["type"] == "shop":
                color = (0,200,0)

            pygame.draw.rect(screen,color,area["rect"])

    def check_interaction(self, player_rect):

        for area in self.areas:
            if player_rect.colliderect(area["rect"]):
                return area["type"]

        return None