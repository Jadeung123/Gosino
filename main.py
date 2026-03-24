# main.py
# Entry point. The Game class owns the loop and delegates
# everything to the systems. It does not contain gameplay logic.

import pygame
import random
import sys

from constants import *
from player import Player
from map import CasinoMap
from slot_machine import SlotMachine
from shop import Shop
from guard import Guard
from roulette import Roulette
from dice_game import DiceGame
from case_opening import CaseOpening
from score_system import ScoreSystem
from message_system import MessageSystem
from day_system import DaySystem
from upgrade_manager import UpgradeManager
from title_screen import TitleScreen
from inventory_panel import InventoryPanel
from blackjack import Blackjack


class Game:
    """
    Top-level controller.
    Owns the main loop and routes between game states.
    All gameplay logic lives in the imported system classes.
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock  = pygame.time.Clock()
        self.font   = pygame.font.SysFont(None, 30)
        self.font_sm = pygame.font.SysFont(None, 26)

        self.running = True
        self.state   = STATE_TITLE
        self._settings_return_state = STATE_TITLE

        self.title_screen = TitleScreen()   # created once — persists across restarts
        self._init_systems()
        self._init_guards()

    # ------------------------------------------------------------------
    def _init_systems(self):
        """Create every game system. Called once at startup and on restart."""
        self.player          = Player(400, 300)
        self.casino_map      = CasinoMap()
        self.slot_machine    = SlotMachine()
        self.shop            = Shop()
        self.roulette        = Roulette()
        self.dice_game       = DiceGame()
        self.case_opening    = CaseOpening()
        self.blackjack       = Blackjack()
        self.score_system    = ScoreSystem()
        self.messages        = MessageSystem()
        self.day_system      = DaySystem()
        self.upgrade_manager = UpgradeManager()
        self.inventory_panel = InventoryPanel()

    def _init_guards(self):
        """Spawn the starting guards and reset the difficulty timer."""
        self.guards = [
            Guard(300, 200, random.choice(GUARD_TYPES)),
            Guard(500, 400, random.choice(GUARD_TYPES)),
            Guard(700, 250, random.choice(GUARD_TYPES)),
        ]
        self.difficulty       = 1
        self.difficulty_timer = 0

    def _restart(self):
        """Full game restart — recreate all systems and guards."""
        self._init_systems()
        self._init_guards()
        self.state = STATE_EXPLORE

    # ==================================================================
    #  MAIN LOOP
    # ==================================================================

    def run(self):
        """Called once. Runs until self.running is False."""
        while self.running:
            self.clock.tick(FPS)
            self._update_systems()
            self._handle_events()
            self._update_state()
            self._draw()

    # ------------------------------------------------------------------
    def _update_systems(self):
        """Tick every system that runs regardless of game state."""
        # Freeze all systems when paused, on title, or game over
        if self.state in (STATE_GAME_OVER, STATE_MENU, STATE_TITLE):
            return

        self.messages.update()
        self.day_system.update()
        self.casino_map.update_cooldowns()
        self.inventory_panel.update()

        if self.day_system.closing and not self.day_system.warned:
            self.messages.add_ui("CASINO CLOSING! GUARDS ALERT!")
            self.day_system.warned = True

    # ==================================================================
    #  EVENT HANDLING
    # ==================================================================

    def _handle_events(self):
        """Read Pygame's event queue and route to the active state."""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False
                return

            # --- Title screen ---
            if self.state == STATE_TITLE:
                result = self.title_screen.handle_input(event, self.screen)
                if result == "play":
                    self.state = STATE_EXPLORE
                elif result == "quit":
                    self.running = False
                elif result == "back_to_game":
                    self.state = self._settings_return_state  # ← go back to wherever we came from
                continue

            # --- Game over screen ---
            if self.state == STATE_GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if self._game_over_restart_rect().collidepoint(mx, my):
                        self._restart()
                    elif self._game_over_menu_rect().collidepoint(mx, my):
                        self._init_systems()
                        self._init_guards()
                        self.state = STATE_TITLE
                return

            # --- Global F-key hotkeys (work in every in-game state) ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self._activate_consumable(0)
                elif event.key == pygame.K_F2:
                    self._activate_consumable(1)
                elif event.key == pygame.K_F3:
                    self._activate_consumable(2)

            # --- ESC toggles menu during explore ---
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                if self.state in (STATE_EXPLORE, STATE_SLOTS, STATE_DICE, STATE_CASE, STATE_ROULETTE, STATE_BLACKJACK, STATE_SHOP):
                    self.inventory_panel.toggle()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.inventory_panel.is_open():
                    self.inventory_panel.close()
                elif self.state == STATE_MENU:
                    self.state = STATE_EXPLORE
                elif self.state == STATE_EXPLORE:
                    self.state = STATE_MENU

            # --- Route to active state handler ---
            if self.state == STATE_DICE:
                self._events_dice(event)
            elif self.state == STATE_ROULETTE:
                self._events_roulette(event)
            elif self.state == STATE_SLOTS:
                self._events_slots(event)
            elif self.state == STATE_CASE:
                self._events_case(event)
            elif self.state == STATE_BLACKJACK:
                self._events_blackjack(event)
            elif self.state == STATE_SHOP:
                self._events_shop(event)
            elif self.state == STATE_UPGRADE:
                self._events_upgrade(event)
            elif self.state == STATE_EXPLORE:
                self._events_explore(event)
            elif self.state == STATE_MENU:
                self._events_menu(event)

    # ------------------------------------------------------------------

    def _events_dice(self, event):
        # Block spinning while on cooldown
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
                and self.casino_map.cooldowns["dice"] > 0):
            self.messages.add_ui(f"Dice cooling down!")
            return

        self.dice_game._shop_ref = self.shop
        result = self.dice_game.handle_input(
            event, self.player, self.score_system, self.messages
        )
        if result == "exit":
            self.dice_game.reset()
            self.state = STATE_EXPLORE
        elif result == "played":
            reduction = getattr(self.player, "cooldown_reduction", 0.0)
            self.casino_map.cooldowns["dice"] = int(240 * (1 - reduction))

    def _events_roulette(self, event):
        # Block spinning while on cooldown
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
                and self.casino_map.cooldowns["roulette"] > 0):
            self.messages.add_ui(f"Roulette cooling down!")
            return

        self.roulette._shop_ref = self.shop
        result = self.roulette.handle_input(
            event, self.player, self.score_system, self.messages
        )
        if result == "exit":
            self.roulette.reset()
            self.state = STATE_EXPLORE
        elif result == "played":
            reduction = getattr(self.player, "cooldown_reduction", 0.0)
            self.casino_map.cooldowns["roulette"] = int(360 * (1 - reduction))

    def _events_slots(self, event):
        # Block spinning while on cooldown
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
                and self.slot_machine.phase == "betting"
                and self.casino_map.cooldowns["slots"] > 0):
            self.messages.add_ui(f"Slots cooling down!")
            return

        self.slot_machine._shop_ref = self.shop
        result = self.slot_machine.handle_input(
            event, self.player, self.score_system, self.messages, self.shop
        )
        if result == "exit":
            self.slot_machine.reset()
            self.state = STATE_EXPLORE
        elif result == "played":
            reduction = getattr(self.player, "cooldown_reduction", 0.0)
            self.casino_map.cooldowns["slots"] = int(300 * (1 - reduction))

    def _events_case(self, event):
        # Block spin while cooling down
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
                and self.casino_map.cooldowns["case"] > 0):
            self.messages.add_ui("Case table cooling down!")
            return

        result = self.case_opening.handle_input(
            event, self.player, self.score_system, self.messages, self.shop
        )
        if result == "exit":
            self.case_opening.reset()
            self.state = STATE_EXPLORE

    def _events_blackjack(self, event):
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
                and self.blackjack.phase == "betting"
                and self.casino_map.cooldowns["blackjack"] > 0):
            self.messages.add_ui("Blackjack table cooling down!")
            return
        result = self.blackjack.handle_input(
            event, self.player, self.score_system, self.messages, self.shop
        )
        if result == "exit":
            self.blackjack.reset()
            self.state = STATE_EXPLORE

    def _events_shop(self, event):
        result = self.shop.handle_input(event, self.player)
        if result == "exit":
            self.state = STATE_EXPLORE

    def _events_upgrade(self, event):
        """Mouse-clickable upgrade screen."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()

            # Upgrade cards
            for i in range(len(self.upgrade_manager.current_choices)):
                if self._upgrade_card_rect(i).collidepoint(mx, my):
                    self.upgrade_manager.buy_upgrade(i, self.player, self.day_system)

            # Reroll button
            if self._upgrade_reroll_rect().collidepoint(mx, my):
                self.upgrade_manager.reroll(self.player)

            # Next day button
            if self._upgrade_next_rect().collidepoint(mx, my):
                self.day_system.next_day(debt_reduction=self.player.debt_reduction)
                if self.player.daily_bonus > 0:
                    self.player.money += self.player.daily_bonus
                    self.messages.add_ui(f"Daily bonus: +${self.player.daily_bonus}!")
                self.shop.roll_stock()
                for guard in self.guards:
                    guard.reset()
                self.messages.add_ui("New Day Started!")
                self.state = STATE_EXPLORE

    def _events_explore(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_e:
            self._handle_interaction()

    def _events_menu(self, event):
        """Handle clicks inside the ESC pause menu."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if self._menu_resume_rect().collidepoint(mx, my):
                self.state = STATE_EXPLORE
            elif self._menu_main_menu_rect().collidepoint(mx, my):
                self._init_systems()
                self._init_guards()
                self.state = STATE_TITLE
            elif self._menu_settings_rect().collidepoint(mx, my):
                self._settings_return_state = STATE_EXPLORE  # ← remember where to go back
                self.title_screen._current = "settings"
                self.state = STATE_TITLE

    # ------------------------------------------------------------------

    def _handle_interaction(self):
        zone = self.casino_map.check_interaction(self.player.get_rect())
        reduction = getattr(self.player, "cooldown_reduction", 0.0)

        if zone == "slots":
            self.slot_machine.reset()
            self.state = STATE_SLOTS

        elif zone == "roulette":
            self.state = STATE_ROULETTE

        elif zone == "dice":
            self.dice_game.reset()
            self.state = STATE_DICE

        elif zone == "case":
            self.case_opening.reset()
            self.state = STATE_CASE

        elif zone == "blackjack":
            self.blackjack.reset()
            self.state = STATE_BLACKJACK

        elif zone == "shop":
            self.state = STATE_SHOP

        elif zone == "exit":
            self._handle_exit()

    def _handle_exit(self):
        if self.player.money >= self.day_system.debt:
            self.player.money -= self.day_system.debt
            self.messages.add_ui("Debt Paid! Day Complete!")
            self.upgrade_manager.roll_upgrades()
            self.state = STATE_UPGRADE
        else:
            self.state = STATE_GAME_OVER

    def _activate_consumable(self, slot_index):
        item = self.shop.inventory[slot_index]
        if item is None:
            self.messages.add_ui("Slot empty!")
            return
        effect = item["effect"]
        if effect == "hot_streak":
            self.shop.use("hot_streak")
            self.shop.activate_hot_streak()
            self.messages.add_ui("Hot Streak! Next 3 gambles pay double!")
            return
        self.messages.add_ui(f"{item['name']} ready! Auto-triggers next gamble.")

    # ==================================================================
    #  STATE UPDATE
    # ==================================================================

    def _update_state(self):
        if self.state == STATE_TITLE:
            self.title_screen.update()

        elif self.state == STATE_SLOTS:
            self.slot_machine.update(
                self.player, self.score_system, self.messages, self.shop
            )

        elif self.state == STATE_ROULETTE:
            self.roulette.update(self.player, self.score_system, self.shop)

        elif self.state == STATE_DICE:
            self.dice_game.update(self.player, self.score_system, self.messages)

        elif self.state == STATE_CASE:
            result = self.case_opening.update(
                self.player, self.score_system, self.messages, self.shop
            )
            if result == "result_ready":
                reduction = getattr(self.player, "cooldown_reduction", 0.0)
                self.casino_map.cooldowns["case"] = int(180 * (1 - reduction))


        elif self.state == STATE_BLACKJACK:
            self.blackjack.update(
                self.player, self.score_system, self.messages, self.shop
            )
            # Check if round just ended this frame
            if self.blackjack.phase == "result" and self.casino_map.cooldowns["blackjack"] == 0:
                reduction = getattr(self.player, "cooldown_reduction", 0.0)
                self.casino_map.cooldowns["blackjack"] = int(240 * (1 - reduction))

        elif self.state == STATE_SHOP:
            self.shop.update()

        elif self.state == STATE_EXPLORE:
            self._update_explore()

    def _update_explore(self):
        keys = pygame.key.get_pressed()
        self.player.move(keys, walls=self.casino_map.walls)

        # Adrenaline upgrade — speed boost during closing
        adrenaline = getattr(self.player, "adrenaline_bonus", 0)
        if adrenaline > 0:
            if self.day_system.closing:
                self.player.speed = self.player.base_speed + adrenaline
            else:
                self.player.speed = self.player.base_speed

        self._update_difficulty()
        self._update_guards()

    def _update_difficulty(self):
        self.difficulty_timer += 1
        if self.difficulty_timer >= DIFFICULTY_INTERVAL:
            self.difficulty       += 1
            self.difficulty_timer  = 0

            self.messages.add_ui("Guards are getting faster!")

            for guard in self.guards:
                guard.update_speed(self.difficulty)
            self.guards.append(Guard(
                random.randint(100, 700),
                random.randint(100, 500),
                "elite"
            ))

    def _update_guards(self):
        for guard in self.guards:
            if self.day_system.closing:
                guard.start_closing_chase(self.player)
                guard.chase_player(self.player)
            else:
                guard.see_player(self.player, self.guards, self.messages)
                if guard.state == "chase":
                    guard.chase_player(self.player)
                else:
                    guard.move(walls=self.casino_map.walls)

            if self.player.get_rect().colliderect(
                pygame.Rect(guard.x, guard.y, 32, 32)
            ):
                self.state = STATE_GAME_OVER

    # ==================================================================
    #  DRAWING
    # ==================================================================

    def _draw(self):
        """Master draw — routes to the correct screen."""

        if self.state == STATE_TITLE:
            self.title_screen.draw(self.screen)
            pygame.display.update()
            return

        if self.state == STATE_GAME_OVER:
            self._draw_game_over()
            pygame.display.update()
            return

        if self.state == STATE_DICE:
            self.dice_game.draw(self.screen, self.player, self.day_system)
            self.inventory_panel.draw(
                self.screen, self.player, self.shop, self.upgrade_manager
            )
            self.messages.draw_ui(self.screen)
            pygame.display.update()
            return

        if self.state == STATE_ROULETTE:
            self.roulette.draw(self.screen, self.player, self.day_system)
            self.inventory_panel.draw(
                self.screen, self.player, self.shop, self.upgrade_manager
            )
            self.messages.draw_ui(self.screen)
            pygame.display.update()
            return

        if self.state == STATE_SLOTS:
            self.slot_machine.draw(self.screen, self.player, self.day_system)
            self.inventory_panel.draw(
                self.screen, self.player, self.shop, self.upgrade_manager
            )
            self.messages.draw_ui(self.screen)
            pygame.display.update()
            return

        if self.state == STATE_CASE:
            self.case_opening.draw(self.screen, self.player, self.day_system)
            self.inventory_panel.draw(
                self.screen, self.player, self.shop, self.upgrade_manager
            )
            self.messages.draw_ui(self.screen)
            pygame.display.update()
            return

        if self.state == STATE_BLACKJACK:
            self.blackjack.draw(self.screen, self.player, self.day_system)
            self.inventory_panel.draw(
                self.screen, self.player, self.shop, self.upgrade_manager
            )
            self.messages.draw_ui(self.screen)
            pygame.display.update()
            return

        if self.state == STATE_SHOP:
            self.shop.draw(self.screen, self.player, self.day_system)
            self.inventory_panel.draw(
                self.screen, self.player, self.shop, self.upgrade_manager
            )
            self.messages.draw_ui(self.screen)
            pygame.display.update()
            return

        # --- Base world (explore / menu / upgrade drawn on top) ---
        self._draw_world()

        if self.state == STATE_UPGRADE:
            self._draw_upgrade_screen()
        elif self.state == STATE_MENU:
            self._draw_menu_overlay()

        self.messages.draw_ui(self.screen)

        if self.title_screen.show_fps:
            fps_surf = self.font_sm.render(
                f"FPS: {int(self.clock.get_fps())}", True, (100, 100, 100)
            )
            self.screen.blit(fps_surf, (SCREEN_WIDTH - 70, 8))

        pygame.display.update()

    # ------------------------------------------------------------------

    def _draw_world(self):
        """Draw the casino floor, guards, player, and HUD."""
        self.screen.fill(GREEN)
        self.casino_map.draw(self.screen)

        for guard in self.guards:
            guard.draw_vision(self.screen, self.player)

        self.player.draw(self.screen)

        for guard in self.guards:
            guard.draw(self.screen)
            guard.draw_detection(self.screen)

        self.messages.draw_world(self.screen)
        self._draw_hud()
        self.inventory_panel.draw(
            self.screen, self.player, self.shop, self.upgrade_manager
        )

    def _draw_hud(self):
        """Top-right HUD: day, timer, debt, money."""
        time_left = self.day_system.get_time_seconds()

        items = [
            (f"Day: {self.day_system.day}",         WHITE,          10),
            (f"Time: {time_left}s",                 (255, 200, 200), 35),
            (f"Debt: ${self.day_system.debt}",      (255, 150, 150), 60),
            (f"Money: ${self.player.money}",        (200, 255, 150), 85),
            (f"Score: {int(self.score_system.score)}", WHITE,        110),
        ]
        for text, color, y in items:
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (SCREEN_WIDTH - surf.get_width() - 10, y))

        # Cooldown indicators — only show if active
        cd = self.casino_map.cooldowns
        labels = []
        if cd["slots"] > 0: labels.append(f"Slots:    {cd['slots'] // 60 + 1}s")
        if cd["roulette"] > 0: labels.append(f"Roulette: {cd['roulette'] // 60 + 1}s")
        if cd["dice"] > 0: labels.append(f"Dice:     {cd['dice'] // 60 + 1}s")
        if cd["case"] > 0: labels.append(f"Cases:    {cd['case'] // 60 + 1}s")
        if cd.get("blackjack", 0) > 0: labels.append(f"Blackjack: {cd['blackjack'] // 60 + 1}s")

        for i, label in enumerate(labels):
            surf = self.font_sm.render(label, True, (180, 140, 80))
            self.screen.blit(surf, (10, 140 + i * 22))

    # ------------------------------------------------------------------
    #  UPGRADE SCREEN
    # ------------------------------------------------------------------

    def _upgrade_card_rect(self, index):
        return pygame.Rect(160, 190 + index * 95, 480, 82)

    def _upgrade_reroll_rect(self):
        return pygame.Rect(160, 490, 220, 44)

    def _upgrade_next_rect(self):
        return pygame.Rect(420, 490, 220, 44)

    def _draw_upgrade_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        font_hd = pygame.font.SysFont(None, 44)
        font    = self.font
        font_sm = self.font_sm

        title = font_hd.render("CHOOSE AN UPGRADE", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 148)))

        mx, my = pygame.mouse.get_pos()

        for i, upgrade in enumerate(self.upgrade_manager.current_choices):
            rect    = self._upgrade_card_rect(i)
            name    = upgrade["name"]
            level   = self.upgrade_manager.levels.get(name, 0)
            max_level = upgrade.get("max_level", 99)
            bought  = upgrade.get("bought", False)
            is_capped = level >= max_level
            hovered = rect.collidepoint(mx, my) and not bought

            if is_capped:
                tag = f"  [MAX LEVEL {level}/{max_level}]"
            elif bought:
                tag = " [PURCHASED]"
            else:
                tag = f"  Lv{level} -> Lv{level + 1}"

            # Card background
            bg = (45, 55, 35) if hovered and not bought else (30, 30, 30)
            if bought:
                bg = (20, 40, 20)
            pygame.draw.rect(self.screen, bg, rect, border_radius=8)

            border = GOLD if hovered else (
                (60, 160, 60) if bought else (70, 70, 90)
            )
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)

            # Text
            name_color = (255, 160, 60) if is_capped else (160, 255, 160) if bought else (255, 255, 200)
            self.screen.blit(
                font.render(f"{name}{tag}", True, name_color),
                (rect.x + 14, rect.y + 10)
            )
            self.screen.blit(
                font_sm.render(upgrade["desc"], True, (180, 180, 180)),
                (rect.x + 14, rect.y + 38)
            )
            cost_color = (120, 120, 120) if bought else GOLD
            cost_surf = font.render(f"${upgrade['cost']}", True, cost_color)
            self.screen.blit(cost_surf, (rect.right - cost_surf.get_width() - 14, rect.y + 10))

        # Reroll button
        rr = self._upgrade_reroll_rect()
        rr_hov = rr.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (50, 50, 80) if rr_hov else (30, 30, 50), rr, border_radius=7)
        pygame.draw.rect(self.screen, (150, 150, 200), rr, 2, border_radius=7)
        rr_label = font.render(f"Reroll  ${self.upgrade_manager.reroll_cost}", True, (200, 200, 255))
        self.screen.blit(rr_label, rr_label.get_rect(center=rr.center))

        # Next day button
        nd = self._upgrade_next_rect()
        nd_hov = nd.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (30, 80, 30) if nd_hov else (20, 55, 20), nd, border_radius=7)
        pygame.draw.rect(self.screen, (80, 200, 80), nd, 2, border_radius=7)
        nd_label = font.render("Next Day  >>", True, (150, 255, 150))
        self.screen.blit(nd_label, nd_label.get_rect(center=nd.center))

    # ------------------------------------------------------------------
    #  PAUSE MENU
    # ------------------------------------------------------------------

    def _menu_resume_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 250, 380, 220, 46)

    def _menu_main_menu_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 250, 440, 220, 46)

    def _menu_settings_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 250, 500, 220, 46)

    def _draw_menu_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(210)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        font_hd = pygame.font.SysFont(None, 44)
        font    = self.font
        font_sm = self.font_sm
        mx, my  = pygame.mouse.get_pos()

        # Title
        title = font_hd.render("PAUSED", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 90)))

        pygame.draw.line(self.screen, (60, 60, 80),
                         (160, 120), (640, 120), 1)

        # Two-column stats
        col1 = [
            ("Day",     str(self.day_system.day)),
            ("Money",   f"${self.player.money}"),
            ("Debt",    f"${self.day_system.debt}"),
            ("Score",   str(int(self.score_system.score))),
        ]
        col2 = [
            ("Speed",   str(self.player.speed)),
            ("Luck",    str(self.player.luck)),
            ("Stealth", str(self.player.stealth)),
        ]

        y = 138
        for label, value in col1:
            self.screen.blit(font.render(f"{label}: {value}", True, WHITE), (175, y))
            y += 28

        y = 138
        for label, value in col2:
            self.screen.blit(font.render(f"{label}: {value}", True, WHITE), (430, y))
            y += 28

        pygame.draw.line(self.screen, (60, 60, 80),
                         (160, 258), (640, 258), 1)

        # Owned upgrades
        self.screen.blit(font_sm.render("UPGRADES:", True, (160, 160, 160)), (175, 268))
        if self.upgrade_manager.levels:
            ux, uy = 175, 290
            for name, level in self.upgrade_manager.levels.items():
                surf = font_sm.render(f"{name} Lv{level}", True, (180, 255, 180))
                if ux + surf.get_width() > 540:
                    ux = 175
                    uy += 22
                self.screen.blit(surf, (ux, uy))
                ux += surf.get_width() + 18
        else:
            self.screen.blit(font_sm.render("None yet", True, (80, 80, 80)), (175, 290))

        # Buttons (right side so they don't overlap upgrades)
        buttons = [
            (self._menu_resume_rect(),    "Resume",    (40, 80, 40),  (80, 200, 80)),
            (self._menu_main_menu_rect(), "Main Menu", (60, 60, 100), (120, 120, 200)),
            (self._menu_settings_rect(),  "Settings",  (60, 40, 80),  (140, 80, 180)),
        ]
        for rect, label, bg, border in buttons:
            hov = rect.collidepoint(mx, my)
            draw_bg = tuple(min(255, c + 25) for c in bg) if hov else bg
            pygame.draw.rect(self.screen, draw_bg, rect, border_radius=7)
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=7)
            surf = font.render(label, True, WHITE)
            self.screen.blit(surf, surf.get_rect(center=rect.center))

    # ------------------------------------------------------------------
    #  GAME OVER
    # ------------------------------------------------------------------

    def _game_over_restart_rect(self):
        return pygame.Rect(SCREEN_WIDTH // 2 - 220, 460, 190, 48)

    def _game_over_menu_rect(self):
        return pygame.Rect(SCREEN_WIDTH // 2 + 30, 460, 190, 48)

    def _draw_game_over(self):
        self.screen.fill((8, 8, 15))

        font_big = pygame.font.SysFont(None, 90)
        font_hd  = pygame.font.SysFont(None, 42)
        font     = self.font
        font_sm  = self.font_sm
        mx, my   = pygame.mouse.get_pos()

        # Title
        title = font_big.render("GAME OVER", True, RED)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 95)))

        pygame.draw.line(self.screen, (80, 30, 30), (150, 150), (650, 150), 2)

        # Summary
        hd = font_hd.render("RUN SUMMARY", True, GOLD)
        self.screen.blit(hd, hd.get_rect(center=(SCREEN_WIDTH // 2, 180)))

        summary = [
            ("Days Survived",  str(self.day_system.day)),
            ("Final Score",    str(int(self.score_system.score))),
            ("Money Left",     f"${self.player.money}"),
            ("Debt at end",    f"${self.day_system.debt}"),
        ]
        y = 216
        for label, value in summary:
            row = font.render(f"{label:<22}{value}", True, WHITE)
            self.screen.blit(row, row.get_rect(center=(SCREEN_WIDTH // 2, y)))
            y += 30

        pygame.draw.line(self.screen, (60, 60, 80), (150, y + 6), (650, y + 6), 1)
        y += 22

        # Upgrades
        hd2 = font_hd.render("UPGRADES EARNED", True, (180, 255, 180))
        self.screen.blit(hd2, hd2.get_rect(center=(SCREEN_WIDTH // 2, y)))
        y += 34

        if self.upgrade_manager.levels:
            for name, level in self.upgrade_manager.levels.items():
                line = font_sm.render(f"  {name}   Lv{level}", True, (160, 220, 160))
                self.screen.blit(line, line.get_rect(center=(SCREEN_WIDTH // 2, y)))
                y += 24
        else:
            none = font_sm.render("No upgrades purchased", True, (80, 80, 80))
            self.screen.blit(none, none.get_rect(center=(SCREEN_WIDTH // 2, y)))

        # Buttons
        buttons = [
            (self._game_over_restart_rect(), "Play Again",  (30, 80, 30),  (80, 200, 80)),
            (self._game_over_menu_rect(),    "Main Menu",   (40, 40, 100), (100, 100, 200)),
        ]
        for rect, label, bg, border in buttons:
            hov = rect.collidepoint(mx, my)
            draw_bg = tuple(min(255, c + 30) for c in bg) if hov else bg
            pygame.draw.rect(self.screen, draw_bg, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)
            surf = font.render(label, True, WHITE)
            self.screen.blit(surf, surf.get_rect(center=rect.center))


# ----------------------------------------------------------------------
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()