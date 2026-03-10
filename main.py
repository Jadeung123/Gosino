import pygame
import random
from player import Player
from map import CasinoMap
from time_system import TimeSystem
from slot_machine import SlotMachine
from shop import Shop
from suspicion_system import SuspicionSystem
from guard import Guard
from roulette import Roulette
from dice_game import DiceGame
from score_system import ScoreSystem
from message_system import MessageSystem

pygame.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gorilla Gambler")

clock = pygame.time.Clock()

player = Player(400, 300)
casino_map = CasinoMap()
time_system = TimeSystem()
slot_machine = SlotMachine()
shop = Shop()
suspicion = SuspicionSystem()
roulette = Roulette()
dice_game = DiceGame()
score_system = ScoreSystem()
messages = MessageSystem()

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

    #SCORE
    score_system.add_survival_score()
    score_system.add_risk_bonus(suspicion.level)

    # EVENTS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                interaction = casino_map.check_interaction(player.get_rect())
                if interaction == "slots":
                    game_state = "slots"
                elif interaction == "roulette":
                    game_state = "roulette"
                elif interaction == "dice":
                    game_state = "dice"
                elif interaction == "shop":
                    game_state = "shop"
    
    if game_state == "slots":
        slot_machine.play(player, score_system, messages)
        messages.add("Suspicion +5", player.x, player.y)
        suspicion.increase(5)
        game_state = "exploring"
    elif game_state == "dice":
        dice_game.play(player, score_system, messages)
        game_state = "exploring"
    elif game_state == "roulette":
        roulette.play(player, score_system, messages)
        game_state = "exploring"
    elif game_state == "shop":
        shop.open_shop(player)
        game_state = "exploring"

    difficulty_timer += 1
    if difficulty_timer > 1800:
        difficulty += 1
        guard.update_speed(difficulty, messages, player)
        guards.append(Guard(random.randint(100, 700), random.randint(100, 700), "elite"))
        difficulty_timer = 0

    # PLAYER MOVEMENT
    keys = pygame.key.get_pressed()
    moved = player.move(keys)

    if moved:
        time_system.add_time(1)

    # GUARD AI
    for guard in guards:
        guard.see_player(player, guards, messages)

        if guard.state == "chase":
            guard.chase_player(player)
            suspicion.increase(1)
        else:
            guard.move()

        # escape check
        distance = ((guard.x - player.x) ** 2 + (guard.y - player.y) ** 2) ** 0.5
        if distance > 250:
            guard.chasing = False

    # GAME OVER
    if suspicion.is_caught():
        print("Security caught the gorilla!")
        print("FINAL SCORE:", score_system.score)
        running = False

    # DRAW
    screen.fill((30, 120, 30))

    casino_map.draw(screen)

    for guard in guards:
        guard.draw_vision(screen)

    player.draw(screen)

    for guard in guards:
        guard.draw(screen)

    time_system.draw(screen, player)
    suspicion.draw(screen)
    messages.draw(screen)
    score_system.draw(screen)

    pygame.display.update()

pygame.quit()