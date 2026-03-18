# roulette.py
import pygame
import random

RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
GOLD = (255, 215, 0)


class Roulette:

    def __init__(self):
        self.font_big = pygame.font.SysFont(None, 64)
        self.font     = pygame.font.SysFont(None, 32)
        self.font_sm  = pygame.font.SysFont(None, 26)

        self.quick_bets  = ["MIN", "HALF", "DOUBLE", "MAX"]
        self.bet_buttons = [
            ("+1000",1000),("+100",100),("+50",50),("+10",10),("+5",5),("+1",1),
            ("-1000",-1000),("-100",-100),("-50",-50),("-10",-10),("-5",-5),("-1",-1),
        ]
        self.reset()

    def _color_of(self, n):
        if n == 0:           return "green"
        if n in RED_NUMBERS: return "red"
        return "black"

    def _rgb(self, name):
        return {"red":(195,50,50),"black":(36,36,36),"green":(36,165,36)}.get(name,(80,80,80))

    def reset(self):
        self.phase          = "betting"
        self.bet            = 10
        self.bet_type       = None
        self.chosen_number  = None
        self.number_input   = ""
        self.typing_number  = False
        self.spin_timer     = 0
        self.spin_duration  = 90
        self.result_number  = None
        self.result_color   = None
        self.result_text    = ""
        self.result_win     = False
        self.flash_timer    = 0
        self.flash_color    = (0,0,0)
        self.session_profit = 0
        self._shop_ref      = None

    # Stored each draw call for hit-testing
    _quick_rects = []
    _adj_rects   = []

    def handle_input(self, event, player, score_system, messages):
        # ── Mouse: quick bet buttons ───────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.phase == "betting":
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

        # ── ESC exits from any phase ───────────────────────────────────
        if event.key == pygame.K_ESCAPE:
            return "exit"

        if self.typing_number:
            if event.key == pygame.K_RETURN:
                if self.number_input.isdigit():
                    n = int(self.number_input)
                    if 0 <= n <= 36:
                        self.chosen_number = n
                        self.bet_type      = "number"
                self.typing_number = False
                self.number_input  = ""
            elif event.key == pygame.K_BACKSPACE:
                self.number_input = self.number_input[:-1]
            elif event.unicode.isdigit() and len(self.number_input) < 2:
                self.number_input += event.unicode
            return

        if self.phase == "result":
            self.phase = "betting"
            return

        if self.phase == "betting":
            if event.key == pygame.K_r:
                self.bet_type = "red";   self.chosen_number = None
            elif event.key == pygame.K_b:
                self.bet_type = "black"; self.chosen_number = None
            elif event.key == pygame.K_n:
                self.typing_number = True; self.number_input = ""
            elif event.key == pygame.K_SPACE:
                result = self._start_spin(player, messages)
                if result == "started":
                    return "played"

    def _start_spin(self, player, messages):
        if self.bet_type is None:
            messages.add("Choose R / B / N first!", player.x, player.y)
            return
        if player.money < self.bet:
            messages.add_ui("Not enough money!")
            return
        player.money   -= self.bet
        self.phase      = "spinning"
        self.spin_timer = 0

        self.result_number = random.randint(0, 36)
        self.result_color  = self._color_of(self.result_number)

        shop = getattr(self, "_shop_ref", None)
        if shop and shop.is_active("guaranteed_win"):
            if self.bet_type == "red":
                self.result_number = 1; self.result_color = "red"
            elif self.bet_type == "black":
                self.result_number = 2; self.result_color = "black"
            elif self.bet_type == "number" and self.chosen_number is not None:
                self.result_number = self.chosen_number
                self.result_color  = self._color_of(self.chosen_number)
            shop.use("guaranteed_win")
            messages.add_ui("Lucky Charm triggered!")
        return "started"

    def _resolve(self, player, score_system):
        shop   = getattr(self, "_shop_ref", None)
        won    = False
        payout = 0

        if self.bet_type == "red"    and self.result_color == "red":
            payout = self.bet * 2;  won = True
        elif self.bet_type == "black" and self.result_color == "black":
            payout = self.bet * 2;  won = True
        elif (self.bet_type == "number" and self.chosen_number is not None
              and self.chosen_number == self.result_number):
            payout = self.bet * 35; won = True

        if not won:
            if shop and shop.is_active("insurance"):
                player.money += self.bet
                shop.use("insurance")
                self.result_text    = "INSURED - bet back"
                self.result_win     = True
                self.flash_color    = (80,180,255)
                self.flash_timer    = 30
                self.phase          = "result"
                return
            self.result_text     = f"LOST  -${self.bet}"
            self.result_win      = False
            self.session_profit -= self.bet
            self.flash_color     = (200,60,60)
        else:
            if shop and shop.hot_streak_count > 0:
                payout *= 2
                shop.consume_hot_streak()
            bonus = getattr(player, "multiplier_bonus", 0)
            if bonus > 0:
                payout = int(payout * (1 + bonus))
            player.money        += payout
            score_system.add_money_score(payout)
            self.result_text     = f"WIN  +${payout}"
            self.result_win      = True
            self.session_profit += payout - self.bet
            self.flash_color     = (60,220,100)

        self.flash_timer = 30
        self.phase       = "result"

    def update(self, player, score_system, shop=None):
        self._shop_ref = shop
        if self.flash_timer > 0: self.flash_timer -= 1
        if self.phase == "spinning":
            self.spin_timer += 1
            if self.spin_timer >= self.spin_duration:
                self._resolve(player, score_system)

    def draw(self, screen, player, day_system):
        W, H = screen.get_size()
        screen.fill((14, 14, 24))

        SB = 185
        pygame.draw.rect(screen, (20,20,34), (0,0,SB,H))
        pygame.draw.line(screen, (48,48,74), (SB,0), (SB,H), 2)

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

        ts = self.font_big.render("ROULETTE", True, GOLD)
        screen.blit(ts, ts.get_rect(center=(MCX, 36)))

        # Wheel
        WCX, WCY, WR = MCX, 170, 74
        if self.phase == "spinning":
            cyc = (self.spin_timer // 6) % 3
            wc  = [(190,50,50),(36,36,36),(36,165,36)][cyc]
            pygame.draw.circle(screen, wc, (WCX,WCY), WR)
            sp = self.font.render("Spinning...", True, (255,255,255))
            screen.blit(sp, sp.get_rect(center=(WCX,WCY)))
        elif self.phase == "result":
            pygame.draw.circle(screen, self._rgb(self.result_color), (WCX,WCY), WR)
            ns = self.font_big.render(str(self.result_number), True, (255,255,255))
            screen.blit(ns, ns.get_rect(center=(WCX,WCY)))
        else:
            pygame.draw.circle(screen, (46,46,46), (WCX,WCY), WR)
            ph = self.font_sm.render("No bet placed", True, (120,120,120))
            screen.blit(ph, ph.get_rect(center=(WCX,WCY)))
        pygame.draw.circle(screen, (170,170,170), (WCX,WCY), WR, 3)

        # Bet type buttons
        BTN_Y = 268
        defs  = [("R - Red","red",MX+4), ("B - Black","black",MX+118), ("N - Number","number",MX+238)]
        for label, btype, bx in defs:
            br  = pygame.Rect(bx, BTN_Y, 106, 34)
            bg  = {"red":(140,34,34),"black":(34,34,34),"number":(26,82,26)}[btype]
            bdr = GOLD if self.bet_type == btype else (58,58,58)
            pygame.draw.rect(screen, bg,  br, border_radius=5)
            pygame.draw.rect(screen, bdr, br, 2, border_radius=5)
            ls  = self.font_sm.render(label, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=br.center))

        # ── Bet display ───────────────────────────────────────────────
        L1 = BTN_Y + 48
        pygame.draw.line(screen, (38,38,58), (MX, L1-6), (MR, L1-6), 1)
        screen.blit(self.font_sm.render("BET:", True, (115,115,115)), (MX+4, L1+5))
        bb = pygame.Rect(MX+56, L1, 92, 30)
        pygame.draw.rect(screen, (28,28,46), bb, border_radius=4)
        pygame.draw.rect(screen, (78,78,108), bb, 2, border_radius=4)
        bv = self.font.render(f"${self.bet}", True, GOLD)
        screen.blit(bv, bv.get_rect(center=bb.center))

        # Active bet summary
        if self.bet_type == "number" and self.chosen_number is not None:
            summary = f"Betting: number {self.chosen_number}  (pays x35)"
        elif self.bet_type:
            summary = f"Betting: {self.bet_type.upper()}  (pays x2)"
        else:
            summary = "No bet selected — press R, B or N"
        screen.blit(self.font_sm.render(summary, True,
                    GOLD if self.bet_type else (100,100,100)), (MX+4, L1+38))

        if self.typing_number:
            tp = self.font_sm.render(f"Type 0-36 then ENTER:  {self.number_input}_",
                                      True, (255,200,100))
            screen.blit(tp, (MX+4, L1+60))

        # ── Result ────────────────────────────────────────────────────
        L2 = L1 + 76
        pygame.draw.line(screen, (38,38,58), (MX, L2-6), (MR, L2-6), 1)

        if self.phase == "result":
            rc = (100,255,120) if self.result_win else (255,90,90)
            rs = self.font_big.render(self.result_text, True, rc)
            max_w = MR - MX - 8
            if rs.get_width() > max_w:
                rs = pygame.transform.scale(
                    rs, (max_w, int(rs.get_height() * max_w / rs.get_width())))
            screen.blit(rs, rs.get_rect(center=(MCX, L2+22)))
        elif self.phase == "betting":
            sp = self.font_sm.render("SPACE = Spin", True, (135,135,135))
            screen.blit(sp, sp.get_rect(center=(MCX, L2+14)))

        # ── Quick bets (dice-style) ───────────────────────────────────
        pygame.draw.line(screen, (38,38,58), (MX, 408), (MR, 408), 1)
        screen.blit(self.font_sm.render("Quick:", True, (100,100,100)), (MX+4, 418))
        self._quick_rects = []
        for j, text in enumerate(self.quick_bets):
            r = pygame.Rect(MX + 4 + j * 80, 438, 72, 24)
            self._quick_rects.append((text, r))
            pygame.draw.rect(screen, (40,40,40), r, border_radius=3)
            pygame.draw.rect(screen, (90,90,90), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=r.center))

        self._adj_rects = []
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
            fl.fill((*self.flash_color, int(55 * self.flash_timer / 30)))
            screen.blit(fl, (0,0))