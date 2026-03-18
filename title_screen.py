# title_screen.py
import pygame
import math
from constants import *


class TitleScreen:

    def __init__(self):
        self.font_title = pygame.font.SysFont(None, 110)
        self.font_sub   = pygame.font.SysFont(None, 38)
        self.font       = pygame.font.SysFont(None, 32)
        self.font_sm    = pygame.font.SysFont(None, 26)

        self.bg_offset  = 0
        self.glow_phase = 0
        self._current   = "title"

        self.fullscreen = DEFAULT_FULLSCREEN
        self.show_fps   = DEFAULT_SHOW_FPS

        # Title buttons — centred at x=400
        self.buttons = {
            "play":     pygame.Rect(325, 300, 150, 50),
            "settings": pygame.Rect(325, 368, 150, 50),
            "quit":     pygame.Rect(325, 436, 150, 50),
        }

        # Settings buttons
        self.settings_buttons = {
            "fullscreen": pygame.Rect(280, 250, 240, 48),
            "show_fps":   pygame.Rect(280, 316, 240, 48),
            "back":       pygame.Rect(325, 530, 150, 48),
        }

    # ------------------------------------------------------------------
    def handle_input(self, event, screen):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        mx, my = pygame.mouse.get_pos()

        if self._current == "title":
            if self.buttons["play"].collidepoint(mx, my):     return "play"
            if self.buttons["settings"].collidepoint(mx, my): self._current = "settings"
            if self.buttons["quit"].collidepoint(mx, my):     return "quit"

        elif self._current == "settings":
            if self.settings_buttons["fullscreen"].collidepoint(mx, my):
                self.fullscreen = not self.fullscreen
                self._apply_fullscreen(screen)
            if self.settings_buttons["show_fps"].collidepoint(mx, my):
                self.show_fps = not self.show_fps
            if self.settings_buttons["back"].collidepoint(mx, my):
                self._current = "title"
                return "back_to_game"

        return None

    def _apply_fullscreen(self, screen):
        if self.fullscreen:
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # ------------------------------------------------------------------
    def update(self):
        self.bg_offset  = (self.bg_offset + 0.4) % 40
        self.glow_phase += 0.04

    # ------------------------------------------------------------------
    def draw(self, screen):
        if self._current == "title":
            self._draw_title(screen)
        else:
            self._draw_settings(screen)

    def _draw_title(self, screen):
        screen.fill((10, 10, 20))

        # Animated diagonal stripes
        for i in range(-SCREEN_HEIGHT, SCREEN_WIDTH + SCREEN_HEIGHT, 40):
            x = i + self.bg_offset
            pygame.draw.line(screen, (18, 18, 32),
                             (int(x), 0), (int(x + SCREEN_HEIGHT), SCREEN_HEIGHT), 18)

        # Glowing title
        glow  = int(abs(math.sin(self.glow_phase)) * 55)
        gc    = (255, min(215 + glow, 255), 0)
        t1    = self.font_title.render("GOSINO", True, gc)
        screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, 200)))

        tag = self.font_sm.render(
            "Pay the debt. Beat the house. Don't get caught.",
            True, (155, 155, 155))
        screen.blit(tag, tag.get_rect(center=(SCREEN_WIDTH // 2, 268)))

        # Buttons — plain text labels, no unicode
        self._btn(screen, self.buttons["play"],     "PLAY",     (42, 140, 60))
        self._btn(screen, self.buttons["settings"], "SETTINGS", (42, 62,  140))
        self._btn(screen, self.buttons["quit"],     "QUIT",     (130, 36, 36))

        ver = self.font_sm.render("v1.0", True, (55, 55, 55))
        screen.blit(ver, (SCREEN_WIDTH - 44, SCREEN_HEIGHT - 24))

    def _draw_settings(self, screen):
        screen.fill((12, 12, 22))

        t = self.font_sub.render("SETTINGS", True, (255, 215, 0))
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 152)))
        pygame.draw.line(screen, (55, 55, 78), (200, 194), (600, 194), 2)

        fs_lbl  = "Fullscreen:   " + ("ON" if self.fullscreen else "OFF")
        fs_col  = (100, 255, 120) if self.fullscreen else (200, 78, 78)
        fps_lbl = "Show FPS:   "   + ("ON" if self.show_fps else "OFF")
        fps_col = (100, 255, 120) if self.show_fps else (200, 78, 78)

        self._btn(screen, self.settings_buttons["fullscreen"],
                  fs_lbl,  (38, 38, 58), text_color=fs_col)
        self._btn(screen, self.settings_buttons["show_fps"],
                  fps_lbl, (38, 38, 58), text_color=fps_col)

        # Keybinds — two columns
        keys_l = ["WASD  -  Move", "E  -  Interact", "ESC  -  Pause menu"]
        keys_r = ["SPACE  -  Action", "F1/F2/F3  -  Use item", "ENTER  -  Exit screen"]
        for i, k in enumerate(keys_l):
            screen.blit(self.font_sm.render(k, True, (110, 110, 110)), (220, 390 + i * 22))
        for i, k in enumerate(keys_r):
            screen.blit(self.font_sm.render(k, True, (110, 110, 110)), (430, 390 + i * 22))

        self._btn(screen, self.settings_buttons["back"], "BACK", (46, 46, 88))

    def _btn(self, screen, rect, text, bg, text_color=(255, 255, 255)):
        mx, my  = pygame.mouse.get_pos()
        hov     = rect.collidepoint(mx, my)
        color   = tuple(min(255, c + 28) for c in bg) if hov else bg
        border  = (255, 215, 0) if hov else (70, 70, 110)
        pygame.draw.rect(screen, color,  rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)
        s = self.font.render(text, True, text_color)
        screen.blit(s, s.get_rect(center=rect.center))