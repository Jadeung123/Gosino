# blackjack.py
# Casino-rules blackjack — dealer stands on soft 17, double down, split.
# Drawn card graphics, same sidebar/top-bar template as other minigames.

import pygame
import random

GOLD  = (255, 215, 0)
WHITE = (255, 255, 255)

# Card suits and ranks
SUITS  = ["♠", "♥", "♦", "♣"]
RANKS  = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
RED_SUITS   = {"♥", "♦"}

# Card dimensions — larger for readability
CARD_W = 80
CARD_H = 112


def _card_value(rank):
    if rank in ("J","Q","K"): return 10
    if rank == "A":           return 11
    return int(rank)


def _hand_value(hand):
    """Return best value of a hand — aces count as 1 if bust."""
    total = sum(_card_value(r) for r, s in hand)
    aces  = sum(1 for r, s in hand if r == "A")
    while total > 21 and aces:
        total -= 10
        aces  -= 1
    return total


def _is_soft_17(hand):
    """True if hand is exactly soft 17 (ace counted as 11)."""
    if _hand_value(hand) != 17:
        return False
    hard = sum(10 if r in ("J","Q","K") else 1 if r == "A" else int(r)
               for r, s in hand)
    return hard != 17


class Blackjack:

    def __init__(self):
        self.font_big  = pygame.font.SysFont(None, 64)
        self.font_hd   = pygame.font.SysFont(None, 38)
        self.font      = pygame.font.SysFont(None, 30)
        self.font_sm   = pygame.font.SysFont(None, 24)
        self.font_card = pygame.font.SysFont(None, 28)
        self.font_suit = pygame.font.SysFont(None, 42)

        self.bet            = 10
        self.typing_bet     = False
        self.bet_input      = ""
        self.session_profit = 0
        self._bet_box       = None

        self.quick_bets  = ["MIN", "HALF", "DOUBLE", "MAX"]
        self.bet_buttons = [
            ("+1000",1000),("+100",100),("+50",50),("+10",10),("+5",5),("+1",1),
            ("-1000",-1000),("-100",-100),("-50",-50),("-10",-10),("-5",-5),("-1",-1),
        ]
        self._quick_rects = []
        self._adj_rects   = []
        self._action_rects = {}   # "hit","stand","double","split" → Rect

        self.reset()

    # ------------------------------------------------------------------

    def reset(self):
        self.phase          = "betting"   # betting → playing → dealer_turn → result
        self.deck           = []
        self.player_hands   = [[]]        # list of hands (split creates 2)
        self.active_hand    = 0           # index of hand currently being played
        self.dealer_hand    = []
        self.dealer_reveal  = False       # show hole card?
        self.result_texts   = []          # one result string per hand
        self.result_wins    = []          # True/False per hand
        self.bets           = [self.bet]  # bet per hand (split duplicates)
        self.can_split      = False
        self.flash_timer    = 0
        self.flash_color    = (0,0,0)
        self.typing_bet     = False
        self.bet_input      = ""
        self._shop_ref      = None
        self.deal_queue = []  # list of (hand_idx, card_idx, start_tick)
        self.deal_tick = 0  # increments each update call
        self.animating = False

    # ------------------------------------------------------------------
    # Deck
    # ------------------------------------------------------------------

    def _build_deck(self):
        deck = [(r, s) for s in SUITS for r in RANKS] * 6   # 6-deck shoe
        random.shuffle(deck)
        return deck

    def _deal(self):
        if len(self.deck) < 10:
            self.deck = self._build_deck()
        return self.deck.pop()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, event, player, score_system, messages, shop=None):
        self._shop_ref = shop

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.phase == "betting":
                # Bet box
                if self._bet_box and self._bet_box.collidepoint(mx, my):
                    self.typing_bet = True
                    self.bet_input  = ""
                    return
                # Quick bets
                for label, rect in self._quick_rects:
                    if rect.collidepoint(mx, my):
                        if label == "MIN":    self.bet = 1
                        elif label == "HALF": self.bet = max(1, self.bet // 2)
                        elif label == "DOUBLE": self.bet = min(player.money, self.bet * 2)
                        elif label == "MAX":  self.bet = player.money
                        return
                for val, rect in self._adj_rects:
                    if rect.collidepoint(mx, my):
                        self.bet = max(1, min(player.money, self.bet + val))
                        return

            if self.phase == "playing":
                for action, rect in self._action_rects.items():
                    if rect.collidepoint(mx, my):
                        self._do_action(action, player, score_system, messages, shop)
                        return

            return

        if event.type != pygame.KEYDOWN:
            return

        # Typing bet
        if self.typing_bet:
            if event.key == pygame.K_RETURN:
                if self.bet_input.isdigit() and self.bet_input:
                    self.bet = max(1, min(player.money, int(self.bet_input)))
                self.typing_bet = False
                self.bet_input  = ""
            elif event.key == pygame.K_BACKSPACE:
                self.bet_input = self.bet_input[:-1]
            elif event.unicode.isdigit():
                self.bet_input += event.unicode
            return

        if event.key == pygame.K_ESCAPE:
            if self.phase != "playing":
                return "exit"

        if self.phase == "betting" and event.key == pygame.K_SPACE:
            self._start_round(player, messages, shop)

        if self.phase == "playing":
            if event.key == pygame.K_h:
                self._do_action("hit",    player, score_system, messages, shop)
            elif event.key == pygame.K_s:
                self._do_action("stand",  player, score_system, messages, shop)
            elif event.key == pygame.K_d:
                self._do_action("double", player, score_system, messages, shop)
            elif event.key == pygame.K_p:
                self._do_action("split",  player, score_system, messages, shop)

        if self.phase == "result" and event.key == pygame.K_SPACE:
            self.reset()

        return None

    # ------------------------------------------------------------------

    def _start_round(self, player, messages, shop):
        if player.money < self.bet:
            messages.add_ui("Not enough money!")
            return

        self.deck = self._build_deck()
        player.money -= self.bet

        # Apply guaranteed win
        if shop and shop.is_active("guaranteed_win"):
            shop.use("guaranteed_win")
            messages.add_ui("Lucky Charm — guaranteed win!")

        # Deal
        self.player_hands  = [[self._deal(), self._deal()]]
        self.dealer_hand   = [self._deal(), self._deal()]
        self.dealer_reveal = False
        self.active_hand   = 0
        self.bets          = [self.bet]
        self.result_texts  = []
        self.result_wins   = []

        # Check split availability
        self._update_can_split(player)

        self.phase = "playing"

        # Instant blackjack check
        if _hand_value(self.player_hands[0]) == 21:
            self._dealer_play(player, None, messages, shop)
        self._queue_deal_animation()
        return "played"

    def _queue_deal_animation(self):
        """Queue slide-in animations for all starting cards."""
        self.deal_tick = 0
        self.deal_queue = []
        # Deal order: player1, dealer1, player2, dealer2
        order = [
            ("player", 0, 0),  # hand_idx, card_idx
            ("dealer", 0, 0),
            ("player", 0, 1),
            ("dealer", 0, 1),
        ]
        for i, (who, hi, ci) in enumerate(order):
            self.deal_queue.append({
                "who": who, "hi": hi, "ci": ci,
                "start": i * 12  # 12 ticks between each card
            })
        self.animating = True

    def _queue_single_card(self, who, hi, ci):
        """Queue slide-in for one card — used for hit, double, dealer draw."""
        self.deal_tick = 0
        self.deal_queue = [{
            "who": who, "hi": hi, "ci": ci,
            "start": 0
        }]
        self.animating = True

    def _get_card_offset(self, who, hi, ci):
        """Return (y_offset, alpha) for a card mid-animation. (0, 255) when done."""
        if not self.animating:
            return 0, 255
        for entry in self.deal_queue:
            if entry["who"] == who and entry["hi"] == hi and entry["ci"] == ci:
                elapsed = self.deal_tick - entry["start"]
                if elapsed < 0:
                    return -120, 0  # not yet started — hidden above
                if elapsed >= 20:
                    return 0, 255  # fully landed
                t = elapsed / 20
                ease = 1 - (1 - t) * (1 - t)  # ease-out quad
                return int(-120 * (1 - ease)), min(255, int(255 * t * 2))
        return 0, 255  # card not in queue — already visible

    # ------------------------------------------------------------------

    def _update_can_split(self, player):
        hand = self.player_hands[self.active_hand]
        self.can_split = (
            len(hand) == 2
            and _card_value(hand[0][0]) == _card_value(hand[1][0])
            and player.money >= self.bets[self.active_hand]
            and len(self.player_hands) < 4   # max 4 splits
        )

    def _do_action(self, action, player, score_system, messages, shop):
        hand = self.player_hands[self.active_hand]

        if action == "hit":
            hand.append(self._deal())
            self._queue_single_card("player", self.active_hand, len(hand) - 1)
            if _hand_value(hand) > 21:
                result = self._next_hand_or_dealer(player, score_system, messages, shop)
                if result == "result_ready":
                    return "result_ready"

        elif action == "stand":
            result = self._next_hand_or_dealer(player, score_system, messages, shop)
            if result == "result_ready":
                return "result_ready"

        elif action == "double":
            extra = self.bets[self.active_hand]
            if player.money < extra:
                messages.add_ui("Not enough to double!")
                return
            player.money -= extra
            self.bets[self.active_hand] *= 2
            hand.append(self._deal())
            self._queue_single_card("player", self.active_hand, len(hand) - 1)
            result = self._next_hand_or_dealer(player, score_system, messages, shop)
            if result == "result_ready":
                return "result_ready"

        elif action == "split" and self.can_split:
            extra = self.bets[self.active_hand]
            if player.money < extra:
                messages.add_ui("Not enough to split!")
                return
            player.money -= extra
            # Split the hand
            card2 = hand.pop()
            new_hand = [card2, self._deal()]
            self._queue_single_card("player", self.active_hand + 1, 1)
            hand.append(self._deal())
            self._queue_single_card("player", self.active_hand, len(hand) - 1)
            self.player_hands.insert(self.active_hand + 1, new_hand)
            self.bets.insert(self.active_hand + 1, extra)
            self._update_can_split(player)

    def _next_hand_or_dealer(self, player, score_system, messages, shop):
        self.active_hand += 1
        if self.active_hand < len(self.player_hands):
            self._update_can_split(player)
        else:
            result = self._dealer_play(player, score_system, messages, shop)
            if result == "result_ready":
                return "result_ready"

    def _dealer_play(self, player, score_system, messages, shop):
        self.dealer_reveal = True
        while _hand_value(self.dealer_hand) < 17 or _is_soft_17(self.dealer_hand):
            self.dealer_hand.append(self._deal())
            self._queue_single_card("dealer", 0, len(self.dealer_hand) - 1)
        result = self._resolve(player, score_system, messages, shop)
        if result == "result_ready":
            return "result_ready"

    def _resolve(self, player, score_system, messages, shop):
        dealer_val = _hand_value(self.dealer_hand)
        dealer_bj  = (len(self.dealer_hand) == 2 and dealer_val == 21)

        self.result_texts = []
        self.result_wins  = []

        for i, hand in enumerate(self.player_hands):
            bet_amt   = self.bets[i]
            pval      = _hand_value(hand)
            player_bj = (len(hand) == 2 and pval == 21 and i == 0
                         and len(self.player_hands) == 1)

            # Apply multiplier bonus
            bonus = getattr(player, "multiplier_bonus", 0)

            if pval > 21:
                # Bust
                self.result_texts.append(f"BUST  -${bet_amt}")
                self.result_wins.append(False)
                self.session_profit -= bet_amt

            elif dealer_bj and not player_bj:
                # Dealer blackjack
                self.result_texts.append(f"Dealer BJ  -${bet_amt}")
                self.result_wins.append(False)
                self.session_profit -= bet_amt

            elif player_bj and not dealer_bj:
                # Blackjack 3:2
                payout = int(bet_amt * 2.5)
                if bonus > 0: payout = int(payout * (1 + bonus))
                if shop and shop.hot_streak_count > 0:
                    payout *= 2
                    shop.consume_hot_streak()
                player.money += payout
                score_system.add_money_score(payout) if score_system else None
                self.result_texts.append(f"BLACKJACK! +${payout - bet_amt}")
                self.result_wins.append(True)
                self.session_profit += payout - bet_amt

            elif pval > dealer_val or dealer_val > 21:
                # Win
                payout = bet_amt * 2
                if bonus > 0: payout = int(payout * (1 + bonus))
                if shop and shop.hot_streak_count > 0:
                    payout *= 2
                    shop.consume_hot_streak()
                player.money += payout
                score_system.add_money_score(payout) if score_system else None
                self.result_texts.append(f"WIN  +${payout - bet_amt}")
                self.result_wins.append(True)
                self.session_profit += payout - bet_amt

            elif pval == dealer_val:
                # Push — return bet
                player.money += bet_amt
                self.result_texts.append("PUSH  (bet back)")
                self.result_wins.append(None)

            else:
                # Lose
                self.result_texts.append(f"LOST  -${bet_amt}")
                self.result_wins.append(False)
                self.session_profit -= bet_amt

        # Insurance fallback
        if not any(self.result_wins) and shop and shop.is_active("insurance"):
            player.money += self.bets[0]
            shop.use("insurance")
            messages.add_ui("Insurance — bet refunded!")

        # Flash
        any_win = any(w for w in self.result_wins if w)
        self.flash_color = (60,220,100) if any_win else (200,60,60)
        self.flash_timer = 40
        self.phase       = "result"
        return "result_ready"

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, player, score_system, messages, shop=None):
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.animating:
            self.deal_tick += 1
            # Check if all cards have finished animating
            last = self.deal_queue[-1] if self.deal_queue else None
            if last and self.deal_tick > last["start"] + 20:
                self.animating = False

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen, player, day_system):
        W, H  = screen.get_size()
        self._quick_rects  = []
        self._adj_rects    = []
        self._action_rects = {}

        # ── Background ────────────────────────────────────────────────
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

        MX  = SB + 10
        MCX = (MX + W) // 2

        # ── Top bar ───────────────────────────────────────────────────
        pygame.draw.rect(screen, (18, 18, 30), (MX, 0, W - MX, 48))
        pygame.draw.line(screen, (50, 50, 80), (MX, 48), (W, 48), 1)
        title = self.font_hd.render("BLACKJACK", True, GOLD)
        screen.blit(title, title.get_rect(center=(MCX, 24)))

        # ── Table felt ────────────────────────────────────────────────
        felt = pygame.Rect(MX + 10, 54, W - MX - 20, 310)
        pygame.draw.rect(screen, (12, 58, 28), felt, border_radius=14)
        pygame.draw.rect(screen, (22, 85, 45), felt, 3, border_radius=14)

        # Inner felt shadow border
        felt_inner = felt.inflate(-10, -10)
        pygame.draw.rect(screen, (16, 68, 34), felt_inner, 1, border_radius=10)

        # ── Dealer section ────────────────────────────────────────────
        dealer_val = _hand_value(self.dealer_hand) if self.dealer_reveal else (
            _card_value(self.dealer_hand[0][0]) if self.dealer_hand else 0
        )
        dval_txt = str(dealer_val) if self.dealer_hand else ""
        screen.blit(self.font_sm.render("DEALER", True, (160, 210, 160)), (MX + 22, 64))
        if dval_txt:
            dv = self.font.render(dval_txt, True, (160, 210, 160))
            dp = pygame.Surface((dv.get_width() + 10, dv.get_height() + 6), pygame.SRCALPHA)
            dp.fill((0, 0, 0, 120))
            screen.blit(dp, (MX + 22, 78))
            screen.blit(dv, (MX + 27, 80))

        if self.dealer_hand:
            self._draw_hand(screen, self.dealer_hand, MCX, 84,
                            hide_second=not self.dealer_reveal,
                            who="dealer", hi=0)

        # ── Divider ───────────────────────────────────────────────────
        pygame.draw.line(screen, (22, 85, 45),
                         (MX + 24, 220), (W - 24, 220), 1)

        # ── Player section ────────────────────────────────────────────
        for hi, hand in enumerate(self.player_hands):
            if not hand:   # skip empty hands (betting phase)
                continue
            pval      = _hand_value(hand)
            is_active = (hi == self.active_hand and self.phase == "playing")
            is_bust   = pval > 21

            # Spread split hands
            offset = (hi - (len(self.player_hands)-1) / 2) * (CARD_W + 14) * max(len(hand), 2)
            hcx    = int(MCX + offset)

            # Hand value badge
            badge_col = (220, 60, 60) if is_bust else (255, 220, 60) if is_active else (140, 200, 140)
            badge_txt = "BUST!" if is_bust else str(pval)

            # Score label in top-left corner of player section — mirrors dealer label style
            bv = self.font.render(badge_txt, True, badge_col)
            bp = pygame.Surface((bv.get_width() + 10, bv.get_height() + 6), pygame.SRCALPHA)
            bp.fill((0, 0, 0, 120))
            screen.blit(self.font_sm.render("YOU", True, (160, 210, 160)), (MX + 22, 226))
            screen.blit(bp, (MX + 22, 240))
            screen.blit(bv, (MX + 27, 242))

            self._draw_hand(screen, hand, hcx, 236,
                            hide_second=False, who="player", hi=hi)

            # Result overlay
            if self.phase == "result" and hi < len(self.result_texts):
                won = self.result_wins[hi]
                rc  = (80,255,120) if won else (255,80,80) if won is False else (220,220,80)
                rs  = self.font_hd.render(self.result_texts[hi], True, rc)
                # Clamp result text width to fit inside felt bounds
                felt_left = MX + 20
                felt_right = W - 20
                max_w = felt_right - felt_left - 20
                if rs.get_width() > max_w:
                    rs = pygame.transform.scale(
                        rs, (max_w, int(rs.get_height() * max_w / rs.get_width())))
                rx = max(felt_left, min(felt_right - rs.get_width(), hcx - rs.get_width() // 2))
                pill = pygame.Surface((rs.get_width() + 20, rs.get_height() + 10), pygame.SRCALPHA)
                pill.fill((0, 0, 0, 180))
                pygame.draw.rect(pill, (*rc, 60),
                                 (0, 0, rs.get_width() + 20, rs.get_height() + 10), 2, border_radius=6)
                screen.blit(pill, (rx - 10, 375))
                screen.blit(rs, (rx, 385))

        # ── Action buttons ────────────────────────────────────────────
        if self.phase == "playing":
            self._draw_actions(screen, MX, W, player)
        elif self.phase == "betting":
            self._draw_betting(screen, MX, MCX, W, player)
        elif self.phase == "result":
            self._draw_result_hint(screen, MCX)

        # ── Flash ─────────────────────────────────────────────────────
        if self.flash_timer > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((*self.flash_color, int(55 * self.flash_timer / 40)))
            screen.blit(fl, (0,0))

    # ------------------------------------------------------------------

    def _draw_hand(self, screen, hand, cx, y, hide_second=False, who="player", hi=0):
        n = len(hand)
        total_w = n * CARD_W + (n - 1) * 8
        start_x = cx - total_w // 2

        for i, (rank, suit) in enumerate(hand):
            y_off, alpha = self._get_card_offset(who, hi, i)
            x = start_x + i * (CARD_W + 8)
            rect = pygame.Rect(x, y + y_off, CARD_W, CARD_H)

            # Draw card onto temp surface so we can apply alpha
            card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            temp_rect = pygame.Rect(0, 0, CARD_W, CARD_H)

            if hide_second and i == 1:
                self._draw_card_back(card_surf, temp_rect)
            else:
                self._draw_card_front(card_surf, temp_rect, rank, suit)

            card_surf.set_alpha(alpha)
            screen.blit(card_surf, rect)

    def _draw_suit(self, screen, suit, cx, cy, size, color):
        """Draw suit symbol as pygame shapes — works on any font/OS."""
        if suit in ("♥", "H"):
            # Heart — two circles + triangle
            r = size // 2
            pygame.draw.circle(screen, color, (cx - r//2, cy - r//4), r//2 + 1)
            pygame.draw.circle(screen, color, (cx + r//2, cy - r//4), r//2 + 1)
            pygame.draw.polygon(screen, color, [
                (cx - r, cy - r//4),
                (cx + r, cy - r//4),
                (cx,     cy + r),
            ])
        elif suit in ("♦", "D"):
            # Diamond
            pygame.draw.polygon(screen, color, [
                (cx,        cy - size),
                (cx + size, cy),
                (cx,        cy + size),
                (cx - size, cy),
            ])
        elif suit in ("♠", "S"):
            # Spade — inverted heart + stem
            r = size // 2
            pygame.draw.circle(screen, color, (cx - r//2, cy + r//4), r//2 + 1)
            pygame.draw.circle(screen, color, (cx + r//2, cy + r//4), r//2 + 1)
            pygame.draw.polygon(screen, color, [
                (cx - r, cy + r//4),
                (cx + r, cy + r//4),
                (cx,     cy - r),
            ])
            # Stem
            pygame.draw.rect(screen, color,
                             pygame.Rect(cx - size//4, cy + r//2, size//2, size//2))
        elif suit in ("♣", "C"):
            # Club — three circles + stem
            r = max(2, size // 3)
            pygame.draw.circle(screen, color, (cx,        cy - r),     r)
            pygame.draw.circle(screen, color, (cx - r,    cy + r//2),  r)
            pygame.draw.circle(screen, color, (cx + r,    cy + r//2),  r)
            pygame.draw.rect(screen, color,
                             pygame.Rect(cx - size//4, cy + r//2, size//2, r + 2))

    def _draw_card_front(self, screen, rect, rank, suit):
        is_red = suit in ("♥", "♦", "H", "D")
        tc     = (185, 28, 28) if is_red else (18, 18, 18)

        # Card body
        pygame.draw.rect(screen, (250, 246, 238), rect, border_radius=7)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(screen, (242, 236, 226), inner, border_radius=5)
        pygame.draw.rect(screen, (160, 148, 132), rect, 1, border_radius=7)

        # Top-left: rank text
        rank_surf = self.font_card.render(rank, True, tc)
        screen.blit(rank_surf, (rect.x + 5, rect.y + 5))

        # Top-left: small suit shape below rank
        self._draw_suit(screen, suit,
                        rect.x + 7,
                        rect.y + 8 + rank_surf.get_height() + 6,
                        5, tc)

        # Centre: large rank
        big = self.font_suit.render(rank, True, tc)
        screen.blit(big, big.get_rect(center=(rect.centerx, rect.centery - 8)))

        # Centre below rank: medium suit shape
        self._draw_suit(screen, suit,
                        rect.centerx,
                        rect.centery + big.get_height() // 2 + 4,
                        9, tc)

        # Bottom-right: mirrored rank
        br_rank = pygame.transform.rotate(
            self.font_card.render(rank, True, tc), 180)
        screen.blit(br_rank,
                    (rect.right - br_rank.get_width() - 5,
                     rect.bottom - br_rank.get_height() - 20))
        # Bottom-right: suit shape above mirrored rank
        self._draw_suit(screen, suit,
                        rect.right - 7,
                        rect.bottom - br_rank.get_height() - 28,
                        5, tc)

    def _draw_card_back(self, screen, rect):
        # Dark back
        pygame.draw.rect(screen, (30, 30, 80), rect, border_radius=6)
        pygame.draw.rect(screen, (60, 60, 140), rect, 2, border_radius=6)

        # Diamond pattern
        inner = rect.inflate(-10, -10)
        pygame.draw.rect(screen, (40, 40, 100), inner, border_radius=4)
        cx, cy = rect.center
        size   = 14
        for dx in range(-2, 3):
            for dy in range(-3, 4):
                if (dx + dy) % 2 == 0:
                    pts = [
                        (cx + dx*size,       cy + dy*size - size//2),
                        (cx + dx*size + size//2, cy + dy*size),
                        (cx + dx*size,       cy + dy*size + size//2),
                        (cx + dx*size - size//2, cy + dy*size),
                    ]
                    pygame.draw.polygon(screen, (55, 55, 120), pts)

    # ------------------------------------------------------------------

    def _draw_actions(self, screen, MX, W, player):
        """Action buttons in 2×2 grid — bigger and better spaced."""
        hand    = self.player_hands[self.active_hand]
        can_dbl = (len(hand) == 2 and player.money >= self.bets[self.active_hand])

        actions = [
            ("HIT",    "H", True,           (36,80,36),   (70,160,70)),
            ("STAND",  "S", True,           (80,36,36),   (160,70,70)),
            ("DOUBLE", "D", can_dbl,        (36,60,80),   (70,120,160)),
            ("SPLIT",  "P", self.can_split, (70,50,20),   (160,120,50)),
        ]

        btn_w  = 148
        btn_h  = 40
        gap    = 10
        MCX    = (MX + W) // 2
        row1_x = MCX - btn_w - gap // 2
        row2_x = MCX + gap // 2
        y1     = 395
        y2     = y1 + btn_h + gap

        positions = [
            (row1_x, y1), (row2_x, y1),
            (row1_x, y2), (row2_x, y2),
        ]

        mx_pos, my_pos = pygame.mouse.get_pos()

        for i, ((label, key, enabled, bg_base, border_base), (rx, ry)) in enumerate(
                zip(actions, positions)):
            rect = pygame.Rect(rx, ry, btn_w, btn_h)
            self._action_rects[label.lower()] = rect

            hov = rect.collidepoint(mx_pos, my_pos) and enabled

            if not enabled:
                bg     = (26, 26, 32)
                border = (45, 45, 55)
                tc     = (65, 65, 70)
            elif hov:
                bg     = tuple(min(255, c+30) for c in bg_base)
                border = GOLD
                tc     = WHITE
            else:
                bg     = bg_base
                border = border_base
                tc     = (220, 240, 220)

            pygame.draw.rect(screen, bg,     rect, border_radius=7)
            pygame.draw.rect(screen, border, rect, 2, border_radius=7)

            lbl = self.font.render(f"{label}  [{key}]", True, tc)
            screen.blit(lbl, lbl.get_rect(center=rect.center))

        # Bet display below buttons
        bets_txt = "  |  ".join(f"${b}" for b in self.bets)
        bs = self.font_sm.render(f"Bet: {bets_txt}", True, GOLD)
        screen.blit(bs, bs.get_rect(center=(MCX, y2 + btn_h + 12)))

    # ------------------------------------------------------------------

    def _draw_betting(self, screen, MX, MCX, W, player):
        """Bet amount + quick bets + adjustment buttons."""
        y0 = 420

        # Bet label + box
        screen.blit(self.font_sm.render("BET:", True, (115,115,115)), (MX, y0+6))
        bb = pygame.Rect(MX+46, y0, 100, 30)
        self._bet_box  = bb
        disp       = (self.bet_input + "_") if self.typing_bet else f"${self.bet}"
        border_col = (150,150,255) if self.typing_bet else (78,78,108)
        pygame.draw.rect(screen, (28,28,46), bb, border_radius=4)
        pygame.draw.rect(screen, border_col, bb, 2, border_radius=4)
        bv = self.font.render(disp, True, GOLD)
        screen.blit(bv, bv.get_rect(center=bb.center))

        hint = self.font_sm.render("SPACE = Deal", True, (70,70,90))
        screen.blit(hint, (MX + 158, y0+6))

        # Quick bets
        qy     = y0 + 38
        qbtn_w = 76
        screen.blit(self.font_sm.render("Quick:", True, (90,90,100)), (MX, qy+4))
        mx_pos, my_pos = pygame.mouse.get_pos()
        for j, text in enumerate(self.quick_bets):
            r   = pygame.Rect(MX + 52 + j * (qbtn_w+4), qy, qbtn_w, 26)
            self._quick_rects.append((text, r))
            hov = r.collidepoint(mx_pos, my_pos)
            pygame.draw.rect(screen, (50,50,72) if hov else (30,30,48), r, border_radius=3)
            pygame.draw.rect(screen, GOLD if hov else (70,70,100), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (220,220,255) if hov else (150,150,190))
            screen.blit(ls, ls.get_rect(center=r.center))

        # Fine adjustment
        adj_y  = qy + 34
        btn6_w = 74
        for i, (text, val) in enumerate(self.bet_buttons):
            r  = pygame.Rect(MX + (i%6)*(btn6_w+4), adj_y + (i//6)*30, btn6_w, 24)
            self._adj_rects.append((val, r))
            bg = (48,28,28) if val < 0 else (28,48,28)
            pygame.draw.rect(screen, bg, r, border_radius=3)
            pygame.draw.rect(screen, (80,80,80), r, 1, border_radius=3)
            ls = self.font_sm.render(text, True, (200,200,200))
            screen.blit(ls, ls.get_rect(center=r.center))

    # ------------------------------------------------------------------

    def _draw_result_hint(self, screen, MCX):
        hint = self.font_sm.render("SPACE = Play again   |   ESC = Leave",
                                    True, (70,70,90))
        screen.blit(hint, hint.get_rect(center=(MCX, 540)))