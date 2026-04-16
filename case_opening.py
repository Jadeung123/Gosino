# case_opening.py
# Case opening minigame — bet-based, one fixed pool, 10 rarity tiers.
# Same betting UI pattern as dice/slots (quick bets + fine adjustment).

import pygame
import random

GOLD = (255, 215, 0)

# ------------------------------------------------------------------
# 10 rarity tiers — ordered worst → best
# ------------------------------------------------------------------
RARITIES = [
    {"name": "Scrap",      "color": (150, 130, 100),  "weight": 25,  "mult": 0.5},
    {"name": "Common",     "color": (180, 180, 180),  "weight": 25,  "mult": 0.75},
    {"name": "Industrial", "color": (100, 150, 255),  "weight": 16,  "mult": 1.5},
    {"name": "Mil-Spec",   "color": (160,  80, 255),  "weight": 13,  "mult": 3.0},
    {"name": "Classified", "color": (255,  80, 180),  "weight": 10,  "mult": 8.0},
    {"name": "Covert",     "color": (220,  50,  50),  "weight": 6,   "mult": 20.0},
    {"name": "Contraband", "color": (255, 215,   0),  "weight": 4,   "mult": 50.0},
    {"name": "Jackpot",    "color": (255, 255, 255),  "weight": 1,   "mult": 100.0},
]

ITEM_NAMES = {
    "Scrap":      ["Cash Bundle", "Silver Coin", "Money Clip",
                   "Poker Chip", "ATM Receipt", "Rolled Bills"],
    "Common":     ["Gold Coin", "Stacked Chips", "Casino Token",
                   "Thick Envelope", "Platinum Card", "Money Bag"],
    "Industrial": ["Gold Bar", "Diamond Ring", "Emerald Pendant",
                   "Ruby Bracelet", "Vault Key", "Briefcase"],
    "Mil-Spec":   ["Large Gold Bar", "Diamond Necklace", "Sapphire Crown",
                   "Solid Gold Watch", "Bearer Bond", "Gem Pouch"],
    "Classified": ["Suitcase of Cash", "Gold Bullion", "Platinum Bar",
                   "Diamond Tiara", "Ruby Necklace", "Vault Code"],
    "Covert":     ["The Black Briefcase", "Crown Jewels", "Gold Ingot Stack",
                   "Legendary Gem Set", "Offshore Account", "Bearer Bonds x10"],
    "Contraband": ["★ Infinite Black Card", "★ The Golden Gorilla",
                   "★ Crown Vault Key", "★ Diamond Skull"],
    "Jackpot":    ["★★ THE JACKPOT VAULT", "★★ GOLDEN THRONE",
                   "★★ INFINITE RICHES", "★★ THE MOTHER LODE"],
}

# ------------------------------------------------------------------
# Layout constants
# ------------------------------------------------------------------
ITEM_W     = 118
ITEM_H     = 240
REEL_Y     = 52
REEL_ITEMS = 48      # more items = longer satisfying scroll
RESULT_POS = 38      # index in reel where result lands

# Bottom section
_BOTTOM_Y  = REEL_Y + ITEM_H    # = 292

# Bet buttons — same as dice
_QUICK_BETS  = ["MIN", "HALF", "DOUBLE", "MAX"]
_BET_BUTTONS = [
    ("+1000", 1000), ("+100", 100), ("+50", 50),
    ("+10",   10),   ("+5",   5),   ("+1",  1),
    ("-1000",-1000), ("-100",-100), ("-50", -50),
    ("-10",  -10),   ("-5",  -5),   ("-1",  -1),
]


def _weighted_rarity():
    total = sum(r["weight"] for r in RARITIES)
    r     = random.uniform(0, total)
    acc   = 0
    for i, rarity in enumerate(RARITIES):
        acc += rarity["weight"]
        if r <= acc:
            return i
    return 0


def _make_reel(result_index):
    items           = [_weighted_rarity() for _ in range(REEL_ITEMS)]
    items[RESULT_POS] = result_index
    return items


