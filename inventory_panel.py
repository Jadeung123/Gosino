# inventory_panel.py
# A centered overlay panel that fades in/out on TAB.
# Shows consumable slots, permanent upgrades, and player stats.

import pygame

GOLD  = (255, 215, 0)
WHITE = (255, 255, 255)

FADE_SPEED = 18   # alpha units per frame — increase for faster fade


class InventoryPanel:

    PANEL_W = 480
    PANEL_H = 420

    def __init__(self):
        self.visible    = False   # is the panel open?
        self.alpha      = 0       # current opacity (0-255)
        self.target     = 0       # target opacity (0 or 255)

        self.font_hd    = pygame.font.SysFont(None, 38)
        self.font       = pygame.font.SysFont(None, 30)
        self.font_sm    = pygame.font.SysFont(None, 24)

    # ------------------------------------------------------------------

    def toggle(self):
        """Open if closed, close if open."""
        self.visible = not self.visible
        self.target  = 255 if self.visible else 0

    def close(self):
        """Force close — called by ESC."""
        self.visible = False
        self.target  = 0

    def is_open(self):
        return self.visible or self.alpha > 0   # still fading out counts

    # ------------------------------------------------------------------

    def update(self):
        """Smoothly move alpha toward target each frame."""
        if self.alpha < self.target:
            self.alpha = min(255, self.alpha + FADE_SPEED)
        elif self.alpha > self.target:
            self.alpha = max(0, self.alpha - FADE_SPEED)

    # ------------------------------------------------------------------

    def draw(self, screen, player, shop, upgrade_manager):
        if self.alpha <= 0:
            return   # fully transparent — skip drawing entirely

        SW, SH = screen.get_size()
        PW, PH = self.PANEL_W, self.PANEL_H
        px = (SW - PW) // 2
        py = (SH - PH) // 2

        # ── Dark background overlay ────────────────────────────────────
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(160, self.alpha)))
        screen.blit(overlay, (0, 0))

        # ── Panel surface (drawn at current alpha) ─────────────────────
        panel = pygame.Surface((PW, PH), pygame.SRCALPHA)
        panel.fill((18, 18, 30, min(240, self.alpha)))

        # Panel border
        border_surf = pygame.Surface((PW, PH), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (*GOLD, min(255, self.alpha)),
                         (0, 0, PW, PH), 2, border_radius=10)
        panel.blit(border_surf, (0, 0))

        screen.blit(panel, (px, py))

        # Skip drawing text content until mostly visible — avoids
        # rendering text at near-zero alpha which looks glitchy
        if self.alpha < 40:
            return

        # Compute text alpha separately so it fades in a bit after panel
        text_alpha = max(0, self.alpha - 40)

        def blit_faded(surf, pos):
            surf.set_alpha(text_alpha)
            screen.blit(surf, pos)

        # ── Title ──────────────────────────────────────────────────────
        title = self.font_hd.render("INVENTORY", True, GOLD)
        blit_faded(title, title.get_rect(center=(SW // 2, py + 28)))

        pygame.draw.line(screen, (*GOLD, text_alpha),
                         (px + 20, py + 52), (px + PW - 20, py + 52), 1)

        # ── SECTION 1: Consumable Slots ────────────────────────────────
        self._blit_faded_text(screen, self.font,
                              "CONSUMABLES  (F1 / F2 / F3)",
                              (px + 20, py + 62), (200, 200, 200), text_alpha)

        for i, slot in enumerate(shop.inventory):
            sx   = px + 20
            sy   = py + 88 + i * 54
            rect = pygame.Rect(sx, sy, PW - 40, 46)

            # Slot background
            bg_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg_surf.fill((30, 30, 50, text_alpha))
            screen.blit(bg_surf, rect.topleft)

            if slot:
                # Colored left accent bar
                bar = pygame.Surface((5, rect.h), pygame.SRCALPHA)
                bar.fill((*slot["color"], text_alpha))
                screen.blit(bar, rect.topleft)

                # Border
                pygame.draw.rect(screen, (*slot["color"], text_alpha),
                                 rect, 2, border_radius=4)

                self._blit_faded_text(screen, self.font,
                                      f"F{i+1}  {slot['name']}",
                                      (sx + 14, sy + 6),
                                      slot["color"], text_alpha)
                self._blit_faded_text(screen, self.font_sm,
                                      slot["desc"],
                                      (sx + 14, sy + 26),
                                      (160, 160, 160), text_alpha)
            else:
                pygame.draw.rect(screen, (50, 50, 70, text_alpha),
                                 rect, 1, border_radius=4)
                self._blit_faded_text(screen, self.font,
                                      f"F{i+1}  — empty —",
                                      (sx + 14, sy + 14),
                                      (70, 70, 90), text_alpha)

        # ── Divider ────────────────────────────────────────────────────
        div_y = py + 256
        pygame.draw.line(screen, (50, 50, 80),
                         (px + 20, div_y), (px + PW - 20, div_y), 1)

        # ── SECTION 2: Player Stats ────────────────────────────────────
        self._blit_faded_text(screen, self.font,
                              "PLAYER STATS",
                              (px + 20, div_y + 10), (200, 200, 200), text_alpha)

        stats = [
            ("Speed",   f"{player.speed:.1f}",   (185, 255, 185)),
            ("Luck",    str(player.luck),         (255, 220, 100)),
            ("Stealth", str(player.stealth),      (140, 200, 255)),
        ]
        for j, (label, value, color) in enumerate(stats):
            col_x = px + 20 + j * 150
            self._blit_faded_text(screen, self.font_sm,
                                  label, (col_x, div_y + 34),
                                  (130, 130, 130), text_alpha)
            self._blit_faded_text(screen, self.font,
                                  value, (col_x, div_y + 52),
                                  color, text_alpha)

        # ── Divider ────────────────────────────────────────────────────
        div2_y = div_y + 86
        pygame.draw.line(screen, (50, 50, 80),
                         (px + 20, div2_y), (px + PW - 20, div2_y), 1)

        # ── SECTION 3: Owned Permanent Upgrades ───────────────────────
        self._blit_faded_text(screen, self.font,
                              "UPGRADES",
                              (px + 20, div2_y + 10), (200, 200, 200), text_alpha)

        if upgrade_manager.levels:
            ux, uy = px + 20, div2_y + 34
            for name, level in upgrade_manager.levels.items():
                surf = self.font_sm.render(f"{name}  Lv{level}", True, (180, 255, 180))
                # Wrap to next line if overflowing panel width
                if ux + surf.get_width() > px + PW - 20:
                    ux  = px + 20
                    uy += 22
                surf.set_alpha(text_alpha)
                screen.blit(surf, (ux, uy))
                ux += surf.get_width() + 16
        else:
            self._blit_faded_text(screen, self.font_sm,
                                  "No upgrades yet",
                                  (px + 20, div2_y + 34),
                                  (70, 70, 90), text_alpha)

        # ── Close hint ─────────────────────────────────────────────────
        hint = self.font_sm.render("TAB / ESC to close", True, (80, 80, 80))
        blit_faded(hint, hint.get_rect(center=(SW // 2, py + PH - 16)))

    # ------------------------------------------------------------------

    def _blit_faded_text(self, screen, font, text, pos, color, alpha):
        surf = font.render(text, True, color)
        surf.set_alpha(alpha)
        screen.blit(surf, pos)