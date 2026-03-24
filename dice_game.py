# dice_game.py
import pygame
import random

GOLD = (255, 215, 0)


class DiceGame:

    # ── Layout constants ─────────────────────────────────────────────
    SB = 185          # sidebar width (same as slots/roulette)

    # Slider lives in the main area; set as class-level defaults,
    # recalculated in __init__ relative to SB.
    SLIDER_Y = 340
    SLIDER_H = 14

    def __init__(self):
        self.bet          = 10
        self.bet_input    = ""
        self.typing_bet   = False
        self.target       = 50
        self.mode         = "over"
        self.rolling      = False
        self.roll_timer   = 0
        self.roll_duration = 60
        self.display_number = 0
        self.final_roll   = 0
        self.dragging     = False
        self.counter_number = 0
        self.roll_history = []
        self.flash_timer  = 0
        self.flash_color  = None
        self.glow_phase   = 0
        self.bar_glow_timer = 0
        self.session_profit = 0
        self._shop_ref    = None

        self.font_big = pygame.font.SysFont(None, 72)
        self.font     = pygame.font.SysFont(None, 32)
        self.font_sm  = pygame.font.SysFont(None, 26)

        # Slider x/width depend on screen; will be set properly in draw()
        # using MX and MR, but we need defaults for input hit-testing too.
        # We update them each draw call via _update_slider_geom().
        self._slider_x = self.SB + 14
        self._slider_w = 800 - self._slider_x - 10

        # Arrow tracks the animated number
        self._arrow_x = self._slider_x

        self.bet_buttons = [
            ("+1000",1000),("+100",100),("+50",50),("+10",10),("+5",5),("+1",1),
            ("-1000",-1000),("-100",-100),("-50",-50),("-10",-10),("-5",-5),("-1",-1),
        ]
        self.quick_bets    = ["MIN", "HALF", "DOUBLE", "MAX"]
        self.quick_targets = [10, 25, 50, 75, 90]

    def _update_slider_geom(self, mx_val, mr_val):
        self._slider_x = mx_val
        self._slider_w = mr_val - mx_val

    # ------------------------------------------------------------------
    def reset(self):
        self.rolling        = False
        self.roll_timer     = 0
        self.display_number = 0
        self.counter_number = 0
        self.final_roll     = 0
        self.dragging       = False
        self.typing_bet     = False
        self.bet_input      = ""
        self._arrow_x       = self._slider_x

    # ------------------------------------------------------------------
    def get_win_chance(self):
        if self.mode == "over":  return max(100 - self.target, 1)
        return max(self.target, 1)

    def get_multiplier(self):
        return round(99 / self.get_win_chance(), 2)

    # ------------------------------------------------------------------
    def start_roll(self, player, shop=None):
        if self.bet <= 0:       self.bet = 1
        self.bet = max(1, min(self.bet, player.money))
        if player.money < self.bet: return False

        player.money      -= self.bet
        self.rolling       = True
        self.roll_timer    = 0
        self.display_number = 0
        self.counter_number = 0
        self.bar_glow_timer = 0
        self.final_roll    = random.randint(0, 100)
        self._shop         = shop

        if shop and shop.is_active("loaded_dice"):
            self.final_roll = random.randint(71, 100)
            shop.use("loaded_dice")

        if shop and shop.is_active("guaranteed_win"):
            if self.mode == "over":
                self.final_roll = self.target + 1 if self.target < 99 else 99
            else:
                self.final_roll = self.target - 1 if self.target > 1  else 1
            shop.use("guaranteed_win")

        return True

    def resolve_roll(self, player, score_system, messages):
        shop = getattr(self, "_shop", None)
        self.roll_history.insert(0, self.final_roll)
        if len(self.roll_history) > 8:
            self.roll_history.pop()
        self.bar_glow_timer = 120

        win = ((self.mode == "over"  and self.final_roll > self.target) or
               (self.mode == "under" and self.final_roll < self.target))

        if not win:
            if shop and shop.is_active("insurance"):
                player.money += self.bet
                shop.use("insurance")
                messages.add_ui("Insurance used — bet refunded!")
                self.flash_color = (80, 180, 255)
                self.flash_timer = 25
                return
            self.session_profit -= self.bet
            messages.add("Lost", player.x, player.y)
            self.flash_color = (200, 60, 60)
            self.flash_timer = 25
            return

        winnings = int(self.bet * self.get_multiplier())

        if shop and shop.hot_streak_count > 0:
            winnings *= 2
            shop.consume_hot_streak()
            messages.add_ui(f"Hot Streak! x2  ({shop.hot_streak_count} left)")

        bonus = getattr(player, "multiplier_bonus", 0)
        if bonus > 0:
            winnings = int(winnings * (1 + bonus))

        player.money        += winnings
        score_system.add_money_score(winnings)
        self.session_profit += winnings - self.bet
        messages.add(f"WIN ${winnings}", player.x, player.y)
        self.flash_color = (60, 220, 100)
        self.flash_timer = 25

    # ------------------------------------------------------------------
    def handle_input(self, event, player, score_system, messages):
        shop = getattr(self, "_shop_ref", None)
        MX   = self.SB + 14
        MR   = 790

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Slider bar
            bar = pygame.Rect(self._slider_x, self.SLIDER_Y, self._slider_w, self.SLIDER_H)
            if bar.collidepoint(mx, my):
                self.dragging = True

            # Bet box  (positioned in main area)
            bet_box = self._bet_box_rect(MX)
            if bet_box.collidepoint(mx, my):
                self.typing_bet = True
                self.bet_input  = ""

            # Bet buttons
            for i, (_, val) in enumerate(self.bet_buttons):
                if self._bet_btn_rect(i, MX).collidepoint(mx, my):
                    self.bet = max(1, min(player.money, self.bet + val))

            # Quick bets
            for j, text in enumerate(self.quick_bets):
                if self._quick_bet_rect(j, MX).collidepoint(mx, my):
                    if text == "MIN":    self.bet = 1
                    elif text == "HALF": self.bet = max(1, self.bet // 2)
                    elif text == "DOUBLE": self.bet = min(player.money, self.bet * 2)
                    elif text == "MAX":  self.bet = player.money

            # Target quick-set buttons
            for k, val in enumerate(self.quick_targets):
                if self._target_btn_rect(k, MX).collidepoint(mx, my):
                    self.target = val

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            pos = (event.pos[0] - self._slider_x) / max(self._slider_w, 1)
            self.target = int(max(0, min(1, pos)) * 100)

        if event.type == pygame.KEYDOWN:
            if self.typing_bet:
                if event.key == pygame.K_RETURN:
                    if self.bet_input:
                        self.bet = max(1, min(player.money, int(self.bet_input)))
                    self.typing_bet = False
                elif event.key == pygame.K_BACKSPACE:
                    self.bet_input = self.bet_input[:-1]
                elif event.unicode.isdigit():
                    self.bet_input += event.unicode
                return

            if event.key == pygame.K_m and not self.rolling:
                self.mode = "under" if self.mode == "over" else "over"
            if event.key == pygame.K_SPACE and not self.rolling:
                if not self.start_roll(player, shop):
                    messages.add_ui("Not enough money!")
            if event.key == pygame.K_ESCAPE and not self.rolling:
                return "exit"

    # ── Rect helpers (all relative to MX) ────────────────────────────
    def _bet_box_rect(self, MX):
        return pygame.Rect(MX + 80, 76, 100, 30)

    def _bet_btn_rect(self, i, MX):
        # 6 per row, 2 rows
        bx = MX + 4 + (i % 6) * 74
        by = 468 + (i // 6) * 34
        return pygame.Rect(bx, by, 66, 28)

    def _quick_bet_rect(self, j, MX):
        return pygame.Rect(MX + 4 + j * 80, 438, 72, 24)

    def _target_btn_rect(self, k, MX):
        return pygame.Rect(MX + 4 + k * 62, 296, 54, 24)

    # ------------------------------------------------------------------
    def update(self, player, score_system, messages):
        if self.bar_glow_timer > 0: self.bar_glow_timer -= 1
        if self.flash_timer > 0:    self.flash_timer -= 1
        if self.rolling:            self.glow_phase += 0.25
        if not self.rolling:        return

        self.roll_timer += 1
        if self.roll_timer < self.roll_duration:
            prog  = self.roll_timer / self.roll_duration
            ease  = prog * prog * (3 - 2 * prog)
            tgt   = int(self.final_roll * ease)
            if self.counter_number < tgt:
                self.counter_number += max(1, (tgt - self.counter_number) // 3)
            self.display_number = self.counter_number
            self._arrow_x = self._slider_x + (self.display_number / 100) * self._slider_w
        else:
            self.rolling        = False
            self.display_number = self.final_roll
            self._arrow_x       = self._slider_x + (self.final_roll / 100) * self._slider_w
            self.resolve_roll(player, score_system, messages)

    # ------------------------------------------------------------------
    def draw(self, screen, player, day_system):
        W, H = screen.get_size()
        MX   = self.SB + 14
        MR   = W - 10
        MCX  = (MX + MR) // 2
        self._update_slider_geom(MX, MR)

        # ── Background with diagonal stripes ─────────────────────────
        screen.fill((10, 10, 20))
        for i in range(-H, W + H, 36):
            pygame.draw.line(screen, (16, 16, 28), (i, 0), (i + H, H), 14)

        # ── SIDEBAR ───────────────────────────────────────────────────
        pygame.draw.rect(screen, (20, 20, 34), (0, 0, self.SB, H))
        pygame.draw.line(screen, (48, 48, 74), (self.SB, 0), (self.SB, H), 2)

        def sb(label, value, vc, y):
            screen.blit(self.font_sm.render(label, True, (100,100,100)), (12, y))
            screen.blit(self.font.render(value,   True, vc),            (12, y+20))

        tl = day_system.get_time_seconds()
        sb("BALANCE",  f"${player.money}",  (185,255,185),  18)
        sb("DAY",      str(day_system.day), (255,255,255),   86)
        sb("TIME",     f"{tl}s",
           (255,90,90) if tl<20 else (255,195,175),         148)
        sb("SESSION",  f"{self.session_profit:+}",
           (100,255,100) if self.session_profit>=0 else (255,100,100), 214)

        # ── TOP BAR with title ────────────────────────────────────────
        pygame.draw.rect(screen, (18, 18, 30), (MX, 0, W - MX, 52))
        pygame.draw.line(screen, (50, 50, 80), (MX, 52), (W, 52), 1)
        ts = self.font_big.render("DICE", True, GOLD)
        screen.blit(ts, ts.get_rect(center=(MCX, 26)))

        # Mode label
        ml = self.font_sm.render(f"Mode: {self.mode.upper()}  (M to toggle)",
                                  True, (120, 120, 140))
        screen.blit(ml, (MX + 4, 56))

        # Bet + win stats row
        screen.blit(self.font_sm.render("Bet:", True, (115,115,115)), (MX+4, 80))
        bb = self._bet_box_rect(MX)
        pygame.draw.rect(screen, (28,28,46), bb, border_radius=4)
        pygame.draw.rect(screen, (78,78,108), bb, 2, border_radius=4)
        disp = self.bet_input if self.typing_bet else str(self.bet)
        bv = self.font.render(disp, True, GOLD)
        screen.blit(bv, bv.get_rect(center=bb.center))
        screen.blit(self.font_sm.render("Click to type", True, (60,60,70)),
                    (MX + 190, 80))

        # Win stats
        chance = self.get_win_chance()
        mult   = self.get_multiplier()
        screen.blit(self.font_sm.render(f"Win chance: {chance}%", True, (100,255,150)),
                    (MX + 310, 72))
        screen.blit(self.font_sm.render(f"Multiplier:  {mult}x",  True, (100,220,130)),
                    (MX + 310, 92))

        # ── DIVIDER ───────────────────────────────────────────────────
        pygame.draw.line(screen, (38,38,58), (MX, 114), (MR, 114), 1)

        # ── ROW 2: roll number | history ──────────────────────────────
        rn = self.font_big.render(str(self.display_number), True, GOLD)
        screen.blit(rn, rn.get_rect(center=(MX + 60, 148)))

        screen.blit(self.font_sm.render("History:", True, (80,80,90)), (MX+130, 126))
        hx = MX + 218
        for roll in self.roll_history:
            r = pygame.Rect(hx, 122, 36, 26)
            pygame.draw.rect(screen, (22,22,36), r, border_radius=3)
            pygame.draw.rect(screen, (55,55,80), r, 1, border_radius=3)
            ns = self.font_sm.render(str(roll), True, (200,200,220))
            screen.blit(ns, ns.get_rect(center=r.center))
            hx += 40

        # ── DIVIDER ───────────────────────────────────────────────────
        pygame.draw.line(screen, (38,38,58), (MX, 172), (MR, 172), 1)

        # ── ROW 3: target label + quick-set buttons ───────────────────
        screen.blit(self.font_sm.render("Target:", True, (110,110,110)), (MX+4, 188))
        tn = self.font.render(str(self.target), True, GOLD)
        screen.blit(tn, (MX+76, 184))

        screen.blit(self.font_sm.render("Quick:", True, (100,100,100)), (MX+145, 188))
        for k, val in enumerate(self.quick_targets):
            r   = self._target_btn_rect(k, MX)
            sel = (self.target == val)
            pygame.draw.rect(screen, (42,42,42), r, border_radius=3)
            pygame.draw.rect(screen, GOLD if sel else (65,65,65), r, 2 if sel else 1, border_radius=3)
            ls = self.font_sm.render(str(val), True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=r.center))

        # ── ROW 4: probability bar ────────────────────────────────────
        pygame.draw.line(screen, (38,38,58), (MX, 220), (MR, 220), 1)
        self._draw_prob_bar(screen, MX, MR)

        # Arrow (above slider)
        ax = int(self._arrow_x)
        pygame.draw.polygon(screen, GOLD,
                             [(ax, self.SLIDER_Y - 14),
                              (ax-7, self.SLIDER_Y - 2),
                              (ax+7, self.SLIDER_Y - 2)])

        # ── DIVIDER ───────────────────────────────────────────────────
        pygame.draw.line(screen, (38,38,58), (MX, 366), (MR, 366), 1)

        # ── ROW 5: quick bets + bet buttons ──────────────────────────
        screen.blit(self.font_sm.render("Quick:", True, (100,100,100)), (MX+4, 418))
        for j, text in enumerate(self.quick_bets):
            r = self._quick_bet_rect(j, MX)
            pygame.draw.rect(screen, (40,40,40), r, border_radius=3)
            pygame.draw.rect(screen, (90,90,90), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=r.center))

        for i, (text, val) in enumerate(self.bet_buttons):
            r  = self._bet_btn_rect(i, MX)
            bg = (48,28,28) if val < 0 else (28,48,28)
            pygame.draw.rect(screen, bg, r, border_radius=3)
            pygame.draw.rect(screen, (90,90,90), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=r.center))

        # ── CONTROLS HINT ─────────────────────────────────────────────
        hint = "Rolling..." if self.rolling else "SPACE = Roll  |  M = Mode"
        hs   = self.font_sm.render(hint, True, (80, 80, 95))
        screen.blit(hs, hs.get_rect(center=(MCX, H - 12)))

        # Flash overlay
        if self.flash_timer > 0 and self.flash_color:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            alpha = int(60 * self.flash_timer / 25)
            fl.fill((*self.flash_color, alpha))
            screen.blit(fl, (0, 0))

    # ------------------------------------------------------------------
    def _draw_prob_bar(self, screen, MX, MR):
        sx, sy = self._slider_x, self.SLIDER_Y
        sw     = self._slider_w

        if self.bar_glow_timer > 0:
            fade  = self.bar_glow_timer / 120
            green = (40, min(255, 160 + int(80 * fade)), 70)
        else:
            green = (40, 160, 70)

        if self.mode == "over":
            lw = int((self.target / 100) * sw)
            pygame.draw.rect(screen, (165,55,55), (sx,        sy, lw + 1,    self.SLIDER_H))
            pygame.draw.rect(screen, green,       (sx + lw,   sy, sw - lw,   self.SLIDER_H))
        else:
            ww = int((self.target / 100) * sw)
            pygame.draw.rect(screen, green,       (sx,        sy, ww + 1,    self.SLIDER_H))
            pygame.draw.rect(screen, (165,55,55), (sx + ww,   sy, sw - ww,   self.SLIDER_H))

        # Target knob
        kx = int(sx + (self.target / 100) * sw)
        pygame.draw.circle(screen, GOLD, (kx, sy + self.SLIDER_H // 2), 9)

        # Result dot
        if not self.rolling and self.final_roll != 0:
            rx = int(sx + (self.final_roll / 100) * sw)
            pygame.draw.circle(screen, (255,255,255), (rx, sy + self.SLIDER_H // 2), 6)

        # Axis labels
        screen.blit(self.font_sm.render("0",   True, (90,90,90)), (sx - 8,      sy + 18))
        screen.blit(self.font_sm.render("100", True, (90,90,90)), (sx + sw - 12, sy + 18))
        screen.blit(self.font_sm.render(str(self.target), True, GOLD),
                    (kx - 10, sy - 20))