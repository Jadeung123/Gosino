# roulette.py
# Full roulette wheel with spinning animation, rolling ball, and number grid betting table.

import pygame
import random
import math

RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
GOLD = (255, 215, 0)

# Roulette wheel number order (standard European layout)
WHEEL_ORDER = [
    0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,
    24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26
]


class Roulette:

    def __init__(self):
        self.font_big  = pygame.font.SysFont(None, 64)
        self.font_hd   = pygame.font.SysFont(None, 36)
        self.font      = pygame.font.SysFont(None, 28)
        self.font_sm   = pygame.font.SysFont(None, 22)
        self.font_tiny = pygame.font.SysFont(None, 17)

        self.quick_bets  = ["MIN", "HALF", "DOUBLE", "MAX"]
        self.bet_buttons = [
            ("+1000",1000),("+100",100),("+50",50),("+10",10),("+5",5),("+1",1),
            ("-1000",-1000),("-100",-100),("-50",-50),("-10",-10),("-5",-5),("-1",-1),
        ]
        self._quick_rects = []
        self._adj_rects   = []
        self._num_rects   = {}   # number → Rect for grid click detection

        # Wheel animation state
        self.wheel_angle  = 0.0    # current rotation of wheel (degrees)
        self.wheel_speed  = 0.0    # degrees per frame
        self.ball_angle   = 0.0    # ball orbit angle (degrees)
        self.ball_speed   = 0.0    # ball orbit speed
        self.ball_radius  = 0.0    # distance from wheel centre
        self.ball_landed  = False

        self.reset()

    # ------------------------------------------------------------------

    def _color_of(self, n):
        if n == 0:           return "green"
        if n in RED_NUMBERS: return "red"
        return "black"

    def _rgb(self, name):
        return {"red":(180,40,40),"black":(24,24,24),"green":(30,140,30)}.get(name,(80,80,80))

    def reset(self):
        self.phase          = "betting"
        self.bet            = 10
        self.bet_type       = None
        self.chosen_number  = None
        self.number_input   = ""
        self.typing_number  = False
        self.spin_timer     = 0
        self.spin_duration  = 150    # longer for satisfying animation
        self.result_number  = None
        self.result_color   = None
        self.result_text    = ""
        self.result_win     = False
        self.flash_timer    = 0
        self.flash_color    = (0,0,0)
        self.session_profit = 0
        self._shop_ref      = None
        self.typing_bet = False
        self.bet_input = ""

        # Reset wheel to idle
        self.wheel_speed  = 0.5    # slow idle rotation
        self.ball_speed   = 0.0
        self.ball_radius  = 0.0
        self.ball_landed  = False

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, event, player, score_system, messages):
        # Mouse — number grid + quick bets
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.phase == "betting":
                if hasattr(self, '_bet_box_rect') and self._bet_box_rect.collidepoint(mx, my):
                    self.typing_bet = True
                    self.bet_input = ""
                    return
                # Number grid
                for num, rect in self._num_rects.items():
                    if rect.collidepoint(mx, my):
                        self.chosen_number = num
                        self.bet_type      = "number"
                        return
                # Quick bets
                if hasattr(self, '_color_rects'):
                    for btype, rect in self._color_rects.items():
                        if rect.collidepoint(mx, my):
                            self.bet_type = btype
                            self.chosen_number = None
                            return
                for label, rect in self._quick_rects:
                    if rect.collidepoint(mx, my):
                        if label == "MIN":    self.bet = 1
                        elif label == "HALF": self.bet = max(1, self.bet // 2)
                        elif label == "DOUBLE": self.bet = min(player.money, self.bet * 2)
                        elif label == "MAX":  self.bet = player.money
                        return
                for delta, rect in self._adj_rects:
                    if rect.collidepoint(mx, my):
                        self.bet = max(1, min(player.money, self.bet + delta))
                        return
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
            self.wheel_speed = 0.5
            self.ball_speed  = 0.0
            self.ball_radius = 0.0
            self.ball_landed = False
            return

        if self.phase == "betting":
            if event.key == pygame.K_r:
                self.bet_type = "red";   self.chosen_number = None
            elif event.key == pygame.K_b:
                self.bet_type = "black"; self.chosen_number = None
            elif event.key == pygame.K_SPACE:
                result = self._start_spin(player, messages)
                if result == "started":
                    return "played"

    # ------------------------------------------------------------------

    def _start_spin(self, player, messages):
        if self.bet_type is None:
            messages.add_ui("Choose a bet first!")
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
                self.result_number = 1;  self.result_color = "red"
            elif self.bet_type == "black":
                self.result_number = 2;  self.result_color = "black"
            elif self.bet_type == "number" and self.chosen_number is not None:
                self.result_number = self.chosen_number
                self.result_color  = self._color_of(self.chosen_number)
            shop.use("guaranteed_win")
            messages.add_ui("Lucky Charm triggered!")

        # Launch wheel and ball
        self.wheel_speed  = 6.0    # fast spin
        self.ball_speed   = -9.0   # opposite direction
        self.ball_radius  = 115.0  # starts at outer track
        self.ball_landed  = False

        return "started"

    # ------------------------------------------------------------------

    def _resolve(self, player, score_system):
        shop   = getattr(self, "_shop_ref", None)
        won    = False
        payout = 0

        if self.bet_type == "red"   and self.result_color == "red":
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
                self.result_text = "INSURED - bet back"
                self.result_win  = True
                self.flash_color = (80,180,255)
                self.flash_timer = 30
                self.phase       = "result"
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

        self.flash_timer = 40
        self.phase       = "result"

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, player, score_system, shop=None):
        self._shop_ref = shop
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Always rotate wheel
        self.wheel_angle = (self.wheel_angle + self.wheel_speed) % 360

        if self.phase == "spinning":
            self.spin_timer += 1
            progress = self.spin_timer / self.spin_duration

            # Decelerate wheel
            if progress < 0.6:
                self.wheel_speed = 6.0
            else:
                t = (progress - 0.6) / 0.4
                self.wheel_speed = max(0.3, 6.0 * (1 - t * t))

            # Ball: orbits fast then spirals inward
            if progress < 0.5:
                self.ball_speed  = -9.0
                self.ball_radius = 115.0
            elif progress < 0.85:
                t = (progress - 0.5) / 0.35
                self.ball_speed  = -9.0 + t * 6.0   # slows down
                self.ball_radius = 115.0 - t * 38.0  # spirals inward
            else:
                self.ball_speed  = self.wheel_speed * 0.8
                self.ball_radius = 77.0               # rests near pockets
                self.ball_landed = True

            self.ball_angle = (self.ball_angle + self.ball_speed) % 360

            if self.spin_timer >= self.spin_duration:
                # Snap ball to result sector
                result_idx   = WHEEL_ORDER.index(self.result_number)
                sector_angle = 360 / 37
                self.ball_angle  = (self.wheel_angle + result_idx * sector_angle + sector_angle / 2) % 360
                self.wheel_speed = 0.3
                self._resolve(player, score_system)

        elif self.phase in ("result", "betting"):
            # Gentle idle rotation
            self.ball_angle = (self.ball_angle + self.wheel_speed * 0.8) % 360

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen, player, day_system):
        W, H = screen.get_size()

        # Background
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
           (255,90,90) if tl<20 else (255,195,175),         124)
        sb("SESSION",  f"{self.session_profit:+}",
           (100,255,100) if self.session_profit>=0 else (255,100,100), 176)

        MX = SB + 8

        # ── Top bar ───────────────────────────────────────────────────
        pygame.draw.rect(screen, (18, 18, 30), (MX, 0, W - MX, 42))
        pygame.draw.line(screen, (50, 50, 80), (MX, 42), (W, 42), 1)
        title = self.font_hd.render("ROULETTE", True, GOLD)
        screen.blit(title, title.get_rect(center=((MX + W) // 2, 21)))

        # ── Layout split ──────────────────────────────────────────────
        # Main area: 168→800 = 632px
        # Wheel left half: 168→168+270 = 270px → WCX=168+135=303
        # Table right half: 168+278→800 = 354px available
        WCX = MX + 135    # wheel centre x
        WCY = 240         # wheel centre y — vertically centred in screen
        WR  = 122         # wheel radius

        self._draw_wheel(screen, WCX, WCY, WR)
        self._draw_table(screen, MX + 278, 46, player)
        self._draw_result_or_hint(screen, WCX, WCY, WR, player)

        # Flash
        if self.flash_timer > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((*self.flash_color, int(55 * self.flash_timer / 40)))
            screen.blit(fl, (0, 0))

    # ------------------------------------------------------------------

    def _draw_wheel(self, screen, cx, cy, R):
        """Draw the spinning wheel with sectors, numbers, and ball."""
        n_sectors   = 37
        sector_deg  = 360 / n_sectors

        # Outer rim
        pygame.draw.circle(screen, (60, 50, 30), (cx, cy), R + 14)
        pygame.draw.circle(screen, (100, 85, 50), (cx, cy), R + 14, 3)
        pygame.draw.circle(screen, (40, 35, 20), (cx, cy), R + 6, 6)

        # Draw each sector
        for i, num in enumerate(WHEEL_ORDER):
            start_angle = math.radians(self.wheel_angle + i * sector_deg - 90)
            end_angle   = math.radians(self.wheel_angle + (i + 1) * sector_deg - 90)

            color_name  = self._color_of(num)
            fill_color  = self._rgb(color_name)

            # Draw filled sector using polygon
            points = [(cx, cy)]
            steps  = max(3, int(sector_deg * 2))
            for s in range(steps + 1):
                a = start_angle + (end_angle - start_angle) * s / steps
                points.append((
                    cx + math.cos(a) * R,
                    cy + math.sin(a) * R
                ))
            if len(points) >= 3:
                pygame.draw.polygon(screen, fill_color, points)

            # Sector divider line
            pygame.draw.line(screen, (60, 50, 30),
                             (cx, cy),
                             (cx + math.cos(start_angle) * R,
                              cy + math.sin(start_angle) * R), 1)

            # Number label — positioned at mid-sector, 75% radius
            mid_angle = math.radians(self.wheel_angle + (i + 0.5) * sector_deg - 90)
            lx = cx + math.cos(mid_angle) * (R * 0.72)
            ly = cy + math.sin(mid_angle) * (R * 0.72)
            ns = self.font_tiny.render(str(num), True, (240, 240, 240))
            # Rotate label to follow sector
            angle_deg = math.degrees(mid_angle) + 90
            rotated   = pygame.transform.rotate(ns, -angle_deg)
            screen.blit(rotated, rotated.get_rect(center=(int(lx), int(ly))))

        # Inner hub
        pygame.draw.circle(screen, (30, 25, 15), (cx, cy), int(R * 0.22))
        pygame.draw.circle(screen, (80, 70, 40), (cx, cy), int(R * 0.22), 2)
        pygame.draw.circle(screen, (120, 100, 60), (cx, cy), int(R * 0.1))

        # Wheel outer border
        pygame.draw.circle(screen, (90, 75, 45), (cx, cy), R, 2)

        # Ball track (faint circle)
        track_r = int(R * 0.88)
        pygame.draw.circle(screen, (50, 45, 30), (cx, cy), track_r, 1)

        # Ball
        if self.ball_radius > 0:
            br   = self.ball_radius
            ba   = math.radians(self.ball_angle - 90)
            bx   = int(cx + math.cos(ba) * br)
            by_  = int(cy + math.sin(ba) * br)

            # Shadow
            pygame.draw.circle(screen, (20, 20, 20), (bx + 2, by_ + 2), 7)
            # Ball
            pygame.draw.circle(screen, (220, 220, 220), (bx, by_), 7)
            pygame.draw.circle(screen, (255, 255, 255), (bx - 2, by_ - 2), 3)

        # Pointer at top
        pygame.draw.polygon(screen, GOLD, [
            (cx,     cy - R - 16),
            (cx - 6, cy - R - 4),
            (cx + 6, cy - R - 4),
        ])

    # ------------------------------------------------------------------

    def _draw_table(self, screen, tx, ty, player):
        """Betting grid sized to fit exactly in 354px (800 - 446 available)."""
        self._num_rects   = {}
        self._quick_rects = []
        self._adj_rects   = []
        mx_pos, my_pos    = pygame.mouse.get_pos()

        # Available: 800 - tx = 800 - 446 = 354px
        # Layout: ZERO_W + GAP + 12*(CELL_W+GAP) <= 354
        # ZERO_W=26, GAP=2, CELL_W=26 → 26+2+12*28=362 — a touch over
        # ZERO_W=24, GAP=2, CELL_W=25 → 24+2+12*27=350 ✓
        AVAIL  = 800 - tx - 4          # 4px right margin
        GAP    = 2
        ZERO_W = 24
        CELL_W = (AVAIL - ZERO_W - GAP - GAP * 11) // 12   # distribute remaining
        CELL_H = 36                     # taller cells — use vertical space
        GRID_W = ZERO_W + GAP + 12 * CELL_W + 11 * GAP

        # ── Section label ─────────────────────────────────────────────
        screen.blit(self.font_sm.render("BETTING TABLE", True, (90,90,110)), (tx, ty))
        pygame.draw.line(screen, (50,50,70), (tx, ty+16), (tx+GRID_W, ty+16), 1)
        gy = ty + 22   # grid top y

        # ── Zero ──────────────────────────────────────────────────────
        zero_rect = pygame.Rect(tx, gy, ZERO_W, CELL_H*3 + GAP*2)
        self._num_rects[0] = zero_rect
        is_sel = (self.bet_type == "number" and self.chosen_number == 0)
        is_hov = zero_rect.collidepoint(mx_pos, my_pos) and self.phase == "betting"
        bg     = (0,140,0) if is_sel else (0,110,0) if is_hov else (0,85,0)
        pygame.draw.rect(screen, bg, zero_rect, border_radius=4)
        pygame.draw.rect(screen, GOLD if is_sel else (0,180,0), zero_rect, 2, border_radius=4)
        screen.blit(self.font_tiny.render("0", True, (255,255,255)),
                    self.font_tiny.render("0", True, (255,255,255)).get_rect(center=zero_rect.center))

        # ── Number grid 1–36 ─────────────────────────────────────────
        gx = tx + ZERO_W + GAP
        for col in range(12):
            for row in range(3):
                num  = col * 3 + (3 - row)
                rect = pygame.Rect(gx + col*(CELL_W+GAP), gy + row*(CELL_H+GAP), CELL_W, CELL_H)
                self._num_rects[num] = rect

                cn        = self._color_of(num)
                is_sel    = (self.bet_type == "number" and self.chosen_number == num)
                is_hov    = rect.collidepoint(mx_pos, my_pos) and self.phase == "betting"
                is_result = (self.phase == "result" and num == self.result_number)

                if is_result:    bg = GOLD
                elif is_sel:     bg = (200,200,60)
                elif is_hov:
                    r2,g2,b2 = self._rgb(cn)
                    bg = (min(255,r2+55), min(255,g2+55), min(255,b2+55))
                else:            bg = self._rgb(cn)

                pygame.draw.rect(screen, bg, rect, border_radius=2)
                border = GOLD if (is_sel or is_result) else (60,60,60)
                pygame.draw.rect(screen, border, rect, 2 if (is_sel or is_result) else 1, border_radius=2)
                tc = (0,0,0) if (is_result or is_sel) else (220,220,220)
                ns = self.font_tiny.render(str(num), True, tc)
                screen.blit(ns, ns.get_rect(center=rect.center))

        # ── Divider ───────────────────────────────────────────────────
        div1_y = gy + 3*(CELL_H+GAP) + 4
        pygame.draw.line(screen, (50,50,70), (tx, div1_y), (tx+GRID_W, div1_y), 1)

        # ── R/B buttons — each exactly half grid width ────────────────
        btn_y  = div1_y + 8
        half_w = (GRID_W - GAP) // 2
        self._color_rects = {}
        for label, btype, bx in [
            ("R - RED",   "red",   tx),
            ("B - BLACK", "black", tx + half_w + GAP),
        ]:
            br  = pygame.Rect(bx, btn_y, half_w, 30)
            self._color_rects[btype] = br
            sel = (self.bet_type == btype)
            bc  = {"red":(145,34,34),"black":(30,30,30)}[btype]
            if sel: bc = tuple(min(255,c+50) for c in bc)
            pygame.draw.rect(screen, bc, br, border_radius=4)
            pygame.draw.rect(screen, GOLD if sel else (70,70,70), br, 2, border_radius=4)
            ls = self.font_sm.render(label, True, (255,255,255))
            screen.blit(ls, ls.get_rect(center=br.center))

        # ── Divider ───────────────────────────────────────────────────
        div2_y = btn_y + 38
        pygame.draw.line(screen, (50,50,70), (tx, div2_y), (tx+GRID_W, div2_y), 1)

        # ── Bet display ───────────────────────────────────────────────
        bet_y = div2_y + 8
        screen.blit(self.font_sm.render("BET:", True, (110,110,110)), (tx, bet_y+5))
        bb = pygame.Rect(tx + 44, bet_y, 88, 28)
        self._bet_box_rect = bb  # ← store for hit-testing
        disp = (self.bet_input + "_") if self.typing_bet else f"${self.bet}"
        border_col = (150, 150, 255) if self.typing_bet else (78, 78, 108)
        pygame.draw.rect(screen, (28, 28, 46), bb, border_radius=4)
        pygame.draw.rect(screen, border_col, bb, 2, border_radius=4)
        bv = self.font.render(disp, True, GOLD)
        screen.blit(bv, bv.get_rect(center=bb.center))

        if self.bet_type == "number" and self.chosen_number is not None:
            summary = f"#{self.chosen_number}  pays x35"
        elif self.bet_type:
            summary = f"{self.bet_type.upper()}  pays x2"
        else:
            summary = "No bet selected"
        screen.blit(self.font_sm.render(summary, True, GOLD if self.bet_type else (65,65,80)),
                    (tx+140, bet_y+5))

        # ── Quick bets ────────────────────────────────────────────────
        qy     = bet_y + 36
        qbtn_w = (GRID_W - GAP*3) // 4
        screen.blit(self.font_sm.render("Quick:", True, (90,90,100)), (tx, qy+4))
        for j, text in enumerate(self.quick_bets):
            r   = pygame.Rect(tx + j*(qbtn_w+GAP), qy+22, qbtn_w, 26)
            self._quick_rects.append((text, r))
            hov = r.collidepoint(mx_pos, my_pos)
            pygame.draw.rect(screen, (50,50,72) if hov else (30,30,48), r, border_radius=3)
            pygame.draw.rect(screen, GOLD if hov else (70,70,100), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (220,220,255) if hov else (150,150,190))
            screen.blit(ls, ls.get_rect(center=r.center))

        # ── Fine adjustment — 6 per row ───────────────────────────────
        adj_y  = qy + 56
        btn6_w = (GRID_W - GAP*5) // 6
        for i, (text, val) in enumerate(self.bet_buttons):
            r  = pygame.Rect(tx + (i%6)*(btn6_w+GAP), adj_y + (i//6)*30, btn6_w, 24)
            self._adj_rects.append((val, r))
            bg = (48,28,28) if val < 0 else (28,48,28)
            pygame.draw.rect(screen, bg, r, border_radius=3)
            pygame.draw.rect(screen, (80,80,80), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (200,200,200))
            screen.blit(ls, ls.get_rect(center=r.center))

        # ── Hint ─────────────────────────────────────────────────────
        hint_y = adj_y + 68
        if self.phase == "betting":
            hs = self.font_sm.render("SPACE = Spin   R/B = Color bet", True, (60,60,80))
        elif self.phase == "spinning":
            hs = self.font_sm.render("Spinning...", True, (120,120,140))
        else:
            hs = self.font_sm.render("Any key = Bet again", True, (60,60,80))
        screen.blit(hs, (tx, hint_y))

    # ------------------------------------------------------------------

    def _draw_result_or_hint(self, screen, cx, cy, R, player):
        """Draw result text below the wheel, or hint text."""
        base_y = cy + R + 20

        if self.phase == "result":
            rc = (100,255,120) if self.result_win else (255,90,90)
            rs = self.font_hd.render(self.result_text, True, rc)
            screen.blit(rs, rs.get_rect(center=(cx, base_y + 20)))

            # Result number pill
            num_col = self._rgb(self.result_color)
            pill    = pygame.Rect(cx - 28, base_y + 48, 56, 30)
            pygame.draw.rect(screen, num_col, pill, border_radius=6)
            pygame.draw.rect(screen, GOLD, pill, 2, border_radius=6)
            ns = self.font.render(str(self.result_number), True, (255,255,255))
            screen.blit(ns, ns.get_rect(center=pill.center))

        elif self.phase == "spinning":
            sp = self.font_sm.render("Rolling...", True, (160,160,180))
            screen.blit(sp, sp.get_rect(center=(cx, base_y + 16)))

        else:
            # Show idle bet type reminder
            if self.bet_type:
                if self.bet_type == "number" and self.chosen_number is not None:
                    txt = f"Bet: #{self.chosen_number}"
                else:
                    txt = f"Bet: {self.bet_type.upper()}"
                ts = self.font_sm.render(txt, True, GOLD)
                screen.blit(ts, ts.get_rect(center=(cx, base_y + 16)))