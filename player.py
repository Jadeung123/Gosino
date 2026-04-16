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
        self.money  = 500
        self.clothing = []

        # Permanent upgrade attributes (set by shop)
        self.slot_threshold   = 5
        self.multiplier_bonus = 0.0
        self.max_bet = 1000
        self.dice_speed_bonus = 0
        self.daily_bonus = 0
        self.cooldown_reduction = 0.0
        self.adrenaline_bonus = 0
        self.debt_reduction = 0

    # ------------------------------------------------------------------

    def move(self, keys, walls=None, screen_w=800, screen_h=558):
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
        """
        Gorilla head — dark grey-blue, heavy brow, small tight muzzle.
        """
        cx = int(self.x + 16)
        cy = int(self.y + 16)

        # Shadow
        pygame.draw.ellipse(screen, (20, 80, 20),
                            (cx - 12, cy + 13, 24, 7))

        # Cheek bulges — behind main head
        pygame.draw.circle(screen, (55, 62, 75), (cx - 12, cy + 3), 6)
        pygame.draw.circle(screen, (55, 62, 75), (cx + 12, cy + 3), 6)

        # Main head
        pygame.draw.circle(screen, (62, 70, 85), (cx, cy), 15)

        # Brow ridge — thick and dark, dominant feature
        pygame.draw.ellipse(screen, (35, 38, 50),
                            (cx - 13, cy - 14, 26, 10))

        # Muzzle — small, darker than head, low on the face
        # Much smaller than before so it doesn't look like a snout
        pygame.draw.ellipse(screen, (75, 80, 92),
                            (cx - 6, cy + 4, 12, 9))

        # Nostrils — close together, small
        pygame.draw.circle(screen, (30, 32, 44), (cx - 2, cy + 7), 2)
        pygame.draw.circle(screen, (30, 32, 44), (cx + 2, cy + 7), 2)

        # Mouth — thin line just below muzzle
        pygame.draw.line(screen, (35, 37, 48),
                         (cx - 4, cy + 11), (cx + 4, cy + 11), 2)

        # Eyes — close together, sitting just under the brow
        pygame.draw.circle(screen, (20, 22, 32), (cx - 4, cy - 4), 4)
        pygame.draw.circle(screen, (20, 22, 32), (cx + 4, cy - 4), 4)

        # Eye shine
        pygame.draw.circle(screen, (200, 215, 235), (cx - 3, cy - 5), 1)
        pygame.draw.circle(screen, (200, 215, 235), (cx + 5, cy - 5), 1)

        # Angry brow lines
        pygame.draw.line(screen, (25, 28, 40),
                         (cx - 10, cy - 13), (cx - 3, cy - 11), 2)
        pygame.draw.line(screen, (25, 28, 40),
                         (cx + 10, cy - 13), (cx + 3, cy - 11), 2)

        # Outline
        pygame.draw.circle(screen, (35, 40, 52), (cx, cy), 15, 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, 32, 32)

    def add_clothing(self, item):
        self.clothing.append(item)

    def has_clothing(self, item):
        return item in self.clothing