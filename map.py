import pygame

class CasinoMap:

    def __init__(self):

        # interaction zones
        self.areas = [
            {"rect": pygame.Rect(100,100,100,100), "type":"slots"},
            {"rect": pygame.Rect(600,100,100,100), "type":"dice"},
            {"rect": pygame.Rect(350,400,100,100), "type":"roulette"},
            {"rect": pygame.Rect(50,450,100,100), "type":"shop"}
        ]

        # load sprites
        try:
            self.slot_sprite = pygame.image.load("sprites/slot.png")
            self.slot_sprite = pygame.transform.scale(self.slot_sprite,(100,100))
        except:
            self.slot_sprite = None

        try:
            self.dice_sprite = pygame.image.load("sprites/dice.png")
            self.dice_sprite = pygame.transform.scale(self.dice_sprite,(100,100))
        except:
            self.dice_sprite = None

        try:
            self.roulette_sprite = pygame.image.load("sprites/roulette.png")
            self.roulette_sprite = pygame.transform.scale(self.roulette_sprite,(100,100))
        except:
            self.roulette_sprite = None

        try:
            self.shop_sprite = pygame.image.load("sprites/shop.png")
            self.shop_sprite = pygame.transform.scale(self.shop_sprite,(100,100))
        except:
            self.shop_sprite = None


    def draw(self, screen):

        for area in self.areas:

            rect = area["rect"]
            area_type = area["type"]

            if area_type == "slots":

                if self.slot_sprite:
                    screen.blit(self.slot_sprite, rect)
                else:
                    pygame.draw.rect(screen,(200,0,0),rect)

            elif area_type == "dice":

                if self.dice_sprite:
                    screen.blit(self.dice_sprite, rect)
                else:
                    pygame.draw.rect(screen,(0,0,200),rect)

            elif area_type == "roulette":

                if self.roulette_sprite:
                    screen.blit(self.roulette_sprite, rect)
                else:
                    pygame.draw.rect(screen,(200,200,0),rect)

            elif area_type == "shop":

                if self.shop_sprite:
                    screen.blit(self.shop_sprite, rect)
                else:
                    pygame.draw.rect(screen,(0,200,0),rect)


    def check_interaction(self, player_rect):

        for area in self.areas:

            if player_rect.colliderect(area["rect"]):
                return area["type"]

        return None