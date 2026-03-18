import pygame

class UpgradeShop:

    def __init__(self):

        self.font = pygame.font.SysFont(None,40)

        self.upgrades = {
            "Starting Money": {"level":0,"cost":200},
            "Better Odds": {"level":0,"cost":300},
            "Longer Day": {"level":0,"cost":250},
        }

    def handle_input(self,event,player):

        if event.type == pygame.MOUSEBUTTONDOWN:

            mx,my = pygame.mouse.get_pos()

            y = 200

            for name,data in self.upgrades.items():

                rect = pygame.Rect(300,y,200,40)

                if rect.collidepoint(mx,my):

                    if player.money >= data["cost"]:

                        player.money -= data["cost"]
                        data["level"] += 1
                        data["cost"] = int(data["cost"] * 1.6)

                y += 70

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return "next_day"

    def draw(self,screen):

        screen.fill((15,15,25))

        title = self.font.render("UPGRADE SHOP",True,(255,255,255))
        screen.blit(title,(320,80))

        y = 200

        for name,data in self.upgrades.items():

            text = f"{name} LVL {data['level']} - ${data['cost']}"
            label = self.font.render(text,True,(200,255,200))

            rect = pygame.Rect(300,y,200,40)

            pygame.draw.rect(screen,(60,60,80),rect)
            pygame.draw.rect(screen,(150,150,200),rect,2)

            screen.blit(label,(rect.x+10,rect.y+8))

            y += 70