class CaseOpening:

    def __init__(self):
        self.font_big = pygame.font.SysFont(None, 64)
        self.font_hd  = pygame.font.SysFont(None, 38)
        self.font     = pygame.font.SysFont(None, 30)
        self.font_sm  = pygame.font.SysFont(None, 24)

        self.bet            = 10
        self.session_profit = 0

        # Stored each draw call for hit-testing
        self._quick_rects = []
        self._adj_rects   = []

        self.reset()

    # ------------------------------------------------------------------

    def reset(self):
        self.phase        = "betting"
        self.reel         = []
        self.scroll_x     = 0.0
        self.scroll_speed = 0.0
        self.result_index = 0
        self.result_item  = ""
        self.spin_timer   = 0
        self.flash_timer  = 0
        self.flash_color  = (0, 0, 0)
        self.target_x     = 0.0
        self._shop_ref    = None
        self.typing_bet = False
        self.bet_input = ""

        # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, event, player, score_system, messages, shop=None):
        self._shop_ref = shop

        # Mouse — quick bet buttons
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.phase == "betting":
                if hasattr(self, '_bet_box') and self._bet_box.collidepoint(mx, my):
                    self.typing_bet = True
                    self.bet_input = ""
                    return
                for label, rect in self._quick_rects:
                    if rect.collidepoint(mx, my):
                        if label == "MIN":      self.bet = 1
                        elif label == "HALF":   self.bet = max(1, self.bet // 2)
                        elif label == "DOUBLE": self.bet = min(player.money, self.bet * 2)
                        elif label == "MAX":    self.bet = player.money
                for val, rect in self._adj_rects:
                    if rect.collidepoint(mx, my):
                        self.bet = max(1, min(player.money, self.bet + val))
            return

        if event.type != pygame.KEYDOWN:
            return

        if self.typing_bet:
            if event.key == pygame.K_RETURN:
                if self.bet_input.isdigit() and self.bet_input:
                    self.bet = max(1, min(player.money, int(self.bet_input)))
                self.typing_bet = False
                self.bet_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.bet_input = self.bet_input[:-1]
            elif event.unicode.isdigit():
                self.bet_input += event.unicode
            return

        if event.key == pygame.K_ESCAPE and self.phase != "spinning":
            return "exit"

        if self.phase == "betting" and event.key == pygame.K_SPACE:
            self._start_spin(player, messages, shop)

        if self.phase == "result" and event.key == pygame.K_SPACE:
            self.phase = "betting"

    # ------------------------------------------------------------------

    def _start_spin(self, player, messages, shop):
        if player.money < self.bet:
            messages.add_ui("Not enough money!")
            return

        player.money -= self.bet

        if shop and shop.is_active("guaranteed_win"):
            self.result_index = random.randint(6, len(RARITIES) - 1)
            shop.use("guaranteed_win")
            messages.add_ui("Lucky Charm triggered!")
        else:
            self.result_index = _weighted_rarity()

        rarity           = RARITIES[self.result_index]
        self.result_item = random.choice(ITEM_NAMES[rarity["name"]])
        self.reel        = _make_reel(self.result_index)

        SB            = 160
        MX            = SB + 10
        REEL_W        = 800 - MX - 10
        centre_offset = REEL_W // 2 - ITEM_W // 2
        self.target_x = RESULT_POS * ITEM_W - centre_offset

        self.scroll_x     = 0.0
        self.scroll_speed = 55.0
        self.spin_timer   = 0
        self.phase        = "spinning"
        return "played"

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, player, score_system, messages, shop=None):
        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.phase != "spinning":
            return

        self.spin_timer += 1
        remaining = self.target_x - self.scroll_x

        if remaining > 600:
            self.scroll_speed = 55.0
        elif remaining > 0:
            t                 = remaining / 600
            ease              = t * t * (3 - 2 * t)
            self.scroll_speed = max(0.8, 55.0 * ease)

        self.scroll_x += self.scroll_speed

        if self.scroll_x >= self.target_x:
            self.scroll_x = self.target_x
            self.phase = "result"
            result = self._resolve(player, score_system, messages, shop or self._shop_ref)
            if result == "result_ready":
                return "result_ready"

    # ------------------------------------------------------------------

    def _resolve(self, player, score_system, messages, shop=None):
        rarity = RARITIES[self.result_index]
        payout = int(self.bet * rarity["mult"])
        won    = rarity["mult"] > 1.0

        if rarity["mult"] == 0.0:
            # Total loss
            if shop and shop.is_active("insurance"):
                player.money += self.bet
                shop.use("insurance")
                messages.add_ui("Insurance — bet refunded!")
                self.flash_color = (80, 180, 255)
                self.flash_timer = 40
                return
            self.session_profit -= self.bet
            self.flash_color     = (180, 40, 40)
            self.flash_timer     = 40
            return

        # Partial or full return
        if shop and won and shop.hot_streak_count > 0:
            payout *= 2
            shop.consume_hot_streak()
            messages.add_ui(f"Hot Streak! x2  ({shop.hot_streak_count} left)")

        bonus = getattr(player, "multiplier_bonus", 0)
        if bonus > 0 and won:
            payout = int(payout * (1 + bonus))

        player.money        += payout
        if won:
            score_system.add_money_score(payout)
        self.session_profit += payout - self.bet

        self.flash_color = rarity["color"]
        self.flash_timer = 50

        if rarity["name"] == "Jackpot":
            messages.add_ui(f"★★ JACKPOT! +${payout}!")
        elif rarity["name"] == "Contraband":
            messages.add_ui(f"★ CONTRABAND! +${payout}!")
        return "result_ready"

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _quick_bet_rect(self, j, MX):
        return pygame.Rect(MX + 4 + j * 80, _BOTTOM_Y + 52, 72, 24)

    def _bet_btn_rect(self, i, MX):
        return pygame.Rect(MX + 4 + (i % 6) * 74, _BOTTOM_Y + 82 + (i // 6) * 34, 66, 28)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen, player, day_system):
        W, H = screen.get_size()
        self._quick_rects = []
        self._adj_rects   = []

        screen.fill((10, 10, 20))
        for i in range(-H, W + H, 36):
            pygame.draw.line(screen, (16, 16, 28), (i, 0), (i + H, H), 14)

        # ── Sidebar ───────────────────────────────────────────────────
        SB = 160
        pygame.draw.rect(screen, (20, 20, 34), (0, 0, SB, H))
        pygame.draw.line(screen, (48, 48, 74), (SB, 0), (SB, H), 2)

        def sb(label, value, vc, y):
            screen.blit(self.font_sm.render(label, True, (100,100,100)), (10, y))
            screen.blit(self.font.render(value,   True, vc),             (10, y+18))

        tl = day_system.get_time_seconds()
        sb("BALANCE",  f"${player.money}",  (185,255,185),  14)
        sb("DAY",      str(day_system.day), (255,255,255),   72)
        sb("TIME",     f"{tl}s",
           (255,90,90) if tl < 20 else (255,195,175),       124)
        sb("SESSION",  f"{self.session_profit:+}",
           (100,255,100) if self.session_profit >= 0 else (255,100,100), 176)

        MX  = SB + 10
        MCX = (MX + W) // 2

        # ── Top bar ───────────────────────────────────────────────────
        pygame.draw.rect(screen, (18, 18, 30), (MX, 0, W - MX, REEL_Y))
        pygame.draw.line(screen, (50, 50, 80), (MX, REEL_Y), (W, REEL_Y), 1)
        title = self.font_hd.render("CASE OPENING", True, GOLD)
        screen.blit(title, title.get_rect(center=(MCX, REEL_Y // 2)))

        # ── Reel ──────────────────────────────────────────────────────
        self._draw_reel(screen, MX, W)

        # ── Bottom section ────────────────────────────────────────────
        pygame.draw.line(screen, (38, 38, 58), (MX, _BOTTOM_Y + 4), (W - 10, _BOTTOM_Y + 4), 1)

        if self.phase == "betting":
            self._draw_betting(screen, player, MX, MCX, W)
            self._draw_odds(screen, MCX)
        elif self.phase == "spinning":
            hint = self.font_sm.render("Opening...", True, (120, 120, 120))
            screen.blit(hint, hint.get_rect(center=(MCX, _BOTTOM_Y + 40)))
        elif self.phase == "result":
            self._draw_result(screen, player, MX, MCX, W)

        # ── Flash ─────────────────────────────────────────────────────
        if self.flash_timer > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((*self.flash_color, int(60 * self.flash_timer / 50)))
            screen.blit(fl, (0, 0))

    # ------------------------------------------------------------------

    def _draw_reel(self, screen, MX, W):
        REEL_W   = W - MX - 10
        screen.set_clip(pygame.Rect(MX, REEL_Y, REEL_W, ITEM_H))
        centre_x = MX + REEL_W // 2
        centre_y = REEL_Y + ITEM_H // 2

        pygame.draw.rect(screen, (14, 14, 22), (MX, REEL_Y, REEL_W, ITEM_H))

        if not self.reel:
            ph = self.font.render("Place a bet and press SPACE", True, (60, 60, 75))
            screen.blit(ph, ph.get_rect(center=(centre_x, centre_y)))
            pygame.draw.rect(screen, (38, 38, 55), (MX, REEL_Y, REEL_W, ITEM_H), 2)
            screen.set_clip(None)
            return

        # Collect visible items, sort far→near so centre renders on top
        visible = []
        for i, rarity_idx in enumerate(self.reel):
            ix   = MX + i * ITEM_W - int(self.scroll_x)
            if ix + ITEM_W < MX - ITEM_W or ix > W + ITEM_W:
                continue
            dist = abs(ix + ITEM_W // 2 - centre_x)
            visible.append((dist, i, rarity_idx, ix))
        visible.sort(key=lambda x: -x[0])

        for dist, i, rarity_idx, ix in visible:
            rarity    = RARITIES[rarity_idx]
            max_dist  = REEL_W // 2
            t         = min(dist / max_dist, 1.0)
            scale     = 1.0 - t * 0.42
            is_centre = dist < ITEM_W // 2

            iw      = int(ITEM_W * scale)
            ih      = int(ITEM_H * scale)
            item_cx = ix + ITEM_W // 2
            item_y  = centre_y - ih // 2
            rect    = pygame.Rect(item_cx - iw // 2, item_y, iw, ih)

            fade    = 0.55 + 0.45 * scale
            r, g, b = rarity["color"]
            fill    = (int(r * fade * 0.35), int(g * fade * 0.35), int(b * fade * 0.35))
            pygame.draw.rect(screen, fill, rect, border_radius=8)

            inner_pad = max(4, int(8 * scale))
            inner     = pygame.Rect(rect.x + inner_pad, rect.y + inner_pad,
                                    rect.w - inner_pad * 2, rect.h - inner_pad * 2)
            if inner.w > 4 and inner.h > 4:
                inner_col = (int(r * fade * 0.6), int(g * fade * 0.6), int(b * fade * 0.6))
                pygame.draw.rect(screen, inner_col, inner, border_radius=5)

            border_alpha = 1.0 if is_centre else max(0.3, scale)
            border_col   = (int(r * border_alpha), int(g * border_alpha), int(b * border_alpha))
            pygame.draw.rect(screen, border_col, rect, 3 if is_centre else 1, border_radius=8)

            if dist < ITEM_W * 1.5:
                font_use = self.font_hd if is_centre else self.font_sm
                mult_txt = f"x{rarity['mult']}" if rarity["mult"] > 0 else "EMPTY"
                ms = font_use.render(mult_txt, True, (255,255,255) if is_centre else (160,160,160))
                screen.blit(ms, ms.get_rect(center=(item_cx, rect.centery)))

            stripe_h = max(3, int(10 * scale))
            stripe   = pygame.Rect(rect.x, rect.bottom - stripe_h, rect.w, stripe_h)
            pygame.draw.rect(screen, rarity["color"], stripe,
                             border_radius=4 if stripe_h > 4 else 0)

        # Rarity legend dots
        dot_y   = REEL_Y + ITEM_H - 16
        dot_r   = 5
        total_w = len(RARITIES) * (dot_r * 2 + 6)
        dot_x   = centre_x - total_w // 2
        for rarity in RARITIES:
            pygame.draw.circle(screen, rarity["color"], (dot_x + dot_r, dot_y), dot_r)
            dot_x += dot_r * 2 + 6

        # Edge fade
        fade_w = 90
        for px in range(fade_w):
            alpha     = int(240 * (1 - px / fade_w) ** 1.5)
            fade_surf = pygame.Surface((1, ITEM_H), pygame.SRCALPHA)
            fade_surf.fill((10, 10, 20, alpha))
            screen.blit(fade_surf, (MX + px,     REEL_Y))
            screen.blit(fade_surf, (W - 10 - px, REEL_Y))

        screen.set_clip(None)
        pygame.draw.rect(screen, (40, 40, 60), (MX, REEL_Y, REEL_W, ITEM_H), 1)

    # ------------------------------------------------------------------

    def _draw_betting(self, screen, player, MX, MCX, W):
        """Bet display + quick bets + adjustment buttons — same style as dice."""

        # Bet display box
        screen.blit(self.font_sm.render("BET:", True, (115,115,115)),
                    (MX + 4, _BOTTOM_Y + 14))
        bb = pygame.Rect(MX + 52, _BOTTOM_Y + 10, 100, 30)
        self._bet_box = bb  # ← store for hit-testing
        disp = (self.bet_input + "_") if self.typing_bet else f"${self.bet}"
        border_col = (150, 150, 255) if self.typing_bet else (78, 78, 108)
        pygame.draw.rect(screen, (28, 28, 46), bb, border_radius=4)
        pygame.draw.rect(screen, border_col, bb, 2, border_radius=4)
        bv = self.font.render(disp, True, GOLD)
        screen.blit(bv, bv.get_rect(center=bb.center))

        # Hint
        hint = self.font_sm.render("SPACE = Open", True, (100,100,100))
        screen.blit(hint, (MX + 168, _BOTTOM_Y + 16))

        # Quick bets
        screen.blit(self.font_sm.render("Quick:", True, (100,100,100)),
                    (MX + 4, _BOTTOM_Y + 50))
        mx_pos, my_pos = pygame.mouse.get_pos()
        for j, text in enumerate(_QUICK_BETS):
            r = self._quick_bet_rect(j, MX)
            self._quick_rects.append((text, r))
            hov = r.collidepoint(mx_pos, my_pos)
            pygame.draw.rect(screen, (50, 50, 72) if hov else (40, 40, 40), r, border_radius=3)
            pygame.draw.rect(screen, GOLD if hov else (90, 90, 90), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (255, 255, 255))
            screen.blit(ls, ls.get_rect(center=r.center))

        # Fine adjustment buttons
        for i, (text, val) in enumerate(_BET_BUTTONS):
            r  = self._bet_btn_rect(i, MX)
            self._adj_rects.append((val, r))
            bg = (48,28,28) if val < 0 else (28,48,28)
            pygame.draw.rect(screen, bg, r, border_radius=3)
            pygame.draw.rect(screen, (90,90,90), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=r.center))

    # ------------------------------------------------------------------

    def _draw_odds(self, screen, MCX):
        MX = 170  # left edge of main area
        oy = _BOTTOM_Y + 162

        pygame.draw.line(screen, (40, 40, 60), (MX, oy - 6), (MX + 440, oy - 6), 1)
        screen.blit(self.font_sm.render("DROP RATES", True, (70, 70, 70)), (MX, oy))
        oy += 20

        # Fixed column positions — aligned by content type
        COL_NAME = MX  # rarity name
        COL_PCT = MX + 120  # percentage
        COL_MULT = MX + 185  # multiplier
        COL_NAME2 = MX + 230  # col 2 name
        COL_PCT2 = MX + 350  # col 2 percentage
        COL_MULT2 = MX + 415  # col 2 multiplier
        ROW_H = 18

        for i, rarity in enumerate(RARITIES):
            mult_txt = f"x{rarity['mult']}"
            is_col2 = i >= 4
            row = i if i < 4 else i - 4

            col_name = COL_NAME2 if is_col2 else COL_NAME
            col_pct = COL_PCT2 if is_col2 else COL_PCT
            col_mult = COL_MULT2 if is_col2 else COL_MULT
            y = oy + row * ROW_H

            screen.blit(self.font_sm.render(rarity["name"], True, rarity["color"]), (col_name, y))
            screen.blit(self.font_sm.render(f"{rarity['weight']}%", True, (160, 160, 160)), (col_pct, y))
            screen.blit(self.font_sm.render(mult_txt, True, (220, 220, 100)), (col_mult, y))

    # ------------------------------------------------------------------

    def _draw_result(self, screen, player, MX, MCX, W):
        rarity = RARITIES[self.result_index]
        payout = int(self.bet * rarity["mult"])
        won    = rarity["mult"] > 1.0
        base_y = _BOTTOM_Y + 20

        # Rarity name
        rn = self.font_big.render(rarity["name"].upper(), True, rarity["color"])
        screen.blit(rn, rn.get_rect(center=(MCX, base_y + 36)))

        # Item name
        it = self.font_hd.render(self.result_item, True, (220, 220, 255))
        screen.blit(it, it.get_rect(center=(MCX, base_y + 80)))

        # Payout
        if rarity["mult"] == 0.0:
            ps = self.font_hd.render(f"-${self.bet}  (nothing)", True, (255, 90, 90))
        elif won:
            ps = self.font_hd.render(f"+${payout - self.bet}  (x{rarity['mult']})",
                                      True, (100, 255, 120))
        else:
            ps = self.font_hd.render(f"-${self.bet - payout}  (x{rarity['mult']})",
                                      True, (255, 180, 80))
        screen.blit(ps, ps.get_rect(center=(MCX, base_y + 116)))

        hint = self.font_sm.render("SPACE = Open again   |   ESC = Leave",
                                    True, (70, 70, 95))
        screen.blit(hint, hint.get_rect(center=(MCX, base_y + 150)))