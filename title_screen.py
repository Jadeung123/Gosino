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

        self.fullscreen    = DEFAULT_FULLSCREEN
        self.show_fps      = DEFAULT_SHOW_FPS

        # Sound settings — two independent channels
        self.sound_enabled = True
        self.sfx_volume    = 0.8   # controls all sound effects
        self.music_volume  = 0.5   # controls background music

        # Slider drag state
        self.dragging_sfx   = False
        self.dragging_music = False

        # Slider track rects — defined once, used in draw + input
        self.sfx_slider_rect = pygame.Rect(380, 330, 200, 8)
        self.music_slider_rect = pygame.Rect(380, 375, 200, 8)

        # Title buttons
        self.buttons = {
            "play": pygame.Rect(325, 300, 150, 50),
            "settings": pygame.Rect(325, 368, 150, 50),
            "stats": pygame.Rect(325, 436, 150, 50),
            "quit": pygame.Rect(325, 504, 150, 50),
        }

        # Settings buttons — only toggles, sliders handled separately
        self.settings_buttons = {
            "fullscreen": pygame.Rect(200, 170, 180, 40),
            "show_fps": pygame.Rect(420, 170, 180, 40),
            "sound": pygame.Rect(300, 270, 200, 40),
            "back": pygame.Rect(325, 540, 150, 48),
        }
        self._sound_manager = None

    # ------------------------------------------------------------------

    def handle_input(self, event, screen):
        if self._current == "title":
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                return None
            mx, my = pygame.mouse.get_pos()
            if self.buttons["play"].collidepoint(mx, my):     return "play"
            if self.buttons["settings"].collidepoint(mx, my): self._current = "settings"
            if self.buttons["stats"].collidepoint(mx, my):    return "stats"
            if self.buttons["quit"].collidepoint(mx, my):     return "quit"

        elif self._current == "settings":
            mx, my = pygame.mouse.get_pos()

            # ── Slider drag start ──────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                # SFX slider
                sfx_handle = pygame.Rect(
                    self.sfx_slider_rect.x + int(self.sfx_volume * self.sfx_slider_rect.width) - 10,
                    self.sfx_slider_rect.y - 8, 20, 26
                )
                if sfx_handle.collidepoint(mx, my) or self.sfx_slider_rect.collidepoint(mx, my):
                    self.dragging_sfx = True
                    self._update_sfx_from_mouse(mx)

                # Music slider
                music_handle = pygame.Rect(
                    self.music_slider_rect.x + int(self.music_volume * self.music_slider_rect.width) - 10,
                    self.music_slider_rect.y - 8, 20, 26
                )
                if music_handle.collidepoint(mx, my) or self.music_slider_rect.collidepoint(mx, my):
                    self.dragging_music = True
                    self._update_music_from_mouse(mx)

                # Toggle buttons
                if self.settings_buttons["fullscreen"].collidepoint(mx, my):
                    self.fullscreen = not self.fullscreen
                    self._apply_fullscreen(screen)
                if self.settings_buttons["show_fps"].collidepoint(mx, my):
                    self.show_fps = not self.show_fps
                if self.settings_buttons["sound"].collidepoint(mx, my):
                    self.sound_enabled = not self.sound_enabled
                    if self._sound_manager:
                        self._sound_manager.enabled = self.sound_enabled
                        self._sound_manager.update_music_volume()
                if self.settings_buttons["back"].collidepoint(mx, my):
                    self._current = "title"
                    return "back_to_game"

            # ── Slider drag move ───────────────────────────────────────
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_sfx:
                    self._update_sfx_from_mouse(mx)
                    if self._sound_manager:
                        self._sound_manager.master_volume = self.sfx_volume
                if self.dragging_music:
                    self._update_music_from_mouse(mx)
                    if self._sound_manager:
                        self._sound_manager.music_volume = self.music_volume
                        self._sound_manager.update_music_volume()
            # ── Slider drag release ────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_sfx   = False
                self.dragging_music = False

        return None

    # ------------------------------------------------------------------

    def _update_sfx_from_mouse(self, mx):
        ratio = (mx - self.sfx_slider_rect.x) / self.sfx_slider_rect.width
        self.sfx_volume = max(0.0, min(1.0, round(ratio, 2)))

    def _update_music_from_mouse(self, mx):
        ratio = (mx - self.music_slider_rect.x) / self.music_slider_rect.width
        self.music_volume = max(0.0, min(1.0, round(ratio, 2)))

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
        for i in range(-SCREEN_HEIGHT, SCREEN_WIDTH + SCREEN_HEIGHT, 40):
            x = i + self.bg_offset
            pygame.draw.line(screen, (18, 18, 32),
                             (int(x), 0), (int(x + SCREEN_HEIGHT), SCREEN_HEIGHT), 18)

        glow = int(abs(math.sin(self.glow_phase)) * 55)
        gc   = (255, min(215 + glow, 255), 0)
        t1   = self.font_title.render("GOSINO", True, gc)
        screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, 200)))

        tag = self.font_sm.render(
            "Pay the debt. Beat the house. Don't get caught.",
            True, (155, 155, 155))
        screen.blit(tag, tag.get_rect(center=(SCREEN_WIDTH // 2, 268)))

        self._btn(screen, self.buttons["play"], "PLAY", (42, 140, 60))
        self._btn(screen, self.buttons["settings"], "SETTINGS", (42, 62, 140))
        self._btn(screen, self.buttons["stats"], "STATISTICS", (20, 90, 90))
        self._btn(screen, self.buttons["quit"], "QUIT", (130, 36, 36))

        ver = self.font_sm.render("v1.0", True, (55, 55, 55))
        screen.blit(ver, (SCREEN_WIDTH - 44, SCREEN_HEIGHT - 24))

    def _draw_settings(self, screen):
        screen.fill((12, 12, 22))

        # Title
        t = self.font_sub.render("SETTINGS", True, (255, 215, 0))
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 45)))
        pygame.draw.line(screen, (55, 55, 78), (150, 70), (650, 70), 1)

        # ── SECTION 1: Display ────────────────────────────────────────
        sec1 = self.font_sm.render("DISPLAY", True, (100, 100, 140))
        screen.blit(sec1, sec1.get_rect(center=(SCREEN_WIDTH // 2, 120)))
        pygame.draw.line(screen, (40, 40, 60), (200, 135), (600, 135), 1)

        fs_lbl = "Fullscreen:  " + ("ON" if self.fullscreen else "OFF")
        fs_col = (100, 255, 120) if self.fullscreen else (200, 78, 78)
        fps_lbl = "Show FPS:  " + ("ON" if self.show_fps else "OFF")
        fps_col = (100, 255, 120) if self.show_fps else (200, 78, 78)
        self._btn(screen, self.settings_buttons["fullscreen"],
                  fs_lbl, (38, 38, 58), text_color=fs_col)
        self._btn(screen, self.settings_buttons["show_fps"],
                  fps_lbl, (38, 38, 58), text_color=fps_col)

        # ── SECTION 2: Sound ──────────────────────────────────────────
        sec2 = self.font_sm.render("SOUND", True, (100, 100, 140))
        screen.blit(sec2, sec2.get_rect(center=(SCREEN_WIDTH // 2, 238)))
        pygame.draw.line(screen, (40, 40, 60), (200, 253), (600, 253), 1)

        # Sound ON/OFF toggle — centered on its own row
        snd_lbl = "Sound:   " + ("ON" if self.sound_enabled else "OFF")
        snd_col = (100, 255, 120) if self.sound_enabled else (200, 78, 78)
        self._btn(screen, self.settings_buttons["sound"],
                  snd_lbl, (38, 38, 58), text_color=snd_col)

        # SFX row — label on left, slider on right
        screen.blit(self.font_sm.render("SFX:", True, (160, 160, 160)),
                    (200, self.sfx_slider_rect.y - 4))
        self._draw_slider(screen, self.sfx_slider_rect,
                          self.sfx_volume, "", self.sfx_slider_rect.y)

        # Music row — label on left, slider on right
        screen.blit(self.font_sm.render("Music:", True, (160, 160, 160)),
                    (200, self.music_slider_rect.y - 4))
        self._draw_slider(screen, self.music_slider_rect,
                          self.music_volume, "", self.music_slider_rect.y)

        # ── SECTION 3: Controls ───────────────────────────────────────
        sec3 = self.font_sm.render("CONTROLS", True, (100, 100, 140))
        screen.blit(sec3, sec3.get_rect(center=(SCREEN_WIDTH // 2, 406)))
        pygame.draw.line(screen, (40, 40, 60), (200, 421), (600, 421), 1)

        keys_l = ["WASD  -  Move", "E  -  Interact", "ESC  -  Pause"]
        keys_r = ["SPACE  -  Action", "F1/F2/F3  -  Use item", "ENTER  -  Exit screen"]
        for i, k in enumerate(keys_l):
            screen.blit(self.font_sm.render(k, True, (110, 110, 110)),
                        (220, 430 + i * 22))
        for i, k in enumerate(keys_r):
            screen.blit(self.font_sm.render(k, True, (110, 110, 110)),
                        (430, 430 + i * 22))

        # Divider above back button
        pygame.draw.line(screen, (40, 40, 60), (200, 508), (600, 508), 1)
        self._btn(screen, self.settings_buttons["back"], "BACK", (46, 46, 88))

    # ------------------------------------------------------------------

    def _draw_slider(self, screen, rect, value, label, label_y):
        """Draws slider track, fill, handle, and percentage."""
        # Percentage label to the right of the handle end
        pct = int(value * 100)
        screen.blit(
            self.font_sm.render(f"{pct}%", True, (255, 215, 0)),
            (rect.right + 14, rect.y - 4)
        )

        # Track background
        pygame.draw.rect(screen, (40, 40, 60), rect, border_radius=5)

        # Filled portion
        fill_w = int(value * rect.width)
        if fill_w > 0:
            pygame.draw.rect(screen, (100, 180, 255),
                             (rect.x, rect.y, fill_w, rect.height),
                             border_radius=5)

        # Handle
        handle_x = rect.x + fill_w
        pygame.draw.circle(screen, (255, 255, 255), (handle_x, rect.centery), 9)
        pygame.draw.circle(screen, (100, 180, 255), (handle_x, rect.centery), 9, 2)

    # ------------------------------------------------------------------

    def _btn(self, screen, rect, text, bg, text_color=(255, 255, 255)):
        mx, my = pygame.mouse.get_pos()
        hov    = rect.collidepoint(mx, my)
        color  = tuple(min(255, c + 28) for c in bg) if hov else bg
        border = (255, 215, 0) if hov else (70, 70, 110)
        pygame.draw.rect(screen, color,  rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)
        s = self.font.render(text, True, text_color)
        screen.blit(s, s.get_rect(center=rect.center))