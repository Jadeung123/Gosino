# slot_machine.py
import pygame
import random

SYMBOLS     = ["CHR", "GEM", "777", "LMN", "STR", "BEL"]
SYMBOL_COLS = [
    (220,  60,  60),
    ( 80, 180, 255),
    (255, 215,   0),
    (220, 220,  60),
    (255, 180,  60),
    (180, 140, 255),
]
GOLD = (255, 215, 0)


class SlotMachine:

    def __init__(self):
        self.font_reel = pygame.font.SysFont(None, 58)
        self.font_big  = pygame.font.SysFont(None, 64)
        self.font      = pygame.font.SysFont(None, 32)
        self.font_sm   = pygame.font.SysFont(None, 26)

        self.quick_bets  = ["MIN", "HALF", "DOUBLE", "MAX"]
        self.bet_buttons = [
            ("+1000",1000),("+100",100),("+50",50),("+10",10),("+5",5),("+1",1),
            ("-1000",-1000),("-100",-100),("-50",-50),("-10",-10),("-5",-5),("-1",-1),
        ]
        self.reset()

    def reset(self):
        self.phase          = "betting"
        self.spin_timer     = 0
        self.reel_offsets   = [1.0, 3.0, 5.0]
        self.reel_speeds    = [0.30, 0.23, 0.17]
        self.reel_stopped   = [False, False, False]
        self.stop_frames    = [38, 54, 70]
        self.final_symbols  = [1, 3, 5]
        self.display_reels  = [1, 3, 5]
        self.bet            = 10
        self.outcome        = "lose"
        self.payout         = 0
        self.result_text    = ""
        self.result_win     = False
        self.flash_timer    = 0
        self.flash_color    = (0, 0, 0)
        self.session_profit = 0
        self._shop          = None
        self.typing_bet = False
        self.bet_input = ""

        # KEY FIX: outcome decided BEFORE animation starts
    def _pick_outcome(self, player, shop):
        threshold = getattr(player, "slot_threshold", 5)
        spin      = random.randint(1, 10)

        if shop and shop.is_active("guaranteed_win"):
            spin = 10
            shop.use("guaranteed_win")

        if spin >= 8:
            sym    = random.randint(0, len(SYMBOLS) - 1)
            final  = [sym, sym, sym]
            return "jackpot", final, self.bet * 3

        if spin >= threshold:
            sym   = random.randint(0, len(SYMBOLS) - 1)
            other = (sym + 1 + random.randint(0, len(SYMBOLS) - 2)) % len(SYMBOLS)
            final = [sym, sym, sym]
            final[random.randint(0, 2)] = other
            return "win", final, self.bet * 2

        pool = list(range(len(SYMBOLS)))
        random.shuffle(pool)
        final = pool[:3]
        while len(set(final)) < 3:
            random.shuffle(pool)
            final = pool[:3]
        return "lose", final, 0

    # Stored each draw call so handle_input can hit-test them
    _quick_rects = []
    _adj_rects   = []

    def handle_input(self, event, player, score_system, messages, shop=None):
        # ── Mouse: quick bet buttons ───────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.phase == "betting":
                if hasattr(self, '_bet_box') and self._bet_box.collidepoint(mx, my):
                    self.typing_bet = True
                    self.bet_input = ""
                    return
                for label, rect in self._quick_rects:
                    if rect.collidepoint(mx, my):
                        if label == "MIN":    self.bet = 1
                        elif label == "HALF": self.bet = max(1, self.bet // 2)
                        elif label == "2X":   self.bet = min(player.money, self.bet * 2)
                        elif label == "MAX":  self.bet = player.money
                for delta, rect in self._adj_rects:
                    if rect.collidepoint(mx, my):
                        self.bet = max(1, min(player.money, self.bet + delta))
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

        # ── ESC exits from any phase ───────────────────────────────────
        if event.key == pygame.K_ESCAPE:
            return "exit"

        if event.key == pygame.K_SPACE and self.phase == "result":
            self.phase = "betting"
            return

        if event.key == pygame.K_SPACE and self.phase == "betting":
            if player.money < self.bet:
                messages.add_ui("Not enough money!")
                return
            player.money -= self.bet
            self.outcome, self.final_symbols, self.payout = self._pick_outcome(player, shop)
            self._shop        = shop
            self.reel_offsets = [float(random.randint(0, len(SYMBOLS)-1)),
                                  float(random.randint(0, len(SYMBOLS)-1)),
                                  float(random.randint(0, len(SYMBOLS)-1))]
            self.display_reels = [int(o) % len(SYMBOLS) for o in self.reel_offsets]
            self.reel_stopped  = [False, False, False]
            self.spin_timer    = 0
            self.phase         = "spinning"
            return "played"

    def update(self, player, score_system, messages, shop=None):
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.phase != "spinning":
            return

        self.spin_timer += 1
        for i in range(3):
            if self.spin_timer >= self.stop_frames[i]:
                self.reel_stopped[i]  = True
                self.display_reels[i] = self.final_symbols[i]
            else:
                self.reel_offsets[i]  += self.reel_speeds[i]
                self.display_reels[i]  = int(self.reel_offsets[i]) % len(SYMBOLS)

        if all(self.reel_stopped):
            self._resolve(player, score_system, messages, self._shop or shop)
            self.phase = "result"

    def _resolve(self, player, score_system, messages, shop=None):
        payout = self.payout
        if payout == 0:
            if shop and shop.is_active("insurance"):
                player.money += self.bet
                shop.use("insurance")
                messages.add_ui("Insurance - bet refunded!")
                self.result_text = "INSURED"
                self.result_win  = True
                self.flash_color = (80, 180, 255)
                self.flash_timer = 35
                return
            self.session_profit -= self.bet
            self.result_text     = f"No win  -${self.bet}"
            self.result_win      = False
            self.flash_color     = (200, 60, 60)
            self.flash_timer     = 35
            return

        if shop and shop.hot_streak_count > 0:
            payout *= 2
            shop.consume_hot_streak()
            messages.add_ui(f"Hot Streak! x2  ({shop.hot_streak_count} left)")

        bonus = getattr(player, "multiplier_bonus", 0)
        if bonus > 0:
            payout += int(self.bet * bonus)

        player.money        += payout
        score_system.add_money_score(payout)
        self.session_profit += payout - self.bet
        prefix               = "JACKPOT!!" if self.outcome == "jackpot" else "WIN"
        self.result_text     = f"{prefix}  +${payout}"
        self.result_win      = True
        self.flash_color     = (60, 220, 100)
        self.flash_timer     = 35

    def draw(self, screen, player, day_system):
        W, H = screen.get_size()
        self._quick_rects = []   # reset each frame
        self._adj_rects   = []
        screen.fill((14, 14, 24))

        SB = 185
        pygame.draw.rect(screen, (20, 20, 34), (0, 0, SB, H))
        pygame.draw.line(screen, (48, 48, 74), (SB, 0), (SB, H), 2)

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

        MX  = SB + 14
        MR  = W - 10
        MCX = (MX + MR) // 2

        ts = self.font_big.render("SLOTS", True, GOLD)
        screen.blit(ts, ts.get_rect(center=(MCX, 36)))

        BOX_X = MX
        BOX_Y = 68
        BOX_W = MR - MX
        BOX_H = 165
        pygame.draw.rect(screen, (22,22,22), (BOX_X,BOX_Y,BOX_W,BOX_H), border_radius=10)
        pygame.draw.rect(screen, GOLD,       (BOX_X,BOX_Y,BOX_W,BOX_H), 3, border_radius=10)

        reel_xs  = [BOX_X + BOX_W*1//6, BOX_X + BOX_W*3//6, BOX_X + BOX_W*5//6]
        REEL_CY  = BOX_Y + BOX_H // 2

        for i, rx in enumerate(reel_xs):
            si  = self.display_reels[i]
            col = SYMBOL_COLS[si]

            if self.phase == "spinning" and not self.reel_stopped[i]:
                for delta, a in [(-1, 35), (1, 35)]:
                    gi  = (si + delta) % len(SYMBOLS)
                    tmp = self.font_reel.render(SYMBOLS[gi], True, SYMBOL_COLS[gi])
                    s   = pygame.Surface(tmp.get_size(), pygame.SRCALPHA)
                    s.blit(tmp, (0,0))
                    s.set_alpha(a)
                    screen.blit(s, s.get_rect(center=(rx, REEL_CY + delta*52)))

            ms = self.font_reel.render(SYMBOLS[si], True, col)
            screen.blit(ms, ms.get_rect(center=(rx, REEL_CY)))

            if self.reel_stopped[i]:
                pygame.draw.rect(screen, GOLD,
                                 (rx-44, BOX_Y+BOX_H-7, 88, 4), border_radius=2)

        pygame.draw.line(screen, GOLD, (BOX_X+4, REEL_CY), (MR-4, REEL_CY), 1)

        # ── Bet display ───────────────────────────────────────────────
        L1 = BOX_Y + BOX_H + 16
        pygame.draw.line(screen, (38,38,58), (MX, L1-8), (MR, L1-8), 1)
        screen.blit(self.font_sm.render("BET:", True, (115,115,115)), (MX+4, L1+6))
        bb = pygame.Rect(MX + 56, L1, 92, 30)
        self._bet_box = bb
        disp = (self.bet_input + "_") if self.typing_bet else f"${self.bet}"
        border_col = (150, 150, 255) if self.typing_bet else (78, 78, 108)
        pygame.draw.rect(screen, (28, 28, 46), bb, border_radius=4)
        pygame.draw.rect(screen, border_col, bb, 2, border_radius=4)
        bv = self.font.render(disp, True, GOLD)
        screen.blit(bv, bv.get_rect(center=bb.center))

        # ── Result row ────────────────────────────────────────────────
        L2 = L1 + 44
        pygame.draw.line(screen, (38,38,58), (MX, L2-6), (MR, L2-6), 1)

        if self.phase == "spinning":
            sp = self.font.render("Spinning...", True, (200,200,200))
            screen.blit(sp, sp.get_rect(center=(MCX, L2+18)))
        elif self.phase == "result":
            rc = (100,255,120) if self.result_win else (255,90,90)
            rs = self.font_big.render(self.result_text, True, rc)
            max_w = MR - MX - 8
            if rs.get_width() > max_w:
                rs = pygame.transform.scale(
                    rs, (max_w, int(rs.get_height() * max_w / rs.get_width())))
            screen.blit(rs, rs.get_rect(center=(MCX, L2+18)))
        else:
            sp = self.font.render("SPACE = Spin", True, (168,168,168))
            screen.blit(sp, sp.get_rect(center=(MCX, L2+18)))

        # ── Quick bets (dice-style) ───────────────────────────────────
        pygame.draw.line(screen, (38,38,58), (MX, 408), (MR, 408), 1)
        screen.blit(self.font_sm.render("Quick:", True, (100,100,100)), (MX+4, 418))
        for j, text in enumerate(self.quick_bets):
            r = pygame.Rect(MX + 4 + j * 80, 438, 72, 24)
            self._quick_rects.append((text, r))
            pygame.draw.rect(screen, (40,40,40), r, border_radius=3)
            pygame.draw.rect(screen, (90,90,90), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=r.center))

        for i, (text, val) in enumerate(self.bet_buttons):
            r  = pygame.Rect(MX + 4 + (i % 6) * 74, 468 + (i // 6) * 34, 66, 28)
            self._adj_rects.append((val, r))
            bg = (48,28,28) if val < 0 else (28,48,28)
            pygame.draw.rect(screen, bg, r, border_radius=3)
            pygame.draw.rect(screen, (90,90,90), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=r.center))

        if self.flash_timer > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((*self.flash_color, int(55 * self.flash_timer / 35)))
            screen.blit(fl, (0,0))