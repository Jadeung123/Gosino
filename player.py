# player.py
# Player movement now includes screen boundary checks
# and wall collision. move() accepts an optional list of
# wall rects and prevents the player from entering them.

import pygame

class Player:

    def __init__(self, x, y):
        self.x      = x
        self.y      = y
        self.speed  = 4
        self.base_speed = 4
        self.luck   = 0
        self.stealth = 0
        self.money  = 100000000
        self.clothing = []

        # Permanent upgrade attributes (set by shop)
        self.slot_threshold   = 5
        self.multiplier_bonus = 0.0
        self.luck = 0
        self.stealth = 0
        self.max_bet = 1000
        self.dice_speed_bonus = 0
        self.daily_bonus = 0
        self.cooldown_reduction = 0.0
        self.adrenaline_bonus = 0
        self.debt_reduction = 0

        self.sprite = pygame.image.load("sprites/gorilla.png")
        self.sprite = pygame.transform.scale(self.sprite, (32, 32))

    # ------------------------------------------------------------------

    def move(self, keys, walls=None, screen_w=800, screen_h=600):
        """
        Move the player, then resolve collisions.
        walls  — list of pygame.Rect objects the player cannot enter.
        """
        # Store position before moving so we can revert on collision
        old_x, old_y = self.x, self.y

        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_d]: self.x += self.speed

        # --- Screen boundary ---
        self.x = max(0, min(screen_w - 32, self.x))
        self.y = max(0, min(screen_h - 32, self.y))

        # --- Wall collision ---
        if walls:
            player_rect = self.get_rect()
            for wall in walls:
                if player_rect.colliderect(wall):
                    # Try sliding: restore only the axis that caused the collision

                    # Test if horizontal movement caused it
                    test_x = pygame.Rect(self.x, old_y, 32, 32)
                    if test_x.colliderect(wall):
                        self.x = old_x   # block horizontal

                    # Test if vertical movement caused it
                    test_y = pygame.Rect(old_x, self.y, 32, 32)
                    if test_y.colliderect(wall):
                        self.y = old_y   # block vertical

    # ------------------------------------------------------------------

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, 32, 32)

    def add_clothing(self, item):
        self.clothing.append(item)

    def has_clothing(self, item):
        return item in self.clothing