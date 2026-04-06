# shop.py
# Redesigned shop — top bar HUD, full-width card grid, polished visuals.
# No hardcoded inventory bar — use TAB to open the inventory panel.

import pygame
import random


ALL_ITEMS = [
    {
        "name":   "Lucky Charm",
        "type":   "consumable",
        "cost":   150,
        "desc":   "Next gamble is guaranteed to win.",
        "effect": "guaranteed_win",
        "color":  (220, 185, 50),
    },
    {
        "name":   "Loaded Dice",
        "type":   "consumable",
        "cost":   200,
        "desc":   "Next dice roll lands above 70.",
        "effect": "loaded_dice",
        "color":  (180, 80, 220),
    },
    {
        "name":   "Hot Streak",
        "type":   "consumable",
        "cost":   180,
        "desc":   "Next 3 gambles pay double winnings.",
        "effect": "hot_streak",
        "color":  (230, 120, 40),
    },
    {
        "name":   "Insurance",
        "type":   "consumable",
        "cost":   100,
        "desc":   "Refunds your bet if you lose once.",
        "effect": "insurance",
        "color":  (60, 190, 230),
    },
    {
        "name":   "Card Counter",
        "type":   "permanent",
        "cost":   400,
        "desc":   "Slots win more often (threshold -1).",
        "effect": "card_counter",
        "color":  (80, 210, 130),
    },
    {
        "name":   "Whale Status",
        "type":   "permanent",
        "cost":   600,
        "desc":   "All multipliers +0.5x permanently.",
        "effect": "whale_status",
        "color":  (90, 150, 255),
    },
]

# Layout constants — computed so nothing clips on 800x600
SCREEN_W  = 800
SCREEN_H  = 600
TOP_BAR_H = 64
PAD       = 16
GAP       = 12
COLS      = 2
CARD_W    = (SCREEN_W - PAD * 2 - GAP * (COLS - 1)) // COLS   # 386px each
CARD_H    = 172
GRID_Y    = TOP_BAR_H + 48


