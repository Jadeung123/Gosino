# day_transition.py
# Shows a summary screen between days.
# Displays what happened and what's coming next.

import pygame
import math

GOLD  = (255, 215, 0)
WHITE = (255, 255, 255)


class DayTransition:

    def __init__(self):
        self.font_big = pygame.font.SysFont(None, 80)
        self.font_hd  = pygame.font.SysFont(None, 44)
        self.font     = pygame.font.SysFont(None, 32)
        self.font_sm  = pygame.font.SysFont(None, 26)

        self.active       = False
        self.timer        = 0          # counts up each frame
        self.glow_phase   = 0.0

        # Data filled in by main.py when a day ends
        self.day_completed  = 1
        self.money_before   = 0
        self.money_after    = 0
        self.debt_paid      = 0
        self.next_debt      = 0

    # ------------------------------------------------------------------

    def start(self, day_completed, money_before, money_after,
              debt_paid, next_debt):
        """
        Call this when the player pays their debt and exits.
        Stores the day summary data and activates the screen.
        """
        self.day_completed = day_completed
        self.money_before  = money_before
        self.money_after   = money_after
        self.debt_paid     = debt_paid
        self.next_debt     = next_debt
        self.timer         = 0
        self.glow_phase    = 0.0
        self.active        = True

    def stop(self):
        self.active = False
        self.timer  = 0

    # ------------------------------------------------------------------

    def update(self):
        if not self.active:
            return
        self.timer      += 1
        self.glow_phase += 0.05

    # ------------------------------------------------------------------

    def handle_input(self, event):
        """
        Returns "continue" when the player is ready to move on.
        We wait at least 90 frames so they can't accidentally skip it.
        """
        if not self.active:
            return None

        if self.timer < 90:
            return None   # too early — ignore input

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                return "continue"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return "continue"

        return None

    # ------------------------------------------------------------------

    def draw(self, screen):
        if not self.active:
            return

        W, H = screen.get_size()

        # Dark background
        screen.fill((8, 8, 15))

        # Animated diagonal stripes — same style as other screens
        for i in range(-H, W + H, 40):
            pygame.draw.line(screen, (14, 14, 26),
                             (i, 0), (i + H, H), 16)

        # Glowing "DAY COMPLETE" title
        glow  = int(abs(math.sin(self.glow_phase)) * 40)
        color = (255, min(215 + glow, 255), 0)
        title = self.font_big.render("DAY COMPLETE", True, color)
        screen.blit(title, title.get_rect(center=(W // 2, 100)))

        pygame.draw.line(screen, (80, 70, 20),
                         (150, 155), (650, 155), 1)

        # Day badge
        day_surf = self.font_hd.render(
            f"Day {self.day_completed} cleared", True, (200, 200, 200)
        )
        screen.blit(day_surf, day_surf.get_rect(center=(W // 2, 190)))

        # Summary rows — only show after a short delay for drama
        rows = [
            ("Money before",  f"${self.money_before}",  (200, 200, 200)),
            ("Debt paid",     f"-${self.debt_paid}",    (255, 110, 110)),
            ("Money after",   f"${self.money_after}",   (120, 255, 140)),
            ("Next day debt", f"${self.next_debt}",     (255, 180,  80)),
        ]

        for i, (label, value, color) in enumerate(rows):
            # Stagger each row's appearance by 20 frames
            if self.timer < 20 + i * 20:
                continue

            y = 250 + i * 52

            # Row background
            row_rect = pygame.Rect(200, y - 8, 400, 40)
            pygame.draw.rect(screen, (18, 18, 30), row_rect, border_radius=6)
            pygame.draw.rect(screen, (40, 40, 60), row_rect, 1, border_radius=6)

            screen.blit(
                self.font.render(label, True, (130, 130, 130)),
                (220, y)
            )
            val_surf = self.font.render(value, True, color)
            screen.blit(val_surf, (row_rect.right - val_surf.get_width() - 20, y))

        # Continue prompt — only show after all rows have appeared
        if self.timer >= 90:
            pulse = int(abs(math.sin(self.glow_phase * 1.5)) * 80)
            hint_color = (100 + pulse, 100 + pulse, 100 + pulse)
            hint = self.font_sm.render(
                "SPACE / CLICK to continue", True, hint_color
            )
            screen.blit(hint, hint.get_rect(center=(W // 2, 530)))