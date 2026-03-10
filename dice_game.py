import pygame
import random

class DiceGame:

    def __init__(self):
        self.bet = 10
        self.bet_input = ""
        self.typing_bet = False

        self.target = 50
        self.mode = "over"

        self.rolling = False
        self.roll_timer = 0
        self.roll_duration = 60

        self.display_number = 0
        self.final_roll = 0

        self.dragging = False

        self.slider_x = 150
        self.slider_y = 420
        self.slider_width = 500

        self.arrow_x = self.slider_x

        self.font_big = pygame.font.SysFont(None, 60)
        self.font = pygame.font.SysFont(None, 36)
        self.small = pygame.font.SysFont(None, 24)

        self.counter_number = 0
        self.roll_history = []

        self.flash_timer = 0
        self.flash_color = None
        self.glow_phase = 0
        self.bar_glow_timer = 0

        self.session_profit = 0

        self.bet_buttons = [
            ("+1000",1000),("+100",100),("+50",50),("+10",10),("+5",5),("+1",1),
            ("-1000",-1000),("-100",-100),("-50",-50),("-10",-10),("-5",-5),("-1",-1)
        ]

        self.quick_bets = ["MIN","HALF","DOUBLE","MAX"]
        self.quick_targets = [10,25,50,75,90]

    def reset(self):
        self.rolling = False
        self.roll_timer = 0
        self.display_number = 0
        self.counter_number = 0
        self.final_roll = 0
        self.dragging = False
        self.typing_bet = False
        self.bet_input = ""
        self.arrow_x = self.slider_x

    # ---------- GAME LOGIC ----------

    def get_win_chance(self):
        if self.mode == "over":
            return max(100 - self.target, 1)
        return max(self.target, 1)

    def get_multiplier(self):
        chance = self.get_win_chance()
        return round(99 / chance, 2)

    def start_roll(self, player):
        # prevent impossible bets
        if self.bet > player.money:
            return False

        if self.bet <= 0:
            self.bet = 1

        self.bar_glow_timer = 0
        self.bet = max(1, min(self.bet, player.money))

        if player.money < self.bet:
            return False

        player.money -= self.bet

        self.rolling = True
        self.roll_timer = 0

        self.display_number = 0
        self.counter_number = 0

        self.final_roll = random.randint(0,100)

        return True

    def resolve_roll(self, player, score_system, messages):
        self.roll_history.insert(0, self.final_roll)
        self.bar_glow_timer = 120
        if len(self.roll_history) > 10:
            self.roll_history.pop()

        win = False

        if self.mode == "over" and self.final_roll > self.target:
            win = True

        if self.mode == "under" and self.final_roll < self.target:
            win = True

        if win:

            mult = self.get_multiplier()
            winnings = int(self.bet * mult)

            player.money += winnings
            score_system.add_money_score(winnings)

            self.session_profit += winnings - self.bet

            messages.add(f"WIN ${winnings}", player.x, player.y)
            self.flash_color = (80,255,120)
            self.flash_timer = 25

        else:
            self.session_profit -= self.bet
            messages.add("Lost bet", player.x, player.y)
            self.flash_color = (255,80,80)
            self.flash_timer = 25

    # ---------- INPUT ----------

    def handle_input(self, event, player, score_system, messages):
        if event.type == pygame.MOUSEBUTTONDOWN:

            mx,my = pygame.mouse.get_pos()

            slider = pygame.Rect(self.slider_x,self.slider_y,self.slider_width,12)

            if slider.collidepoint(mx,my):
                self.dragging = True

            bet_box = pygame.Rect(340,200,120,40)

            if bet_box.collidepoint(mx,my):
                self.typing_bet = True
                self.bet_input = ""

            bx,by = 150,470

            for i,(text,val) in enumerate(self.bet_buttons):

                rect = pygame.Rect(bx+(i%6)*80, by+(i//6)*40, 70,30)

                if rect.collidepoint(mx,my):
                    self.bet = max(1, min(player.money, self.bet + val))

            qx,qy = 150,440

            for text in self.quick_bets:

                rect = pygame.Rect(qx,qy,80,25)

                if rect.collidepoint(mx,my):

                    if text == "MIN":
                        self.bet = 1

                    elif text == "HALF":
                        self.bet = max(1,self.bet//2)

                    elif text == "DOUBLE":
                        self.bet = min(player.money,self.bet*2)

                    elif text == "MAX":
                        self.bet = player.money

                qx += 90

            tx,ty = 150,390

            for val in self.quick_targets:

                rect = pygame.Rect(tx,ty,60,25)

                if rect.collidepoint(mx,my):
                    self.target = val

                tx += 70

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:

            mx = pygame.mouse.get_pos()[0]

            pos = (mx-self.slider_x)/self.slider_width
            pos = max(0,min(1,pos))

            self.target = int(pos*100)

        if event.type == pygame.KEYDOWN:

            if self.typing_bet:

                if event.key == pygame.K_RETURN:
                    if self.bet_input != "":
                        typed_bet = int(self.bet_input)
                        self.bet = max(1, min(player.money, typed_bet))
                    self.typing_bet = False

                elif event.key == pygame.K_BACKSPACE:
                    self.bet_input = self.bet_input[:-1]

                elif event.unicode.isdigit():
                    self.bet_input += event.unicode

                return

            if event.key == pygame.K_m and not self.rolling:
                self.mode = "under" if self.mode=="over" else "over"

            if event.key == pygame.K_SPACE and not self.rolling:

                started = self.start_roll(player)

                if not started:
                    messages.add("Not enough money", player.x, player.y)

            if event.key == pygame.K_RETURN and not self.rolling:
                return "exit"

    # ---------- UPDATE ----------

    def update(self, player, score_system, messages):

        # --- timers should always run ---
        if self.bar_glow_timer > 0:
            self.bar_glow_timer -= 1

        if self.flash_timer > 0:
            self.flash_timer -= 1

        # glow animation phase
        if self.rolling:
            self.glow_phase += 0.25


        # --- stop here if not rolling ---
        if not self.rolling:
            return


        # --- roll animation ---
        self.roll_timer += 1

        if self.roll_timer < self.roll_duration:

            progress = self.roll_timer / self.roll_duration
            ease = progress * progress * (3 - 2 * progress)

            target_value = int(self.final_roll * ease)

            if self.counter_number < target_value:
                self.counter_number += max(1, (target_value - self.counter_number) // 3)

            self.display_number = self.counter_number
            self.arrow_x = self.slider_x + (self.display_number / 100) * self.slider_width

        else:

            # roll finished
            self.rolling = False
            self.display_number = self.final_roll
            self.arrow_x = self.slider_x + (self.final_roll / 100) * self.slider_width

            self.resolve_roll(player, score_system, messages)

    # ---------- DRAW ----------

    def draw_probability_bar(self, screen):

        # determine color
        if self.bar_glow_timer > 0:
            fade = self.bar_glow_timer / 120
            glow = int(80 * fade)
            green_color = (60, min(255, 200 + glow), 80)
        else:
            green_color = (60, 200, 80)

        if self.mode == "over":

            lose = (self.target / 100) * self.slider_width
            win = self.slider_width - lose

            pygame.draw.rect(
                screen,
                (180, 60, 60),
                (self.slider_x, self.slider_y, lose, 12)
            )

            pygame.draw.rect(
                screen,
                green_color,
                (self.slider_x + lose, self.slider_y, win, 12)
            )

        else:

            win = (self.target / 100) * self.slider_width
            lose = self.slider_width - win

            pygame.draw.rect(
                screen,
                green_color,
                (self.slider_x, self.slider_y, win, 12)
            )

            pygame.draw.rect(
                screen,
                (180, 60, 60),
                (self.slider_x + win, self.slider_y, lose, 12)
            )

        # slider knob
        knob = self.slider_x + (self.target / 100) * self.slider_width
        pygame.draw.circle(screen, (255,220,0), (int(knob), self.slider_y + 6), 10)

        # result marker
        if not self.rolling and self.final_roll != 0:
            result_x = self.slider_x + (self.final_roll / 100) * self.slider_width
            pygame.draw.circle(screen, (255,255,255), (int(result_x), self.slider_y + 6), 6)

    def draw_arrow(self,screen):
        pygame.draw.polygon(screen,(255,255,0),[
            (self.arrow_x,380),
            (self.arrow_x-8,400),
            (self.arrow_x+8,400)
        ])

    def draw_history(self, screen):
        title = self.small.render("ROLL HISTORY", True, (200,200,200))
        screen.blit(title, (320, 20))

        x = 250
        y = 50

        for roll in self.roll_history:

            rect = pygame.Rect(x, y, 40, 30)

            pygame.draw.rect(screen,(40,40,40),rect)
            pygame.draw.rect(screen,(100,100,100),rect,2)

            num = self.small.render(str(roll), True, (255,255,255))
            screen.blit(num,(rect.x+10, rect.y+5))

            x += 45

    def draw_bet_buttons(self,screen):
        bx,by = 150,470

        for i,(text,val) in enumerate(self.bet_buttons):

            rect = pygame.Rect(bx+(i%6)*80, by+(i//6)*40,70,30)

            pygame.draw.rect(screen,(70,70,70),rect)
            pygame.draw.rect(screen,(120,120,120),rect,2)

            t = self.small.render(text,True,(255,255,255))
            screen.blit(t,(rect.x+10,rect.y+5))

    def draw_quick_bets(self, screen):
        x = 150
        y = 440

        for text in self.quick_bets:

            rect = pygame.Rect(x,y,80,25)

            pygame.draw.rect(screen,(60,60,60),rect)
            pygame.draw.rect(screen,(120,120,120),rect,2)

            label = self.small.render(text,True,(255,255,255))
            screen.blit(label,(rect.x+10,rect.y+4))

            x += 90

    def draw_target_buttons(self, screen):
        x = 150
        y = 390

        for val in self.quick_targets:

            rect = pygame.Rect(x,y,60,25)

            pygame.draw.rect(screen,(60,60,60),rect)
            pygame.draw.rect(screen,(120,120,120),rect,2)

            label = self.small.render(str(val),True,(255,255,255))
            screen.blit(label,(rect.x+20,rect.y+4))

            x += 70

    def draw(self, screen, player, day_system):
        screen.fill((18,18,18))

        balance = self.font.render(f"BALANCE: ${player.money}", True, (200,255,200))
        screen.blit(balance,(20,20))

        day = self.font.render(f"DAY: {day_system.day}",True,(255,255,255))
        screen.blit(day,(20,60))

        time_left = day_system.get_time_seconds()
        timer = self.font.render(f"CLOSING IN: {time_left}",True,(255,180,180))
        screen.blit(timer,(20,100))

        profit_color = (100,255,100) if self.session_profit >= 0 else (255,100,100)
        profit = self.font.render(f"SESSION: {self.session_profit}",True,profit_color)
        screen.blit(profit,(20,140))

        title = self.font_big.render("DICE",True,(255,255,255))
        screen.blit(title,(350,60))

        self.draw_history(screen)

        mode = self.font.render(f"MODE: {self.mode.upper()}",True,(200,200,200))
        screen.blit(mode,(340,140))

        target = self.font.render(f"TARGET: {self.target}",True,(255,220,0))
        screen.blit(target,(350,180))

        bet_box = pygame.Rect(340,200,120,40)

        pygame.draw.rect(screen,(50,50,50),bet_box)
        pygame.draw.rect(screen,(150,150,150),bet_box,2)

        bet_display = self.bet_input if self.typing_bet else str(self.bet)

        bet_text = self.font.render(bet_display,True,(255,255,255))
        screen.blit(bet_text,(bet_box.x+10,bet_box.y+5))

        chance = self.get_win_chance()
        chance_text = self.font.render(f"WIN CHANCE {chance}%",True,(200,255,200))
        screen.blit(chance_text,(300,260))

        mult = self.get_multiplier()
        mult_text = self.font.render(f"MULTIPLIER {mult}x",True,(150,255,150))
        screen.blit(mult_text,(320,300))

        roll_text = self.font_big.render(str(self.display_number),True,(255,200,200))
        screen.blit(roll_text,(360,330))

        self.draw_target_buttons(screen)
        self.draw_arrow(screen)
        self.draw_probability_bar(screen)
        self.draw_quick_bets(screen)
        self.draw_bet_buttons(screen)

        if self.rolling:
            txt = self.small.render("Rolling...",True,(255,200,200))
        else:
            txt = self.small.render("SPACE = Roll | ENTER = Exit",True,(180,180,180))

        screen.blit(txt,(300,550))

        if self.flash_timer > 0 and self.flash_color:

            flash_surface = pygame.Surface((screen.get_width(), screen.get_height()))
            flash_surface.set_alpha(60)
            flash_surface.fill(self.flash_color)

            screen.blit(flash_surface,(0,0))