class Shop:

    MAX_INVENTORY = 3

    def __init__(self):
        self.font_title = pygame.font.SysFont(None, 46)
        self.font_hd    = pygame.font.SysFont(None, 34)
        self.font       = pygame.font.SysFont(None, 28)
        self.font_sm    = pygame.font.SysFont(None, 22)

        self.stock            = []
        self.inventory        = [None, None, None]
        self.hot_streak_count = 0
        self.feedback         = ""
        self.feedback_ok      = True
        self.feedback_timer   = 0

        self.roll_stock()

    # ------------------------------------------------------------------
    #  STOCK
    # ------------------------------------------------------------------

    def roll_stock(self):
        permanents  = [i for i in ALL_ITEMS if i["type"] == "permanent"]
        consumables = [i for i in ALL_ITEMS if i["type"] == "consumable"]
        chosen = (
            random.sample(permanents,  min(2, len(permanents)))
            + random.sample(consumables, min(2, len(consumables)))
        )
        random.shuffle(chosen)
        self.stock = [dict(item, sold=False) for item in chosen]

    # ------------------------------------------------------------------
    #  INVENTORY HELPERS
    # ------------------------------------------------------------------

    def _inventory_full(self):
        return all(slot is not None for slot in self.inventory)

    def _add_to_inventory(self, item):
        for i, slot in enumerate(self.inventory):
            if slot is None:
                self.inventory[i] = item.copy()
                return True
        return False

    def has_effect(self, effect_name):
        return any(
            slot is not None and slot["effect"] == effect_name
            for slot in self.inventory
        )

    def consume_slot(self, slot_index):
        if 0 <= slot_index < self.MAX_INVENTORY:
            self.inventory[slot_index] = None

    # ------------------------------------------------------------------
    #  PURCHASE
    # ------------------------------------------------------------------

    def _buy(self, item, player):
        if item["sold"]:
            return "already_sold", "Already sold!"
        if player.money < item["cost"]:
            return "no_money", "Not enough money!"
        if item["type"] == "consumable" and self._inventory_full():
            return "inv_full", "Inventory full! (max 3)"

        player.money -= item["cost"]
        item["sold"]  = True

        if item["type"] == "consumable":
            self._add_to_inventory(item)
            return "ok", f"Bought {item['name']}!"
        self._apply_permanent(item, player)
        return "ok", f"Bought {item['name']}! Effect applied."

    def _apply_permanent(self, item, player):
        effect = item["effect"]
        if effect == "card_counter":
            player.slot_threshold = getattr(player, "slot_threshold", 5) - 1
        elif effect == "whale_status":
            player.multiplier_bonus = getattr(player, "multiplier_bonus", 0) + 0.5

    # ------------------------------------------------------------------
    #  INPUT
    # ------------------------------------------------------------------

    def handle_input(self, event, player):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            return "exit"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()

            for i, item in enumerate(self.stock):
                if self._card_rect(i).collidepoint(mx, my):
                    status, msg         = self._buy(item, player)
                    self.feedback       = msg
                    self.feedback_ok    = (status == "ok")
                    self.feedback_timer = 140
                    return status

            if self._exit_rect().collidepoint(mx, my):
                return "exit"

    # ------------------------------------------------------------------
    #  UPDATE
    # ------------------------------------------------------------------

    def update(self):
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    # ------------------------------------------------------------------
    #  LAYOUT HELPERS
    # ------------------------------------------------------------------

    def _card_rect(self, index):
        col = index % COLS
        row = index // COLS
        x   = PAD + col * (CARD_W + GAP)
        y   = GRID_Y + row * (CARD_H + GAP)
        return pygame.Rect(x, y, CARD_W, CARD_H)

    def _exit_rect(self):
        btn_w = 180
        return pygame.Rect(SCREEN_W // 2 - btn_w // 2, SCREEN_H - 46, btn_w, 36)

    # ------------------------------------------------------------------
    #  DRAW
    # ------------------------------------------------------------------

    def draw(self, screen, player, day_system):
        W, H = screen.get_size()

        # ── Deep background with subtle diagonal stripes ───────────────
        screen.fill((10, 10, 20))
        for i in range(-H, W + H, 36):
            pygame.draw.line(screen, (16, 16, 28),
                             (i, 0), (i + H, H), 14)

        # ── Top bar ───────────────────────────────────────────────────
        pygame.draw.rect(screen, (18, 18, 32), (0, 0, W, TOP_BAR_H))
        pygame.draw.line(screen, (50, 50, 80), (0, TOP_BAR_H), (W, TOP_BAR_H), 1)

        # Balance — left
        screen.blit(self.font_sm.render("BALANCE", True, (90, 90, 90)),        (16, 8))
        screen.blit(self.font_hd.render(f"${player.money}", True, (120, 255, 140)), (16, 26))

        # Title — centre
        title = self.font_title.render("BACK-ROOM DEALER", True, (255, 215, 0))
        screen.blit(title, title.get_rect(center=(W // 2, TOP_BAR_H // 2)))

        # Day + time — right
        tl     = day_system.get_time_seconds()
        tc     = (255, 80, 80) if tl < 20 else (255, 190, 140)
        day_s  = self.font_sm.render(f"DAY {day_system.day}", True, (160, 160, 160))
        time_s = self.font_hd.render(f"{tl}s", True, tc)
        screen.blit(day_s,  day_s.get_rect(topright=(W - 16, 8)))
        screen.blit(time_s, time_s.get_rect(topright=(W - 16, 26)))

        # ── Subtitle ──────────────────────────────────────────────────
        sub = self.font_sm.render(
            "Click a card to purchase   •   TAB = Inventory",
            True, (70, 70, 95)
        )
        screen.blit(sub, sub.get_rect(center=(W // 2, TOP_BAR_H + 26)))

        # ── Item cards ────────────────────────────────────────────────
        mx, my = pygame.mouse.get_pos()
        for i, item in enumerate(self.stock):
            self._draw_card(screen, item, i, player, mx, my)

        # ── Feedback toast ────────────────────────────────────────────
        if self.feedback_timer > 0:
            color = (80, 230, 120) if self.feedback_ok else (255, 90, 90)
            alpha = min(255, self.feedback_timer * 3)

            fs   = self.font.render(self.feedback, True, color)
            pw   = fs.get_width() + 28
            ph   = fs.get_height() + 12
            pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pill.fill((20, 20, 36, min(220, alpha)))
            pygame.draw.rect(pill, (*color, alpha), (0, 0, pw, ph), 2, border_radius=8)
            screen.blit(pill, (W // 2 - pw // 2, SCREEN_H - 90))
            fs.set_alpha(alpha)
            screen.blit(fs, (W // 2 - fs.get_width() // 2, SCREEN_H - 84))

        # ── Exit button ───────────────────────────────────────────────
        exit_r = self._exit_rect()
        hov    = exit_r.collidepoint(mx, my)
        pygame.draw.rect(screen, (55, 55, 80) if hov else (28, 28, 45),
                         exit_r, border_radius=7)
        pygame.draw.rect(screen, (180, 180, 220) if hov else (80, 80, 110),
                         exit_r, 2, border_radius=7)
        el = self.font.render("Leave", True,
                              (230, 230, 255) if hov else (160, 160, 180))
        screen.blit(el, el.get_rect(center=exit_r.center))

    # ------------------------------------------------------------------

    def _draw_card(self, screen, item, index, player, mx, my):
        rect    = self._card_rect(index)
        is_sold = item["sold"]
        can_buy = (not is_sold) and (player.money >= item["cost"])
        hovered = rect.collidepoint(mx, my) and not is_sold

        # Background
        pygame.draw.rect(screen, (20, 20, 28) if is_sold else (26, 26, 44),
                         rect, border_radius=10)

        # Hover highlight
        if hovered:
            hi = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            hi.fill((255, 255, 255, 14))
            screen.blit(hi, rect.topleft)

        # Left accent bar
        accent = (40, 40, 52) if is_sold else item["color"]
        pygame.draw.rect(screen, accent,
                         pygame.Rect(rect.x, rect.y, 5, rect.h),
                         border_radius=4)

        # Border
        if is_sold:
            pygame.draw.rect(screen, (36, 36, 50), rect, 2, border_radius=10)
        elif hovered:
            pygame.draw.rect(screen, (255, 215, 0), rect, 2, border_radius=10)
        elif can_buy:
            b = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(b, (*item["color"], 100),
                             (0, 0, rect.w, rect.h), 2, border_radius=10)
            screen.blit(b, rect.topleft)
        else:
            pygame.draw.rect(screen, (48, 48, 64), rect, 2, border_radius=10)

        tx  = rect.x + 18
        dim = (70, 70, 82)

        # Name
        screen.blit(
            self.font_hd.render(item["name"], True,
                                dim if is_sold else (240, 240, 255)),
            (tx, rect.y + 14)
        )

        # Type badge
        is_perm  = item["type"] == "permanent"
        tag_text = "PERMANENT" if is_perm else "CONSUMABLE"
        tag_col  = dim if is_sold else (
            (80, 220, 140) if is_perm else (255, 195, 70)
        )
        badge    = self.font_sm.render(tag_text, True, tag_col)
        if not is_sold:
            bg_b = pygame.Surface(
                (badge.get_width() + 10, badge.get_height() + 4), pygame.SRCALPHA
            )
            bg_b.fill((*tag_col, 30))
            screen.blit(bg_b, (tx - 2, rect.y + 46))
        screen.blit(badge, (tx, rect.y + 48))

        # Description
        screen.blit(
            self.font_sm.render(item["desc"], True,
                                dim if is_sold else (150, 150, 165)),
            (tx, rect.y + 76)
        )

        # Divider
        pygame.draw.line(screen, (36, 36, 54),
                         (tx, rect.y + 106), (rect.right - 18, rect.y + 106), 1)

        # Price area
        if is_sold:
            screen.blit(self.font.render("SOLD", True, (60, 60, 72)),
                        (tx, rect.y + 116))
        elif not can_buy:
            screen.blit(self.font_hd.render(f"${item['cost']}", True, (120, 120, 135)),
                        (tx, rect.y + 112))
            need = item["cost"] - player.money
            screen.blit(self.font_sm.render(f"Need ${need} more", True, (160, 75, 75)),
                        (tx, rect.y + 142))
        else:
            price_col = (255, 235, 80) if hovered else (255, 215, 0)
            screen.blit(self.font_hd.render(f"${item['cost']}", True, price_col),
                        (tx, rect.y + 112))
            if hovered:
                hs = self.font_sm.render("Click to buy", True, (140, 255, 150))
                screen.blit(hs, (rect.right - hs.get_width() - 14,
                                 rect.y + rect.h - 22))

    # ------------------------------------------------------------------
    #  EFFECT HELPERS
    # ------------------------------------------------------------------

    def is_active(self, effect_name):
        return any(
            slot is not None and slot["effect"] == effect_name
            for slot in self.inventory
        )

    def use(self, effect_name):
        for i, slot in enumerate(self.inventory):
            if slot is not None and slot["effect"] == effect_name:
                self.inventory[i] = None
                return True
        return False

    def activate_hot_streak(self):
        self.hot_streak_count = 3

    def consume_hot_streak(self):
        if self.hot_streak_count > 0:
            self.hot_streak_count -= 1
            return True
        return False