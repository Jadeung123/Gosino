# map.py
# CasinoMap defines interaction zones AND wall zones.
# Walls are plain Rects the player and guards cannot enter.
# draw() renders both the floor decorations and the walls.

import pygame
from constants import PLAY_HEIGHT

class CasinoMap:

    def __init__(self):
        from constants import PLAY_HEIGHT
        self.cooldowns = {"slots": 0, "dice": 0, "roulette": 0, "case": 0, "blackjack": 0}

        # --- Interaction zones ---
        # 5 gambling machines along the top wall, evenly spaced
        # Shop bottom-left, Exit bottom-right
        self.areas = [
            {"rect": pygame.Rect(20, 50, 100, 90), "type": "slots"},
            {"rect": pygame.Rect(210, 40, 110, 90), "type": "blackjack"},
            {"rect": pygame.Rect(340, 40, 110, 90), "type": "roulette"},
            {"rect": pygame.Rect(470, 40, 110, 90), "type": "dice"},
            {"rect": pygame.Rect(670, 50, 100, 90), "type": "case"},
            {"rect": pygame.Rect(20, 420, 110, 110), "type": "shop"},
            {"rect": pygame.Rect(650, 448, 110, 80), "type": "exit"},
        ]

        # --- Walls ---
        self.walls = [
            # Perimeter only
            pygame.Rect(0, 0, 800, 10),
            pygame.Rect(0, PLAY_HEIGHT - 10, 800, 10),
            pygame.Rect(0, 0, 10, PLAY_HEIGHT),
            pygame.Rect(790, 0, 10, PLAY_HEIGHT),

            # 6 pillars — only solid obstacles on the floor
            pygame.Rect(165, 140, 24, 24),
            pygame.Rect(611, 140, 24, 24),
            pygame.Rect(165, 280, 24, 24),
            pygame.Rect(611, 280, 24, 24),
            pygame.Rect(165, 390, 24, 24),
            pygame.Rect(611, 390, 24, 24),
        ]

    # ------------------------------------------------------------------

    def draw(self, screen):
        """Draw floor, then each zone with a custom drawn icon, then pillars."""
        self._draw_floor(screen)
        self._draw_ceiling_lights(screen)

        for area in self.areas:
            rect = area["rect"]
            area_type = area["type"]
            cx = rect.centerx
            cy = rect.centery

            if area_type == "slots":
                self._draw_slots(screen, rect, cx, cy)
            elif area_type == "dice":
                self._draw_dice(screen, rect, cx, cy)
            elif area_type == "roulette":
                self._draw_roulette(screen, rect, cx, cy)
            elif area_type == "case":
                self._draw_case(screen, rect, cx, cy)
            elif area_type == "blackjack":
                self._draw_blackjack(screen, rect, cx, cy)
            elif area_type == "shop":
                self._draw_shop(screen, rect, cx, cy)
            elif area_type == "exit":
                self._draw_exit(screen, rect, cx, cy)

        self._draw_pillars(screen)

    # ── Zone icon drawing methods ─────────────────────────────────────────

    def _draw_slots(self, screen, rect, cx, cy):
        """Slot machine — three reels with symbols."""
        # Machine body
        pygame.draw.rect(screen, (140, 20, 20), rect, border_radius=8)
        pygame.draw.rect(screen, (200, 40, 40), rect, 3, border_radius=8)

        # Three reel windows
        reel_y = cy - 18
        for i, color in enumerate([(255, 215, 0), (255, 80, 80), (80, 200, 255)]):
            rx = rect.x + 14 + i * 26
            pygame.draw.rect(screen, (20, 20, 20),
                             (rx, reel_y, 20, 28), border_radius=3)
            pygame.draw.rect(screen, color,
                             (rx, reel_y, 20, 28), 2, border_radius=3)
            # Symbol inside reel
            pygame.draw.circle(screen, color, (rx + 10, reel_y + 14), 6)

        # Lever on the right side
        pygame.draw.rect(screen, (80, 80, 80),
                         (rect.right - 10, cy - 20, 6, 30), border_radius=3)
        pygame.draw.circle(screen, (200, 60, 60),
                           (rect.right - 7, cy - 22), 6)

        # Label
        font = pygame.font.SysFont(None, 20)
        screen.blit(font.render("SLOTS", True, (255, 215, 0)),
                    (cx - 20, rect.bottom - 18))

    def _draw_dice(self, screen, rect, cx, cy):
        """Dice table — two dice with dots."""
        # Table felt
        pygame.draw.rect(screen, (20, 80, 160), rect, border_radius=8)
        pygame.draw.rect(screen, (60, 120, 220), rect, 3, border_radius=8)

        # Draw one die — helper
        def draw_die(dx, dy, value, size=28):
            dr = pygame.Rect(dx - size // 2, dy - size // 2, size, size)
            pygame.draw.rect(screen, (240, 240, 240), dr, border_radius=5)
            pygame.draw.rect(screen, (180, 180, 180), dr, 2, border_radius=5)
            # Dot positions for value
            dots = {
                1: [(0, 0)],
                2: [(-6, -6), (6, 6)],
                5: [(-6, -6), (6, -6), (0, 0), (-6, 6), (6, 6)],
            }
            for ox, oy in dots.get(value, [(0, 0)]):
                pygame.draw.circle(screen, (20, 20, 20),
                                   (dx + ox, dy + oy), 3)

        draw_die(cx - 16, cy - 10, 5)
        draw_die(cx + 16, cy + 10, 2)

        font = pygame.font.SysFont(None, 20)
        screen.blit(font.render("DICE", True, (255, 255, 255)),
                    (cx - 15, rect.bottom - 18))

    def _draw_roulette(self, screen, rect, cx, cy):
        """Roulette wheel — spinning wheel with sectors."""
        # Table felt
        pygame.draw.rect(screen, (20, 100, 40), rect, border_radius=8)
        pygame.draw.rect(screen, (40, 160, 70), rect, 3, border_radius=8)

        # Wheel background
        pygame.draw.circle(screen, (30, 20, 10), (cx, cy - 5), 35)

        # Alternating red/black sectors (8 sectors)
        import math
        for i in range(8):
            angle = i * 45
            color = (180, 30, 30) if i % 2 == 0 else (20, 20, 20)
            start_rad = math.radians(angle)
            end_rad = math.radians(angle + 45)
            points = [(cx, cy - 5)]
            for a in range(angle, angle + 46, 5):
                r = math.radians(a)
                points.append((cx + math.cos(r) * 33,
                               cy - 5 + math.sin(r) * 33))
            if len(points) > 2:
                pygame.draw.polygon(screen, color, points)

        # Wheel rim
        pygame.draw.circle(screen, (180, 140, 60), (cx, cy - 5), 35, 3)
        # Center hub
        pygame.draw.circle(screen, (200, 160, 80), (cx, cy - 5), 8)
        pygame.draw.circle(screen, (120, 90, 30), (cx, cy - 5), 8, 2)

        # Ball
        pygame.draw.circle(screen, (240, 240, 240), (cx + 22, cy - 18), 4)

        font = pygame.font.SysFont(None, 20)
        screen.blit(font.render("ROULETTE", True, (255, 215, 0)),
                    (cx - 28, rect.bottom - 18))

    def _draw_case(self, screen, rect, cx, cy):
        """Case opening — a glowing mystery case."""
        # Background
        pygame.draw.rect(screen, (80, 30, 100), rect, border_radius=8)
        pygame.draw.rect(screen, (140, 60, 180), rect, 3, border_radius=8)

        # Case body
        case_rect = pygame.Rect(cx - 28, cy - 15, 56, 38)
        pygame.draw.rect(screen, (160, 120, 40), case_rect, border_radius=5)
        pygame.draw.rect(screen, (200, 160, 60), case_rect, 3, border_radius=5)

        # Case lid
        lid_rect = pygame.Rect(cx - 28, cy - 28, 56, 16)
        pygame.draw.rect(screen, (140, 100, 30), lid_rect, border_radius=5)
        pygame.draw.rect(screen, (200, 160, 60), lid_rect, 3, border_radius=5)

        # Latch
        pygame.draw.rect(screen, (220, 180, 80),
                         (cx - 6, cy - 17, 12, 6), border_radius=2)

        # Glow effect — question mark
        font = pygame.font.SysFont(None, 32)
        qs = font.render("?", True, (255, 220, 80))
        screen.blit(qs, qs.get_rect(center=(cx, cy + 5)))

        font2 = pygame.font.SysFont(None, 20)
        screen.blit(font2.render("CASES", True, (200, 150, 255)),
                    (cx - 18, rect.bottom - 18))

    def _draw_blackjack(self, screen, rect, cx, cy):
        """Blackjack table — two playing cards fanned out."""
        # Table felt
        pygame.draw.rect(screen, (20, 90, 40), rect, border_radius=8)
        pygame.draw.rect(screen, (40, 150, 70), rect, 3, border_radius=8)

        # Card drawing helper
        def draw_card(x, y, label, color=(240, 240, 240), angle=0):
            import math
            cw, ch = 30, 40
            surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, cw, ch), border_radius=4)
            pygame.draw.rect(surf, (180, 180, 180), (0, 0, cw, ch), 2, border_radius=4)
            f = pygame.font.SysFont(None, 22)
            ls = f.render(label, True, (200, 30, 30))
            surf.blit(ls, (3, 2))
            rotated = pygame.transform.rotate(surf, angle)
            screen.blit(rotated, rotated.get_rect(center=(x, y)))

        draw_card(cx - 14, cy - 5, "A", angle=15)
        draw_card(cx + 14, cy - 5, "K", angle=-15)
        draw_card(cx, cy + 5, "21", angle=0)

        font = pygame.font.SysFont(None, 20)
        screen.blit(font.render("BLACKJACK", True, (255, 215, 0)),
                    (cx - 30, rect.bottom - 18))

    def _draw_shop(self, screen, rect, cx, cy):
        """Shop — a dealer's counter with items."""
        # Counter background
        pygame.draw.rect(screen, (60, 35, 15), rect, border_radius=8)
        pygame.draw.rect(screen, (100, 65, 30), rect, 3, border_radius=8)

        # Counter top
        pygame.draw.rect(screen, (90, 55, 25),
                         (rect.x + 4, cy - 8, rect.width - 8, 20),
                         border_radius=4)

        # Items on counter — three colored gems
        for i, color in enumerate([(255, 80, 80), (80, 180, 255), (255, 215, 0)]):
            ix = rect.x + 18 + i * 26
            iy = cy - 4
            # Diamond shape
            pygame.draw.polygon(screen, color, [
                (ix, iy - 8), (ix + 8, iy),
                (ix, iy + 8), (ix - 8, iy)
            ])
            pygame.draw.polygon(screen, (255, 255, 255), [
                (ix, iy - 8), (ix + 8, iy),
                (ix, iy + 8), (ix - 8, iy)
            ], 1)

        # Price tag
        pygame.draw.rect(screen, (240, 220, 160),
                         (rect.x + 8, cy + 14, 30, 14), border_radius=2)
        font_s = pygame.font.SysFont(None, 16)
        screen.blit(font_s.render("$$$", True, (80, 40, 10)),
                    (rect.x + 10, cy + 16))

        font = pygame.font.SysFont(None, 20)
        screen.blit(font.render("SHOP", True, (255, 215, 0)),
                    (cx - 14, rect.bottom - 18))

    def _draw_exit(self, screen, rect, cx, cy):
        """
        Exit zone drawn as a floor rug with EXIT text.
        Blends into the floor rather than looking like a box.
        """
        # Rug base — deep green felt
        pygame.draw.rect(screen, (20, 80, 35), rect, border_radius=6)

        # Rug border — double gold stripe
        pygame.draw.rect(screen, (180, 140, 40), rect, 4, border_radius=6)
        inner = pygame.Rect(rect.x + 6, rect.y + 6,
                            rect.width - 12, rect.height - 12)
        pygame.draw.rect(screen, (140, 100, 25), inner, 2, border_radius=4)

        # Fringe lines on left and right edges — like a real rug
        for fy in range(rect.y + 8, rect.bottom - 8, 8):
            pygame.draw.line(screen, (160, 120, 30),
                             (rect.x + 2, fy), (rect.x + 6, fy), 2)
            pygame.draw.line(screen, (160, 120, 30),
                             (rect.right - 6, fy), (rect.right - 2, fy), 2)

        # EXIT text — large and centered on the rug
        font_big = pygame.font.SysFont(None, 36)
        font_sm = pygame.font.SysFont(None, 18)

        exit_surf = font_big.render("EXIT", True, (220, 180, 60))
        screen.blit(exit_surf, exit_surf.get_rect(center=(cx, cy - 8)))

        # Small arrow underneath
        arrow = font_sm.render("walk here to leave", True, (140, 110, 40))
        screen.blit(arrow, arrow.get_rect(center=(cx, cy + 14)))

    def _draw_floor(self, screen):
        """
        Dark wood plank floor with gold dividers.
        Matches the casino's dark/gold color scheme.
        """
        from constants import PLAY_HEIGHT

        # Base dark floor color
        screen.fill((28, 18, 10))

        # Wood plank rows — alternating dark brown shades
        plank_h = 36
        colors = [(38, 24, 12), (32, 20, 10), (42, 27, 13), (35, 22, 11)]
        for row in range(0, PLAY_HEIGHT, plank_h):
            color = colors[(row // plank_h) % len(colors)]
            pygame.draw.rect(screen, color, (0, row, 800, plank_h))
            # Gold divider line between planks
            pygame.draw.line(screen, (65, 48, 20),
                             (0, row), (800, row), 1)

        # Vertical plank seams — staggered like real wood
        for row in range(0, PLAY_HEIGHT, plank_h):
            offset = 120 if (row // plank_h) % 2 == 0 else 0
            for col in range(offset, 800, 200):
                pygame.draw.line(screen, (22, 14, 7),
                                 (col, row), (col, row + plank_h), 1)

        # Red carpet in the center walkway
        carpet_rect = pygame.Rect(175, 130, 450, 290)
        pygame.draw.rect(screen, (90, 12, 12), carpet_rect)
        pygame.draw.rect(screen, (160, 120, 30), carpet_rect, 3)

        # Carpet inner grid pattern
        for i in range(175, 625, 45):
            pygame.draw.line(screen, (105, 16, 16), (i, 130), (i, 420), 1)
        for j in range(130, 420, 45):
            pygame.draw.line(screen, (105, 16, 16), (175, j), (625, j), 1)

        # Gold corner ornaments
        for cx, cy in [(175, 130), (625, 130), (175, 420), (625, 420)]:
            pygame.draw.circle(screen, (180, 140, 35), (cx, cy), 8)
            pygame.draw.circle(screen, (120, 90, 20), (cx, cy), 8, 2)

    def _draw_pillars(self, screen):
        """6 pillars flanking the carpet — ornate with gold caps."""
        pillar_rects = [
            pygame.Rect(165, 140, 24, 24),
            pygame.Rect(611, 140, 24, 24),
            pygame.Rect(165, 280, 24, 24),
            pygame.Rect(611, 280, 24, 24),
            pygame.Rect(165, 390, 24, 24),
            pygame.Rect(611, 390, 24, 24),
        ]
        for rect in pillar_rects:
            # Pillar base — dark wood
            pygame.draw.rect(screen, (60, 40, 20), rect, border_radius=4)
            # Gold cap top
            pygame.draw.rect(screen, (180, 140, 40),
                             (rect.x, rect.y, rect.w, 6), border_radius=2)
            # Gold cap bottom
            pygame.draw.rect(screen, (180, 140, 40),
                             (rect.x, rect.bottom - 6, rect.w, 6), border_radius=2)
            # Outline
            pygame.draw.rect(screen, (140, 100, 40), rect, 2, border_radius=4)

    def _draw_ceiling_lights(self, screen):
        """
        Gold light dots along the top wall.
        Simple but makes the casino feel lit and alive.
        """
        light_positions = [80, 200, 340, 400, 460, 600, 720]
        for lx in light_positions:
            # Outer glow ring
            pygame.draw.circle(screen, (80, 70, 20), (lx, 12), 7)
            # Bright center
            pygame.draw.circle(screen, (255, 215, 0), (lx, 12), 4)
            # Highlight
            pygame.draw.circle(screen, (255, 245, 180), (lx, 11), 2)

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