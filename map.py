# map.py
# CasinoMap defines interaction zones AND wall zones.
# Walls are plain Rects the player and guards cannot enter.
# draw() renders both the floor decorations and the walls.

import pygame
from constants import PLAY_HEIGHT

class CasinoMap:

    def __init__(self):

        self.cooldowns = {"slots": 0, "dice": 0, "roulette": 0, "case": 0, "blackjack": 0}

        # --- Interaction zones ---
        self.areas = [
            {"rect": pygame.Rect(100, 100, 100, 100), "type": "slots"},
            {"rect": pygame.Rect(600, 100, 100, 100), "type": "dice"},
            {"rect": pygame.Rect(350, 400, 100, 100), "type": "roulette"},
            {"rect": pygame.Rect(650, 200, 100, 100), "type": "case"},
            {"rect": pygame.Rect(350, 150, 100, 100), "type": "blackjack"},
            {"rect": pygame.Rect(50,  450, 100, 100), "type": "shop"},
            {"rect": pygame.Rect(700, 500,  80,  80), "type": "exit"},
        ]

        # --- Wall zones (blocks player movement) ---
        # These mirror the casino furniture / machine positions
        # plus a perimeter wall so the player cannot leave the room.
        self.walls = [
            # Perimeter (10px thick)
            pygame.Rect(0, 0, 800, 10),  # top
            pygame.Rect(0, 0, 10, PLAY_HEIGHT),  # left
            pygame.Rect(790, 0, 10, PLAY_HEIGHT),  # right

            # Decorative pillars (solid blocks, no interaction)
            pygame.Rect(250, 200, 30, 30),
            pygame.Rect(520, 200, 30, 30),
            pygame.Rect(250, 350, 30, 30),
            pygame.Rect(520, 350, 30, 30),
        ]

        # --- Load sprites ---
        try:
            self.slot_sprite = pygame.image.load("sprites/slot.png")
            self.slot_sprite = pygame.transform.scale(self.slot_sprite, (100, 100))
        except:
            self.slot_sprite = None

        try:
            self.dice_sprite = pygame.image.load("sprites/dice.png")
            self.dice_sprite = pygame.transform.scale(self.dice_sprite, (100, 100))
        except:
            self.dice_sprite = None

        try:
            self.roulette_sprite = pygame.image.load("sprites/roulette.png")
            self.roulette_sprite = pygame.transform.scale(self.roulette_sprite, (100, 100))
        except:
            self.roulette_sprite = None

        try:
            self.shop_sprite = pygame.image.load("sprites/shop.png")
            self.shop_sprite = pygame.transform.scale(self.shop_sprite, (100, 100))
        except:
            self.shop_sprite = None

    # ------------------------------------------------------------------

    def draw(self, screen):
        # Draw floor pattern first
        self._draw_floor(screen)

        # Draw interaction zones
        for area in self.areas:
            rect      = area["rect"]
            area_type = area["type"]

            if area_type == "slots":
                if self.slot_sprite:
                    screen.blit(self.slot_sprite, rect)
                else:
                    pygame.draw.rect(screen, (200, 0, 0), rect)

            elif area_type == "dice":
                if self.dice_sprite:
                    screen.blit(self.dice_sprite, rect)
                else:
                    pygame.draw.rect(screen, (0, 0, 200), rect)

            elif area_type == "roulette":
                if self.roulette_sprite:
                    screen.blit(self.roulette_sprite, rect)
                else:
                    pygame.draw.rect(screen, (200, 200, 0), rect)

            elif area_type == "case":
                pygame.draw.rect(screen, (180, 50, 50), rect)
                font = pygame.font.SysFont(None, 22)
                screen.blit(
                    font.render("CASES", True, (255, 255, 255)),
                    (rect.x + 22, rect.y + 38)
                )

            elif area_type == "blackjack":
                pygame.draw.rect(screen, (30, 100, 50), rect)
                font = pygame.font.SysFont(None, 22)
                screen.blit(font.render("BJ", True, (255, 255, 255)), (rect.x + 36, rect.y + 38))

            elif area_type == "shop":
                if self.shop_sprite:
                    screen.blit(self.shop_sprite, rect)
                else:
                    pygame.draw.rect(screen, (0, 200, 0), rect)

            elif area_type == "exit":
                pygame.draw.rect(screen, (200, 200, 255), rect)
                font = pygame.font.SysFont(None, 22)
                screen.blit(
                    font.render("EXIT", True, (0, 0, 0)),
                    (rect.x + 22, rect.y + 32)
                )

        # Draw pillars on top
        self._draw_pillars(screen)

    def _draw_floor(self, screen):
        """Checkerboard tile pattern for the casino floor."""
        tile = 40
        color1 = (34, 110, 34)
        color2 = (28, 95, 28)

        for row in range(0, PLAY_HEIGHT, tile):  # was range(0, 600, tile)
            for col in range(0, 800, tile):
                color = color1 if (row // tile + col // tile) % 2 == 0 else color2
                pygame.draw.rect(screen, color, (col, row, tile, tile))

    def _draw_pillars(self, screen):
        """Draw the decorative pillar wall blocks."""
        pillar_rects = [
            pygame.Rect(250, 200, 30, 30),
            pygame.Rect(520, 200, 30, 30),
            pygame.Rect(250, 350, 30, 30),
            pygame.Rect(520, 350, 30, 30),
        ]
        for rect in pillar_rects:
            pygame.draw.rect(screen, (80,  60,  40),  rect)
            pygame.draw.rect(screen, (120, 90,  60),  rect, 3)

    # ------------------------------------------------------------------

    def check_interaction(self, player_rect):
        for area in self.areas:
            if player_rect.colliderect(area["rect"]):
                return area["type"]
        return None

    def update_cooldowns(self):
        for game in self.cooldowns:
            if self.cooldowns[game] > 0:
                self.cooldowns[game] -= 1