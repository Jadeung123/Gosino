import pygame
import random
from player import Player
from map import CasinoMap
from time_system import TimeSystem
from slot_machine import SlotMachine
from shop import Shop
from guard import Guard
from roulette import Roulette
from dice_game import DiceGame
from score_system import ScoreSystem
from message_system import MessageSystem
from day_system import DaySystem

pygame.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gorilla Gambler")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

# SYSTEMS
player = Player(400, 300)
casino_map = CasinoMap()
time_system = TimeSystem()
slot_machine = SlotMachine()
shop = Shop()
roulette = Roulette()
dice_game = DiceGame()
score_system = ScoreSystem()
messages = MessageSystem()
day_system = DaySystem()

# GUARDS
guard_types = ["normal", "fast", "watcher", "lazy"]
guards = [
    Guard(300, 200, random.choice(guard_types)),
    Guard(500, 400, random.choice(guard_types)),
    Guard(700, 250, random.choice(guard_types))
]

difficulty = 1
difficulty_timer = 0

game_state = "exploring"
running = True

while running:

    clock.tick(60)

    messages.update()
    day_system.update()
    casino_map.update_cooldowns()

    score_system.add_survival_score()

    # ---------------- EVENTS ---------------- #

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # dice game controls
        if game_state == "dice":
            result = dice_game.handle_input(event, player, score_system, messages)

            if result == "exit":
                dice_game.reset()
                game_state = "exploring"

            continue

        if event.type == pygame.KEYDOWN and game_state == "exploring":

            if event.key == pygame.K_e:

                interaction = casino_map.check_interaction(player.get_rect())

                if interaction == "slots":

                    if casino_map.cooldowns["slots"] > 0:
                        messages.add("Machine cooling down", player.x, player.y)

                    else:
                        game_state = "slots"
                        casino_map.cooldowns["slots"] = 300

                elif interaction == "roulette":

                    if casino_map.cooldowns["roulette"] > 0:
                        messages.add("Roulette spinning", player.x, player.y)

                    else:
                        game_state = "roulette"
                        casino_map.cooldowns["roulette"] = 360

                elif interaction == "dice":

                    if casino_map.cooldowns["dice"] > 0:
                        messages.add("Table busy", player.x, player.y)

                    else:
                        dice_game.reset()
                        game_state = "dice"
                        casino_map.cooldowns["dice"] = 240

                elif interaction == "shop":
                    game_state = "shop"

                elif interaction == "exit":

                    if player.money >= day_system.debt:

                        player.money -= day_system.debt
                        day_system.next_day()

                        messages.add("Next Day!", player.x, player.y)

                    else:

                        print("You failed to pay the debt!")
                        print("FINAL SCORE:", score_system.score)
                        running = False

    # ---------------- GAME STATES ---------------- #

    if game_state == "slots":

        slot_machine.play(player, score_system, messages)
        game_state = "exploring"

    elif game_state == "dice":

        dice_game.update(player, score_system, messages)
        dice_game.draw(screen, player, day_system)

        pygame.display.update()
        continue

    elif game_state == "roulette":

        roulette.play(player, score_system, messages)
        game_state = "exploring"

    elif game_state == "shop":

        shop.open_shop(player)
        game_state = "exploring"

    # ---------------- PLAYER MOVEMENT ---------------- #

    if game_state == "exploring":

        keys = pygame.key.get_pressed()
        player.move(keys)

    # ---------------- DIFFICULTY SCALING ---------------- #

    difficulty_timer += 1

    if difficulty_timer > 1800:

        difficulty += 1

        for guard in guards:
            guard.update_speed(difficulty, messages, player)

        guards.append(
            Guard(
                random.randint(100, 700),
                random.randint(100, 700),
                "elite"
            )
        )

        difficulty_timer = 0

    # ---------------- GUARD AI ---------------- #

    for guard in guards:

        if day_system.closing:

            guard.state = "chase"
            guard.chase_player(player)

        else:

            guard.see_player(player, guards, messages)

            if guard.state == "chase":
                guard.chase_player(player)
            else:
                guard.move()

        # COLLISION → GAME OVER

        if player.get_rect().colliderect(pygame.Rect(guard.x, guard.y, 32, 32)):

            print("The guards caught the gorilla!")
            print("FINAL SCORE:", score_system.score)

            running = False

    # ---------------- DRAW ---------------- #

    screen.fill((30, 120, 30))

    casino_map.draw(screen)

    for guard in guards:
        guard.draw_vision(screen)

    player.draw(screen)

    for guard in guards:
        guard.draw(screen)
        guard.draw_detection(screen)

    time_system.draw(screen, player)

    messages.draw(screen)
    score_system.draw(screen)

    # UI

    time_left = day_system.get_time_seconds()

    day_text = font.render(f"Day: {day_system.day}", True, (255,255,255))
    time_text = font.render(f"Closing in: {time_left}", True, (255,200,200))
    debt_text = font.render(f"Debt: ${day_system.debt}", True, (255,150,150))

    screen.blit(day_text,(650,10))
    screen.blit(time_text,(650,40))
    screen.blit(debt_text,(650,70))

    pygame.display.update()

pygame.quit()